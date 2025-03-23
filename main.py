import os
import sys
import json
import argparse
import logging
import time
from typing import Dict, List, Any
from datetime import datetime
import pandas as pd

# 配置根日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sentiment_map.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 导入模块
from modules.collector.data_collector import DataCollector
from modules.processor.data_processor import DataProcessor
from modules.processor.data_aggregator import DataAggregator
from modules.visualizer.map_visualizer import MapVisualizer
from modules.visualizer.chart_generator import ChartGenerator

class SentimentMapApp:
    """情绪地图应用主类"""
    
    def __init__(self, config_path: str = "config/config.json"):
        """初始化应用
        
        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 初始化组件
        self.collector = DataCollector(config_path)
        self.processor = DataProcessor(self.config)
        self.aggregator = DataAggregator(self.config)
        self.map_visualizer = MapVisualizer(self.config)
        self.chart_generator = ChartGenerator(self.config)
        
        logger.info(f"情绪地图应用初始化完成")
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            return {}
    
    def run(self, keyword: str, platforms: List[str] = None, 
            limit: int = None, domain: str = "general", 
            output_dir: str = "output") -> Dict[str, Any]:
        """运行完整的情绪地图生成流程
        
        Args:
            keyword: 搜索关键词
            platforms: 平台列表
            limit: 每个平台的数据条数限制
            domain: 情感分析领域
            output_dir: 输出目录
            
        Returns:
            Dict: 处理结果数据
        """
        start_time = time.time()
        logger.info(f"开始处理关键词 '{keyword}'")
        
        # 1. 采集数据
        try:
            logger.info(f"开始采集数据...")
            raw_data = self.collector.collect(keyword, platforms, limit)
            logger.info(f"数据采集完成，共获取 {sum(len(items) for items in raw_data.values())} 条数据")
        except Exception as e:
            logger.error(f"数据采集失败: {str(e)}")
            return {"success": False, "error": f"数据采集失败: {str(e)}"}
        
        # 2. 处理数据
        try:
            logger.info(f"开始处理数据...")
            processed_data = self.processor.process(raw_data, domain)
            
            # 检查是否有处理后的数据
            all_data = processed_data.get("all_data")
            if all_data.empty:
                logger.warning(f"没有可用的处理结果，可能是数据采集失败或没有匹配的内容")
                return {"success": False, "error": "没有可用的处理结果"}
                
            logger.info(f"数据处理完成，有效数据 {len(all_data)} 条")
        except Exception as e:
            logger.error(f"数据处理失败: {str(e)}")
            return {"success": False, "error": f"数据处理失败: {str(e)}"}
        
        # 3. 聚合数据
        try:
            logger.info(f"开始聚合数据...")
            
            # 按省份聚合
            province_data = self.aggregator.aggregate_by_province(all_data)
            logger.info(f"省份聚合完成，有 {len(province_data)} 个省份的有效数据")
            
            # 按平台和省份聚合
            platform_province_data = self.aggregator.aggregate_by_platform(
                processed_data.get("platform_data", {})
            )
            
            # 获取情感分布
            sentiment_distribution = self.aggregator.get_sentiment_distribution(all_data)
            
            # 获取平台比较
            platform_comparison = self.aggregator.get_platform_comparison(
                processed_data.get("platform_data", {})
            )
            
            # 获取时间趋势
            time_trend = self.aggregator.get_time_trend(all_data)
            
            logger.info(f"数据聚合完成")
        except Exception as e:
            logger.error(f"数据聚合失败: {str(e)}")
            return {"success": False, "error": f"数据聚合失败: {str(e)}"}
        
        # 4. 可视化
        try:
            logger.info(f"开始生成可视化...")
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 创建时间戳文件夹，避免覆盖先前结果
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_dir = os.path.join(output_dir, f"{keyword}_{timestamp}")
            os.makedirs(result_dir, exist_ok=True)
            
            # 生成主地图
            main_map = self.map_visualizer.create_sentiment_map(
                province_data,
                title=f"'{keyword}' 情绪地图"
            )
            map_file = os.path.join(result_dir, "sentiment_map.html")
            self.map_visualizer.save_to_html(main_map, map_file)
            
            # 如果有多个平台，生成平台对比
            if len(platform_province_data) > 1:
                platform_timeline = self.map_visualizer.create_platform_comparison(
                    platform_province_data,
                    list(platform_province_data.keys())
                )
                platform_file = os.path.join(result_dir, "platform_comparison.html")
                self.map_visualizer.save_to_html(platform_timeline, platform_file)
            
            # 生成情感分布图
            if sentiment_distribution:
                sentiment_pie = self.chart_generator.create_sentiment_distribution(
                    sentiment_distribution
                )
                pie_file = os.path.join(result_dir, "sentiment_distribution.html")
                self.chart_generator.save_to_html(sentiment_pie, pie_file)
            
            # 生成平台比较图
            if len(platform_comparison) > 1:
                platform_bar = self.chart_generator.create_platform_comparison_chart(
                    platform_comparison
                )
                bar_file = os.path.join(result_dir, "platform_scores.html")
                self.chart_generator.save_to_html(platform_bar, bar_file)
            
            # 生成时间趋势图
            if time_trend:
                time_line = self.chart_generator.create_time_trend_chart(time_trend)
                time_file = os.path.join(result_dir, "time_trend.html")
                self.chart_generator.save_to_html(time_line, time_file)
            
            # 保存原始数据
            all_data.to_csv(os.path.join(result_dir, "processed_data.csv"), 
                             encoding='utf-8', index=False)
            
            logger.info(f"可视化生成完成，结果已保存至 {result_dir}")
        except Exception as e:
            logger.error(f"生成可视化失败: {str(e)}")
            return {"success": False, "error": f"生成可视化失败: {str(e)}"}
        
        # 计算总耗时
        elapsed_time = time.time() - start_time
        logger.info(f"处理完成，总耗时: {elapsed_time:.2f}秒")
        
        return {
            "success": True,
            "keyword": keyword,
            "result_dir": result_dir,
            "data_count": len(all_data),
            "province_count": len(province_data),
            "files": {
                "map": map_file,
                "data": os.path.join(result_dir, "processed_data.csv")
            },
            "summary": {
                "province_data": province_data,
                "sentiment_distribution": sentiment_distribution,
                "platform_comparison": platform_comparison
            }
        }
    
    def close(self):
        """关闭资源连接"""
        if hasattr(self, 'collector'):
            self.collector.close()
        logger.info("应用资源已释放")

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="中国社交媒体情绪地图生成工具")
    
    parser.add_argument("--keyword", "-k", type=str, required=True,
                        help="搜索关键词")
    
    parser.add_argument("--platforms", "-p", type=str, default="zhihu,weibo",
                        help="数据来源平台，逗号分隔 (默认: zhihu,weibo)")
    
    parser.add_argument("--limit", "-l", type=int, default=None,
                        help="每个平台的数据条数限制 (默认: 使用配置文件中的设置)")
    
    parser.add_argument("--domain", "-d", type=str, default="general",
                        help="情感分析领域 (默认: general)")
    
    parser.add_argument("--output", "-o", type=str, default="output",
                        help="输出目录 (默认: output)")
    
    parser.add_argument("--config", "-c", type=str, default="config/config.json",
                        help="配置文件路径 (默认: config/config.json)")
    
    return parser.parse_args()

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 初始化应用
    app = SentimentMapApp(args.config)
    
    try:
        # 运行处理流程
        platforms = args.platforms.split(",") if args.platforms else None
        
        result = app.run(
            keyword=args.keyword,
            platforms=platforms,
            limit=args.limit,
            domain=args.domain,
            output_dir=args.output
        )
        
        if result["success"]:
            print(f"\n处理成功!\n")
            print(f"关键词: {result['keyword']}")
            print(f"数据条数: {result['data_count']}")
            print(f"结果保存在: {result['result_dir']}")
            print("\n生成的文件:")
            for name, path in result["files"].items():
                print(f"- {name}: {path}")
        else:
            print(f"\n处理失败: {result.get('error', '未知错误')}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("用户中断了处理")
        print("\n处理已中断")
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
        print(f"\n发生错误: {str(e)}")
        sys.exit(1)
    finally:
        # 释放资源
        app.close()

if __name__ == "__main__":
    main()
