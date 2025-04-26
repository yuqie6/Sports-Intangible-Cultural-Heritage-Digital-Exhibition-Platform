"""
日志配置模块

本模块提供了应用的日志配置和日志记录功能，包括：
1. 应用日志：记录应用运行时的一般信息和警告
2. 错误日志：专门记录错误和异常信息
3. 访问日志：记录HTTP请求的详细信息
4. 性能日志：记录函数执行时间等性能指标

日志系统特性：
- 文件轮转：使用RotatingFileHandler自动轮转日志文件，防止单个文件过大
- 分级记录：根据日志级别(INFO, WARNING, ERROR等)分别处理
- 格式化输出：为不同类型的日志定制不同的输出格式
- 自动创建：自动创建日志目录和文件
- 编码处理：统一使用UTF-8编码，确保中文正常显示
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging(app):
    """设置应用的日志系统

    为Flask应用配置完整的日志系统，包括应用日志、错误日志、访问日志和性能日志。
    创建必要的日志目录和文件，配置日志格式和轮转策略。
    将配置好的日志记录器添加到应用实例中，以便在整个应用中使用。

    日志文件配置:
    - app.log: 记录应用级别的警告和错误信息
    - error.log: 专门记录错误级别的日志
    - access.log: 记录HTTP请求的访问信息
    - performance.log: 记录性能相关的指标

    所有日志文件都配置了轮转策略，当文件达到指定大小时自动创建新文件，
    并保留指定数量的备份文件，防止日志占用过多磁盘空间。

    Args:
        app: Flask应用实例
    """
    # 使用绝对路径指定日志目录
    log_dir = '/var/www/heritage_platform/Sports-Intangible-Cultural-Heritage-Digital-Exhibition-Platform/heritage_platform/logs'
    # 确保日志目录存在，不存在则创建
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
    # 将应用日志级别调整为 WARNING，减少不必要的 INFO 日志
    app_handler.setLevel(logging.WARNING)
    app.logger.addHandler(app_handler)
    # 将应用日志记录器的级别也调整为 WARNING
    app.logger.setLevel(logging.WARNING)

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
    """记录HTTP请求的访问日志

    作为Flask的after_request处理函数，在每个请求处理完成后记录访问信息。
    记录的信息包括客户端IP地址、请求方法、URL路径和响应状态码。

    使用自定义的日志格式，通过extra参数传递额外的上下文信息，
    确保日志中包含完整的请求信息，便于后续分析和排查问题。

    Args:
        response: Flask响应对象，包含响应状态码等信息

    Returns:
        response: 原始响应对象，不做修改

    使用方式:
        在Flask应用中注册为after_request处理函数:
        app.after_request(log_access)
    """
    from flask import request, current_app
    logger = current_app.config.get('ACCESS_LOGGER')
    if logger:
        logger.info(
            '',  # 实际消息内容为空，因为所有信息都通过extra参数传递
            extra={
                'remote_addr': request.remote_addr,
                'method': request.method,
                'url': request.full_path,
                'status': response.status_code
            }
        )
    return response

def log_performance(func_name, execution_time):
    """记录函数执行性能日志

    记录函数的执行时间等性能指标，用于性能分析和优化。
    通常与性能监控装饰器配合使用，自动记录函数的执行时间。

    性能日志格式为：Function: {函数名} - Execution time: {执行时间}ms
    执行时间保留两位小数，单位为毫秒。

    Args:
        func_name (str): 被监控的函数名称
        execution_time (float): 函数执行时间，单位为毫秒

    使用示例:
        # 手动记录性能
        start_time = time.time()
        result = expensive_function()
        execution_time = (time.time() - start_time) * 1000  # 转换为毫秒
        log_performance('expensive_function', execution_time)

        # 或者使用装饰器自动记录
        @performance_logger
        def expensive_function():
            # 函数实现
            pass
    """
    from flask import current_app
    logger = current_app.config.get('PERF_LOGGER')
    if logger:
        logger.info(f'Function: {func_name} - Execution time: {execution_time:.2f}ms')
