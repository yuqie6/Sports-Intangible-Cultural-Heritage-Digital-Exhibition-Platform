"""
数据采集模块

负责从各社交平台获取数据
"""

from .data_collector import DataCollector
from .zhihu_api import ZhihuAPI
from .weibo_api import WeiboAPI

__all__ = ['DataCollector', 'ZhihuAPI', 'WeiboAPI']
