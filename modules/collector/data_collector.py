import json
import time
import random
import sqlite3
import os
import threading
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
        self.config_path = config_path
        self.api_keys_path = api_keys_path
        
        # 尝试加载API密钥
        try:
            self.api_keys = self._load_json(api_keys_path)
        except Exception as e:
            logger.warning(f"无法加载API密钥: {str(e)}，将使用有限功能")
            self.api_keys = {}
        
        # 导入平台适配器
        self.adapters = {}
        self._load_platform_adapters()
        
        # 线程本地存储，保存每个线程的数据库连接
        self.thread_local = threading.local()
        
        # 数据库路径
        self.db_path = self.config.get("database", {}).get("path", "db/sentiment_data.db")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
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
            
        # 导入小红书适配器
        if platforms_config.get("xiaohongshu", {}).get("enabled", False):
            try:
                from .xiaohongshu_api import XiaohongshuAPI
                self.adapters["xiaohongshu"] = XiaohongshuAPI(
                    self.config, 
                    self.api_keys.get("xiaohongshu", {})
                )
                logger.info("小红书适配器加载成功")
            except Exception as e:
                logger.error(f"加载小红书适配器失败: {str(e)}")
    
    def _get_db_connection(self):
        """获取当前线程的数据库连接"""
        if not hasattr(self.thread_local, "conn"):
            # 为当前线程创建新的连接
            self.thread_local.conn = sqlite3.connect(self.db_path)
            self.thread_local.cursor = self.thread_local.conn.cursor()
            
            # 创建数据表
            self.thread_local.cursor.execute('''
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
            self.thread_local.conn.commit()
            
        return self.thread_local.conn, self.thread_local.cursor
    
    def collect(self, keyword: str, platforms: List[str] = None, 
                limit: int = None, use_cache: bool = True, 
                use_mock: bool = True) -> Dict[str, List]:
        """从多个平台收集数据
        
        Args:
            keyword: 搜索关键词
            platforms: 平台列表，默认为全部可用平台
            limit: 每个平台的数据条数限制
            use_cache: 是否使用缓存数据
            use_mock: 当真实数据采集失败时是否使用模拟数据
            
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
                    try:
                        cached_data = self._get_from_cache(platform, keyword)
                        if cached_data and len(cached_data) >= limit:
                            logger.info(f"使用缓存数据，共{len(cached_data)}条")
                            results[platform] = cached_data[:limit]
                            continue
                    except Exception as e:
                        logger.error(f"从缓存获取数据失败: {str(e)}")
                
                # 收集新数据
                try:
                    platform_data = self.adapters[platform].search(keyword, limit)
                    
                    # 如果数据不足且允许使用模拟数据
                    if use_mock and (not platform_data or len(platform_data) < limit // 2):
                        from .mock_data import MockDataGenerator
                        logger.warning(f"从{platform}获取的真实数据不足({len(platform_data)}条)，添加模拟数据")
                        
                        # 创建模拟数据生成器
                        mock_generator = MockDataGenerator()
                        
                        # 生成补充数据
                        mock_count = limit - len(platform_data)
                        mock_data = mock_generator.generate_data(keyword, platform, mock_count)
                        
                        # 合并数据
                        platform_data.extend(mock_data)
                        logger.info(f"已添加 {len(mock_data)} 条模拟数据")
                    
                    # 存入数据库
                    try:
                        self._save_to_database(platform, keyword, platform_data)
                    except Exception as db_error:
                        logger.error(f"保存数据到数据库失败: {str(db_error)}")
                    
                    results[platform] = platform_data
                    logger.info(f"成功获取{len(platform_data)}条数据")
                except Exception as e:
                    logger.error(f"从{platform}获取数据失败: {str(e)}")
                    
                    # 如果采集失败且允许使用模拟数据
                    if use_mock:
                        from .mock_data import MockDataGenerator
                        logger.warning(f"使用模拟数据代替{platform}真实数据")
                        
                        # 创建模拟数据生成器
                        mock_generator = MockDataGenerator()
                        
                        # 生成模拟数据
                        mock_data = mock_generator.generate_data(keyword, platform, limit)
                        
                        results[platform] = mock_data
                        logger.info(f"已生成 {len(mock_data)} 条模拟数据")
                    else:
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
        if not data:
            return
            
        conn, cursor = self._get_db_connection()
        current_time = datetime.now().isoformat()
        
        for item in data:
            try:
                cursor.execute(
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
        
        conn.commit()
    
    def _get_from_cache(self, platform: str, keyword: str) -> List[Dict]:
        """从数据库获取缓存数据"""
        # 获取缓存过期天数
        cache_expire_days = self.config.get("app", {}).get("cache_expire_days", 3)
        expire_date = (datetime.now() - timedelta(days=cache_expire_days)).isoformat()
        
        try:
            conn, cursor = self._get_db_connection()
            
            cursor.execute(
                '''
                SELECT platform, content_id, content, author, location, 
                       publish_time, extra_data
                FROM raw_content
                WHERE platform = ? AND keyword = ? AND collected_at > ?
                ''',
                (platform, keyword, expire_date)
            )
            
            results = []
            for row in cursor.fetchall():
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
        if hasattr(self.thread_local, 'conn'):
            self.thread_local.conn.close()
            logger.info("数据库连接已关闭")
            
        # 关闭平台适配器
        for adapter in self.adapters.values():
            if hasattr(adapter, 'close'):
                adapter.close()

# 使用示例
if __name__ == "__main__":
    collector = DataCollector()
    data = collector.collect("编程竞赛", platforms=["zhihu"], limit=50)
    print(f"获取到知乎数据: {len(data.get('zhihu', []))}条")
    collector.close()
