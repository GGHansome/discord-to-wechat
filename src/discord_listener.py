#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discord消息监听器
使用Selenium监听Discord频道的新消息
"""

import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
import subprocess

logger = logging.getLogger(__name__)


class DiscordListener:
    """Discord消息监听器"""
    
    def __init__(
        self,
        channel_urls: List[str],
        on_new_message: Callable[[Dict[str, Any], str], None],
        check_interval: int = 3,
        headless_mode: bool = False
    ):
        """
        初始化Discord监听器
        :param channel_urls: Discord频道URL列表
        :param on_new_message: 新消息回调函数，参数为 (message_info, channel_url)
        :param check_interval: 检查间隔（秒）
        :param headless_mode: 是否使用无头模式
        """
        self.channel_urls = channel_urls if isinstance(channel_urls, list) else [channel_urls]
        self.on_new_message = on_new_message
        self.check_interval = check_interval
        self.headless_mode = headless_mode
        self.driver = None
        # 为每个频道维护独立的最后消息ID
        self.last_message_ids = {url: None for url in self.channel_urls}
        # 为每个频道维护独立的浏览器标签页句柄（window handle）
        self.channel_handles = {}
    
    def init_chrome(self):
        """初始化Chrome浏览器"""
        logger.info("⏳ 正在配置Chrome浏览器...")
        
        chrome_options = Options()
        
        # 无头模式配置
        if self.headless_mode:
            chrome_options.add_argument('--headless=new')
            logger.info("   使用无头模式运行")
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--no-zygote')
        chrome_options.add_argument('--single-process')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor,UseOzonePlatform')
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # 设置用户数据目录，保存登录状态
        chrome_options.add_argument('--user-data-dir=./chrome_data')
        
        # 禁用一些不必要的功能
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 优先使用 Selenium Manager 自动管理驱动，避免第三方驱动管理带来的兼容问题
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            logger.error(f"   通过 Selenium Manager 启动失败: {e}")
            logger.info("   回退到系统 chromedriver...")
            # 回退到系统已有的 chromedriver（若存在）。优先查 PATH，否则使用常见路径。
            try:
                import shutil
                chromedriver_path = shutil.which('chromedriver') or '/usr/bin/chromedriver'
                self.driver = webdriver.Chrome(service=Service(executable_path=chromedriver_path), options=chrome_options)
            except Exception as e2:
                logger.error(f"   使用系统 chromedriver 启动失败: {e2}")
                raise
        
        logger.info("✅ Chrome浏览器已成功启动")
    
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
            
            # 等待用户登录完成
            while 'login' in self.driver.current_url:
                time.sleep(2)
            
            logger.info("✅ Discord登录成功！")
        else:
            logger.info("✅ Discord已经登录，跳过登录步骤")
        
        # 等待几秒让页面完全加载
        time.sleep(3)
    
    def navigate_to_channel(self, channel_url: Optional[str] = None):
        """
        打开/切换到指定频道。
        - 如果提供 channel_url：切换到该频道所在的标签页（不存在则新开标签页）
        - 如果不提供：将所有频道分别打开在独立标签页
        :param channel_url: 频道URL，如果为None则为首次批量打开
        """
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
        # 切回第一个频道，保持一致性
        first_handle = self.channel_handles.get(self.channel_urls[0])
        if first_handle:
            try:
                self.driver.switch_to.window(first_handle)
            except Exception:
                pass
        logger.info("✅ 频道已成功打开")

    def switch_to_channel(self, channel_url: str) -> bool:
        """切换到指定频道对应的标签页，不存在则创建。返回是否成功。"""
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
    
    def extract_message_info(self, message_element) -> Optional[Dict[str, Any]]:
        """
        提取消息信息
        :param message_element: 消息DOM元素
        :return: 消息信息字典
        """
        try:
            # 获取消息ID
            message_id = message_element.get_attribute('id')
            # 将消息滚动到视口，触发懒加载并尽量避免虚拟化导致的元素未渲染
            try:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'nearest'});",
                    message_element
                )
                time.sleep(0.05)
                # 按 ID 重新获取一次元素，规避 StaleElementReference
                if message_id:
                    try:
                        fresh_el = self.driver.find_element(By.ID, message_id)
                        if fresh_el:
                            message_element = fresh_el
                    except Exception:
                        pass
            except Exception:
                pass
            
            # 获取用户名
            try:
                # 仅从消息头部(h3.header)中获取用户名，避免误取“回复预览”的用户名
                username_element = message_element.find_element(
                    By.CSS_SELECTOR,
                    'h3[class*="header"] span[class*="username"]'
                )
                username = username_element.text
            except (NoSuchElementException, StaleElementReferenceException) as e:
                logger.debug(f"获取用户名失败: {e}")
                # 若当前消息未显示用户名（同一用户连续消息），回溯上一条有用户名的消息
                username = None
                try:
                    prev_items = message_element.find_elements(
                        By.XPATH,
                        'preceding-sibling::li[starts-with(@id, "chat-messages-")]'
                    )
                    for prev in reversed(prev_items[-8:]):  # 限制最多回溯8条
                        try:
                            prev_username_el = prev.find_element(
                                By.CSS_SELECTOR,
                                'h3[class*="header"] span[class*="username"]'
                            )
                            text_value = prev_username_el.text
                            if text_value:
                                username = text_value
                                break
                        except Exception:
                            continue
                except Exception:
                    pass
                # 如果依然没有，从 aria-label 兜底解析用户名（格式通常为："用户名, 时间, 内容..."）
                if not username:
                    try:
                        aria_label = message_element.get_attribute('aria-label')
                        if aria_label:
                            username_from_aria = aria_label.split(',')[0].strip()
                            if username_from_aria:
                                username = username_from_aria
                    except Exception:
                        pass
                if not username:
                    username = "未知用户"
            
            # 获取消息内容
            try:
                # 使用最后一个 messageContent 作为正文，避免误取“回复预览”中的内容
                content_elements = message_element.find_elements(
                    By.CSS_SELECTOR,
                    'div[class*="messageContent"]'
                )
                if content_elements:
                    content = content_elements[-1].text
                else:
                    raise NoSuchElementException('未找到messageContent')
            except (NoSuchElementException, StaleElementReferenceException) as e:
                logger.debug(f"获取消息内容失败: {e}")
                content = "[无法获取消息内容]"
            
            # 获取时间戳
            try:
                time_element = message_element.find_element(
                    By.CSS_SELECTOR,
                    'time'
                )
                timestamp = time_element.get_attribute('datetime')
            except (NoSuchElementException, StaleElementReferenceException) as e:
                logger.debug(f"获取时间戳失败: {e}")
                timestamp = datetime.now().isoformat()
            
            # 获取附件
            attachments = []
            try:
                # 尝试 1：常见的附件/图片外层 a 标签
                attachment_elements = message_element.find_elements(
                    By.CSS_SELECTOR,
                    'a[class*="imageWrapper"], a[class*="attachment"]'
                )
                for att in attachment_elements:
                    href = att.get_attribute('href')
                    if href:
                        attachments.append(href)
            except (NoSuchElementException, StaleElementReferenceException) as e:
                logger.debug(f"获取附件失败: {e}")
            
            # 兜底：更通用地从 a[href] 与 img[src] 中提取 Discord CDN 的资源
            try:
                if not attachments:
                    cdn_hosts = ['cdn.discordapp.com', 'media.discordapp.net']
                    image_video_exts = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.mp4', '.mov', '.webm']
                    # a[href]
                    all_links = message_element.find_elements(By.CSS_SELECTOR, 'a[href]')
                    for link in all_links:
                        href = (link.get_attribute('href') or '').strip()
                        if not href:
                            continue
                        lower_href = href.lower()
                        if (any(host in lower_href for host in cdn_hosts) and ('/attachments/' in lower_href or any(lower_href.endswith(ext) for ext in image_video_exts))):
                            attachments.append(href)
                    # img[src]
                    if not attachments:
                        all_imgs = message_element.find_elements(By.CSS_SELECTOR, 'img[src]')
                        for img in all_imgs:
                            src = (img.get_attribute('src') or '').strip()
                            if not src:
                                continue
                            lower_src = src.lower()
                            # 过滤表情等非附件资源，仅保留 attachments 路径下的资源
                            if any(host in lower_src for host in cdn_hosts) and '/attachments/' in lower_src:
                                attachments.append(src)
                # 去重，保持顺序
                if attachments:
                    seen = set()
                    attachments = [x for x in attachments if not (x in seen or seen.add(x))]
            except Exception:
                pass
            
            # 文本为空时做兜底：尝试从常见 markup 节点取值，或仅附件占位
            try:
                if not content or not content.strip() or content == "[无法获取消息内容]":
                    try:
                        markup_nodes = message_element.find_elements(
                            By.CSS_SELECTOR,
                            'div[class*="markup"]'
                        )
                        if markup_nodes:
                            fallback_text = markup_nodes[-1].text
                            if fallback_text and fallback_text.strip():
                                content = fallback_text
                    except Exception:
                        pass
                    if (not content or not content.strip()) and attachments:
                        content = f"[附件 {len(attachments)} 个]"
            except Exception:
                pass
            
            return {
                'id': message_id,
                'username': username,
                'content': content,
                'timestamp': timestamp,
                'attachments': attachments
            }
        except Exception as e:
            logger.error(f"❌ 提取消息信息失败: {e}")
            return None
    
    def get_channel_name(self, channel_url: str) -> str:
        """
        从URL中提取频道标识
        :param channel_url: 频道URL
        :return: 频道名称
        """
        try:
            parts = channel_url.rstrip('/').split('/')
            if len(parts) >= 2:
                return f"频道{parts[-1]}"
            return "未知频道"
        except:
            return "未知频道"
    
    def monitor_messages(self):
        """监控Discord消息（支持多频道）"""
        logger.info("✅ 所有准备工作已完成，开始监控消息...")
        logger.info(f"💡 正在监控 {len(self.channel_urls)} 个频道")
        logger.info("💡 提示：有新消息时会自动转发")
        logger.info("💡 按 Ctrl+C 可以退出程序\n")
        
        error_count = 0
        max_errors = 5
        
        while True:
            # 遍历所有频道
            for channel_idx, channel_url in enumerate(self.channel_urls):
                try:
                    # 切换到当前频道的标签页（不做整页导航）
                    if not self.switch_to_channel(channel_url):
                        logger.warning(f"无法切换到频道 [{channel_idx + 1}]，跳过本轮")
                        continue
                    
                    # 等待消息列表加载
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'li[id^="chat-messages-"]'))
                    )
                    
                    # 获取所有消息
                    messages = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        'li[id^="chat-messages-"]'
                    )
                    
                    if messages:
                        # 找出所有新消息
                        new_messages = []
                        found_last = False
                        last_message_id = self.last_message_ids[channel_url]
                        
                        if last_message_id is None:
                            # 首次运行，只处理最后一条消息（避免重复发送历史消息）
                            new_messages = [messages[-1]]
                            logger.info(f"🎬 频道 [{channel_idx + 1}/{len(self.channel_urls)}] 首次运行，从最新消息开始监控")
                        else:
                            # 找到上次处理的消息位置，收集之后的所有新消息
                            for message in messages:
                                msg_id = message.get_attribute('id')
                                
                                if msg_id == last_message_id:
                                    found_last = True
                                    continue
                                
                                # 收集上次消息之后的所有消息
                                if found_last:
                                    new_messages.append(message)
                            
                            # 如果没找到上次的消息（可能被滚动出视野或页面刷新）
                            if not found_last and len(new_messages) == 0:
                                # 只处理最后一条，避免重复发送大量历史消息
                                last_msg_id = messages[-1].get_attribute('id')
                                if last_msg_id != last_message_id:
                                    new_messages = [messages[-1]]
                                    logger.info(f"⚠️  频道 [{channel_idx + 1}] 未找到上次消息记录，可能页面已刷新")
                        
                        # 按顺序处理所有新消息
                        if new_messages:
                            if len(new_messages) > 1:
                                logger.info(f"📬 频道 [{channel_idx + 1}] 发现 {len(new_messages)} 条新消息，依次处理中...")
                            
                            for idx, message in enumerate(new_messages, 1):
                                message_info = self.extract_message_info(message)
                                
                                if message_info:
                                    if len(new_messages) > 1:
                                        logger.info(f"\n📨 频道 [{channel_idx + 1}] 新消息 [{idx}/{len(new_messages)}]:")
                                    else:
                                        logger.info(f"\n📨 频道 [{channel_idx + 1}] 新消息:")
                                    logger.info(f"   用户: {message_info['username']}")
                                    logger.info(f"   内容: {message_info['content'][:50]}...")
                                    
                                    # 调用回调函数处理消息
                                    channel_name = self.get_channel_name(channel_url)
                                    self.on_new_message(message_info, channel_name)
                                    
                                    # 更新该频道最后处理的消息ID
                                    self.last_message_ids[channel_url] = message_info['id']
                                    
                                    # 如果是批量处理，稍微延迟一下避免刷屏
                                    if len(new_messages) > 1 and idx < len(new_messages):
                                        time.sleep(0.5)
                    
                    # 重置错误计数
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
            
            # 完成一轮所有频道的检查后，等待一段时间再进行下一轮
            time.sleep(self.check_interval)
    
    def cleanup(self):
        """清理资源"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("   ✅ Chrome浏览器已关闭")
            except Exception as e:
                logger.debug(f"   关闭Chrome失败: {e}")
                # 遇到 chromedriver 无法优雅退出时，尝试强制终止残留进程（macOS）
                try:
                    service = getattr(self.driver, 'service', None)
                    proc = getattr(service, 'process', None) if service else None
                    if proc:
                        try:
                            proc.terminate()
                        except Exception:
                            pass
                        try:
                            proc.kill()
                        except Exception:
                            pass
                except Exception:
                    pass
                # 最后一招：直接杀掉可能残留的 chromedriver 进程
                try:
                    subprocess.run(["pkill", "-f", "chromedriver"], check=False)
                except Exception:
                    pass

