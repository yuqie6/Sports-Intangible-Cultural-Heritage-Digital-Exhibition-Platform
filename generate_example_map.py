"""生成示例地图图片"""
import os
from modules.visualizer.map_visualizer import MapVisualizer
from pyecharts.render import make_snapshot
from snapshot_selenium import snapshot

# 确保目录存在
os.makedirs("static/images", exist_ok=True)

# 示例数据
province_data = {
    "北京": {"score": 0.75, "count": 20},
    "上海": {"score": 0.68, "count": 15},
    "广东": {"score": 0.63, "count": 12},
    "江苏": {"score": 0.58, "count": 8},
    "四川": {"score": 0.45, "count": 6},
    "湖北": {"score": 0.3, "count": 5},
    "山东": {"score": 0.28, "count": 7}
}

# 创建可视化器
visualizer = MapVisualizer()

# 生成地图
chart = visualizer.create_sentiment_map(
    province_data, 
    title="示例情绪地图：'编程竞赛'话题"
)

# 保存为HTML
html_path = "static/images/example_map.html"
chart.render(html_path)

# 转换为PNG (需要安装 snapshot-selenium)
try:
    make_snapshot(snapshot, html_path, "static/images/example_map.png")
    print(f"示例地图已保存到 static/images/example_map.png")
except Exception as e:
    print(f"无法生成PNG: {e}")
    print("请手动将生成的HTML转换为PNG图片")
