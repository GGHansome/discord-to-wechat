#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息发送器抽象基类
定义统一的消息发送接口，方便扩展多种发送方式
"""

from abc import ABC, abstractmethod
from src.core.models import DiscordMessage
from zoneinfo import ZoneInfo
from datetime import datetime

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
    def send_message(self, message: DiscordMessage) -> bool:
        """
        发送消息
        :param message: Discord消息对象
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
    
    def format_message(self, message: DiscordMessage) -> str:
        """
        格式化消息内容（可被子类重写）
        :param message: Discord消息对象
        :return: 格式化后的消息文本
        """
        # 转换时间为北京时间
        try:
            if message.timestamp:
                # 假设已经是 datetime 对象（如果是字符串在 listener 里转换更好，这里做兜底）
                if isinstance(message.timestamp, str):
                    from dateutil import parser
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

        content = f"来自 {message.username} 消息\n"
        if message.channel_name:
             content += f"({message.channel_name})\n"
        content += f"🕐 时间: {bj_time_str}\n"
        content += f"━━━━━━━━━━━━\n"
        content += f"{message.content}\n"
        
        if message.attachments:
            content += f"\n📎 附件({len(message.attachments)}):\n"
            for i, att in enumerate(message.attachments[:3], 1):
                content += f"{i}. {att}\n"
        
        return content

