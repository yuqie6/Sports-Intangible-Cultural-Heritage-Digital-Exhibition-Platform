import redis
from redis.connection import ConnectionPool
from redis.exceptions import ConnectionError, TimeoutError
from flask import current_app
import logging
from functools import wraps
from time import sleep

class RedisManager:
    _instance = None
    _pool = None
    _redis_client = None

    def __init__(self):
        raise RuntimeError('请使用 get_instance() 方法获取 RedisManager 实例')

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化Redis连接池和客户端"""
        try:
            if self._pool is None:
                self._pool = ConnectionPool(
                    host=current_app.config.get('REDIS_HOST', 'localhost'),
                    port=current_app.config.get('REDIS_PORT', 6379),
                    db=current_app.config.get('REDIS_DB', 0),
                    max_connections=10,  # 最大连接数
                    socket_timeout=5,    # 套接字超时
                    socket_connect_timeout=5,  # 连接超时
                    retry_on_timeout=True  # 超时时重试
                )
            if self._redis_client is None:
                self._redis_client = redis.Redis(connection_pool=self._pool)
        except Exception as e:
            logging.error(f'Redis初始化失败: {str(e)}')
            raise

    def get_redis(self):
        """获取Redis客户端实例"""
        return self._redis_client

def retry_on_redis_error(max_retries=3, delay=1):
    """Redis操作重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, TimeoutError) as e:
                    retries += 1
                    if retries == max_retries:
                        logging.error(f'Redis操作失败，已达到最大重试次数: {str(e)}')
                        raise
                    logging.warning(f'Redis操作失败，正在进行第{retries}次重试: {str(e)}')
                    sleep(delay)
        return wrapper
    return decorator

# 使用示例
@retry_on_redis_error()
def set_key(key, value, expire=None):
    """设置Redis键值对
    
    Args:
        key: 键名
        value: 值
        expire: 过期时间（秒）
    """
    redis_client = RedisManager.get_instance().get_redis()
    redis_client.set(key, value, ex=expire)

@retry_on_redis_error()
def get_key(key):
    """获取Redis键值
    
    Args:
        key: 键名
    Returns:
        键值，如果不存在返回None
    """
    redis_client = RedisManager.get_instance().get_redis()
    return redis_client.get(key)