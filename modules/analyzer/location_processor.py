import json
import re
import os
from typing import Dict, List, Optional, Tuple, Set
import logging

# 配置日志
logger = logging.getLogger(__name__)

class LocationProcessor:
    """地区信息处理器"""
    
    def __init__(self, location_dict_path: str = "data/location_dict.json"):
        """初始化地区处理器
        
        Args:
            location_dict_path: 地区词典路径
        """
        # 加载地区词典
        self.location_dict = self._load_location_dict(location_dict_path)
        
        # 省级行政区标准名称和简称映射
        self.province_map = self._create_province_map()
        
        # 大区划分
        self.region_map = {
            "华北": ["北京", "天津", "河北", "山西", "内蒙古"],
            "东北": ["辽宁", "吉林", "黑龙江"],
            "华东": ["上海", "江苏", "浙江", "安徽", "福建", "江西", "山东"],
            "华中": ["河南", "湖北", "湖南"],
            "华南": ["广东", "广西", "海南"],
            "西南": ["重庆", "四川", "贵州", "云南", "西藏"],
            "西北": ["陕西", "甘肃", "青海", "宁夏", "新疆"]
        }
        
        # 创建反向映射
        self.province_to_region = {}
        for region, provinces in self.region_map.items():
            for province in provinces:
                self.province_to_region[province] = region
                
        logger.info("地区处理器初始化完成")
    
    def _load_location_dict(self, file_path: str) -> Dict:
        """加载地区词典"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"无法加载地区词典 {file_path}: {str(e)}")
            raise
    
    def _create_province_map(self) -> Dict[str, str]:
        """创建省级行政区标准名称和简称映射"""
        province_map = {
            "北京": "北京", "京": "北京",
            "天津": "天津", "津": "天津",
            "上海": "上海", "沪": "上海",
            "重庆": "重庆", "渝": "重庆",
            "河北": "河北", "冀": "河北",
            "山西": "山西", "晋": "山西",
            "辽宁": "辽宁", "辽": "辽宁",
            "吉林": "吉林", "吉": "吉林",
            "黑龙江": "黑龙江", "黑": "黑龙江",
            "江苏": "江苏", "苏": "江苏",
            "浙江": "浙江", "浙": "浙江",
            "安徽": "安徽", "皖": "安徽",
            "福建": "福建", "闽": "福建",
            "江西": "江西", "赣": "江西",
            "山东": "山东", "鲁": "山东",
            "河南": "河南", "豫": "河南",
            "湖北": "湖北", "鄂": "湖北",
            "湖南": "湖南", "湘": "湖南",
            "广东": "广东", "粤": "广东",
            "广西": "广西", "桂": "广西",
            "海南": "海南", "琼": "海南",
            "四川": "四川", "川": "四川", "蜀": "四川",
            "贵州": "贵州", "黔": "贵州", "贵": "贵州",
            "云南": "云南", "滇": "云南", "云": "云南",
            "西藏": "西藏", "藏": "西藏",
            "陕西": "陕西", "陕": "陕西", "秦": "陕西",
            "甘肃": "甘肃", "甘": "甘肃", "陇": "甘肃",
            "青海": "青海", "青": "青海",
            "宁夏": "宁夏", "宁": "宁夏",
            "新疆": "新疆", "新": "新疆",
            "内蒙古": "内蒙古", "内蒙": "内蒙古",
            "香港": "香港", "港": "香港",
            "澳门": "澳门", "澳": "澳门",
            "台湾": "台湾", "台": "台湾"
        }
        return province_map
    
    def extract_location(self, text: str) -> List[str]:
        """从文本中提取可能的地区名称
        
        Args:
            text: 输入文本
            
        Returns:
            提取的地区名称列表
        """
        locations = []
        for alias in self.province_map.keys():
            if alias in text:
                locations.append(alias)
        return locations
    
    def standardize_location(self, location: str) -> Optional[str]:
        """标准化地区名称
        
        Args:
            location: 地区名称
            
        Returns:
            标准化后的省级行政区名称，如果无法识别则返回None
        """
        if not location:
            return None
            
        # 直接匹配
        if location in self.province_map:
            return self.province_map[location]
        
        # 部分匹配
        for alias, province in self.province_map.items():
            if alias in location:
                return province
        
        # 检查是否是城市
        city_to_province = self.location_dict.get("city_to_province", {})
        for city, province in city_to_province.items():
            if city in location:
                return province
        
        return None
    
    def get_region(self, province: str) -> Optional[str]:
        """获取省份所属大区
        
        Args:
            province: 省级行政区名称
            
        Returns:
            大区名称，如果无法识别则返回None
        """
        standardized = self.standardize_location(province)
        if not standardized:
            return None
            
        return self.province_to_region.get(standardized)
    
    def analyze_text_location(self, text: str) -> Dict[str, str]:
        """分析文本中的地区信息
        
        Args:
            text: 输入文本
            
        Returns:
            Dict: {"province": 省份, "region": 大区}
        """
        locations = self.extract_location(text)
        
        if not locations:
            return {"province": "未知", "region": "未知"}
        
        # 使用第一个识别到的位置
        province = self.standardize_location(locations[0])
        if not province:
            return {"province": "未知", "region": "未知"}
            
        region = self.get_region(province)
        
        return {
            "province": province,
            "region": region if region else "未知"
        }
    
    def merge_location_info(self, text_location: Dict[str, str], 
                           user_location: Dict[str, str]) -> Dict[str, str]:
        """合并文本和用户资料中的地区信息
        
        Args:
            text_location: 从文本提取的地区
            user_location: 从用户资料获取的地区
            
        Returns:
            Dict: {"province": 省份, "region": 大区}
        """
        # 优先使用用户资料中的位置
        if user_location.get("province") != "未知":
            return user_location
            
        # 其次使用文本中提取的位置    
        if text_location.get("province") != "未知":
            return text_location
            
        # 都无法识别时返回未知
        return {"province": "未知", "region": "未知"}