#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息发送器抽象基类
定义统一的消息发送接口，方便扩展多种发送方式
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class MessageSender(ABC):
    """消息发送器抽象基类"""
    
    def __init__(self):
        """初始化发送器"""
        self.is_ready = False
    
    @abstractmethod
    def login(self) -> bool:
        """
        登录/初始化发送器
        :return: 是否成功
        """
        pass
    
    @abstractmethod
    def send_message(self, message_info: Dict[str, Any], channel_name: str = "") -> bool:
        """
        发送消息
        :param message_info: 消息信息字典，包含 username, content, timestamp, attachments 等
        :param channel_name: 频道名称
        :return: 是否发送成功
        """
        pass
    
    @abstractmethod
    def keep_alive(self):
        """
        保持连接活跃（如果需要）
        某些发送器需要在后台线程保持心跳
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """
        清理资源
        """
        pass
    
    def format_message(self, message_info: Dict[str, Any], channel_name: str = "") -> str:
        """
        格式化消息内容（可被子类重写）
        :param message_info: 消息信息
        :param channel_name: 频道名称
        :return: 格式化后的消息文本
        """
        from datetime import datetime
        
        username = message_info.get('username', '未知用户')
        content = f"来自 {username} 消息\n"
        content += f"🕐 时间: {datetime.now().strftime('%H:%M:%S')}\n"
        content += f"━━━━━━━━━━━━\n"
        content += f"{message_info.get('content', '')}\n"
        
        attachments = message_info.get('attachments', [])
        if attachments:
            content += f"\n📎 附件({len(attachments)}):\n"
            for i, att in enumerate(attachments[:3], 1):
                content += f"{i}. {att}\n"
        
        return content

