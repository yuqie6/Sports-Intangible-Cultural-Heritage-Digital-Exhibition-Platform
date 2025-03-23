import requests
import json
import time
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import os
import base64

# 导入WebDriver管理器
from ..utils.webdriver_manager import WebDriverManager

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
        self.cookies = api_keys.get("zhihu", {}).get("cookies", [])
        
        # 获取知乎相关配置
        zhihu_config = config.get("data_collection", {}).get("platforms", {}).get("zhihu", {})
        self.search_url = zhihu_config.get("search_url", "https://www.zhihu.com/search")
        self.max_per_request = zhihu_config.get("max_per_request", 20)
        self.use_selenium = zhihu_config.get("use_selenium", True)  # 默认使用selenium
        self.max_retries = zhihu_config.get("max_retries", 3)
        self.timeout = zhihu_config.get("timeout", 30)  # 增加超时时间
        self.debug_mode = config.get("app", {}).get("debug", False)
        
        # 确保调试目录存在
        if self.debug_mode:
            os.makedirs("debug", exist_ok=True)
        
        # 更全面的请求头设置
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://www.zhihu.com/",
            "DNT": "1",
            "Cache-Control": "max-age=0"
        }
        
        # 准备cookies字典
        self.cookies_dict = {}
        if isinstance(self.cookies, list):
            for cookie in self.cookies:
                if isinstance(cookie, dict) and 'name' in cookie and 'value':
                    self.cookies_dict[cookie['name']] = cookie['value']
        
        # 替换WebDriver初始化代码
        self.driver = None
        self.webdriver_manager = WebDriverManager()
        if self.use_selenium:
            self._init_selenium()
            
        logger.info("知乎数据采集适配器初始化完成")
        
        # 新增设置: 是否直接使用模拟数据
        self.always_use_mock = config.get("app", {}).get("debug", False) and config.get("app", {}).get("use_mock_data", True)
        if self.always_use_mock:
            logger.info("调试模式: 将直接使用模拟数据替代真实数据")
            
        # 新增搜索API相关设置
        self.api_search_enabled = zhihu_config.get("api_search_enabled", False)
        self.api_search_url = zhihu_config.get("api_search_url", "https://www.zhihu.com/api/v4/search_v3")
    
    def _init_selenium(self):
        """初始化Selenium WebDriver"""
        try:
            # 使用WebDriver管理器获取驱动
            self.driver = self.webdriver_manager.get_driver(
                name="zhihu",
                cookies=self.cookies_dict,
                domain="zhihu.com",
                headers=self.headers
            )
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
        # 如果设置为总是使用模拟数据，则跳过真实请求
        if self.always_use_mock:
            logger.info(f"调试模式: 跳过真实请求，直接返回空数据以触发模拟数据生成")
            return []
            
        # 尝试使用API搜索(如果启用)
        if self.api_search_enabled:
            try:
                logger.info(f"尝试使用知乎API搜索: {keyword}")
                api_results = self._search_with_api(keyword, limit)
                if api_results:
                    return api_results
                logger.warning("API搜索返回空结果，尝试备用方法")
            except Exception as e:
                logger.error(f"API搜索失败: {str(e)}")
                
        # 优先使用Selenium，失败则尝试requests
        try:
            if self.use_selenium and self.driver:
                return self._search_with_selenium(keyword, limit)
            else:
                logger.warning("Selenium未启用或初始化失败，尝试使用requests")
                return self._search_with_requests(keyword, limit)
        except Exception as e:
            logger.error(f"搜索知乎内容失败: {str(e)}")
            # 如果默认方法失败，尝试另一种方法
            if self.use_selenium:
                logger.info("Selenium方法失败，尝试使用requests")
                return self._search_with_requests(keyword, limit)
            else:
                logger.info("Requests方法失败，尝试使用Selenium")
                if self.driver is None:
                    self._init_selenium()
                if self.driver:
                    return self._search_with_selenium(keyword, limit)
            
            # 两种方法都失败
            return []
    
    def _search_with_requests(self, keyword: str, limit: int) -> List[Dict]:
        """使用requests库搜索知乎内容"""
        results = []
        page = 1
        retry_count = 0
        
        logger.info(f"使用requests方式采集知乎数据，关键词: {keyword}")
        
        while len(results) < limit and retry_count < self.max_retries:
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
                    cookies=self.cookies_dict,
                    timeout=self.timeout
                )
                
                # 检查响应状态
                if response.status_code != 200:
                    logger.error(f"请求知乎搜索页面失败: HTTP {response.status_code}")
                    retry_count += 1
                    time.sleep(random.uniform(2, 5))  # 重试前等待
                    continue
                
                # 调试模式下保存响应内容
                if self.debug_mode:
                    with open(f"debug/zhihu_response_page{page}.html", 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    logger.info(f"已保存响应内容到 debug/zhihu_response_page{page}.html")
                
                # 解析HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                items = self._parse_search_results(soup)
                
                if not items:
                    logger.info("没有找到更多结果或解析失败")
                    # 检查是否存在验证码
                    if "验证码" in response.text:
                        logger.warning("检测到验证码，请使用Selenium模式或更新cookies")
                        break
                    page += 1
                    if page > 5:  # 最多查找5页
                        break
                    continue
                
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
                
                # 重置重试计数器
                retry_count = 0
                
            except Exception as e:
                logger.error(f"使用requests采集知乎数据时出错: {str(e)}")
                retry_count += 1
                time.sleep(random.uniform(2, 5))  # 重试前等待
        
        return results[:limit]
    
    def _search_with_api(self, keyword: str, limit: int) -> List[Dict]:
        """使用知乎搜索API获取数据"""
        results = []
        offset = 0
        limit_per_request = min(20, limit)  # 知乎API通常限制每页20条
        
        try:
            while len(results) < limit:
                # 构建API请求参数
                params = {
                    "q": keyword,
                    "t": "general",
                    "correction": 1,
                    "offset": offset,
                    "limit": limit_per_request,
                    "filter_fields": "",
                    "lc_idx": 0,
                    "show_all_topics": 0,
                    "search_source": "Normal"
                }
                
                # 设置请求头
                headers = {
                    **self.headers,
                    "x-requested-with": "fetch",
                    "x-zse-93": "101_3_2.0",  # 加入知乎特定头
                    "content-type": "application/json"
                }
                
                # 发送请求
                response = requests.get(
                    self.api_search_url, 
                    params=params,
                    headers=headers,
                    cookies=self.cookies_dict,
                    timeout=self.timeout
                )
                
                # 调试响应
                if self.debug_mode and response.text:
                    with open(f"debug/zhihu_api_response_{offset}.json", 'w', encoding='utf-8') as f:
                        try:
                            f.write(json.dumps(response.json(), ensure_ascii=False, indent=2))
                        except:
                            f.write(response.text)
                
                # 检查响应
                if response.status_code != 200:
                    logger.error(f"API请求失败: 状态码 {response.status_code}")
                    break
                
                # 解析JSON响应
                try:
                    data = response.json()
                    items = data.get("data", [])
                    
                    if not items:
                        logger.info("API返回的数据列表为空")
                        break
                    
                    # 处理每个搜索结果
                    for item in items:
                        try:
                            object_type = item.get("object", {}).get("type")
                            if object_type in ["answer", "article", "question"]:
                                processed_item = self._process_api_item(item)
                                if processed_item:
                                    results.append(processed_item)
                                    
                                    if len(results) >= limit:
                                        break
                        except Exception as e:
                            logger.warning(f"处理API结果项时出错: {str(e)}")
                            continue
                    
                    # 检查是否有下一页
                    if "paging" in data and data["paging"]["is_end"]:
                        break
                        
                    # 更新偏移量
                    offset += limit_per_request
                    
                    # 请求间隔
                    time.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    logger.error(f"解析API响应时出错: {str(e)}")
                    break
                    
        except Exception as e:
            logger.error(f"使用API搜索时出错: {str(e)}")
            
        logger.info(f"API搜索完成，获取到 {len(results)} 条结果")
        return results
    
    def _process_api_item(self, item: Dict) -> Optional[Dict]:
        """处理API返回的单个搜索结果"""
        try:
            # 提取对象部分
            obj = item.get("object", {})
            obj_type = obj.get("type", "")
            obj_id = str(obj.get("id", ""))
            
            # 根据类型提取内容
            if obj_type == "answer":
                content = obj.get("excerpt", "")
                question = obj.get("question", {}).get("name", "")
                if question and content:
                    content = f"{question}: {content}"
                elif question:
                    content = question
                    
                url = f"https://www.zhihu.com/question/{obj.get('question', {}).get('id', '')}/answer/{obj_id}"
                
            elif obj_type == "article":
                content = obj.get("excerpt", "")
                title = obj.get("title", "")
                if title and content:
                    content = f"{title}: {content}"
                elif title:
                    content = title
                    
                url = f"https://zhuanlan.zhihu.com/p/{obj_id}"
                
            elif obj_type == "question":
                content = obj.get("name", "")
                url = f"https://www.zhihu.com/question/{obj_id}"
                
            else:
                return None
                
            # 提取作者信息
            author = obj.get("author", {}).get("name", "")
            author_url_token = obj.get("author", {}).get("url_token", "")
            
            # 提取发布时间
            created = obj.get("created_time", 0)
            if created:
                try:
                    publish_time = datetime.fromtimestamp(created).isoformat()
                except:
                    publish_time = datetime.now().isoformat()
            else:
                publish_time = datetime.now().isoformat()
            
            # 提取地区信息
            location = ""
            
            # 返回处理后的数据
            return {
                "platform": "zhihu",
                "content_id": obj_id,
                "content": content,
                "author": author,
                "location": location,
                "publish_time": publish_time,
                "extra_data": {
                    "type": obj_type,
                    "url": url,
                    "author_url_token": author_url_token
                }
            }
        except Exception as e:
            logger.warning(f"处理API项目时出错: {str(e)}")
            return None
    
    def _extract_content_from_links(self) -> List[Dict]:
        """从页面中提取问题和回答链接，然后组装内容"""
        items = []
        try:
            # 增强链接查找逻辑
            content_links = []
            for link_type in ["a", "div[role='link']", "[data-za-detail-view-element_name='Title']"]:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, link_type)
                    logger.info(f"找到 {len(elements)} 个 {link_type} 元素")
                    
                    for elem in elements:
                        try:
                            href = elem.get_attribute("href") or ""
                            if not href and link_type != "a":
                                # 对于非链接元素，尝试找到它的父链接
                                parent = elem.find_element(By.XPATH, "./ancestor::a")
                                if parent:
                                    href = parent.get_attribute("href") or ""
                            
                            if "/question/" in href or "/answer/" in href:
                                text = elem.text or elem.get_attribute("textContent") or ""
                                content_links.append((href, text))
                        except:
                            continue
                except:
                    continue
            
            logger.info(f"找到 {len(content_links)} 个内容链接")
            
            # 从链接中提取内容
            for i, (href, text) in enumerate(content_links):
                try:
                    # 从链接中提取ID
                    content_id = ""
                    match = re.search(r"/(question|answer)/(\d+)", href)
                    if match:
                        content_type = match.group(1)
                        content_id = match.group(2)
                    else:
                        continue
                    
                    # 确保文本内容长度合适
                    content = text
                    if len(content) < 10 and i < len(content_links) - 1:
                        # 如果文本太短，尝试合并下一个链接的文本
                        content += " " + content_links[i+1][1]
                    
                    # 创建内容项
                    item = {
                        "content_id": content_id,
                        "type": content_type,
                        "content": content,
                        "author": "",  # 无法直接获取
                        "location": "未知",
                        "publish_time": datetime.now().isoformat(),
                        "url": href
                    }
                    
                    # 避免重复
                    if not any(existing["content_id"] == content_id for existing in items):
                        items.append(item)
                except Exception as e:
                    logger.warning(f"处理链接时出错: {str(e)}")
            
        except Exception as e:
            logger.error(f"提取链接内容时出错: {str(e)}")
        
        return items
    
    def _search_with_selenium(self, keyword: str, limit: int) -> List[Dict]:
        """使用Selenium WebDriver搜索知乎内容"""
        results = []
        
        logger.info(f"使用Selenium方式采集知乎数据，关键词: {keyword}")
        
        try:
            # 更新为更可靠的搜索方式
            search_url = f"{self.search_url}?q={keyword}&type=content"
            self.driver.get(search_url)
            
            # 检查是否有登录墙
            login_wall_detected = False
            try:
                # 等待页面加载
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                html_content = self.driver.page_source
                
                # 保存调试信息
                if self.debug_mode:
                    with open("debug/zhihu_raw_page.html", 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    
                    # 保存页面截图
                    screenshot_path = "debug/zhihu_screenshot.png"
                    self.driver.save_screenshot(screenshot_path)
                    logger.info(f"已保存页面截图到 {screenshot_path}")
                
                # 登录墙检测
                if "登录" in html_content and (
                   "继续浏览" in html_content or 
                   "想了解更多内容" in html_content or
                   "立即登录" in html_content):
                    login_wall_detected = True
                    logger.warning("检测到知乎登录墙，尝试改用请求方式")
                    
                    # 如果有登录拦截，使用请求方式
                    try:
                        return self._search_with_requests(keyword, limit)
                    except Exception as e:
                        logger.error(f"切换到请求方式失败: {str(e)}")
                
                # 验证码检测
                if "验证码" in html_content or "安全验证" in html_content:
                    logger.warning("检测到知乎验证码，请更新cookies或降低请求频率")
                    # 保存验证码图片
                    captcha_elements = self.driver.find_elements(By.TAG_NAME, "img")
                    for idx, img in enumerate(captcha_elements):
                        try:
                            src = img.get_attribute("src")
                            if src and ("captcha" in src or "验证码" in img.get_attribute("alt", "")):
                                img_path = f"debug/captcha_{idx}.png"
                                img.screenshot(img_path)
                                logger.warning(f"已保存验证码图片到 {img_path}")
                        except:
                            pass
                    
                    # 无法继续爬取，返回空结果
                    return []
                
            except Exception as e:
                logger.warning(f"页面检查时出错: {str(e)}")
            
            # 如果检测到登录墙或验证码，用请求方式
            if login_wall_detected:
                # 已经在上面尝试过请求方式
                pass
            else:
                # 直接提取页面内容并手动检查
                html_content = self.driver.page_source
                if "抱歉，没有找到相关内容" in html_content:
                    logger.warning(f"知乎搜索结果：未找到与\"{keyword}\"相关的内容")
                    return []
                    
                # 查看是否有登录墙
                if "立即登录，体验更多功能" in html_content or "登录注册" in html_content:
                    logger.warning("检测到登录墙，尝试从页面中提取可见内容")
                    # 尝试新方法：直接从链接提取内容
                    link_items = self._extract_content_from_links()
                    if link_items:
                        for item in link_items:
                            processed_item = self._process_item(item)
                            if processed_item:
                                results.append(processed_item)
                                if len(results) >= limit:
                                    break
                    logger.info(f"从链接中提取了 {len(results)} 条内容")
                    return results[:limit]
            
            # 尝试点击"更多"按钮加载更多内容
            try:
                more_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), '更多') or contains(text(), '显示更多')]")
                if more_buttons:
                    for button in more_buttons:
                        try:
                            self.driver.execute_script("arguments[0].click();", button)
                            time.sleep(1)
                            logger.info("已点击'更多'按钮")
                        except:
                            pass
            except:
                pass
                
            # 滚动加载更多内容，直到达到限制或没有更多内容
            scroll_count = 0
            last_results_len = 0
            
            while len(results) < limit and scroll_count < 15:  # 最多滚动15次
                # 先截取当前页面内容以便调试
                page_source = self.driver.page_source
                
                # 手动查找内容区块
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # 尝试解析页面内容
                items = self._parse_search_results(soup)
                
                if not items:
                    logger.warning("未找到内容元素，尝试备选方案：提取链接内容")
                    # 尝试从链接提取内容
                    link_items = self._extract_content_from_links()
                    if link_items:
                        for item in link_items:
                            processed_item = self._process_item(item)
                            if processed_item:
                                results.append(processed_item)
                                if len(results) >= limit:
                                    break
                
                # 处理解析到的项目
                for item in items:
                    content_id = item.get("content_id", "")
                    
                    # 检查是否已经处理过此项
                    if any(r.get("content_id") == content_id for r in results):
                        continue
                        
                    processed_item = self._process_item(item)
                    if processed_item:
                        results.append(processed_item)
                        
                        # 如果达到限制，则提前结束
                        if len(results) >= limit:
                            break
                
                # 如果没有新内容，增加计数
                if len(results) == last_results_len:
                    scroll_count += 1
                else:
                    last_results_len = len(results)
                    scroll_count = 0
                
                # 滚动到页面底部
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # 等待新内容加载
                time.sleep(2)
                
            logger.info(f"使用Selenium获取到 {len(results)} 条结果")
                
        except Exception as e:
            logger.error(f"使用Selenium采集知乎数据时出错: {str(e)}")
            
        finally:
            # 不关闭WebDriver，以便重用
            pass
            
        return results[:limit]
    
    def _parse_search_results(self, soup: BeautifulSoup) -> List[Dict]:
        """从HTML解析搜索结果"""
        items = []
        
        try:
            # 更广泛地查找所有可能包含内容的元素
            
            # 1. 尝试从问题和回答链接中提取内容
            question_links = soup.select("a[href*='/question/']")
            answer_links = soup.select("a[href*='/answer/']")
            
            logger.info(f"找到 {len(question_links)} 个问题链接, {len(answer_links)} 个回答链接")
            
            # 从链接中提取内容
            for link in question_links + answer_links:
                try:
                    href = link.get("href", "")
                    if not href:
                        continue
                        
                    # 提取内容ID和类型
                    match = re.search(r"/(question|answer)/(\d+)", href)
                    if not match:
                        continue
                        
                    content_type = match.group(1)
                    content_id = match.group(2)
                    
                    # 获取链接文本
                    link_text = link.get_text(strip=True)
                    
                    # 尝试获取父元素中的更多文本
                    parent = link.parent
                    parent_text = ""
                    if parent:
                        parent_text = parent.get_text(strip=True)
                        
                    # 使用更长的文本
                    content = parent_text if len(parent_text) > len(link_text) else link_text
                    
                    # 如果内容太短，继续寻找更多内容
                    if len(content) < 20:
                        # 尝试找到相关内容块
                        container = parent
                        for _ in range(3):  # 最多向上查找3层
                            if container:
                                container = container.parent
                                if container:
                                    container_text = container.get_text(strip=True)
                                    if len(container_text) > len(content):
                                        content = container_text
                    
                    # 确保链接URL完整
                    if not href.startswith("http"):
                        url = f"https://www.zhihu.com{href}"
                    else:
                        url = href
                    
                    # 创建项目
                    if content and len(content) > 10:  # 只加入有足够内容的项
                        item = {
                            "content_id": content_id,
                            "type": content_type,
                            "content": content,
                            "author": "",  # 无法直接获取
                            "location": "",
                            "publish_time": datetime.now().isoformat(),
                            "url": url
                        }
                        
                        # 避免重复
                        if not any(existing.get("content_id") == content_id for existing in items):
                            items.append(item)
                except Exception as e:
                    logger.warning(f"处理链接时出错: {str(e)}")
            
            # 2. 尝试从文本块中提取内容
            if len(items) < 5:  # 如果链接方法提取的内容太少
                # 寻找长文本块
                text_blocks = []
                for tag in soup.find_all(["p", "div", "span"]):
                    text = tag.get_text(strip=True)
                    if len(text) > 100:  # 只关注较长的文本块
                        text_blocks.append(text)
                
                logger.info(f"找到 {len(text_blocks)} 个长文本块")
                
                # 为每个文本块创建一个项目
                for i, text in enumerate(text_blocks):
                    # 生成一个唯一ID
                    content_id = f"text_block_{int(time.time())}_{i}"
                    
                    item = {
                        "content_id": content_id,
                        "type": "text_block",
                        "content": text,
                        "author": "",
                        "location": "",
                        "publish_time": datetime.now().isoformat()
                    }
                    
                    items.append(item)
            
            logger.info(f"解析到 {len(items)} 个搜索结果")
            
        except Exception as e:
            logger.error(f"解析搜索结果时出错: {str(e)}")
        
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
        content = item.get("content", "")
        
        # 常见城市识别
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "重庆", "武汉", 
                 "西安", "南京", "天津", "苏州", "长沙", "郑州", "东莞", "青岛", 
                 "沈阳", "宁波", "昆明"]
        
        # 尝试从内容中识别城市
        for city in cities:
            if city in content:
                return city
        
        # 从作者名称识别城市
        for city in cities:
            if city in author:
                return city
            
        return "未知"
        
    def close(self):
        """释放资源"""
        # 不再直接关闭WebDriver，而是交由管理器处理
        pass
