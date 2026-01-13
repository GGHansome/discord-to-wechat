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
from typing import Dict, Any, List

# 导入配置模块
import config

# 导入各个模块
from src.discord_listener import DiscordListener
from src.sender.message_sender import MessageSender
from src.sender.sender_wechat import WechatSender
from src.sender.sender_working_wechat import WorkingWechatSender

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
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
        enterprise_wechat_webhook_list: List[Dict[str, str]] = None,
        check_interval: int = 3,
        headless_mode: bool = False
    ):
        """
        初始化Discord到微信的消息桥
        :param sender_type: 发送器类型 ("wechat" 或 "enterprise_wechat")
        :param discord_channel_urls: Discord频道的URL列表
        :param wechat_receiver_name: 微信接收者的备注名或昵称（微信个人号时使用）
        :param enterprise_wechat_webhook: 企业微信机器人Webhook地址 (旧版)
        :param enterprise_wechat_webhook_list: 企业微信机器人Webhook配置列表 (新版)
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
            enterprise_wechat_webhook,
            enterprise_wechat_webhook_list
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
        enterprise_wechat_webhook: str = None,
        enterprise_wechat_webhook_list: List[Dict[str, str]] = None
    ) -> MessageSender:
        """
        创建消息发送器
        :param sender_type: 发送器类型
        :param wechat_receiver_name: 微信接收者名称
        :param enterprise_wechat_webhook: 企业微信Webhook (旧版)
        :param enterprise_wechat_webhook_list: 企业微信Webhook列表 (新版)
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
            
            # 优先检查新的列表配置
            has_list_config = enterprise_wechat_webhook_list and len(enterprise_wechat_webhook_list) > 0
            # 检查旧的单个配置
            has_single_config = enterprise_wechat_webhook and "YOUR_WEBHOOK_KEY" not in enterprise_wechat_webhook
            
            if not has_list_config and not has_single_config:
                logger.error("❌ 请先在 config.py 中配置 ENTERPRISE_WECHAT_WEBHOOK_LIST 或 ENTERPRISE_WECHAT_WEBHOOK")
                raise ValueError("企业微信Webhook未配置")
            
            return WorkingWechatSender(
                webhook_url=enterprise_wechat_webhook,
                webhook_configs=enterprise_wechat_webhook_list
            )
        
        else:
            logger.error(f"❌ 不支持的发送器类型: {sender_type}")
            logger.error("   支持的类型: wechat, enterprise_wechat")
            raise ValueError(f"不支持的发送器类型: {sender_type}")
    
    def _on_new_message(self, message_info: Dict[str, Any], channel_name: str, channel_url: str = ""):
        """
        新消息回调函数
        :param message_info: 消息信息
        :param channel_name: 频道名称
        :param channel_url: 频道URL
        """
        # 发送消息
        # 统一接口调用，所有 Sender 都已支持 kwargs 参数
        self.sender.send_message(message_info, channel_name, channel_url=channel_url)
    
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
    if not config.DISCORD_CHANNEL_URLS or len(config.DISCORD_CHANNEL_URLS) == 0:
        logger.error("❌ 请先在 config.py 中配置 DISCORD_CHANNEL_URLS")
        return False
    
    # 检查发送器类型
    if config.SENDER_TYPE not in ["wechat", "enterprise_wechat"]:
        logger.error(f"❌ SENDER_TYPE 配置错误: {config.SENDER_TYPE}")
        return False
    
    # 根据发送器类型检查相应配置
    if config.SENDER_TYPE == "wechat":
        if "你的大号" in config.WECHAT_RECEIVER_NAME or config.WECHAT_RECEIVER_NAME == "na":
            logger.error("❌ 请先在 config.py 中配置 WECHAT_RECEIVER_NAME")
            return False
    
    elif config.SENDER_TYPE == "enterprise_wechat":
        # 获取可能存在的配置
        webhook = getattr(config, 'ENTERPRISE_WECHAT_WEBHOOK', None)
        webhook_list = getattr(config, 'ENTERPRISE_WECHAT_WEBHOOK_LIST', None)
        
        valid_list = webhook_list and len(webhook_list) > 0
        valid_single = webhook and "YOUR_WEBHOOK_KEY" not in webhook
        
        if not valid_list and not valid_single:
            logger.error("❌ 请先在 config.py 中配置 ENTERPRISE_WECHAT_WEBHOOK_LIST 或 ENTERPRISE_WECHAT_WEBHOOK")
            return False
    
    return True


def print_startup_info():
    """打印启动信息"""
    logger.info("\n" + "=" * 60)
    logger.info("    Discord to WeChat/Enterprise WeChat Bridge")
    logger.info("=" * 60)
    
    # 发送方式信息
    if config.SENDER_TYPE == "wechat":
        logger.info("📱 发送方式: 微信个人号")
        logger.info(f"👤 接收者: {config.WECHAT_RECEIVER_NAME}")
    elif config.SENDER_TYPE == "enterprise_wechat":
        logger.info("🤖 发送方式: 企业微信机器人")
        
        webhook_list = getattr(config, 'ENTERPRISE_WECHAT_WEBHOOK_LIST', None)
        if webhook_list:
             logger.info(f"🔗 已配置 {len(webhook_list)} 个Webhook映射")
        else:
             webhook = getattr(config, 'ENTERPRISE_WECHAT_WEBHOOK', "")
             logger.info(f"🔗 Webhook: {webhook[:30]}...")
    
    # Discord频道信息
    logger.info(f"\n📋 监控 {len(config.DISCORD_CHANNEL_URLS)} 个Discord频道")
    
    # 运行配置
    logger.info(f"\n⚙️  运行配置:")
    logger.info(f"   检查间隔: {config.CHECK_INTERVAL} 秒")
    logger.info(f"   无头模式: {'是' if config.HEADLESS_MODE else '否'}")
    logger.info("=" * 60 + "\n")


def main():
    """主函数"""
    # 验证配置
    if not validate_config():
        return
    
    # 打印启动信息
    print_startup_info()
    
    # 获取配置项（安全获取）
    enterprise_wechat_webhook = getattr(config, 'ENTERPRISE_WECHAT_WEBHOOK', None)
    enterprise_wechat_webhook_list = getattr(config, 'ENTERPRISE_WECHAT_WEBHOOK_LIST', None)
    
    # 创建并运行桥接器
    try:
        bridge = DiscordToWechatBridge(
            sender_type=config.SENDER_TYPE,
            discord_channel_urls=config.DISCORD_CHANNEL_URLS,
            wechat_receiver_name=config.WECHAT_RECEIVER_NAME,
            enterprise_wechat_webhook=enterprise_wechat_webhook,
            enterprise_wechat_webhook_list=enterprise_wechat_webhook_list,
            check_interval=config.CHECK_INTERVAL,
            headless_mode=config.HEADLESS_MODE
        )
        
        bridge.run()
    
    except ValueError as e:
        logger.error(f"配置错误: {e}")
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)


if __name__ == "__main__":
    main()
