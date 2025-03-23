import requests
import json
import time
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class WeiboAPI:
    """微博API适配器"""
    
    def __init__(self, config: Dict, api_keys: Dict):
        """初始化微博API适配器
        
        Args:
            config: 主配置字典
            api_keys: API密钥字典
        """
        self.config = config
        self.api_keys = api_keys
        
        # 获取微博相关配置
        weibo_config = config.get("data_collection", {}).get("platforms", {}).get("weibo", {})
        self.api_base = weibo_config.get("api_base", "https://api.weibo.com/2")
        self.search_endpoint = weibo_config.get("search_endpoint", "/search/topics.json")
        self.max_per_request = weibo_config.get("max_per_request", 50)
        
        # 获取微博API密钥
        self.app_key = api_keys.get("app_key", "")
        self.app_secret = api_keys.get("app_secret", "")
        self.access_token = api_keys.get("access_token", "")
        
        if self.app_key and self.app_secret and self.access_token:
            logger.info("已配置微博API密钥")
        else:
            logger.warning("微博API密钥配置不完整，功能可能受限")
        
        # 设置请求头
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
    
    def search(self, keyword: str, limit: int) -> List[Dict]:
        """搜索微博内容
        
        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        results = []
        page = 1
        
        # 检查是否有必要的API密钥
        if not self.access_token:
            logger.error("无法访问微博API: 缺少访问令牌")
            return results
        
        while len(results) < limit:
            try:
                # 构建请求URL和参数
                url = f"{self.api_base}{self.search_endpoint}"
                params = {
                    "access_token": self.access_token,
                    "q": keyword,
                    "count": min(self.max_per_request, limit - len(results)),
                    "page": page
                }
                
                # 发送请求
                response = requests.get(url, params=params, headers=self.headers)
                
                # 检查响应状态
                if response.status_code != 200:
                    logger.error(f"微博API请求失败: HTTP {response.status_code}, {response.text}")
                    break
                
                # 解析响应数据
                data = response.json()
                
                if "statuses" not in data or not data["statuses"]:
                    logger.info("微博API返回的数据为空")
                    break
                
                # 处理每个搜索结果
                for item in data["statuses"]:
                    processed_item = self._process_item(item)
                    if processed_item:
                        results.append(processed_item)
                        
                        # 如果达到限制，则提前结束
                        if len(results) >= limit:
                            break
                
                # 更新页码，准备获取下一页
                page += 1
                
                # 如果返回的结果数量少于请求的数量，说明没有更多数据了
                if len(data["statuses"]) < params["count"]:
                    break
                    
                # 请求间隔，避免频率限制
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                logger.error(f"从微博获取数据时出错: {str(e)}")
                break
        
        return results[:limit]
    
    def _process_item(self, item: Dict) -> Optional[Dict]:
        """处理微博搜索结果项"""
        try:
            # 提取微博ID
            content_id = str(item.get("id", ""))
            
            # 提取微博内容
            content = item.get("text", "")
            
            # 提取作者信息
            user = item.get("user", {})
            author = user.get("screen_name", "")
            
            # 提取地区信息
            location = self._extract_location(item)
            
            # 提取发布时间
            created_at = item.get("created_at", "")
            try:
                # 微博的时间格式较特殊，需要特殊处理
                dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S +0800 %Y")
                publish_time = dt.isoformat()
            except Exception:
                publish_time = ""
            
            # 提取额外信息
            extra_data = {
                "reposts_count": item.get("reposts_count", 0),
                "comments_count": item.get("comments_count", 0),
                "attitudes_count": item.get("attitudes_count", 0),
                "source": item.get("source", "")
            }
            
            return {
                "platform": "weibo",
                "content_id": content_id,
                "content": content,
                "author": author,
                "location": location,
                "publish_time": publish_time,
                "extra_data": extra_data
            }
        except Exception as e:
            logger.error(f"处理微博数据时出错: {str(e)}")
            return None
    
    def _extract_location(self, item: Dict) -> str:
        """从微博中提取地区信息"""
        try:
            # 从用户信息中获取地区
            user = item.get("user", {})
            location = user.get("location", "")
            if location:
                # 微博的location可能是"省份 城市"的格式
                province = location.split(" ")[0] if " " in location else location
                return province
            
            # 从地理信息中获取
            geo = item.get("geo")
            if geo:
                # 这里需要根据实际API返回格式进行调整
                pass
                
            return "未知"
        except Exception as e:
            logger.error(f"提取微博地区信息时出错: {str(e)}")
            return "未知"
