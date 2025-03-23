from flask import Flask, request, jsonify, send_file
import os
import json
import time
import logging
from typing import Dict, List, Any
from datetime import datetime
import tempfile
import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 导入模块
from modules.collector.data_collector import DataCollector
from modules.processor.data_processor import DataProcessor
from modules.processor.data_aggregator import DataAggregator
from modules.visualizer.map_visualizer import MapVisualizer
from modules.visualizer.chart_generator import ChartGenerator

# 初始化Flask应用
app = Flask(__name__)

# 初始化组件
config_path = "config/config.json"
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    logger.info("配置加载成功")
except Exception as e:
    logger.error(f"配置加载失败: {str(e)}")
    config = {}

collector = DataCollector(config_path)
processor = DataProcessor(config)
aggregator = DataAggregator(config)
map_visualizer = MapVisualizer(config)
chart_generator = ChartGenerator(config)

# 为了在API中跟踪活跃任务
active_tasks = {}

# 路由：API首页
@app.route('/')
def index():
    return jsonify({
        "name": "中国社交媒体情绪地图 API",
        "version": config.get("app", {}).get("version", "1.0.0"),
        "endpoints": {
            "/api/collect": "采集数据 (POST)",
            "/api/analyze": "分析数据 (POST)",
            "/api/visualize": "生成可视化 (POST)",
            "/api/sentiment_map": "完整处理流程 (POST)"
        }
    })

# 路由：采集数据
@app.route('/api/collect', methods=['POST'])
def collect_data():
    try:
        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "无效的请求数据"}), 400
            
        keyword = data.get('keyword')
        if not keyword:
            return jsonify({"success": False, "error": "必须提供关键词"}), 400
            
        platforms = data.get('platforms', ["zhihu"])
        limit = data.get('limit', None)
        use_cache = data.get('use_cache', True)
        
        # 采集数据
        logger.info(f"开始采集数据，关键词: {keyword}, 平台: {platforms}")
        start_time = time.time()
        
        raw_data = collector.collect(keyword, platforms, limit, use_cache)
        
        # 统计结果
        total_count = sum(len(items) for items in raw_data.values())
        platform_counts = {platform: len(items) for platform, items in raw_data.items()}
        
        elapsed_time = time.time() - start_time
        logger.info(f"数据采集完成，共 {total_count} 条，耗时: {elapsed_time:.2f}秒")
        
        return jsonify({
            "success": True,
            "keyword": keyword,
            "total_count": total_count,
            "platform_counts": platform_counts,
            "elapsed_time": elapsed_time,
            # 不直接返回原始数据，避免响应过大
            "data_summary": {
                platform: {
                    "count": len(items),
                    "sample": items[0] if items else None
                } for platform, items in raw_data.items()
            }
        })
    except Exception as e:
        logger.error(f"采集数据时出错: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# 路由：分析数据
@app.route('/api/analyze', methods=['POST'])
def analyze_data():
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "无效的请求数据"}), 400
            
        # 检查是否提供了原始数据或关键词
        raw_data = data.get('raw_data')
        keyword = data.get('keyword')
        
        if not raw_data and not keyword:
            return jsonify({
                "success": False, 
                "error": "必须提供原始数据或关键词"
            }), 400
        
        # 如果只提供了关键词，先采集数据
        if not raw_data and keyword:
            platforms = data.get('platforms', ["zhihu"])
            limit = data.get('limit', None)
            use_cache = data.get('use_cache', True)
            
            logger.info(f"使用关键词采集数据: {keyword}")
            raw_data = collector.collect(keyword, platforms, limit, use_cache)
        
        # 分析数据
        domain = data.get('domain', 'general')
        logger.info(f"开始分析数据，领域: {domain}")
        
        start_time = time.time()
        processed_data = processor.process(raw_data, domain)
        
        # 检查是否有处理后的数据
        all_data = processed_data.get("all_data")
        if all_data.empty:
            return jsonify({
                "success": False, 
                "error": "处理后没有有效数据"
            }), 400
        
        # 数据聚合
        province_data = aggregator.aggregate_by_province(all_data)
        sentiment_distribution = aggregator.get_sentiment_distribution(all_data)
        
        elapsed_time = time.time() - start_time
        logger.info(f"数据分析完成，有效数据 {len(all_data)} 条，耗时: {elapsed_time:.2f}秒")
        
        return jsonify({
            "success": True,
            "data_count": len(all_data),
            "province_count": len(province_data),
            "elapsed_time": elapsed_time,
            "sentiment_distribution": sentiment_distribution,
            "province_data": province_data
        })
    except Exception as e:
        logger.error(f"分析数据时出错: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# 路由：生成可视化
@app.route('/api/visualize', methods=['POST'])
def generate_visualization():
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "无效的请求数据"}), 400
        
        # 检查是否提供了省份数据
        province_data = data.get('province_data')
        if not province_data:
            return jsonify({
                "success": False, 
                "error": "必须提供省份数据"
            }), 400
        
        # 生成可视化
        title = data.get('title', '情绪地图')
        logger.info(f"生成可视化: {title}")
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp:
            temp_path = tmp.name
        
        # 创建并保存地图
        main_map = map_visualizer.create_sentiment_map(
            province_data,
            title=title
        )
        map_visualizer.save_to_html(main_map, temp_path)
        
        logger.info(f"可视化生成完成，保存至临时文件: {temp_path}")
        
        # 返回文件
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=f"sentiment_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            mimetype='text/html'
        )
    except Exception as e:
        logger.error(f"生成可视化时出错: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# 路由：完整处理流程
@app.route('/api/sentiment_map', methods=['POST'])
def full_process():
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "无效的请求数据"}), 400
            
        keyword = data.get('keyword')
        if not keyword:
            return jsonify({"success": False, "error": "必须提供关键词"}), 400
            
        platforms = data.get('platforms', ["zhihu"])
        limit = data.get('limit', None)
        domain = data.get('domain', 'general')
        
        # 创建任务ID
        task_id = f"{keyword}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 记录任务
        active_tasks[task_id] = {
            "status": "started",
            "keyword": keyword,
            "start_time": datetime.now().isoformat(),
            "progress": 0
        }
        
        # 1. 采集数据
        logger.info(f"[{task_id}] 开始采集数据")
        active_tasks[task_id]["status"] = "collecting"
        active_tasks[task_id]["progress"] = 10
        
        start_time = time.time()
        raw_data = collector.collect(keyword, platforms, limit)
        
        active_tasks[task_id]["progress"] = 30
        
        # 2. 处理数据
        logger.info(f"[{task_id}] 开始处理数据")
        active_tasks[task_id]["status"] = "processing"
        
        processed_data = processor.process(raw_data, domain)
        all_data = processed_data.get("all_data")
        
        if all_data.empty:
            active_tasks[task_id]["status"] = "failed"
            active_tasks[task_id]["error"] = "处理后没有有效数据"
            return jsonify({
                "success": False, 
                "error": "处理后没有有效数据",
                "task_id": task_id
            })
        
        active_tasks[task_id]["progress"] = 60
        
        # 3. 聚合数据
        logger.info(f"[{task_id}] 开始聚合数据")
        active_tasks[task_id]["status"] = "aggregating"
        
        province_data = aggregator.aggregate_by_province(all_data)
        sentiment_distribution = aggregator.get_sentiment_distribution(all_data)
        platform_province_data = aggregator.aggregate_by_platform(
            processed_data.get("platform_data", {})
        )
        
        active_tasks[task_id]["progress"] = 80
        
        # 4. 生成可视化
        logger.info(f"[{task_id}] 开始生成可视化")
        active_tasks[task_id]["status"] = "visualizing"
        
        # 创建临时目录
        temp_dir = os.path.join(tempfile.gettempdir(), task_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        # 主地图
        map_path = os.path.join(temp_dir, "sentiment_map.html")
        main_map = map_visualizer.create_sentiment_map(
            province_data,
            title=f"'{keyword}' 情绪地图"
        )
        map_visualizer.save_to_html(main_map, map_path)
        
        # 情感分布图
        dist_path = None
        if sentiment_distribution:
            dist_path = os.path.join(temp_dir, "sentiment_distribution.html")
            sentiment_pie = chart_generator.create_sentiment_distribution(
                sentiment_distribution
            )
            chart_generator.save_to_html(sentiment_pie, dist_path)
        
        # 平台对比图
        platform_path = None
        if len(platform_province_data) > 1:
            platform_path = os.path.join(temp_dir, "platform_comparison.html")
            platform_timeline = map_visualizer.create_platform_comparison(
                platform_province_data,
                list(platform_province_data.keys())
            )
            map_visualizer.save_to_html(platform_timeline, platform_path)
        
        # 保存数据
        data_path = os.path.join(temp_dir, "processed_data.csv")
        all_data.to_csv(data_path, index=False, encoding='utf-8')
        
        # 完成
        elapsed_time = time.time() - start_time
        logger.info(f"[{task_id}] 处理完成，耗时: {elapsed_time:.2f}秒")
        
        active_tasks[task_id]["status"] = "completed"
        active_tasks[task_id]["progress"] = 100
        active_tasks[task_id]["elapsed_time"] = elapsed_time
        active_tasks[task_id]["result_dir"] = temp_dir
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "keyword": keyword,
            "status": "completed",
            "data_count": len(all_data),
            "province_count": len(province_data),
            "elapsed_time": elapsed_time,
            "files": {
                "map": map_path,
                "data": data_path,
                "distribution": dist_path,
                "platform_comparison": platform_path
            },
            "result_dir": temp_dir
        })
    except Exception as e:
        logger.error(f"处理过程中出错: {str(e)}")
        if task_id in active_tasks:
            active_tasks[task_id]["status"] = "failed"
            active_tasks[task_id]["error"] = str(e)
        return jsonify({"success": False, "error": str(e), "task_id": task_id}), 500

# 路由：获取任务状态
@app.route('/api/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    if task_id in active_tasks:
        return jsonify({
            "success": True,
            "task": active_tasks[task_id]
        })
    else:
        return jsonify({
            "success": False,
            "error": f"任务 {task_id} 不存在"
        }), 404

# 启动服务器
if __name__ == '__main__':
    # 获取端口
    port = int(os.environ.get('PORT', 5000))
    debug = config.get("app", {}).get("debug", False)
    
    # 启动服务
    logger.info(f"API服务启动在端口 {port}, debug模式: {debug}")
    app.run(host='0.0.0.0', port=port, debug=debug)
