import importlib.util
import os
import sys
from typing import List, Dict, Optional, Any

class Config:
    """配置管理类"""
    
    def __init__(self):
        self.sender_type: str = "wechat"
        self.discord_channel_urls: List[str] = []
        self.wechat_receiver_name: str = ""
        self.enterprise_wechat_webhook: str = ""
        self.enterprise_wechat_webhook_list: List[Dict[str, str]] = []
        self.check_interval: int = 3
        self.headless_mode: bool = False
        
        self.load_config()

    def load_config(self):
        """从 config.py 加载配置"""
        try:
            # 动态导入根目录下的 config.py
            config_path = os.path.join(os.getcwd(), 'config.py')
            spec = importlib.util.spec_from_file_location("config", config_path)
            if spec and spec.loader:
                config_module = importlib.util.module_from_spec(spec)
                sys.modules["config"] = config_module
                spec.loader.exec_module(config_module)
                
                # 安全读取配置
                self.sender_type = getattr(config_module, 'SENDER_TYPE', 'wechat')
                self.discord_channel_urls = getattr(config_module, 'DISCORD_CHANNEL_URLS', [])
                self.wechat_receiver_name = getattr(config_module, 'WECHAT_RECEIVER_NAME', '')
                self.enterprise_wechat_webhook = getattr(config_module, 'ENTERPRISE_WECHAT_WEBHOOK', '')
                self.enterprise_wechat_webhook_list = getattr(config_module, 'ENTERPRISE_WECHAT_WEBHOOK_LIST', [])
                self.check_interval = getattr(config_module, 'CHECK_INTERVAL', 3)
                self.headless_mode = getattr(config_module, 'HEADLESS_MODE', False)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            # 可以抛出异常或者使用默认值

# 全局单例
app_config = Config()

