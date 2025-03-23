import requests
import json
import time
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ZhihuAPI:
    """知乎API适配器"""
    
    def __init__(self, config: Dict, api_keys: Dict):
        """初始化知乎API适配器
        
        Args:
            config: 主配置字典
            api_keys: API密钥字典
        """
        self.config = config
        self.api_keys = api_keys
        
        # 获取知乎相关配置
        zhihu_config = config.get("data_collection", {}).get("platforms", {}).get("zhihu", {})
        self.api_base = zhihu_config.get("api_base", "https://www.zhihu.com/api/v4")
        self.search_endpoint = zhihu_config.get("search_endpoint", "/search_v3")
        self.max_per_request = zhihu_config.get("max_per_request", 20)
        
        # 设置请求头
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Content-Type": "application/json;charset=UTF-8"
        }
        
        # 如果有API密钥，则添加到请求头
        api_key = api_keys.get("api_key")
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
            logger.info("已配置知乎API密钥")
    
    def search(self, keyword: str, limit: int) -> List[Dict]:
        """搜索知乎内容
        
        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        results = []
        offset = 0
        
        while len(results) < limit:
            try:
                # 构建请求URL和参数
                url = f"{self.api_base}{self.search_endpoint}"
                params = {
                    "q": keyword,
                    "t": "general",
                    "limit": min(self.max_per_request, limit - len(results)),
                    "offset": offset
                }
                
                # 发送请求
                response = requests.get(url, params=params, headers=self.headers)
                
                # 检查响应状态
                if response.status_code != 200:
                    logger.error(f"知乎API请求失败: HTTP {response.status_code}, {response.text}")
                    break
                
                # 解析响应数据
                data = response.json()
                
                if "data" not in data or not data["data"]:
                    logger.info("知乎API返回的数据为空")
                    break
                
                # 处理每个搜索结果
                for item in data["data"]:
                    if self._is_valid_item(item):
                        processed_item = self._process_item(item)
                        if processed_item:
                            results.append(processed_item)
                            
                            # 如果达到限制，则提前结束
                            if len(results) >= limit:
                                break
                
                # 更新偏移量，准备获取下一页
                offset += len(data["data"])
                
                # 如果没有更多数据，则结束
                if len(data["data"]) < self.max_per_request:
                    break
                    
                # 请求间隔，避免频率限制
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                logger.error(f"从知乎获取数据时出错: {str(e)}")
                break
        
        return results[:limit]
    
    def _is_valid_item(self, item: Dict) -> bool:
        """检查搜索结果项是否有效"""
        return (
            "type" in item and 
            item["type"] in ["answer", "article"] and
            "object" in item and 
            isinstance(item["object"], dict)
        )
    
    def _process_item(self, item: Dict) -> Optional[Dict]:
        """处理搜索结果项"""
        try:
            obj = item.get("object", {})
            
            # 提取内容，根据类型不同，字段可能不同
            content = ""
            if item["type"] == "answer":
                content = obj.get("content", "")
            elif item["type"] == "article":
                content = obj.get("excerpt", "")
            
            # 提取作者信息
            author_obj = obj.get("author", {})
            author = author_obj.get("name", "")
            
            # 提取内容ID
            content_id = str(obj.get("id", ""))
            
            # 提取地区信息
            location = self._extract_location(item)
            
            # 提取发布时间
            if item["type"] == "answer":
                created_time = obj.get("created_time", 0)
            else:  # 文章
                created_time = obj.get("created", 0)
                
            publish_time = datetime.fromtimestamp(created_time).isoformat() if created_time else ""
            
            # 提取额外信息
            extra_data = {
                "type": item["type"],
                "vote_count": obj.get("voteup_count", 0),
                "comment_count": obj.get("comment_count", 0),
                "url": obj.get("url", "")
            }
            
            return {
                "platform": "zhihu",
                "content_id": content_id,
                "content": content,
                "author": author,
                "location": location,
                "publish_time": publish_time,
                "extra_data": extra_data
            }
        except Exception as e:
            logger.error(f"处理知乎数据时出错: {str(e)}")
            return None
    
    def _extract_location(self, item: Dict) -> str:
        """从知乎回答或文章中提取地区信息"""
        try:
            # 尝试从用户信息中获取
            author = item.get("object", {}).get("author", {})
            
            # 检查locations字段
            locations = author.get("locations", [])
            if locations and isinstance(locations, list) and len(locations) > 0:
                return locations[0].get("name", "未知")
            
            # 尝试从用户headline中获取
            headline = author.get("headline", "")
            if headline:
                # 这里可以添加更复杂的地区提取逻辑
                provinces = ["北京", "上海", "广东", "江苏", "浙江", "四川", 
                             "湖北", "河南", "山东", "陕西", "重庆", "天津"]
                for province in provinces:
                    if province in headline:
                        return province
            
            return "未知"
        except Exception as e:
            logger.error(f"提取知乎地区信息时出错: {str(e)}")
            return "未知"
