"""生成和保存静态地图图片"""
import os
import sys
import json
import argparse
from typing import Dict, List, Any
from datetime import datetime
from pyecharts.render import make_snapshot
from snapshot_selenium import snapshot

# 将项目根目录添加到系统路径以导入模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.visualizer.map_visualizer import MapVisualizer

def load_config(config_path="config/config.json") -> Dict:
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置文件失败: {str(e)}")
        return {}

def create_and_save_map(province_data: Dict[str, Dict], 
                       title: str = "情绪地图",
                       output_dir: str = "output") -> Dict:
    """创建并保存情绪地图
    
    Args:
        province_data: 省份情绪数据
        title: 地图标题
        output_dir: 输出目录
        
    Returns:
        Dict: 包含生成文件路径的字典
    """
    # 创建目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 初始化可视化器
    config = load_config()
    visualizer = MapVisualizer(config)
    
    # 文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"sentiment_map_{timestamp}"
    html_path = os.path.join(output_dir, f"{base_filename}.html")
    png_path = os.path.join(output_dir, f"{base_filename}.png")
    
    # 创建地图
    main_map = visualizer.create_sentiment_map(
        province_data,
        title=title
    )
    
    # 保存HTML
    visualizer.save_to_html(main_map, html_path)
    print(f"地图HTML已保存到: {html_path}")
    
    # 生成静态图片
    try:
        make_snapshot(snapshot, html_path, png_path)
        print(f"地图PNG已保存到: {png_path}")
    except Exception as e:
        print(f"生成PNG图片失败: {str(e)}")
        print("请确保已安装snapshot-selenium依赖")
        
    return {
        "html_path": html_path,
        "png_path": png_path if os.path.exists(png_path) else None
    }

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="生成静态情绪地图")
    parser.add_argument("--data", type=str, default=None, help="省份数据JSON文件")
    parser.add_argument("--title", type=str, default="情绪地图", help="地图标题")
    parser.add_argument("--output", type=str, default="output", help="输出目录")
    
    args = parser.parse_args()
    
    # 加载省份数据
    province_data = {}
    if args.data:
        try:
            with open(args.data, 'r', encoding='utf-8') as f:
                province_data = json.load(f)
        except Exception as e:
            print(f"加载数据文件失败: {str(e)}")
            return
    else:
        # 使用示例数据
        province_data = {
            "北京": {"score": 0.75, "count": 20},
            "上海": {"score": 0.68, "count": 15},
            "广东": {"score": 0.63, "count": 12},
            "江苏": {"score": 0.58, "count": 8},
            "四川": {"score": 0.45, "count": 6},
            "湖北": {"score": 0.3, "count": 5},
            "山东": {"score": 0.28, "count": 7}
        }
    
    # 创建和保存地图
    create_and_save_map(province_data, args.title, args.output)

if __name__ == "__main__":
    main()
