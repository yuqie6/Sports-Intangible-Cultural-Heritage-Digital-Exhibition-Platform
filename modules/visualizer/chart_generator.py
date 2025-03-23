from pyecharts import options as opts
from pyecharts.charts import Bar, Pie, Line
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime

# 配置日志
logger = logging.getLogger(__name__)

class ChartGenerator:
    """生成辅助图表，如情绪分布、时间趋势等"""
    
    def __init__(self, config: Dict = None):
        """初始化图表生成器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 获取图表配置
        chart_config = self.config.get("visualization", {}).get("chart", {})
        
        # 图表尺寸
        self.width = chart_config.get("width", "600px")
        self.height = chart_config.get("height", "400px")
        
        # 情感类别映射
        self.sentiment_categories = {
            "very_negative": "非常消极",
            "negative": "消极", 
            "neutral": "中性",
            "positive": "积极",
            "very_positive": "非常积极",
            "insufficient": "数据不足"
        }
        
        logger.info("图表生成器初始化完成")
    
    def create_sentiment_distribution(self, 
                                     sentiment_counts: Dict[str, int], 
                                     chart_type: str = "pie") -> Any:
        """创建情绪分布图表
        
        Args:
            sentiment_counts: 情绪类别计数 {"very_positive": 计数, ...}
            chart_type: 图表类型，"pie"或"bar"
            
        Returns:
            Pie或Bar图表对象
        """
        try:
            # 转换类别名称
            data = [(self.sentiment_categories.get(k, k), v) 
                    for k, v in sentiment_counts.items()]
            
            # 创建图表
            if chart_type == "pie":
                c = (
                    Pie(init_opts=opts.InitOpts(width=self.width, height=self.height))
                    .add(
                        "",
                        data,
                        radius=["30%", "75%"],
                        center=["50%", "50%"],
                        rosetype="radius"
                    )
                    .set_global_opts(
                        title_opts=opts.TitleOpts(title="情绪分布"),
                        legend_opts=opts.LegendOpts(
                            orient="vertical",
                            pos_right="5%",
                            pos_top="middle"
                        )
                    )
                    .set_series_opts(
                        label_opts=opts.LabelOpts(formatter="{b}: {c} ({d}%)")
                    )
                )
            else:  # bar
                x_data = [item[0] for item in data]
                y_data = [item[1] for item in data]
                
                c = (
                    Bar(init_opts=opts.InitOpts(width=self.width, height=self.height))
                    .add_xaxis(x_data)
                    .add_yaxis("数量", y_data)
                    .set_global_opts(
                        title_opts=opts.TitleOpts(title="情绪分布"),
                        xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45)),
                        yaxis_opts=opts.AxisOpts(name="数量")
                    )
                )
                
            return c
            
        except Exception as e:
            logger.error(f"创建情绪分布图表时出错: {str(e)}")
            # 返回一个空图表
            return Pie(init_opts=opts.InitOpts(width=self.width, height=self.height))
    
    def create_platform_comparison_chart(self, 
                                        platform_scores: Dict[str, float]) -> Bar:
        """创建平台对比柱状图
        
        Args:
            platform_scores: {平台: 平均情感得分}
            
        Returns:
            Bar: 平台对比柱状图
        """
        try:
            # 排序数据
            sorted_data = sorted(platform_scores.items(), key=lambda x: x[1])
            platforms = [item[0] for item in sorted_data]
            scores = [item[1] for item in sorted_data]
            
            c = (
                Bar(init_opts=opts.InitOpts(width=self.width, height=self.height))
                .add_xaxis(platforms)
                .add_yaxis("情感得分", scores, category_gap="50%")
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="平台情感得分对比"),
                    xaxis_opts=opts.AxisOpts(
                        axislabel_opts=opts.LabelOpts(rotate=0)
                    ),
                    yaxis_opts=opts.AxisOpts(
                        name="情感得分", 
                        min_=0, 
                        max_=1,
                        axislabel_opts=opts.LabelOpts(formatter="{value}")
                    )
                )
            )
            
            return c
            
        except Exception as e:
            logger.error(f"创建平台对比图表时出错: {str(e)}")
            # 返回一个空图表
            return Bar(init_opts=opts.InitOpts(width=self.width, height=self.height))
    
    def create_time_trend_chart(self, time_data: Dict[str, float]) -> Line:
        """创建时间趋势折线图
        
        Args:
            time_data: {时间点: 平均情感得分}
            
        Returns:
            Line: 时间趋势折线图
        """
        try:
            # 排序数据
            sorted_data = sorted(time_data.items(), key=lambda x: x[0])
            times = []
            scores = []
            
            for time_str, score in sorted_data:
                # 优化时间标签显示
                try:
                    dt = datetime.fromisoformat(time_str)
                    times.append(dt.strftime("%m-%d %H:%M"))
                except:
                    times.append(time_str)
                scores.append(score)
            
            c = (
                Line(init_opts=opts.InitOpts(width=self.width, height=self.height))
                .add_xaxis(times)
                .add_yaxis(
                    "情感得分", 
                    scores, 
                    is_symbol_show=True,
                    symbol_size=8,
                    linestyle_opts=opts.LineStyleOpts(width=2)
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="情感得分时间趋势"),
                    xaxis_opts=opts.AxisOpts(
                        type_="category",
                        axislabel_opts=opts.LabelOpts(rotate=45),
                        boundary_gap=False
                    ),
                    yaxis_opts=opts.AxisOpts(
                        name="情感得分", 
                        min_=0, 
                        max_=1,
                        axislabel_opts=opts.LabelOpts(formatter="{value}")
                    ),
                    tooltip_opts=opts.TooltipOpts(trigger="axis")
                )
            )
            
            return c
            
        except Exception as e:
            logger.error(f"创建时间趋势图表时出错: {str(e)}")
            # 返回一个空图表
            return Line(init_opts=opts.InitOpts(width=self.width, height=self.height))
    
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
