#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信机器人消息发送器
使用企业微信机器人Webhook API发送消息
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime
from dateutil import parser
from zoneinfo import ZoneInfo
from .base import MessageSender
from src.core.models import DiscordMessage
from src.utils.logger import get_logger

logger = get_logger(__name__)

class WorkingWechatSender(MessageSender):
    """企业微信机器人发送器"""
    
    def __init__(self, webhook_url: str = None, webhook_configs: List[Dict[str, str]] = None):
        """
        初始化企业微信机器人发送器
        :param webhook_url: 单个Webhook地址 (兼容旧版)
        :param webhook_configs: Webhook配置列表 [{'hook': '...', 'channel': '...'}]
        """
        super().__init__()
        self.webhook_url = webhook_url
        self.webhook_configs = webhook_configs or []
        self.webhook_map = {}
        
        # 建立频道到Webhook的映射
        if self.webhook_configs:
            for config in self.webhook_configs:
                hook = config.get('hook')
                channel = config.get('channel')
                if hook and channel:
                    # 去除可能的尾部斜杠以匹配
                    normalized_channel = channel.rstrip('/')
                    self.webhook_map[normalized_channel] = hook
    
    def login(self) -> bool:
        """
        验证Webhook地址是否有效
        :return: 是否验证成功
        """
        logger.info("\n" + "=" * 50)
        logger.info("🔐 正在初始化企业微信机器人...")
        logger.info("=" * 50)
        
        # 收集所有需要测试的Webhook
        hooks_to_test = set()
        if self.webhook_url and not "YOUR_WEBHOOK_KEY" in self.webhook_url:
            hooks_to_test.add(self.webhook_url)
        
        for config in self.webhook_configs:
            hook = config.get('hook')
            if hook and "YOUR_WEBHOOK_KEY" not in hook:
                hooks_to_test.add(hook)
        
        if not hooks_to_test:
            logger.error("❌ 请先配置企业微信机器人的Webhook地址")
            logger.error("提示：在企业微信群中添加机器人，获取Webhook地址")
            return False
            
        success_count = 0
        total_count = len(hooks_to_test)
        
        logger.info(f"正在验证 {total_count} 个Webhook地址...")
        
        for i, hook_url in enumerate(hooks_to_test, 1):
            try:
                # 发送测试消息验证连接
                test_data = {
                    "msgtype": "text",
                    "text": {
                        "content": f"✅ 企业微信机器人初始化成功 ({i}/{total_count})\nDiscord消息桥接器已启动"
                    }
                }
                
                response = requests.post(
                    hook_url,
                    json=test_data,
                    timeout=30
                )
                
                result = response.json()
                
                if result.get('errcode') == 0:
                    logger.info(f"✅ Webhook {i} 连接成功！")
                    success_count += 1
                else:
                    logger.error(f"❌ Webhook {i} 连接失败: {result.get('errmsg', '未知错误')}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Webhook {i} 连接失败: {e}")
            except Exception as e:
                logger.error(f"❌ Webhook {i} 初始化异常: {e}")
        
        if success_count > 0:
            logger.info(f"✅ 成功连接 {success_count}/{total_count} 个机器人的Webhook")
            self.is_ready = True
            return True
        else:
            logger.error("❌ 所有Webhook连接均失败")
            return False
    
    def get_webhook_for_channel(self, channel_url: str) -> Optional[str]:
        """根据频道URL获取对应的Webhook"""
        if not channel_url:
            return self.webhook_url
            
        # 尝试精确匹配
        normalized_url = channel_url.rstrip('/')
        if normalized_url in self.webhook_map:
            return self.webhook_map[normalized_url]
            
        # 如果没有特定匹配，但有默认的单个webhook，则使用它
        return self.webhook_url

    def send_message(self, message: DiscordMessage) -> bool:
        """
        发送消息到企业微信群
        :param message: Discord消息对象
        :return: 是否发送成功
        """
        if not self.is_ready:
            logger.warning("⚠️  企业微信机器人未就绪，跳过发送")
            return False
            
        target_webhook = self.get_webhook_for_channel(message.channel_url)
        
        if not target_webhook:
            logger.warning(f"⚠️  未找到频道 [{message.channel_name}] 对应的Webhook配置，且无默认Webhook")
            return False
            
        try:
            # 使用Markdown格式发送消息
            content = self._format_markdown_message(message)
            
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": content
                }
            }
            
            response = requests.post(
                target_webhook,
                json=data,
                timeout=10
            )
            
            result = response.json()
            
            if result.get('errcode') == 0:
                logger.info(f"✅ 消息已发送到企业微信: {message.content[:30]}...")
                return True
            else:
                logger.error(f"❌ 发送企业微信消息失败: {result.get('errmsg', '未知错误')}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 发送企业微信消息网络错误: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 发送企业微信消息异常: {e}")
            return False
    
    def _format_markdown_message(self, message: DiscordMessage) -> str:
        """
        格式化为Markdown消息
        :param message: Discord消息对象
        :return: Markdown格式的消息文本
        """
        # 解析 UTC 时间戳并转换为北京时间（Asia/Shanghai）
        try:
            if message.timestamp:
                if isinstance(message.timestamp, str):
                    bj_time = parser.isoparse(message.timestamp).astimezone(ZoneInfo('Asia/Shanghai'))
                elif isinstance(message.timestamp, datetime):
                     bj_time = message.timestamp.astimezone(ZoneInfo('Asia/Shanghai'))
                else:
                    bj_time = datetime.now(ZoneInfo('Asia/Shanghai'))
            else:
                bj_time = datetime.now(ZoneInfo('Asia/Shanghai'))
            bj_time_str = bj_time.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            bj_time_str = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')

        content = f"来自 **{message.username}** 消息"
        # if message.channel_name:
        #     content += f" ({message.channel_name})"
        content += f"\n"
        content += f"> 🕐 时间: {bj_time_str}\n\n"
        
        content += f"{message.content}\n"
        
        if message.attachments:
            content += f"\n**📎 附件({len(message.attachments)}):**\n"
            for i, att in enumerate(message.attachments[:3], 1):
                content += f"{i}. [{att}]({att})\n"
        
        return content
    
    def keep_alive(self):
        """
        企业微信机器人不需要保持心跳
        """
        pass
    
    def cleanup(self):
        """
        清理资源
        """
        try:
            logger.info("   ✅ 企业微信机器人发送器已清理")
        except Exception as e:
            logger.debug(f"   清理企业微信发送器失败: {e}")

