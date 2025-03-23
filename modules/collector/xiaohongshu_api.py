import requests
import json
import time
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re
import os
from ..utils.webdriver_manager import WebDriverManager

logger = logging.getLogger(__name__)

class XiaohongshuAPI:
    """小红书数据采集适配器"""
    
    def __init__(self, config: Dict, api_keys: Dict):
        """初始化小红书数据采集适配器
        
        Args:
            config: 主配置字典
            api_keys: API密钥字典（用于存储cookies等）
        """
        self.config = config
        self.cookies = api_keys.get("xiaohongshu", {}).get("cookies", [])
        
        # 获取小红书相关配置
        xiaohongshu_config = config.get("data_collection", {}).get("platforms", {}).get("xiaohongshu", {})
        self.search_url = xiaohongshu_config.get("search_url", "https://www.xiaohongshu.com/search_result")
        self.max_per_request = xiaohongshu_config.get("max_per_request", 20)
        self.use_selenium = xiaohongshu_config.get("use_selenium", True)
        self.max_retries = xiaohongshu_config.get("max_retries", 3)
        self.timeout = xiaohongshu_config.get("timeout", 30)
        self.debug_mode = config.get("app", {}).get("debug", False)
        
        # 确保调试目录存在
        if self.debug_mode:
            os.makedirs("debug", exist_ok=True)
        
        # 请求头设置
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.xiaohongshu.com/",
            "DNT": "1",
            "Cache-Control": "max-age=0"
        }
        
        # 准备cookies字典
        self.cookies_dict = {}
        if isinstance(self.cookies, list):
            for cookie in self.cookies:
                if isinstance(cookie, dict) and 'name' in cookie and 'value' in cookie:
                    self.cookies_dict[cookie['name']] = cookie['value']
        
        # 初始化Selenium WebDriver
        self.driver = None
        if self.use_selenium:
            self._init_selenium()
            
        # 是否使用模拟数据
        self.always_use_mock = config.get("app", {}).get("debug", False) and config.get("app", {}).get("use_mock_data", True)
        if self.always_use_mock:
            logger.info("调试模式: 将直接使用模拟数据替代真实数据")
            
        logger.info("小红书数据采集适配器初始化完成")
    
    def _init_selenium(self):
        """初始化Selenium WebDriver"""
        try:
            # 使用WebDriver管理器获取驱动
            self.driver = self.webdriver_manager.get_driver(
                name="xiaohongshu",
                cookies=self.cookies_dict,
                domain="xiaohongshu.com",
                headers=self.headers
            )
            logger.info("Selenium WebDriver初始化成功")
        except Exception as e:
            logger.error(f"Selenium WebDriver初始化失败: {str(e)}")
            self.use_selenium = False
    
    def search(self, keyword: str, limit: int) -> List[Dict]:
        """搜索小红书内容
        
        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        # 如果设置为总是使用模拟数据，则跳过真实请求
        if self.always_use_mock:
            logger.info(f"调试模式: 跳过真实请求，直接返回空数据以触发模拟数据生成")
            return []
        
        # 使用Selenium进行搜索
        if self.use_selenium and self.driver:
            return self._search_with_selenium(keyword, limit)
        else:
            logger.error("小红书采集必须使用Selenium模式")
            return []
    
    def _search_with_selenium(self, keyword: str, limit: int) -> List[Dict]:
        """使用Selenium WebDriver搜索小红书内容"""
        results = []
        
        logger.info(f"使用Selenium方式采集小红书数据，关键词: {keyword}")
        
        try:
            # 构建搜索URL
            search_url = f"{self.search_url}?keyword={keyword}&source=web_search_result_notes"
            self.driver.get(search_url)
            
            # 等待页面加载
            try:
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".note-item, .search-card"))
                )
            except TimeoutException:
                logger.warning("页面加载超时，但继续处理")
            
            # 保存页面源码用于调试
            if self.debug_mode:
                with open("debug/xiaohongshu_page.html", 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                self.driver.save_screenshot("debug/xiaohongshu_screenshot.png")
                logger.info("已保存页面源码和截图到debug目录")
            
            # 检查是否有登录墙
            if "登录" in self.driver.page_source and ("查看更多" in self.driver.page_source or "立即登录" in self.driver.page_source):
                logger.warning("检测到小红书登录墙")
                # 尝试提取可见的笔记信息
            
            # 滚动加载更多内容
            scroll_count = 0
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while len(results) < limit and scroll_count < 10:
                # 滚动到页面底部
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # 等待加载
                
                # 提取笔记数据
                note_elements = self.driver.find_elements(By.CSS_SELECTOR, ".note-item, .search-card, .feed-card")
                
                if note_elements:
                    logger.info(f"找到 {len(note_elements)} 个笔记元素")
                    
                    # 处理新加载的内容
                    for elem in note_elements:
                        try:
                            note_data = self._extract_note_data(elem)
                            if note_data and not any(r.get("content_id") == note_data.get("content_id") for r in results):
                                results.append(note_data)
                                if len(results) >= limit:
                                    break
                        except Exception as e:
                            logger.warning(f"提取笔记数据时出错: {str(e)}")
                else:
                    logger.warning("未找到笔记元素")
                
                # 检查是否已经滚动到底部
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    scroll_count += 1
                else:
                    scroll_count = 0
                last_height = new_height
            
            logger.info(f"采集到 {len(results)} 条小红书数据")
            
        except Exception as e:
            logger.error(f"使用Selenium采集小红书数据时出错: {str(e)}")
        
        return results[:limit]
    
    def _extract_note_data(self, element) -> Optional[Dict]:
        """从笔记元素中提取数据"""
        try:
            # 尝试提取标题和内容
            title_elem = element.find_element(By.CSS_SELECTOR, ".title, .content-title")
            title = title_elem.text if title_elem else ""
            
            content_elem = element.find_element(By.CSS_SELECTOR, ".desc, .content-desc")
            content = content_elem.text if content_elem else ""
            
            # 如果标题和内容都为空，可能是不同的元素结构
            if not title and not content:
                content = element.text
            
            # 合并标题和内容
            full_content = title
            if title and content:
                full_content = f"{title}: {content}"
            elif content:
                full_content = content
                
            # 如果内容太短，可能是无效内容
            if len(full_content) < 10:
                return None
            
            # 提取笔记ID
            note_link = element.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
            note_id = ""
            if note_link:
                match = re.search(r'/discovery/item/([a-zA-Z0-9]+)', note_link)
                if match:
                    note_id = match.group(1)
                else:
                    # 生成一个随机ID
                    note_id = f"xhs_{int(time.time())}_{random.randint(1000, 9999)}"
            
            # 提取作者信息
            author = ""
            author_elem = element.find_element(By.CSS_SELECTOR, ".user-name, .author-name")
            if author_elem:
                author = author_elem.text
            
            # 提取位置信息
            location = ""
            location_elem = element.find_element(By.CSS_SELECTOR, ".location, .user-location")
            if location_elem:
                location = location_elem.text
            
            # 创建数据项
            return {
                "platform": "xiaohongshu",
                "content_id": note_id,
                "content": full_content,
                "author": author,
                "location": location,
                "publish_time": datetime.now().isoformat(),  # 小红书不显示具体时间
                "extra_data": {
                    "type": "note",
                    "url": note_link
                }
            }
        except Exception as e:
            logger.debug(f"解析笔记元素时出错: {str(e)}")
            return None
    
    def _extract_location(self, text: str) -> str:
        """从文本中提取位置信息"""
        # 常见城市列表
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "重庆", "武汉", 
                 "西安", "南京", "天津", "苏州", "长沙", "郑州", "东莞", "青岛", 
                 "沈阳", "宁波", "昆明"]
        
        for city in cities:
            if city in text:
                return city
                
        return "未知"
        
    def close(self):
        """释放资源"""
        # 不再直接关闭WebDriver，而是交由管理器处理
        pass
