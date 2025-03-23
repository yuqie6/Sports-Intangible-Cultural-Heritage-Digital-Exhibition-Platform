import json
import time
import random
import sqlite3
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataCollector:
    """多平台数据采集器"""
    
    def __init__(self, config_path: str = "config/config.json", 
                 api_keys_path: str = "config/api_keys.json"):
        """初始化数据采集器
        
        Args:
            config_path: 主配置文件路径
            api_keys_path: API密钥配置文件路径
        """
        # 加载配置
        self.config = self._load_json(config_path)
        
        # 尝试加载API密钥
        try:
            self.api_keys = self._load_json(api_keys_path)
        except Exception as e:
            logger.warning(f"无法加载API密钥: {str(e)}，将使用有限功能")
            self.api_keys = {}
        
        # 导入平台适配器
        self.adapters = {}
        self._load_platform_adapters()
        
        # 初始化数据库
        self._init_database()
        
    def _load_json(self, file_path: str) -> Dict:
        """加载JSON配置文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"无法加载配置文件 {file_path}: {str(e)}")
            raise
    
    def _load_platform_adapters(self):
        """加载各平台适配器"""
        platforms_config = self.config.get("data_collection", {}).get("platforms", {})
        
        # 导入知乎适配器
        if platforms_config.get("zhihu", {}).get("enabled", False):
            try:
                from .zhihu_api import ZhihuAPI
                self.adapters["zhihu"] = ZhihuAPI(
                    self.config, 
                    self.api_keys.get("zhihu", {})
                )
                logger.info("知乎适配器加载成功")
            except Exception as e:
                logger.error(f"加载知乎适配器失败: {str(e)}")
        
        # 导入微博适配器
        if platforms_config.get("weibo", {}).get("enabled", False):
            try:
                from .weibo_api import WeiboAPI
                self.adapters["weibo"] = WeiboAPI(
                    self.config, 
                    self.api_keys.get("weibo", {})
                )
                logger.info("微博适配器加载成功")
            except Exception as e:
                logger.error(f"加载微博适配器失败: {str(e)}")
    
    def _init_database(self):
        """初始化SQLite数据库"""
        db_path = self.config.get("database", {}).get("path", "db/sentiment_data.db")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        # 创建数据表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS raw_content (
            id INTEGER PRIMARY KEY,
            platform TEXT,
            content_id TEXT,
            keyword TEXT,
            content TEXT,
            author TEXT,
            location TEXT,
            publish_time TEXT,
            collected_at TEXT,
            extra_data TEXT,
            UNIQUE (platform, content_id)
        )
        ''')
        self.conn.commit()
    
    def collect(self, keyword: str, platforms: List[str] = None, 
                limit: int = None, use_cache: bool = True) -> Dict[str, List]:
        """从多个平台收集数据
        
        Args:
            keyword: 搜索关键词
            platforms: 平台列表，默认为全部可用平台
            limit: 每个平台的数据条数限制
            use_cache: 是否使用缓存数据
            
        Returns:
            Dict[str, List]: 按平台分组的数据
        """
        if platforms is None:
            platforms = list(self.adapters.keys())
        
        if limit is None:
            limit = self.config.get("data_collection", {}).get("default_limit", 100)
            
        results = {}
        
        for platform in platforms:
            if platform in self.adapters:
                logger.info(f"正在从{platform}获取关于'{keyword}'的数据...")
                
                # 检查缓存
                if use_cache:
                    cached_data = self._get_from_cache(platform, keyword)
                    if cached_data and len(cached_data) >= limit:
                        logger.info(f"使用缓存数据，共{len(cached_data)}条")
                        results[platform] = cached_data[:limit]
                        continue
                
                # 收集新数据
                try:
                    platform_data = self.adapters[platform].search(keyword, limit)
                    
                    # 存入数据库
                    self._save_to_database(platform, keyword, platform_data)
                    
                    results[platform] = platform_data
                    logger.info(f"成功获取{len(platform_data)}条数据")
                except Exception as e:
                    logger.error(f"从{platform}获取数据失败: {str(e)}")
                    results[platform] = []
                
                # 随机延迟，避免频繁请求
                interval = self.config.get("data_collection", {}).get("request_interval", {})
                time.sleep(random.uniform(
                    interval.get("min", 1), 
                    interval.get("max", 3)
                ))
            else:
                logger.warning(f"平台 {platform} 不可用或未配置适配器")
        
        return results
    
    def _save_to_database(self, platform: str, keyword: str, data: List[Dict]):
        """保存数据到数据库"""
        current_time = datetime.now().isoformat()
        
        for item in data:
            try:
                self.cursor.execute(
                    '''
                    INSERT OR REPLACE INTO raw_content 
                    (platform, content_id, keyword, content, author, location, 
                     publish_time, collected_at, extra_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        platform,
                        item.get("content_id", ""),
                        keyword,
                        item.get("content", ""),
                        item.get("author", ""),
                        item.get("location", "未知"),
                        item.get("publish_time", ""),
                        current_time,
                        json.dumps(item.get("extra_data", {}), ensure_ascii=False)
                    )
                )
            except Exception as e:
                logger.error(f"保存数据失败: {str(e)}")
        
        self.conn.commit()
    
    def _get_from_cache(self, platform: str, keyword: str) -> List[Dict]:
        """从数据库获取缓存数据"""
        # 获取缓存过期天数
        cache_expire_days = self.config.get("app", {}).get("cache_expire_days", 3)
        expire_date = (datetime.now() - timedelta(days=cache_expire_days)).isoformat()
        
        try:
            self.cursor.execute(
                '''
                SELECT platform, content_id, content, author, location, 
                       publish_time, extra_data
                FROM raw_content
                WHERE platform = ? AND keyword = ? AND collected_at > ?
                ''',
                (platform, keyword, expire_date)
            )
            
            results = []
            for row in self.cursor.fetchall():
                results.append({
                    "platform": row[0],
                    "content_id": row[1],
                    "content": row[2],
                    "author": row[3],
                    "location": row[4],
                    "publish_time": row[5],
                    "extra_data": json.loads(row[6]) if row[6] else {}
                })
            
            return results
        except Exception as e:
            logger.error(f"从缓存获取数据失败: {str(e)}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        if hasattr(self, 'conn'):
            self.conn.close()
            logger.info("数据库连接已关闭")

# 使用示例
if __name__ == "__main__":
    collector = DataCollector()
    data = collector.collect("编程竞赛", platforms=["zhihu"], limit=50)
    print(f"获取到知乎数据: {len(data.get('zhihu', []))}条")
    collector.close()
