#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discord消息监听器
使用Selenium监听Discord频道的新消息
"""

import time
from typing import List, Callable, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.core.models import DiscordMessage
from src.utils.logger import get_logger
from src.services.listener.browser import BrowserManager
from src.services.listener.discord_parser import DiscordParser

logger = get_logger(__name__)


class DiscordListener:
    """Discord消息监听器"""
    
    def __init__(
        self,
        channel_urls: List[str],
        on_new_message: Callable[[DiscordMessage], None],
        check_interval: int = 3,
        headless_mode: bool = False
    ):
        """
        初始化Discord监听器
        :param channel_urls: Discord频道URL列表
        :param on_new_message: 新消息回调函数，参数为 (message: DiscordMessage)
        :param check_interval: 检查间隔（秒）
        :param headless_mode: 是否使用无头模式
        """
        self.channel_urls = channel_urls if isinstance(channel_urls, list) else [channel_urls]
        self.on_new_message = on_new_message
        self.check_interval = check_interval
        
        # 浏览器管理器
        self.browser_manager = BrowserManager(headless_mode)
        self.driver = None
        
        # 为每个频道维护独立的最后消息ID
        self.last_message_ids = {url: None for url in self.channel_urls}
        # 为每个频道维护独立的浏览器标签页句柄（window handle）
        self.channel_handles = {}
    
    def init_chrome(self):
        """初始化Chrome浏览器"""
        self.driver = self.browser_manager.init_chrome()
    
    def login_discord(self):
        """登录Discord（首次需要手动登录）"""
        logger.info("⏳ 正在打开Discord...")
        self.driver.get('https://discord.com/login')
        
        # 检查是否已经登录
        time.sleep(3)
        current_url = self.driver.current_url
        
        if 'login' in current_url:
            logger.info("⚠️  请在浏览器中登录Discord...")
            logger.info("   提示：登录后会自动保存登录状态，下次不用再登录")
            logger.info("   🌐 如果使用Docker，请访问 http://localhost:7900 在noVNC中登录")
            logger.info("   🔑 noVNC默认密码: secret")
            
            # 等待用户登录完成
            while 'login' in self.driver.current_url:
                time.sleep(2)
            
            logger.info("✅ Discord登录成功！")
            logger.info("⏳ 正在保存登录状态，请稍候...")
            # 登录成功后多等待几秒，确保Chrome有足够时间将会话数据写入磁盘
            time.sleep(8)
            logger.info("✅ 登录状态已保存")
        else:
            logger.info("✅ Discord已经登录，跳过登录步骤")
        
        # 等待几秒让页面完全加载
        time.sleep(3)
    
    def restart_browser(self):
        """重启浏览器并重新登录"""
        logger.info("♻️ 正在重启浏览器...")
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass
            
        self.channel_handles = {}
        self.init_chrome()
        self.login_discord()
        logger.info("✅ 浏览器重启完成")

    def navigate_to_channel(self, channel_url: Optional[str] = None):
        """打开/切换到指定频道"""
        if channel_url:
            self.switch_to_channel(channel_url)
        else:
            # 初始化打开所有频道
            logger.info(f"⏳ 正在打开 {len(self.channel_urls)} 个频道...")
            for idx, url in enumerate(self.channel_urls, 1):
                logger.info(f"   [{idx}/{len(self.channel_urls)}] {url}")
                self.switch_to_channel(url)
                # 稍微等待，避免操作过快
                time.sleep(2)

            # 切回第一个频道
            if self.channel_urls:
                self.switch_to_channel(self.channel_urls[0])
            logger.info("✅ 频道已成功打开")

    def switch_to_channel(self, channel_url: str) -> bool:
        """切换到指定频道对应的标签页"""
        try:
            # 1. 尝试直接使用缓存的句柄
            handle = self.channel_handles.get(channel_url)
            # 句柄存在且有效
            if handle and handle in self.driver.window_handles:
                # 获取当前窗口句柄，如果当前窗口已关闭，设为 None
                try:
                    current_handle = self.driver.current_window_handle
                except Exception:
                    current_handle = None

                if current_handle != handle:
                    logger.info("⏳ 正在切换到频道标签页...")
                    # logger.info(f"   URL: {channel_url}")
                    self.driver.switch_to.window(handle)
                    time.sleep(0.1)
                return True

            # 2. 尝试通过已开启的标签页反查URL匹配的句柄
            # for h in self.driver.window_handles:
            #     try:
            #         self.driver.switch_to.window(h)
            #         current = (self.driver.current_url or '').strip()
            #         if current.startswith(channel_url) or channel_url in current:
            #             self.channel_handles[channel_url] = h
            #             return True
            #     except Exception:
            #         continue
            # 2. (已移除) 不需要反查现有标签页，直接根据缓存或新建
            # 这里的反查逻辑会导致每次打开新频道时都遍历旧标签页，造成不必要的切换和闪烁。
            # 既然是自动化程序，我们假设状态由程序控制，直接进入步骤 3 进行打开/新建。
            # 它唯一的用处是：如果你的浏览器崩溃重启了，并且自动恢复了上次打开的 5 个频道标签页。
            # 此时程序重启，通过“反查”可以直接复用这 5 个标签页，而不用新开 5 个。

            # 3. 未找到则需要打开
            # 如果是第一个初始化的频道（还没有任何句柄记录），则复用当前页面（如登录后的页面）
            if not self.channel_handles:
                logger.info(f"⏳ 初始化频道，覆盖当前页面: {channel_url}")
                self.driver.get(channel_url)
                self.channel_handles[channel_url] = self.driver.current_window_handle
                time.sleep(1)
                return True

            # 否则新建标签页
            logger.info("⏳ 未找到频道标签页，正在新建...")
            logger.info(f"   URL: {channel_url}")
            
            # 确保在打开新窗口前有一个有效的上下文
            # 如果当前窗口已关闭（例如用户手动关闭了标签页），switch_to.new_window 可能会失败
            try:
                self.driver.current_window_handle
            except Exception:
                # 当前窗口句柄失效，尝试切换到任意存在的窗口
                try:
                    if self.driver.window_handles:
                        self.driver.switch_to.window(self.driver.window_handles[0])
                except Exception:
                    pass

            # 遍历所有句柄查找未被记录的
            # === 使用 Selenium 4 新 API ===
            self.driver.switch_to.new_window('tab')
            self.driver.get(channel_url)
            self.channel_handles[channel_url] = self.driver.current_window_handle
            
            return True
        except Exception as e:
            logger.error(f"切换频道标签页失败: {e}")
            return False
    
    def get_channel_name(self, channel_url: str) -> str:
        """从URL中提取频道标识"""
        try:
            parts = channel_url.rstrip('/').split('/')
            if len(parts) >= 2:
                return f"频道{parts[-1]}"
            return "未知频道"
        except:
            return "未知频道"
    
    def monitor_messages(self):
        """监控Discord消息"""
        logger.info("✅ 所有准备工作已完成，开始监控消息...")
        logger.info(f"💡 正在监控 {len(self.channel_urls)} 个频道")
        
        # 为每个频道维护独立的错误计数器
        channel_errors = {url: 0 for url in self.channel_urls}
        max_errors = 5
        
        while True:
            for channel_idx, channel_url in enumerate(self.channel_urls):
                try:
                    if not self.switch_to_channel(channel_url):
                        # 主动抛出异常，以便触发下方的错误计数和恢复逻辑
                        raise Exception("无法切换到频道标签页 (Switch failed)")
                    
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'li[id^="chat-messages-"]'))
                    )
                    
                    messages = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        'li[id^="chat-messages-"]'
                    )
                    
                    if messages:
                        new_messages = []
                        found_last = False
                        last_message_id = self.last_message_ids[channel_url]
                        
                        if last_message_id is None:
                            new_messages = [messages[-1]]
                            logger.info(f"🎬 频道 [{channel_idx + 1}/{len(self.channel_urls)}] 首次运行，从最新消息开始监控")
                        else:
                            for message in messages:
                                msg_id = message.get_attribute('id')
                                if msg_id == last_message_id:
                                    found_last = True
                                    continue
                                if found_last:
                                    new_messages.append(message)
                            
                            if not found_last and len(new_messages) == 0:
                                last_msg_id = messages[-1].get_attribute('id')
                                if last_msg_id != last_message_id:
                                    new_messages = [messages[-1]]
                                    logger.info(f"⚠️  频道 [{channel_idx + 1}] 未找到上次消息记录，可能页面已刷新")
                        
                        if new_messages:
                            if len(new_messages) > 1:
                                logger.info(f"📬 频道 [{channel_idx + 1}] 发现 {len(new_messages)} 条新消息，依次处理中...")
                            
                            for idx, message_element in enumerate(new_messages, 1):
                                # 确保元素可见以便提取信息（Parser内部不再处理滚动，交由Parser调用前确保可见？
                                # 或者保留滚动逻辑在这里，或者在Parser里做。
                                # 最佳实践：Listener负责交互(滚动)，Parser负责提取。
                                try:
                                    self.driver.execute_script(
                                        "arguments[0].scrollIntoView({block: 'nearest'});",
                                        message_element
                                    )
                                    time.sleep(0.05)
                                except Exception:
                                    pass

                                # 提取消息并构建 DiscordMessage 对象
                                channel_name = self.get_channel_name(channel_url)
                                msg_obj = DiscordParser.parse_message(message_element, channel_url, channel_name)
                                
                                if msg_obj:
                                    if len(new_messages) > 1:
                                        logger.info(f"\n📨 频道 [{channel_idx + 1}] 新消息 [{idx}/{len(new_messages)}]:")
                                    else:
                                        logger.info(f"\n📨 频道 [{channel_idx + 1}] 新消息:")
                                    logger.info(f"   用户: {msg_obj.username}")
                                    logger.info(f"   内容: {msg_obj.content[:50]}...")
                                    
                                    # 回调
                                    self.on_new_message(msg_obj)
                                    
                                    self.last_message_ids[channel_url] = msg_obj.id
                                    
                                    if len(new_messages) > 1 and idx < len(new_messages):
                                        time.sleep(0.5)
                    
                    # 成功执行，重置该频道的错误计数
                    channel_errors[channel_url] = 0
                    
                except Exception as e:
                    channel_errors[channel_url] += 1
                    current_errors = channel_errors[channel_url]
                    logger.error(f"⚠️  频道 [{channel_idx + 1}] 监控错误 ({current_errors}/{max_errors}): {e}")
                    
                    if current_errors >= max_errors:
                        logger.warning(f"❌ 频道 [{channel_idx + 1}] 错误次数过多，尝试重新加载页面...")
                        try:
                            self.driver.refresh()
                            time.sleep(5)
                            channel_errors[channel_url] = 0
                        except Exception as refresh_error:
                            logger.error(f"页面刷新失败，可能是标签页崩溃: {refresh_error}")
                            
                            # 检查浏览器是否完全崩溃/关闭
                            is_fatal = False
                            try:
                                if not self.driver.window_handles:
                                    is_fatal = True
                            except Exception:
                                is_fatal = True
                            
                            if is_fatal:
                                logger.error("🔥 检测到浏览器已关闭或崩溃，正在重启...")
                                self.restart_browser()
                                break # 跳出 for 循环，重新开始 while 循环

                            logger.info("♻️ 尝试移除失效句柄，下次将重新打开该频道...")
                            
                            # 移除失效句柄，触发重新打开逻辑
                            if channel_url in self.channel_handles:
                                del self.channel_handles[channel_url]
                            
                            # 尝试关闭崩溃的标签页
                            try:
                                self.driver.close()
                            except:
                                pass
                                
                            # 重置错误计数
                            channel_errors[channel_url] = 0
                            
                            # 尝试切回第一个可用窗口
                            try:
                                if len(self.driver.window_handles) > 0:
                                    self.driver.switch_to.window(self.driver.window_handles[0])
                            except:
                                pass
                    
                    time.sleep(5)
            
            time.sleep(self.check_interval)
    
    def cleanup(self):
        """清理资源"""
        if self.browser_manager:
            self.browser_manager.cleanup()
