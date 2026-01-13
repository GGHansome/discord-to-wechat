
from datetime import datetime
from typing import Optional, List
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

from src.core.models import DiscordMessage
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DiscordParser:
    """Discord 消息解析器：负责从 DOM 元素中提取数据"""

    @staticmethod
    def parse_message(message_element, channel_url: str, channel_name: str) -> Optional[DiscordMessage]:
        """从消息元素中提取 DiscordMessage"""
        try:
            message_id = message_element.get_attribute('id')
            
            # 1. 提取用户名
            username = DiscordParser._extract_username(message_element)
            
            # 2. 提取内容
            content = DiscordParser._extract_content(message_element)
            
            # 3. 提取时间戳
            timestamp = DiscordParser._extract_timestamp(message_element)
            
            # 4. 提取附件
            attachments = DiscordParser._extract_attachments(message_element)
            
            # 内容兜底
            content = DiscordParser._finalize_content(content, attachments, message_element)

            return DiscordMessage(
                id=message_id,
                username=username,
                content=content,
                timestamp=timestamp,
                channel_url=channel_url,
                attachments=attachments,
                channel_name=channel_name
            )
            
        except Exception as e:
            logger.error(f"❌ 提取消息信息失败: {e}")
            return None

    @staticmethod
    def _extract_username(element) -> str:
        username = "未知用户"
        try:
            username_element = element.find_element(
                By.CSS_SELECTOR, 'h3[class*="header"] span[class*="username"]'
            )
            return username_element.text
        except (NoSuchElementException, StaleElementReferenceException):
            # 尝试回溯查找（针对连续消息）
            return DiscordParser._trace_back_username(element) or \
                   DiscordParser._extract_username_from_aria(element) or \
                   "未知用户"

    @staticmethod
    def _trace_back_username(element) -> Optional[str]:
        try:
            prev_items = element.find_elements(
                By.XPATH, 'preceding-sibling::li[starts-with(@id, "chat-messages-")]'
            )
            for prev in reversed(prev_items[-8:]):
                try:
                    el = prev.find_element(By.CSS_SELECTOR, 'h3[class*="header"] span[class*="username"]')
                    if el.text:
                        return el.text
                except Exception:
                    continue
        except Exception:
            pass
        return None

    @staticmethod
    def _extract_username_from_aria(element) -> Optional[str]:
        try:
            aria_label = element.get_attribute('aria-label')
            if aria_label:
                name = aria_label.split(',')[0].strip()
                if name: return name
        except Exception:
            pass
        return None

    @staticmethod
    def _extract_content(element) -> str:
        try:
            content_elements = element.find_elements(By.CSS_SELECTOR, 'div[class*="messageContent"]')
            if content_elements:
                return content_elements[-1].text
        except Exception:
            pass
        return "[无法获取消息内容]"

    @staticmethod
    def _extract_timestamp(element) -> datetime:
        try:
            time_element = element.find_element(By.CSS_SELECTOR, 'time')
            timestamp_str = time_element.get_attribute('datetime')
            if timestamp_str:
                from dateutil import parser
                return parser.isoparse(timestamp_str)
        except Exception:
            pass
        return datetime.now()

    @staticmethod
    def _extract_attachments(element) -> List[str]:
        attachments = []
        try:
            # 常规附件
            atts = element.find_elements(By.CSS_SELECTOR, 'a[class*="imageWrapper"], a[class*="attachment"]')
            for att in atts:
                href = att.get_attribute('href')
                if href: attachments.append(href)
            
            # CDN 兜底
            if not attachments:
                attachments.extend(DiscordParser._extract_cdn_links(element))
                
            # 去重
            if attachments:
                seen = set()
                attachments = [x for x in attachments if not (x in seen or seen.add(x))]
                
        except Exception:
            pass
        return attachments

    @staticmethod
    def _extract_cdn_links(element) -> List[str]:
        links = []
        cdn_hosts = ['cdn.discordapp.com', 'media.discordapp.net']
        exts = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.mp4', '.mov', '.webm']
        
        try:
            # Check a[href]
            all_links = element.find_elements(By.CSS_SELECTOR, 'a[href]')
            for link in all_links:
                href = (link.get_attribute('href') or '').strip()
                if not href: continue
                lower = href.lower()
                if (any(h in lower for h in cdn_hosts) and 
                   ('/attachments/' in lower or any(lower.endswith(e) for e in exts))):
                    links.append(href)
            
            # Check img[src] if empty
            if not links:
                all_imgs = element.find_elements(By.CSS_SELECTOR, 'img[src]')
                for img in all_imgs:
                    src = (img.get_attribute('src') or '').strip()
                    if not src: continue
                    lower = src.lower()
                    if any(h in lower for h in cdn_hosts) and '/attachments/' in lower:
                        links.append(src)
        except Exception:
            pass
        return links

    @staticmethod
    def _finalize_content(content: str, attachments: List[str], element) -> str:
        if content == "[无法获取消息内容]" or not content.strip():
            try:
                markup = element.find_elements(By.CSS_SELECTOR, 'div[class*="markup"]')
                if markup and markup[-1].text.strip():
                    content = markup[-1].text
            except Exception:
                pass
            
            if (not content or not content.strip()) and attachments:
                content = f"[附件 {len(attachments)} 个]"
        return content

