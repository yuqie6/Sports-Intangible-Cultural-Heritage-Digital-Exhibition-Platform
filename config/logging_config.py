"""日志配置"""
import os
import logging
import logging.config
import sys
from datetime import datetime

# 确保日志目录存在
os.makedirs("logs", exist_ok=True)

# 定义不同级别的日志格式
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'simple': {
            'format': '%(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'ERROR',  # 只显示错误以上级别
            'formatter': 'simple',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
        },
        'file': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': f'logs/app_{datetime.now().strftime("%Y%m%d")}.log',
            'encoding': 'utf-8',
        },
        'error_file': {
            'level': 'ERROR',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': f'logs/error_{datetime.now().strftime("%Y%m%d")}.log',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        '': {  # 根日志器
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': True
        },
        'modules': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False
        },
        'selenium': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False
        },
        'urllib3': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False
        },
        'WDM': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False
        },
        'jieba': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False
        }
    },
}

def setup_logging(debug=False):
    """设置日志配置"""
    # 如果是调试模式，则调整日志级别
    if debug:
        LOGGING_CONFIG['handlers']['console']['level'] = 'INFO'
        LOGGING_CONFIG['loggers']['']['level'] = 'DEBUG'
        LOGGING_CONFIG['loggers']['modules']['level'] = 'DEBUG'
    
    # 应用日志配置
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # 禁用第三方库的日志
    logging.getLogger('selenium').setLevel(logging.CRITICAL)
    logging.getLogger('urllib3').setLevel(logging.CRITICAL)
    logging.getLogger('WDM').setLevel(logging.CRITICAL)
    logging.getLogger('jieba').setLevel(logging.ERROR)
    
    # 禁用Matplotlib的字体日志
    logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
