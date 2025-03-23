import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import time
import base64
from datetime import datetime
import logging
from typing import Dict, List, Any, Optional
import tempfile
from pyecharts import options as opts
from pyecharts.charts import Map, Timeline, Pie, Bar, Line
from streamlit_echarts import st_pyecharts

# 导入模块
from modules.collector.data_collector import DataCollector
from modules.processor.data_processor import DataProcessor
from modules.processor.data_aggregator import DataAggregator
from modules.visualizer.map_visualizer import MapVisualizer
from modules.visualizer.chart_generator import ChartGenerator

# 导入日志配置
from config.logging_config import setup_logging

# 设置日志
setup_logging(debug=False)

# 配置日志
logging.basicConfig(
    level=logging.ERROR,  # 将级别改为ERROR,只显示错误信息
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('streamlit_app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 加载配置
@st.cache_data
def load_config(config_path="config/config.json"):
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {str(e)}")
        return {}

# 初始化应用
def init_app(config):
    # 不再在缓存函数中创建DataCollector实例
    processor = DataProcessor(config)
    aggregator = DataAggregator(config)
    map_visualizer = MapVisualizer(config)
    chart_generator = ChartGenerator(config)
    return {
        'processor': processor,
        'aggregator': aggregator,
        'map_visualizer': map_visualizer,
        'chart_generator': chart_generator
    }

# 获取可用领域
@st.cache_data
def get_available_domains():
    domains = ["general"]  # 默认通用领域
    domain_dir = "data/sentiment_dict"
    try:
        if os.path.exists(domain_dir):
            for file in os.listdir(domain_dir):
                if file.endswith(".json"):
                    domain_name = file.replace(".json", "")
                    if domain_name != "general":
                        domains.append(domain_name)
    except:
        pass
    return domains

# 下载数据
def get_csv_download_link(df, filename="data.csv"):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">下载 CSV 文件</a>'
    return href

# 应用标题和介绍
def render_header():
    st.set_page_config(
        page_title="中国社交媒体情绪地图",
        page_icon="🌏",
        layout="wide"
    )
    st.title("🌏 中国社交媒体情绪地图")
    st.markdown("""
    这个应用可以分析社交媒体上关于特定话题的情绪倾向，并在中国地图上显示不同地区的情绪差异。
    
    **使用方法：** 输入关键词（如"编程竞赛"），选择平台和其他参数，然后点击"开始分析"按钮。
    """)

# 侧边栏参数设置
def render_sidebar():
    st.sidebar.header("参数设置")
    
    # 关键词输入
    keyword = st.sidebar.text_input("关键词", value="编程竞赛", help="输入要分析的关键词")
    
    # 平台选择 - 添加小红书作为选项
    platforms = st.sidebar.multiselect(
        "数据来源平台",
        options=["zhihu", "weibo", "xiaohongshu"],
        default=["zhihu", "xiaohongshu"],
        help="选择要分析的平台"
    )
    
    # 数据量设置
    data_limit = st.sidebar.slider(
        "每个平台数据量",
        min_value=20,
        max_value=200,
        value=100,
        step=10,
        help="每个平台获取的数据条数"
    )
    
    # 领域选择
    domains = get_available_domains()
    domain = st.sidebar.selectbox(
        "情感分析领域",
        options=domains,
        index=0,
        help="选择特定领域的情感分析词典"
    )
    
    # 显示设置
    st.sidebar.header("显示设置")
    
    # 地图显示方式选择
    map_display = st.sidebar.radio(
        "地图显示方式",
        options=["交互式HTML", "静态图片"],
        index=0,
        help="选择地图的显示方式。如果HTML版本无法正常显示，请尝试静态图片。"
    )
    
    # 操作按钮
    start_button = st.sidebar.button("开始分析")
    
    # 关于信息
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### 关于
    中国社交媒体情绪地图是一个开源项目，旨在分析社交平台上的公开内容，展示不同地区对特定话题的情绪差异。
    
    [查看项目源码](https://github.com/yourusername/china-social-media-sentiment-map)
    """)
    
    return {
        "keyword": keyword,
        "platforms": platforms,
        "data_limit": data_limit,
        "domain": domain,
        "map_display": map_display,
        "start_button": start_button
    }

# 处理和展示结果
def process_and_display(components, params):
    if not params["platforms"]:
        st.error("请至少选择一个平台")
        return
    
    # 显示处理进度
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    try:
        # 数据采集 - 为每个请求创建新的收集器
        progress_placeholder.progress(0.1)
        status_placeholder.info("正在采集数据...")
        
        # 每次调用创建新的收集器实例
        collector = DataCollector()
        start_time = time.time()
        
        raw_data = collector.collect(
            params["keyword"], 
            params["platforms"], 
            params["data_limit"]
        )
        
        data_count = sum(len(items) for items in raw_data.values())
        if data_count == 0:
            status_placeholder.error(f"没有找到关于\"{params['keyword']}\"的相关内容，请尝试其他关键词")
            progress_placeholder.empty()
            return
            
        progress_placeholder.progress(0.3)
        status_placeholder.info(f"已采集 {data_count} 条数据，正在处理...")
        
        # 数据处理
        processor = components['processor']
        processed_data = processor.process(raw_data, params["domain"])
        
        all_data = processed_data.get("all_data")
        if all_data.empty:
            status_placeholder.error("处理后没有有效数据，请尝试其他关键词或平台")
            progress_placeholder.empty()
            return
            
        progress_placeholder.progress(0.6)
        status_placeholder.info(f"数据处理完成，正在生成可视化...")
        
        # 数据聚合
        aggregator = components['aggregator']
        province_data = aggregator.aggregate_by_province(all_data)
        
        if not province_data:
            status_placeholder.warning("没有足够的地区信息用于生成地图，显示部分结果")
        
        # 平台聚合
        platform_province_data = aggregator.aggregate_by_platform(
            processed_data.get("platform_data", {})
        )
        
        # 情感分布
        sentiment_distribution = aggregator.get_sentiment_distribution(all_data)
        
        # 平台比较
        platform_comparison = aggregator.get_platform_comparison(
            processed_data.get("platform_data", {})
        )
        
        # 时间趋势
        time_trend = aggregator.get_time_trend(all_data)
        
        progress_placeholder.progress(0.8)
        status_placeholder.info("正在渲染结果...")
        
        # 生成可视化
        map_visualizer = components['map_visualizer']
        chart_generator = components['chart_generator']
        
        # 清除进度和状态
        elapsed_time = time.time() - start_time
        progress_placeholder.empty()
        status_placeholder.success(f"分析完成！耗时 {elapsed_time:.1f} 秒")
        
        # 创建结果选项卡
        tab1, tab2, tab3, tab4 = st.tabs(["情绪地图", "情感分布", "平台对比", "原始数据"])
        
        with tab1:
            st.header(f"关于\"{params['keyword']}\"的情绪地图")
            
            # 显示情绪地图
            if province_data:
                main_map = map_visualizer.create_sentiment_map(
                    province_data,
                    title=f"'{params['keyword']}' 情绪地图"
                )
                
                # 根据选择的显示方式显示地图
                if params["map_display"] == "交互式HTML":
                    try:
                        st_pyecharts(main_map, height="500px")
                    except Exception as e:
                        st.error(f"显示交互式地图时出错: {str(e)}")
                        st.info("尝试使用静态图片代替...")
                        
                        # 生成静态图片
                        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp:
                            temp_html = tmp.name
                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                            temp_png = tmp.name
                            
                        # 保存HTML和PNG
                        map_visualizer.save_to_html(main_map, temp_html)
                        map_visualizer.save_to_png(main_map, temp_png)
                        
                        # 显示静态图片
                        if os.path.exists(temp_png):
                            st.image(temp_png, caption=f"'{params['keyword']}' 情绪地图")
                else:
                    # 直接生成静态图片
                    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp:
                        temp_html = tmp.name
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                        temp_png = tmp.name
                        
                    # 保存HTML和PNG
                    map_visualizer.save_to_html(main_map, temp_html)
                    map_visualizer.save_to_png(main_map, temp_png)
                    
                    # 显示静态图片
                    if os.path.exists(temp_png):
                        st.image(temp_png, caption=f"'{params['keyword']}' 情绪地图")
                
                # 如果有多个平台，显示平台对比
                if len(platform_province_data) > 1:
                    st.subheader("不同平台的情绪差异")
                    platform_timeline = map_visualizer.create_platform_comparison(
                        platform_province_data,
                        list(platform_province_data.keys())
                    )
                    
                    # 根据显示方式显示平台对比
                    if params["map_display"] == "交互式HTML":
                        try:
                            st_pyecharts(platform_timeline, height="500px")
                        except:
                            st.error("无法显示交互式平台对比地图")
                    else:
                        # 生成静态平台对比图片
                        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp:
                            temp_platform_html = tmp.name
                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                            temp_platform_png = tmp.name
                            
                        map_visualizer.save_to_html(platform_timeline, temp_platform_html)
                        map_visualizer.save_to_png(platform_timeline, temp_platform_png)
                        
                        if os.path.exists(temp_platform_png):
                            st.image(temp_platform_png, caption="平台情绪对比")
            else:
                st.warning("没有足够的地区数据来生成地图。这可能是因为：\n\n"
                           "1. 社交媒体内容缺少地区信息\n"
                           "2. 样本数量不足以生成有代表性的地区分布")
                
            # 显示省份详情
            if province_data:
                st.subheader("省份详情")
                province_df = pd.DataFrame([
                    {
                        "省份": province,
                        "情绪得分": data["score"],
                        "样本数量": data["count"],
                        "情绪类别": data["score"] < 0.4 and "消极" or (
                            data["score"] > 0.6 and "积极" or "中性"
                        )
                    }
                    for province, data in province_data.items()
                ]).sort_values("情绪得分", ascending=False)
                
                st.dataframe(province_df)
        
        with tab2:
            st.header("情感分布分析")
            
            # 情感分布饼图
            if sentiment_distribution:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("情感类别分布")
                    sentiment_pie = chart_generator.create_sentiment_distribution(
                        sentiment_distribution, "pie"
                    )
                    st_pyecharts(sentiment_pie, height="400px")
                
                with col2:
                    st.subheader("情感类别统计")
                    sentiment_df = pd.DataFrame([
                        {"情感类别": components['map_visualizer'].sentiment_categories.get(k, k), 
                         "数量": v, 
                         "百分比": f"{v/sum(sentiment_distribution.values())*100:.1f}%"}
                        for k, v in sentiment_distribution.items()
                    ])
                    st.dataframe(sentiment_df)
            
            # 时间趋势
            if time_trend and len(time_trend) > 1:
                st.subheader("情感得分随时间变化")
                time_line = chart_generator.create_time_trend_chart(time_trend)
                st_pyecharts(time_line, height="400px")
        
        with tab3:
            st.header("平台数据对比")
            
            if len(platform_comparison) > 1:
                # 平台情绪得分对比
                st.subheader("平台情绪得分对比")
                platform_bar = chart_generator.create_platform_comparison_chart(
                    platform_comparison
                )
                st_pyecharts(platform_bar, height="400px")
            
            # 平台数据统计
            platform_stats = []
            for platform, items in raw_data.items():
                if items:
                    processed = processed_data["platform_data"].get(platform, pd.DataFrame())
                    platform_stats.append({
                        "平台": platform,
                        "原始数据量": len(items),
                        "有效数据量": len(processed) if not processed.empty else 0,
                        "平均情绪得分": platform_comparison.get(platform, 0),
                        "有地区信息比例": f"{len(processed[processed['province'] != '未知'])/len(processed)*100:.1f}%" if not processed.empty and len(processed) > 0 else "0%"
                    })
            
            if platform_stats:
                st.subheader("平台数据统计")
                st.dataframe(pd.DataFrame(platform_stats))
                
                # 添加平台说明
                st.markdown("""
                **平台说明**:
                - **知乎**: 问答社区，内容偏向专业和深度
                - **微博**: 短内容社交平台，实时性强
                - **小红书**: 生活方式分享社区，内容偏向个人体验
                """)
        
        with tab4:
            st.header("原始处理数据")
            
            # 显示原始数据表格
            if not all_data.empty:
                st.dataframe(all_data)
                
                # 添加下载链接
                st.markdown(get_csv_download_link(all_data, f"{params['keyword']}_data.csv"), unsafe_allow_html=True)
            else:
                st.info("没有处理后的数据可供显示")
    
    except Exception as e:
        logger.error(f"处理过程中出错: {str(e)}")
        progress_placeholder.empty()
        status_placeholder.error(f"处理失败: {str(e)}")
        st.exception(e)

# 主函数
def main():
    # 渲染页面头部
    render_header()
    
    # 侧边栏参数
    params = render_sidebar()
    
    # 加载配置和初始化组件
    config = load_config()
    components = init_app(config)
    
    # 如果点击分析按钮，处理和显示结果
    if params["start_button"]:
        process_and_display(components, params)
    else:
        # 显示欢迎内容
        st.info("👈 请在左侧设置参数并点击\"开始分析\"按钮开始分析")
        
        # 显示示例图片
        if os.path.exists("static/images/example_map.png"):
            st.image("static/images/example_map.png", caption="示例情绪地图", use_column_width=True)
        else:
            # 如果没有示例图片，显示提示信息
            st.warning("没有找到示例图片，您可以运行 `python generate_example_map.py` 生成示例图片")
            st.markdown("""
            ## 支持的平台
            
            本工具现在支持以下平台的数据采集与分析：
            
            - **知乎**: 中国最大的问答社区之一
            - **微博**: 中国流行的微博客平台
            - **小红书**: 生活方式分享社区
            
            针对知乎的反爬机制，我们提供了模拟数据生成功能。如果您在分析时没有得到足够的真实数据，系统将自动补充模拟数据。
            """)

if __name__ == "__main__":
    main()
