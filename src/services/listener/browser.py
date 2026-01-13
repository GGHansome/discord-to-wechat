
import logging
import os
import shutil
import subprocess
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)

class BrowserManager:
    """浏览器管理器：负责 Chrome 的初始化、启动和关闭"""

    def __init__(self, headless_mode: bool = False):
        self.headless_mode = headless_mode
        self.driver: Optional[webdriver.Chrome] = None

    def init_chrome(self) -> webdriver.Chrome:
        """初始化并返回 Chrome 驱动"""
        logger.info("⏳ 正在配置Chrome浏览器...")
        
        chrome_options = Options()
        try:
            chrome_options.page_load_strategy = 'eager'
        except Exception:
            pass
        
        # 远程 Selenium 支持
        remote_url = os.getenv('SELENIUM_REMOTE_URL')
        if remote_url:
            return self._init_remote_chrome(remote_url, chrome_options)
        
        # 本地 Chrome 配置
        self._configure_local_options(chrome_options)
        
        # 启动驱动
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            logger.error(f"   通过 Selenium Manager 启动失败: {e}")
            logger.info("   回退到系统 chromedriver...")
            self.driver = self._init_system_chromedriver(chrome_options)
            
        logger.info("✅ Chrome浏览器已成功启动")
        return self.driver

    def _init_remote_chrome(self, remote_url: str, options: Options) -> webdriver.Remote:
        if self.headless_mode:
            options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-data-dir=/home/seluser/discord-chrome-data')
        options.add_argument('--profile-directory=Default')

        # 代理支持：
        # - 仅设置 HTTP(S)_PROXY 环境变量通常不足以让 Chrome 自动走代理
        # - 这里读取 CHROME_PROXY（优先）或 HTTPS_PROXY/HTTP_PROXY，并注入 --proxy-server
        proxy = (os.getenv("CHROME_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY") or "").strip()
        if proxy:
            # Chrome 支持的示例：
            # - http://host:port
            # - socks5://host:port
            options.add_argument(f"--proxy-server={proxy}")
            logger.info(f"   Chrome 已启用代理: {proxy}")
        
        try:
            logger.info(f"   使用远程 Selenium: {remote_url}")
            self.driver = webdriver.Remote(command_executor=remote_url, options=options)
            logger.info("✅ Chrome浏览器已成功启动(远程)")
            return self.driver
        except Exception as e:
            logger.error(f"   连接远程 Selenium 失败: {e}")
            raise

    def _configure_local_options(self, options: Options):
        if self.headless_mode:
            options.add_argument('--headless=new')
            logger.info("   使用无头模式运行")
            
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-extensions')
        options.add_argument('--no-zygote')
        options.add_argument('--disable-features=VizDisplayCompositor,UseOzonePlatform')
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-data-dir=./chrome_data')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

    def _init_system_chromedriver(self, options: Options) -> webdriver.Chrome:
        try:
            chromedriver_path = shutil.which('chromedriver') or '/usr/bin/chromedriver'
            return webdriver.Chrome(service=Service(executable_path=chromedriver_path), options=options)
        except Exception as e:
            logger.error(f"   使用系统 chromedriver 启动失败: {e}")
            raise

    def cleanup(self):
        """清理浏览器资源"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("   ✅ Chrome浏览器已关闭")
            except Exception as e:
                logger.debug(f"   关闭Chrome失败: {e}")
                self._force_kill_chromedriver()

    def _force_kill_chromedriver(self):
        # 尝试强制终止残留进程
        try:
            subprocess.run(["pkill", "-f", "chromedriver"], check=False)
        except Exception:
            pass

