import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging(app):
    # 使用绝对路径指定日志目录
    log_dir = '/var/www/heritage_platform/Sports-Intangible-Cultural-Heritage-Digital-Exhibition-Platform/heritage_platform/logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # 配置基本日志格式
    log_format = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(module)s:%(lineno)d] - %(message)s'
    )

    # 应用日志配置
    app_log_file = os.path.join(log_dir, 'app.log')
    app_handler = RotatingFileHandler(
        app_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    app_handler.setFormatter(log_format)
    app_handler.setLevel(logging.INFO)
    app.logger.addHandler(app_handler)
    app.logger.setLevel(logging.INFO)

    # 错误日志配置
    error_log_file = os.path.join(log_dir, 'error.log')
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setFormatter(log_format)
    error_handler.setLevel(logging.ERROR)
    app.logger.addHandler(error_handler)

    # 访问日志配置
    access_log_file = os.path.join(log_dir, 'access.log')
    access_handler = RotatingFileHandler(
        access_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    access_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(remote_addr)s - %(method)s %(url)s %(status)s - %(message)s'
    ))
    access_handler.setLevel(logging.INFO)

    # 性能日志配置
    perf_log_file = os.path.join(log_dir, 'performance.log')
    perf_handler = RotatingFileHandler(
        perf_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    perf_handler.setFormatter(logging.Formatter(
        '%(asctime)s - [PERF] %(message)s'
    ))
    perf_handler.setLevel(logging.INFO)

    # 创建自定义日志记录器
    access_logger = logging.getLogger('access_log')
    access_logger.addHandler(access_handler)
    access_logger.setLevel(logging.INFO)
    
    perf_logger = logging.getLogger('perf_log')
    perf_logger.addHandler(perf_handler)
    perf_logger.setLevel(logging.INFO)

    # 设置日志记录器到应用配置中
    app.config['ACCESS_LOGGER'] = access_logger
    app.config['PERF_LOGGER'] = perf_logger

def log_access(response):
    """记录访问日志"""
    from flask import request, current_app
    logger = current_app.config.get('ACCESS_LOGGER')
    if logger:
        logger.info(
            '',
            extra={
                'remote_addr': request.remote_addr,
                'method': request.method,
                'url': request.full_path,
                'status': response.status_code
            }
        )
    return response

def log_performance(func_name, execution_time):
    """记录性能日志"""
    from flask import current_app
    logger = current_app.config.get('PERF_LOGGER')
    if logger:
        logger.info(f'Function: {func_name} - Execution time: {execution_time:.2f}ms')