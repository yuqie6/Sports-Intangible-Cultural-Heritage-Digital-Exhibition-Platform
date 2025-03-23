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
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class ZhihuAPI:
    """知乎数据采集适配器（使用网页解析方式）"""
    
    def __init__(self, config: Dict, api_keys: Dict):
        """初始化知乎数据采集适配器
        
        Args:
            config: 主配置字典
            api_keys: API密钥字典（用于存储cookies等）
        """
        self.config = config
        self.cookies = api_keys.get("cookies", {})
        
        # 获取知乎相关配置
        zhihu_config = config.get("data_collection", {}).get("platforms", {}).get("zhihu", {})
        self.search_url = zhihu_config.get("search_url", "https://www.zhihu.com/search")
        self.max_per_request = zhihu_config.get("max_per_request", 20)
        self.use_selenium = zhihu_config.get("use_selenium", False)
        
        # 设置请求头
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.zhihu.com/",
            "DNT": "1"
        }
        
        # 初始化Selenium WebDriver（如果启用）
        self.driver = None
        if self.use_selenium:
            self._init_selenium()
            
        logger.info("知乎数据采集适配器初始化完成")
    
    def _init_selenium(self):
        """初始化Selenium WebDriver"""
        try:
            options = Options()
            options.add_argument('--headless')  # 无头模式
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument(f'user-agent={self.headers["User-Agent"]}')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # 加载cookies
            if self.cookies:
                self.driver.get("https://www.zhihu.com/")
                for cookie in self.cookies:
                    self.driver.add_cookie(cookie)
                    
            logger.info("Selenium WebDriver初始化成功")
        except Exception as e:
            logger.error(f"Selenium WebDriver初始化失败: {str(e)}")
            self.use_selenium = False
    
    def search(self, keyword: str, limit: int) -> List[Dict]:
        """搜索知乎内容
        
        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        if self.use_selenium and self.driver:
            return self._search_with_selenium(keyword, limit)
        else:
            return self._search_with_requests(keyword, limit)
    
    def _search_with_requests(self, keyword: str, limit: int) -> List[Dict]:
        """使用requests库搜索知乎内容"""
        results = []
        page = 1
        
        logger.info(f"使用requests方式采集知乎数据，关键词: {keyword}")
        
        while len(results) < limit:
            try:
                # 构建请求参数
                params = {
                    "q": keyword,
                    "type": "content",
                    "offset": (page - 1) * self.max_per_request
                }
                
                # 发送请求
                response = requests.get(
                    self.search_url, 
                    params=params, 
                    headers=self.headers,
                    cookies=self.cookies
                )
                
                # 检查响应状态
                if response.status_code != 200:
                    logger.error(f"请求知乎搜索页面失败: HTTP {response.status_code}")
                    break
                
                # 解析HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                items = self._parse_search_results(soup)
                
                if not items:
                    logger.info("没有找到更多结果或解析失败")
                    break
                
                # 处理搜索结果
                for item in items:
                    processed_item = self._process_item(item)
                    if processed_item:
                        results.append(processed_item)
                        
                        # 如果达到限制，则提前结束
                        if len(results) >= limit:
                            break
                
                # 更新页码
                page += 1
                
                # 请求间隔，避免频率限制
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logger.error(f"使用requests采集知乎数据时出错: {str(e)}")
                break
        
        return results[:limit]
    
    def _search_with_selenium(self, keyword: str, limit: int) -> List[Dict]:
        """使用Selenium WebDriver搜索知乎内容"""
        results = []
        
        logger.info(f"使用Selenium方式采集知乎数据，关键词: {keyword}")
        
        try:
            # 打开搜索页面
            search_url = f"{self.search_url}?q={keyword}&type=content"
            self.driver.get(search_url)
            
            # 等待页面加载
            time.sleep(3)
            
            # 滚动加载更多内容，直到达到限制或没有更多内容
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while len(results) < limit:
                # 滚动到页面底部
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # 等待页面加载
                time.sleep(2)
                
                # 解析当前页面的内容
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                items = self._parse_search_results(soup)
                
                # 处理搜索结果
                for item in items:
                    item_id = item.get("content_id", "")
                    
                    # 检查是否已经处理过此项
                    if any(r.get("content_id") == item_id for r in results):
                        continue
                        
                    processed_item = self._process_item(item)
                    if processed_item:
                        results.append(processed_item)
                        
                        # 如果达到限制，则提前结束
                        if len(results) >= limit:
                            break
                
                # 检查是否滚动到了底部
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    # 页面高度没有变化，说明没有加载更多内容
                    break
                    
                last_height = new_height
                
        except Exception as e:
            logger.error(f"使用Selenium采集知乎数据时出错: {str(e)}")
            
        finally:
            # 不关闭WebDriver，以便重用
            pass
            
        return results[:limit]
    
    def _parse_search_results(self, soup: BeautifulSoup) -> List[Dict]:
        """从HTML解析搜索结果
        
        注意：此函数需要根据知乎页面实际结构进行调整
        """
        items = []
        
        # 示例：解析知乎搜索结果
        # 注意：这里的选择器需要根据知乎实际页面结构调整
        content_cards = soup.select(".SearchResult-Card")
        
        for card in content_cards:
            try:
                # 提取内容ID
                content_id = card.get("data-zop", "")
                if isinstance(content_id, str) and content_id:
                    try:
                        content_id = json.loads(content_id).get("itemId", "")
                    except:
                        pass
                
                # 提取内容类型（回答或文章）
                content_type = "answer"
                if card.select_one(".PostItem"):
                    content_type = "article"
                
                # 提取内容
                content_element = card.select_one(".RichText")
                content = content_element.text.strip() if content_element else ""
                
                # 提取作者
                author_element = card.select_one(".AuthorInfo-name")
                author = author_element.text.strip() if author_element else ""
                
                # 提取位置信息
                location = ""
                location_element = card.select_one(".AuthorInfo-badge")
                if location_element:
                    location = location_element.text.strip()
                
                # 提取发布时间
                time_element = card.select_one(".ContentItem-time")
                publish_time = ""
                if time_element:
                    time_text = time_element.text.strip()
                    # 解析时间文本，格式视知乎实际显示而定
                    # 这里仅作示例
                    publish_time = datetime.now().isoformat()
                
                # 创建结果项
                item = {
                    "content_id": content_id,
                    "type": content_type,
                    "content": content,
                    "author": author,
                    "location": location,
                    "publish_time": publish_time
                }
                
                items.append(item)
                
            except Exception as e:
                logger.warning(f"解析搜索结果项时出错: {str(e)}")
                continue
                
        return items
    
    def _process_item(self, item: Dict) -> Optional[Dict]:
        """处理搜索结果项"""
        try:
            # 提取标准格式的数据
            return {
                "platform": "zhihu",
                "content_id": item.get("content_id", ""),
                "content": item.get("content", ""),
                "author": item.get("author", ""),
                "location": self._extract_location(item),
                "publish_time": item.get("publish_time", ""),
                "extra_data": {
                    "type": item.get("type", ""),
                    "url": item.get("url", "")
                }
            }
        except Exception as e:
            logger.error(f"处理知乎数据时出错: {str(e)}")
            return None
    
    def _extract_location(self, item: Dict) -> str:
        """从知乎回答或文章中提取地区信息"""
        # 直接使用item中的location字段
        location = item.get("location", "")
        if location:
            return location
            
        # 尝试从作者信息中推断
        author = item.get("author", "")
        if "北京" in author or "帝都" in author:
            return "北京"
        # 可以添加更多城市识别规则
            
        return "未知"
        
    def close(self):
        """释放资源"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Selenium WebDriver已关闭")
            except:
                pass
