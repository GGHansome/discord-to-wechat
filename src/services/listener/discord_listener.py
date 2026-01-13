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
            logger.info("   🔑 noVNC密码: secret")
            
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
    
    def navigate_to_channel(self, channel_url: Optional[str] = None):
        """打开/切换到指定频道"""
        if channel_url:
            self.switch_to_channel(channel_url)
        else:
            self.open_all_channels_in_tabs()

    def open_all_channels_in_tabs(self):
        """将所有频道分别在独立标签页中打开并记录句柄"""
        logger.info(f"⏳ 正在打开 {len(self.channel_urls)} 个频道...")
        for idx, url in enumerate(self.channel_urls, 1):
            logger.info(f"   [{idx}/{len(self.channel_urls)}] {url}")
            if idx == 1:
                # 第一个频道使用当前标签页
                self.driver.get(url)
                time.sleep(5)
                self.channel_handles[url] = self.driver.current_window_handle
            else:
                try:
                    # 直接新开标签并导航到该URL
                    self.driver.execute_script("window.open(arguments[0], '_blank');", url)
                    time.sleep(1)
                    # 取出新增的句柄
                    known_handles = set(self.channel_handles.values())
                    for handle in self.driver.window_handles:
                        if handle not in known_handles:
                            self.driver.switch_to.window(handle)
                            break
                    # 记录该频道的句柄
                    self.channel_handles[url] = self.driver.current_window_handle
                    # 等待频道主要消息节点出现
                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'li[id^="chat-messages-"]'))
                        )
                    except Exception:
                        pass
                except Exception as e:
                    logger.warning(f"打开频道标签页失败，回退为当前页导航: {e}")
                    self.driver.get(url)
                    time.sleep(3)
                    self.channel_handles[url] = self.driver.current_window_handle
        # 切回第一个频道
        first_handle = self.channel_handles.get(self.channel_urls[0])
        if first_handle:
            try:
                self.driver.switch_to.window(first_handle)
            except Exception:
                pass
        logger.info("✅ 频道已成功打开")

    def switch_to_channel(self, channel_url: str) -> bool:
        """切换到指定频道对应的标签页"""
        try:
            handle = self.channel_handles.get(channel_url)
            # 句柄存在且有效
            if handle and handle in self.driver.window_handles:
                if self.driver.current_window_handle != handle:
                    logger.info("⏳ 正在切换到频道标签页...")
                    logger.info(f"   URL: {channel_url}")
                    self.driver.switch_to.window(handle)
                    time.sleep(0.1)
                return True

            # 尝试通过已开启的标签页反查URL匹配的句柄
            for h in self.driver.window_handles:
                try:
                    self.driver.switch_to.window(h)
                    current = (self.driver.current_url or '').strip()
                    if current.startswith(channel_url) or channel_url in current:
                        self.channel_handles[channel_url] = h
                        return True
                except Exception:
                    continue

            # 未找到则新开标签页
            logger.info("⏳ 未找到频道标签页，正在新建...")
            logger.info(f"   URL: {channel_url}")
            self.driver.execute_script("window.open(arguments[0], '_blank');", channel_url)
            time.sleep(1)
            # 记录新句柄
            for h in self.driver.window_handles:
                if h not in self.channel_handles.values():
                    try:
                        self.driver.switch_to.window(h)
                        self.channel_handles[channel_url] = h
                        break
                    except Exception:
                        continue
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
        
        error_count = 0
        max_errors = 5
        
        while True:
            for channel_idx, channel_url in enumerate(self.channel_urls):
                try:
                    if not self.switch_to_channel(channel_url):
                        logger.warning(f"无法切换到频道 [{channel_idx + 1}]，跳过本轮")
                        continue
                    
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
                    
                    error_count = 0
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"⚠️  频道 [{channel_idx + 1}] 监控错误 ({error_count}/{max_errors}): {e}")
                    
                    if error_count >= max_errors:
                        logger.warning("❌ 错误次数过多，尝试重新加载页面...")
                        try:
                            self.driver.refresh()
                            time.sleep(5)
                            error_count = 0
                        except:
                            logger.error("页面刷新失败，将在10秒后重试")
                    
                    time.sleep(5)
            
            time.sleep(self.check_interval)
    
    def cleanup(self):
        """清理资源"""
        if self.browser_manager:
            self.browser_manager.cleanup()
