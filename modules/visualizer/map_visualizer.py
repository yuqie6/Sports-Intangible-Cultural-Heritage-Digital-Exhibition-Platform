from pyecharts import options as opts
from pyecharts.charts import Map, Timeline
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import logging

# 配置日志
logger = logging.getLogger(__name__)

class MapVisualizer:
    """情绪地图可视化工具"""
    
    def __init__(self, config: Dict = None):
        """初始化可视化工具
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 获取可视化配置
        visual_config = self.config.get("visualization", {}).get("map", {})
        
        # 地图尺寸
        self.width = visual_config.get("width", "900px")
        self.height = visual_config.get("height", "600px")
        
        # 颜色配置
        self.color_ranges = visual_config.get("color_ranges", [
            "#FF4136",  # 非常消极 (0.0-0.2)
            "#FF851B",  # 消极 (0.2-0.4)
            "#FFDC00",  # 中性 (0.4-0.6)
            "#2ECC40",  # 积极 (0.6-0.8)
            "#01FF70",  # 非常积极 (0.8-1.0)
        ])
        
        # 数据不足颜色
        self.insufficient_data_color = visual_config.get("insufficient_data_color", "#CCCCCC")
        
        # 情感类别映射
        self.sentiment_categories = {
            "very_negative": "非常消极",
            "negative": "消极", 
            "neutral": "中性",
            "positive": "积极",
            "very_positive": "非常积极",
            "insufficient": "数据不足"
        }
        
        logger.info("地图可视化器初始化完成")
    
    def create_sentiment_map(self, 
                            province_data: Dict[str, Dict], 
                            title: str = "中国社交媒体情绪地图",
                            subtitle: str = None) -> Map:
        """创建情绪地图
        
        Args:
            province_data: 省份情绪数据 {省份: {"score": 情感得分, "count": 样本数}}
            title: 地图标题
            subtitle: 副标题
            
        Returns:
            Map: 情绪地图
        """
        try:
            # 准备地图数据
            data_pairs = []
            insufficient_data = []
            
            minimum_samples = self.config.get("sentiment_analysis", {}).get("minimum_samples", 5)
            
            for province, data in province_data.items():
                if data.get("count", 0) >= minimum_samples:  # 至少N个样本才视为有效
                    data_pairs.append((province, data["score"]))
                else:
                    insufficient_data.append((province, 0))
            
            # 创建地图
            full_title = title
            if subtitle:
                full_title = f"{title}\n{subtitle}"
                
            c = (
                Map(init_opts=opts.InitOpts(width=self.width, height=self.height))
                .add(
                    "情绪指数", 
                    data_pairs, 
                    "china",
                    is_map_symbol_show=False,
                    label_opts=opts.LabelOpts(is_show=True),
                    tooltip_opts=opts.TooltipOpts(
                        formatter=self._sentiment_tooltip_formatter
                    )
                )
            )
            
            # 如果有数据不足的省份，添加额外系列
            if insufficient_data:
                c.add(
                    "数据不足", 
                    insufficient_data, 
                    "china",
                    is_map_symbol_show=False,
                    label_opts=opts.LabelOpts(is_show=True),
                    itemstyle_opts=opts.ItemStyleOpts(color=self.insufficient_data_color)
                )
            
            # 设置全局选项
            c.set_global_opts(
                title_opts=opts.TitleOpts(
                    title=full_title,
                    subtitle="数据来源：知乎、微博",
                    pos_left="center"
                ),
                visualmap_opts=opts.VisualMapOpts(
                    min_=0,
                    max_=1,
                    range_color=self.color_ranges,
                    is_piecewise=False,
                    pos_left="10%",
                    pos_bottom="10%",
                    orient="horizontal",
                    range_text=["极端消极", "极端积极"],
                    textstyle_opts=opts.TextStyleOpts(color="#000")
                ),
                legend_opts=opts.LegendOpts(
                    is_show=True,
                    pos_right="10%",
                    pos_bottom="10%",
                    orient="vertical"
                )
            )
            
            return c
            
        except Exception as e:
            logger.error(f"创建情绪地图时出错: {str(e)}")
            # 返回一个空地图
            return Map(init_opts=opts.InitOpts(width=self.width, height=self.height)).add(
                "无数据", 
                [("北京", 0)], 
                "china",
                is_map_symbol_show=False
            )
    
    def _sentiment_tooltip_formatter(self, params):
        """自定义情绪提示框格式化"""
        province = params.name
        value = params.value
        
        if params.seriesName == "数据不足":
            return f"{province}: 数据不足"
            
        category = "未知"
        if 0 <= value < 0.2:
            category = "非常消极"
        elif 0.2 <= value < 0.4:
            category = "消极"
        elif 0.4 <= value < 0.6:
            category = "中性"
        elif 0.6 <= value < 0.8:
            category = "积极"
        elif 0.8 <= value <= 1:
            category = "非常积极"
            
        return f"{province}<br/>情绪得分: {value:.2f}<br/>情绪类别: {category}"
    
    def create_platform_comparison(self, 
                                 province_data: Dict[str, Dict[str, Dict]], 
                                 platforms: List[str]) -> Timeline:
        """创建平台对比时间轴
        
        Args:
            province_data: {平台: {省份: {"score": 情感得分, "count": 样本数}}}
            platforms: 平台列表
            
        Returns:
            Timeline: 平台对比时间轴
        """
        try:
            timeline = Timeline(init_opts=opts.InitOpts(width=self.width, height=self.height))
            timeline.add_schema(
                play_interval=3000,
                is_auto_play=True,
                is_loop_play=True
            )
            
            for platform in platforms:
                if platform in province_data:
                    platform_map = self.create_sentiment_map(
                        province_data[platform],
                        title="中国社交媒体情绪地图",
                        subtitle=f"平台：{platform}"
                    )
                    timeline.add(platform_map, platform)
                    
            return timeline
            
        except Exception as e:
            logger.error(f"创建平台对比时间轴时出错: {str(e)}")
            # 返回一个空时间轴
            map_chart = Map(init_opts=opts.InitOpts(width=self.width, height=self.height)).add(
                "无数据", 
                [("北京", 0)], 
                "china",
                is_map_symbol_show=False
            )
            timeline = Timeline(init_opts=opts.InitOpts(width=self.width, height=self.height))
            timeline.add(map_chart, "无数据")
            return timeline
    
    def save_to_html(self, chart, file_path: str):
        """保存图表为HTML文件
        
        Args:
            chart: pyecharts图表对象
            file_path: 输出文件路径
        """
        try:
            chart.render(file_path)
            logger.info(f"图表已保存至: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存图表时出错: {str(e)}")
            return False
    
    def save_to_png(self, chart, file_path: str) -> bool:
        """保存图表为PNG图片
        
        Args:
            chart: pyecharts图表对象
            file_path: 输出文件路径
            
        Returns:
            bool: 是否成功保存
        """
        try:
            # 首先保存为临时HTML文件
            temp_html = file_path.replace('.png', '_temp.html')
            chart.render(temp_html)
            
            # 使用snapshot-selenium将HTML转换为PNG
            from pyecharts.render import make_snapshot
            from snapshot_selenium import snapshot
            
            make_snapshot(snapshot, temp_html, file_path)
            
            # 删除临时HTML文件
            import os
            if os.path.exists(temp_html):
                os.remove(temp_html)
            
            logger.info(f"图表已保存为PNG图片: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存PNG图片时出错: {str(e)}")
            return False
