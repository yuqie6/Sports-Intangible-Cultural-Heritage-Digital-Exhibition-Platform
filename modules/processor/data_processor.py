import logging
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
from datetime import datetime

from ..analyzer.sentiment_analyzer import SentimentAnalyzer
from ..analyzer.location_processor import LocationProcessor

# 配置日志
logger = logging.getLogger(__name__)

class DataProcessor:
    """数据处理管道，将原始数据转换为结构化分析结果"""
    
    def __init__(self, config: Dict = None):
        """初始化数据处理器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 初始化情感分析器（默认使用general领域）
        self.sentiment_analyzer = SentimentAnalyzer(config=config)
        
        # 初始化地区处理器
        self.location_processor = LocationProcessor()
        
        logger.info("数据处理器初始化完成")
    
    def process(self, data: Dict[str, List[Dict]], domain: str = "general") -> Dict[str, Any]:
        """处理从不同平台收集的数据
        
        Args:
            data: {平台: [数据项]}格式的原始数据
            domain: 情感分析领域
            
        Returns:
            Dict: 处理后的结构化数据
        """
        # 如果需要特定领域的情感分析，则重新初始化分析器
        if domain != "general":
            self.sentiment_analyzer = SentimentAnalyzer(config=self.config, domain=domain)
            logger.info(f"已切换到 {domain} 领域情感分析")
        
        all_processed_data = []
        platform_processed_data = {}
        
        # 处理每个平台的数据
        for platform, platform_data in data.items():
            logger.info(f"处理 {platform} 平台数据，共 {len(platform_data)} 条")
            
            processed_platform_data = []
            for item in platform_data:
                processed_item = self._process_item(item)
                if processed_item:
                    processed_platform_data.append(processed_item)
                    all_processed_data.append(processed_item)
            
            platform_processed_data[platform] = processed_platform_data
            logger.info(f"{platform} 平台数据处理完成，有效数据 {len(processed_platform_data)} 条")
        
        # 转换为DataFrame便于后续处理
        if all_processed_data:
            all_df = pd.DataFrame(all_processed_data)
            platforms_df = {platform: pd.DataFrame(data) 
                           for platform, data in platform_processed_data.items() 
                           if data}
            
            return {
                "all_data": all_df,
                "platform_data": platforms_df,
                "raw_processed": all_processed_data,
                "platform_raw_processed": platform_processed_data
            }
        else:
            logger.warning("没有有效的处理结果")
            return {
                "all_data": pd.DataFrame(),
                "platform_data": {},
                "raw_processed": [],
                "platform_raw_processed": {}
            }
    
    def _process_item(self, item: Dict) -> Optional[Dict]:
        """处理单个数据项
        
        Args:
            item: 原始数据项
            
        Returns:
            Dict: 处理后的数据项，失败返回None
        """
        try:
            # 提取基本信息
            content = item.get("content", "")
            platform = item.get("platform", "")
            author = item.get("author", "")
            location = item.get("location", "未知")
            publish_time = item.get("publish_time", "")
            
            # 跳过内容为空的项
            if not content:
                return None
            
            # 情感分析
            sentiment_result = self.sentiment_analyzer.analyze(content)
            
            # 地区处理
            # 如果原始数据中已有地区信息，则优先使用
            location_from_user = {}
            if location and location != "未知":
                province = self.location_processor.standardize_location(location)
                if province:
                    region = self.location_processor.get_region(province)
                    location_from_user = {
                        "province": province,
                        "region": region if region else "未知"
                    }
                else:
                    location_from_user = {"province": "未知", "region": "未知"}
            else:
                location_from_user = {"province": "未知", "region": "未知"}
            
            # 从内容中提取地区信息
            location_from_text = self.location_processor.analyze_text_location(content)
            
            # 合并地区信息
            location_info = self.location_processor.merge_location_info(
                location_from_text, location_from_user
            )
            
            # 组装处理后的数据项
            processed_item = {
                "platform": platform,
                "content_id": item.get("content_id", ""),
                "content": content,
                "author": author,
                "province": location_info["province"],
                "region": location_info["region"],
                "publish_time": publish_time,
                "sentiment_score": sentiment_result["score"],
                "sentiment_category": sentiment_result["category"],
                "confidence": sentiment_result["confidence"],
                "processed_at": datetime.now().isoformat()
            }
            
            # 添加额外信息
            extra_data = item.get("extra_data", {})
            if extra_data:
                for key, value in extra_data.items():
                    if key not in processed_item:
                        processed_item[f"extra_{key}"] = value
            
            return processed_item
            
        except Exception as e:
            logger.error(f"处理数据项时出错: {str(e)}")
            return None
    
    def set_analyzer_domain(self, domain: str):
        """设置情感分析器的领域
        
        Args:
            domain: 领域名称
        """
        self.sentiment_analyzer = SentimentAnalyzer(config=self.config, domain=domain)
        logger.info(f"情感分析器已切换到 {domain} 领域")
