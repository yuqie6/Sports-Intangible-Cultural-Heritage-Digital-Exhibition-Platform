import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import logging

# 配置日志
logger = logging.getLogger(__name__)

class DataAggregator:
    """数据聚合器，将处理后的数据聚合为可视化所需格式"""
    
    def __init__(self, config: Dict = None):
        """初始化数据聚合器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.minimum_samples = self.config.get("sentiment_analysis", {}).get("minimum_samples", 5)
        logger.info(f"数据聚合器初始化完成，最小样本数: {self.minimum_samples}")
    
    def aggregate_by_province(self, data: pd.DataFrame) -> Dict[str, Dict]:
        """按省份聚合数据
        
        Args:
            data: 处理后的数据DataFrame
            
        Returns:
            Dict: {省份: {"score": 平均得分, "count": 样本数, "categories": 情感类别计数}}
        """
        if data.empty:
            logger.warning("聚合数据为空")
            return {}
        
        # 按省份分组
        try:
            grouped = data.groupby("province")
            
            result = {}
            for province, group in grouped:
                # 跳过"未知"省份
                if province == "未知":
                    continue
                    
                count = len(group)
                
                # 如果样本数不足，则跳过
                if count < self.minimum_samples:
                    logger.info(f"省份 {province} 样本数({count})不足，跳过")
                    continue
                
                # 计算平均情感得分
                avg_score = group["sentiment_score"].mean()
                
                # 计算各情感类别的计数
                category_counts = group["sentiment_category"].value_counts().to_dict()
                
                # 计算置信度加权平均值
                weighted_score = (group["sentiment_score"] * group["confidence"]).sum() / group["confidence"].sum() \
                    if group["confidence"].sum() > 0 else avg_score
                
                result[province] = {
                    "score": float(avg_score),
                    "weighted_score": float(weighted_score),
                    "count": int(count),
                    "categories": category_counts
                }
            
            return result
            
        except Exception as e:
            logger.error(f"按省份聚合数据时出错: {str(e)}")
            return {}
    
    def aggregate_by_platform(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, Dict]]:
        """按平台和省份聚合数据
        
        Args:
            data: {平台: DataFrame}格式的数据
            
        Returns:
            Dict: {平台: {省份: {"score": 平均得分, "count": 样本数}}}
        """
        result = {}
        
        for platform, df in data.items():
            if not df.empty:
                province_data = self.aggregate_by_province(df)
                if province_data:
                    result[platform] = province_data
        
        return result
    
    def get_sentiment_distribution(self, data: pd.DataFrame) -> Dict[str, int]:
        """获取情感分布统计
        
        Args:
            data: 处理后的数据DataFrame
            
        Returns:
            Dict: {情感类别: 计数}
        """
        if data.empty:
            return {}
            
        try:
            # 计算情感类别分布
            distribution = data["sentiment_category"].value_counts().to_dict()
            
            # 添加未知省份的计数
            unknown_count = len(data[data["province"] == "未知"])
            if unknown_count > 0:
                distribution["insufficient"] = unknown_count
                
            return distribution
            
        except Exception as e:
            logger.error(f"获取情感分布时出错: {str(e)}")
            return {}
    
    def get_platform_comparison(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """比较不同平台的总体情感得分
        
        Args:
            data: {平台: DataFrame}格式的数据
            
        Returns:
            Dict: {平台: 平均情感得分}
        """
        result = {}
        
        for platform, df in data.items():
            if not df.empty:
                avg_score = df["sentiment_score"].mean()
                result[platform] = float(avg_score)
                
        return result
    
    def get_time_trend(self, data: pd.DataFrame, interval: str = 'D') -> Dict[str, float]:
        """获取情感随时间的变化趋势
        
        Args:
            data: 处理后的数据DataFrame
            interval: 时间间隔，例如'D'表示按天，'H'表示按小时
            
        Returns:
            Dict: {时间点: 平均情感得分}
        """
        if data.empty:
            return {}
            
        try:
            # 确保publish_time列为datetime类型
            if 'publish_time' in data.columns:
                data['publish_time'] = pd.to_datetime(data['publish_time'], errors='coerce')
                
                # 按时间间隔分组
                grouped = data.groupby(pd.Grouper(key='publish_time', freq=interval))
                
                result = {}
                for time_point, group in grouped:
                    if not group.empty:
                        avg_score = group["sentiment_score"].mean()
                        result[time_point.isoformat()] = float(avg_score)
                
                return result
            else:
                logger.warning("数据中缺少publish_time列，无法生成时间趋势")
                return {}
                
        except Exception as e:
            logger.error(f"获取时间趋势时出错: {str(e)}")
            return {}
