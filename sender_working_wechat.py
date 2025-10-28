#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信机器人消息发送器
使用企业微信机器人Webhook API发送消息
"""

import logging
import requests
from typing import Dict, Any
from datetime import datetime
from message_sender import MessageSender

logger = logging.getLogger(__name__)


class WorkingWechatSender(MessageSender):
    """企业微信机器人发送器"""
    
    def __init__(self, webhook_url: str):
        """
        初始化企业微信机器人发送器
        :param webhook_url: 企业微信机器人的Webhook地址
        """
        super().__init__()
        self.webhook_url = webhook_url
    
    def login(self) -> bool:
        """
        验证Webhook地址是否有效
        :return: 是否验证成功
        """
        logger.info("\n" + "=" * 50)
        logger.info("🔐 正在初始化企业微信机器人...")
        logger.info("=" * 50)
        
        if not self.webhook_url or "YOUR_WEBHOOK_KEY" in self.webhook_url:
            logger.error("❌ 请先配置企业微信机器人的Webhook地址")
            logger.error("提示：在企业微信群中添加机器人，获取Webhook地址")
            return False
        
        try:
            # 发送测试消息验证连接
            test_data = {
                "msgtype": "text",
                "text": {
                    "content": "✅ 企业微信机器人初始化成功\nDiscord消息桥接器已启动"
                }
            }
            
            response = requests.post(
                self.webhook_url,
                json=test_data,
                timeout=10
            )
            
            result = response.json()
            
            if result.get('errcode') == 0:
                logger.info("✅ 企业微信机器人连接成功！")
                self.is_ready = True
                return True
            else:
                logger.error(f"❌ 企业微信机器人连接失败: {result.get('errmsg', '未知错误')}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 企业微信机器人连接失败: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 企业微信机器人初始化异常: {e}")
            return False
    
    def send_message(self, message_info: Dict[str, Any], channel_name: str = "") -> bool:
        """
        发送消息到企业微信群
        :param message_info: 消息信息
        :param channel_name: 频道名称
        :return: 是否发送成功
        """
        if not self.is_ready:
            logger.warning("⚠️  企业微信机器人未就绪，跳过发送")
            return False
        
        try:
            # 使用Markdown格式发送消息
            content = self._format_markdown_message(message_info, channel_name)
            
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": content
                }
            }
            
            response = requests.post(
                self.webhook_url,
                json=data,
                timeout=10
            )
            
            result = response.json()
            
            if result.get('errcode') == 0:
                logger.info(f"✅ 消息已发送到企业微信: {message_info['content'][:30]}...")
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
    
    def _format_markdown_message(self, message_info: Dict[str, Any], channel_name: str = "") -> str:
        """
        格式化为Markdown消息
        :param message_info: 消息信息
        :param channel_name: 频道名称
        :return: Markdown格式的消息文本
        """
        username = message_info.get('username', '未知用户')
        content = f"来自 **{username}** 消息\n"
        content += f"> 🕐 时间: {datetime.now().strftime('%H:%M:%S')}\n\n"
        
        content += f"{message_info.get('content', '')}\n"
        
        attachments = message_info.get('attachments', [])
        if attachments:
            content += f"\n**📎 附件({len(attachments)}):**\n"
            for i, att in enumerate(attachments[:3], 1):
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

