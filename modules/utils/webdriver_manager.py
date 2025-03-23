"""浏览器驱动管理器 - 单例模式实现"""
import logging
import atexit
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 配置日志
logger = logging.getLogger(__name__)

class WebDriverManager:
    """WebDriver管理器 - 单例模式，减少浏览器实例创建"""
    
    _instance = None
    _drivers = {}
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(WebDriverManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化管理器"""
        logger.debug("WebDriver管理器初始化")
        self._drivers = {}
        # 注册退出函数，确保所有浏览器实例都被关闭
        atexit.register(self.close_all)
    
    def get_driver(self, name="default", cookies=None, domain=None, headers=None):
        """获取一个WebDriver实例，如果不存在则创建"""
        # 如果已存在且正常，直接返回
        if name in self._drivers and self._is_driver_alive(self._drivers[name]):
            logger.debug(f"重用现有WebDriver: {name}")
            return self._drivers[name]
        
        # 创建新的WebDriver实例
        logger.debug(f"创建新的WebDriver: {name}")
        driver = self._create_driver(headers)
        
        # 如果提供了cookie和域名，则设置cookie
        if cookies and domain:
            self._set_cookies(driver, cookies, domain)
        
        # 存储并返回
        self._drivers[name] = driver
        return driver
    
    def _is_driver_alive(self, driver):
        """检查WebDriver实例是否仍然有效"""
        try:
            # 简单测试以检查会话是否仍然有效
            _ = driver.current_url
            return True
        except:
            return False
    
    def _create_driver(self, headers=None):
        """创建一个新的WebDriver实例"""
        # 使用环境变量中的标志或默认标志
        chrome_flags = os.environ.get("CHROME_BROWSER_FLAGS", "")
        flags = chrome_flags.split() if chrome_flags else []
        
        # 创建选项
        options = Options()
        
        # 添加所有标志
        for flag in flags:
            if flag:
                options.add_argument(flag)
        
        # 额外设置
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 添加请求头
        if headers and isinstance(headers, dict):
            user_agent = headers.get("User-Agent")
            if user_agent:
                options.add_argument(f'user-agent={user_agent}')
        
        # 创建服务
        service = Service(ChromeDriverManager(log_level=logging.CRITICAL).install())
        
        # 创建并返回WebDriver
        driver = webdriver.Chrome(service=service, options=options)
        
        # 添加反自动化检测脚本
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        
        return driver
    
    def _set_cookies(self, driver, cookies, domain):
        """设置浏览器cookies"""
        # 先访问域名
        scheme = "https" if not domain.startswith(("http:", "https:")) else ""
        base_url = f"{scheme}://{domain}" if scheme else domain
        
        # 确保URL有协议前缀
        if not base_url.startswith(("http:", "https:")):
            base_url = f"https://{base_url}"
            
        driver.get(base_url)
        
        # 设置cookies
        if isinstance(cookies, dict):
            # 字典形式的cookies
            for name, value in cookies.items():
                driver.add_cookie({
                    'name': name,
                    'value': value,
                    'domain': f".{domain.split('//')[1]}" if "//" in domain else f".{domain}"
                })
        elif isinstance(cookies, list):
            # 列表形式的cookies
            for cookie in cookies:
                if isinstance(cookie, dict) and 'name' in cookie and 'value' in cookie:
                    driver.add_cookie({
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': cookie.get('domain', f".{domain.split('//')[1]}" if "//" in domain else f".{domain}")
                    })
        
        # 重新加载页面以应用cookies
        driver.get(base_url)
        time.sleep(1)
    
    def close(self, name="default"):
        """关闭指定的WebDriver实例"""
        if name in self._drivers:
            try:
                self._drivers[name].quit()
                logger.debug(f"已关闭WebDriver: {name}")
            except:
                pass
            del self._drivers[name]
    
    def close_all(self):
        """关闭所有WebDriver实例"""
        for name in list(self._drivers.keys()):
            self.close(name)
        logger.debug("已关闭所有WebDriver实例")
