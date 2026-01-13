#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信个人号消息发送器
使用itchat实现微信个人号消息发送功能
"""

import logging
import threading
import itchat
from typing import Dict, Any
from .message_sender import MessageSender

logger = logging.getLogger(__name__)


class WechatSender(MessageSender):
    """微信个人号发送器"""
    
    def __init__(self, receiver_name: str):
        """
        初始化微信发送器
        :param receiver_name: 接收者的备注名或昵称
        """
        super().__init__()
        self.receiver_name = receiver_name
        self.receiver = None
        self.wechat_thread = None
    
    def login(self) -> bool:
        """
        登录微信（扫码登录）
        :return: 是否登录成功
        """
        logger.info("\n" + "=" * 50)
        logger.info("🔐 正在登录微信个人号...")
        logger.info("=" * 50)
        logger.info("⚠️  请使用小号微信扫描下方二维码登录")
        logger.info("提示：登录成功后，会自动继续后续步骤\n")
        
        try:
            # 启用热登录，保存登录状态
            # enableCmdQR=2 在控制台显示二维码
            itchat.auto_login(hotReload=True, enableCmdQR=2)
            
            logger.info("\n✅ 微信登录成功！")
            
            # 查找接收者
            logger.info(f"🔍 正在查找微信联系人: {self.receiver_name}")
            friends = itchat.search_friends(name=self.receiver_name)
            
            if friends:
                self.receiver = friends[0]
                logger.info(f"✅ 找到联系人: {self.receiver['NickName']}")
                self.is_ready = True
                return True
            else:
                logger.error(f"❌ 找不到联系人: {self.receiver_name}")
                logger.error("提示：请确认备注名或昵称正确")
                self.is_ready = False
                return False
                
        except Exception as e:
            logger.error(f"❌ 微信登录失败: {e}")
            self.is_ready = False
            return False
    
    def send_message(self, message_info: Dict[str, Any], channel_name: str = "", **kwargs) -> bool:
        """
        发送消息到微信
        :param message_info: 消息信息
        :param channel_name: 频道名称
        :param kwargs: 其他可选参数
        :return: 是否发送成功
        """
        if not self.is_ready or not self.receiver:
            logger.warning("⚠️  微信未就绪，跳过发送")
            return False
        
        try:
            # 格式化消息
            content = self.format_message(message_info, channel_name)
            
            # 发送到微信
            itchat.send(content, toUserName=self.receiver['UserName'])
            logger.info(f"✅ 消息已发送到微信: {message_info['content'][:30]}...")
            return True
            
        except Exception as e:
            logger.error(f"❌ 发送微信消息失败: {e}")
            return False
    
    def keep_alive(self):
        """
        在独立线程中运行微信（保持心跳）
        """
        def run_wechat():
            if self.is_ready:
                logger.info("🔄 微信监听线程已启动（保持在线状态）")
                itchat.run()
        
        self.wechat_thread = threading.Thread(target=run_wechat, daemon=True)
        self.wechat_thread.start()
    
    def cleanup(self):
        """
        清理资源
        """
        try:
            # itchat会自动保存登录状态，这里不需要特别清理
            logger.info("   ✅ 微信发送器已清理")
        except Exception as e:
            logger.debug(f"   清理微信发送器失败: {e}")

