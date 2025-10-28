#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discord到微信/企业微信消息桥接器
使用浏览器自动化监听Discord消息，通过多种方式转发消息

支持的发送方式：
1. 微信个人号（itchat）- 小号发送给大号
2. 企业微信机器人（Webhook）- 发送到企业微信群
"""

import logging
from typing import Dict, Any

# 导入配置
from config import (
    SENDER_TYPE,
    DISCORD_CHANNEL_URLS,
    WECHAT_RECEIVER_NAME,
    ENTERPRISE_WECHAT_WEBHOOK,
    CHECK_INTERVAL,
    HEADLESS_MODE,
    LOG_FILE
)

# 导入各个模块
from discord_listener import DiscordListener
from message_sender import MessageSender
from sender_wechat import WechatSender
from sender_working_wechat import WorkingWechatSender

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class DiscordToWechatBridge:
    """Discord到微信/企业微信的消息桥接器"""
    
    def __init__(
        self,
        sender_type: str,
        discord_channel_urls: list,
        wechat_receiver_name: str = None,
        enterprise_wechat_webhook: str = None,
        check_interval: int = 3,
        headless_mode: bool = False
    ):
        """
        初始化Discord到微信的消息桥
        :param sender_type: 发送器类型 ("wechat" 或 "enterprise_wechat")
        :param discord_channel_urls: Discord频道的URL列表
        :param wechat_receiver_name: 微信接收者的备注名或昵称（微信个人号时使用）
        :param enterprise_wechat_webhook: 企业微信机器人Webhook地址
        :param check_interval: 检查间隔（秒）
        :param headless_mode: 是否使用无头模式
        """
        self.sender_type = sender_type
        self.discord_channel_urls = discord_channel_urls
        self.check_interval = check_interval
        self.headless_mode = headless_mode
        
        # 初始化消息发送器
        self.sender = self._create_sender(
            sender_type,
            wechat_receiver_name,
            enterprise_wechat_webhook
        )
        
        # 初始化Discord监听器
        self.listener = DiscordListener(
            channel_urls=discord_channel_urls,
            on_new_message=self._on_new_message,
            check_interval=check_interval,
            headless_mode=headless_mode
        )
    
    def _create_sender(
        self,
        sender_type: str,
        wechat_receiver_name: str = None,
        enterprise_wechat_webhook: str = None
    ) -> MessageSender:
        """
        创建消息发送器
        :param sender_type: 发送器类型
        :param wechat_receiver_name: 微信接收者名称
        :param enterprise_wechat_webhook: 企业微信Webhook
        :return: 消息发送器实例
        """
        if sender_type == "wechat":
            logger.info("📱 使用发送方式: 微信个人号")
            if not wechat_receiver_name or wechat_receiver_name == "na":
                logger.error("❌ 请先在 config.py 中配置 WECHAT_RECEIVER_NAME")
                raise ValueError("微信接收者名称未配置")
            return WechatSender(receiver_name=wechat_receiver_name)
        
        elif sender_type == "enterprise_wechat":
            logger.info("🤖 使用发送方式: 企业微信机器人")
            if not enterprise_wechat_webhook or "YOUR_WEBHOOK_KEY" in enterprise_wechat_webhook:
                logger.error("❌ 请先在 config.py 中配置 ENTERPRISE_WECHAT_WEBHOOK")
                raise ValueError("企业微信Webhook未配置")
            return WorkingWechatSender(webhook_url=enterprise_wechat_webhook)
        
        else:
            logger.error(f"❌ 不支持的发送器类型: {sender_type}")
            logger.error("   支持的类型: wechat, enterprise_wechat")
            raise ValueError(f"不支持的发送器类型: {sender_type}")
    
    def _on_new_message(self, message_info: Dict[str, Any], channel_name: str):
        """
        新消息回调函数
        :param message_info: 消息信息
        :param channel_name: 频道名称
        """
        # 发送消息
        self.sender.send_message(message_info, channel_name)
    
    def run(self):
        """运行主程序"""
        try:
            logger.info("🚀 Discord to WeChat Bridge 启动中...")
            logger.info("=" * 50)
            
            # 步骤 1: 初始化并登录发送器
            logger.info("\n" + "=" * 50)
            logger.info("🔧 步骤 1/4: 初始化消息发送器...")
            logger.info("=" * 50)
            
            if not self.sender.login():
                logger.error("❌ 消息发送器初始化失败，程序退出")
                return
            
            # 启动发送器的保持活跃线程（如果需要）
            self.sender.keep_alive()
            
            # 步骤 2: 初始化浏览器
            logger.info("\n" + "=" * 50)
            logger.info("🔧 步骤 2/4: 初始化Chrome浏览器...")
            logger.info("=" * 50)
            self.listener.init_chrome()
            
            # 步骤 3: 登录Discord
            logger.info("\n" + "=" * 50)
            logger.info("🔐 步骤 3/4: 登录Discord...")
            logger.info("=" * 50)
            self.listener.login_discord()
            
            # 步骤 4: 打开频道并开始监控
            logger.info("\n" + "=" * 50)
            logger.info("📱 步骤 4/4: 打开Discord频道并开始监控...")
            logger.info("=" * 50)
            self.listener.navigate_to_channel()
            
            # 开始监控消息
            self.listener.monitor_messages()
            
        except KeyboardInterrupt:
            logger.info("\n\n⏹️  程序被用户中断")
        except Exception as e:
            logger.error(f"\n❌ 程序异常: {e}", exc_info=True)
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        logger.info("\n🧹 清理资源...")
        
        # 清理监听器
        if self.listener:
            self.listener.cleanup()
        
        # 清理发送器
        if self.sender:
            self.sender.cleanup()
        
        logger.info("👋 程序已退出")


def validate_config():
    """验证配置是否正确"""
    # 检查Discord配置
    if not DISCORD_CHANNEL_URLS or len(DISCORD_CHANNEL_URLS) == 0:
        logger.error("❌ 请先在 config.py 中配置 DISCORD_CHANNEL_URLS")
        logger.error("   格式: DISCORD_CHANNEL_URLS = [")
        logger.error("       \"https://discord.com/channels/服务器ID/频道ID\",")
        logger.error("   ]")
        return False
    
    # 检查是否包含占位符
    for url in DISCORD_CHANNEL_URLS:
        if "服务器ID" in url or url.endswith("/频道ID"):
            logger.error("❌ 请先在 config.py 中配置正确的 Discord 频道 URL")
            logger.error("   格式: https://discord.com/channels/服务器ID/频道ID")
            return False
    
    # 检查发送器类型
    if SENDER_TYPE not in ["wechat", "enterprise_wechat"]:
        logger.error(f"❌ SENDER_TYPE 配置错误: {SENDER_TYPE}")
        logger.error("   支持的值: wechat 或 enterprise_wechat")
        return False
    
    # 根据发送器类型检查相应配置
    if SENDER_TYPE == "wechat":
        if "你的大号" in WECHAT_RECEIVER_NAME or WECHAT_RECEIVER_NAME == "na":
            logger.error("❌ 请先在 config.py 中配置 WECHAT_RECEIVER_NAME")
            logger.error("   填写你大号在小号微信中的备注名或昵称")
            return False
    
    elif SENDER_TYPE == "enterprise_wechat":
        if "YOUR_WEBHOOK_KEY" in ENTERPRISE_WECHAT_WEBHOOK:
            logger.error("❌ 请先在 config.py 中配置 ENTERPRISE_WECHAT_WEBHOOK")
            logger.error("   获取方式：")
            logger.error("   1. 在企业微信群中，点击群设置 -> 群机器人 -> 添加机器人")
            logger.error("   2. 复制机器人的 Webhook 地址到 config.py")
            return False
    
    return True


def print_startup_info():
    """打印启动信息"""
    logger.info("\n" + "=" * 60)
    logger.info("    Discord to WeChat/Enterprise WeChat Bridge")
    logger.info("=" * 60)
    
    # 发送方式信息
    if SENDER_TYPE == "wechat":
        logger.info("📱 发送方式: 微信个人号")
        logger.info(f"👤 接收者: {WECHAT_RECEIVER_NAME}")
    elif SENDER_TYPE == "enterprise_wechat":
        logger.info("🤖 发送方式: 企业微信机器人")
        logger.info(f"🔗 Webhook: {ENTERPRISE_WECHAT_WEBHOOK[:50]}...")
    
    # Discord频道信息
    logger.info(f"\n📋 监控 {len(DISCORD_CHANNEL_URLS)} 个Discord频道:")
    for idx, url in enumerate(DISCORD_CHANNEL_URLS, 1):
        logger.info(f"   [{idx}] {url}")
    
    # 运行配置
    logger.info(f"\n⚙️  运行配置:")
    logger.info(f"   检查间隔: {CHECK_INTERVAL} 秒")
    logger.info(f"   无头模式: {'是' if HEADLESS_MODE else '否'}")
    logger.info(f"   日志文件: {LOG_FILE}")
    logger.info("=" * 60 + "\n")


def main():
    """主函数"""
    # 验证配置
    if not validate_config():
        return
    
    # 打印启动信息
    print_startup_info()
    
    # 创建并运行桥接器
    try:
        bridge = DiscordToWechatBridge(
            sender_type=SENDER_TYPE,
            discord_channel_urls=DISCORD_CHANNEL_URLS,
            wechat_receiver_name=WECHAT_RECEIVER_NAME,
            enterprise_wechat_webhook=ENTERPRISE_WECHAT_WEBHOOK,
            check_interval=CHECK_INTERVAL,
            headless_mode=HEADLESS_MODE
        )
        
        bridge.run()
    
    except ValueError as e:
        logger.error(f"配置错误: {e}")
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)


if __name__ == "__main__":
    main()
