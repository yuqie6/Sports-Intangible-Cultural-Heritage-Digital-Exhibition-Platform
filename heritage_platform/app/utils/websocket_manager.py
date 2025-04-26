"""
WebSocket连接管理模块

本模块提供WebSocket连接的管理功能，包括：
- 连接注册与注销
- 用户活动状态跟踪
- 连接超时检测
- 错误处理和重连机制
- WebSocket事件处理器的错误处理装饰器

通过这些功能，应用可以更可靠地管理WebSocket连接，处理连接异常，
并提供更好的实时通信体验。
"""

from flask import current_app  # 获取当前Flask应用实例
from flask_socketio import disconnect  # 断开Socket.IO连接
from functools import wraps  # 用于保留被装饰函数的元数据
import time  # 时间相关功能
from threading import Lock  # 线程锁，用于保护共享资源

class WebSocketManager:
    """WebSocket连接管理器类

    负责管理应用中的WebSocket连接，包括连接的注册、注销、
    活动状态跟踪和错误处理。使用线程锁确保在多线程环境下的安全操作。

    属性:
        _connections (dict): 存储用户连接信息的字典，键为用户ID
        _lock (Lock): 线程锁，用于保护_connections字典的并发访问
        max_retries (int): 连接错误时的最大重试次数
        retry_delay (int): 重试之间的延迟时间（秒）
        connection_timeout (int): 连接超时时间（秒）
    """
    def __init__(self):
        """初始化WebSocket管理器

        创建一个新的WebSocket管理器实例，初始化连接字典和线程锁，
        并设置默认的重试参数和超时时间。
        """
        self._connections = {}  # 用户ID到连接信息的映射
        self._lock = Lock()  # 创建线程锁
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 1  # 重试延迟（秒）
        self.connection_timeout = 30  # 连接超时时间（秒）

    def register_connection(self, user_id, session_id):
        """注册新的WebSocket连接

        将用户的WebSocket连接信息存储到连接字典中，包括会话ID、
        连接时间、重试计数和最后活动时间。

        参数:
            user_id (int): 用户ID
            session_id (str): Socket.IO会话ID

        返回:
            无返回值
        """
        with self._lock:  # 使用线程锁保护共享资源
            self._connections[user_id] = {
                'session_id': session_id,  # Socket.IO会话ID
                'connected_at': time.time(),  # 连接时间戳
                'retry_count': 0,  # 重试计数器
                'last_activity': time.time()  # 最后活动时间戳
            }

    def unregister_connection(self, user_id):
        """注销WebSocket连接

        从连接字典中移除指定用户的连接信息。

        参数:
            user_id (int): 要注销连接的用户ID

        返回:
            无返回值
        """
        with self._lock:  # 使用线程锁保护共享资源
            if user_id in self._connections:
                del self._connections[user_id]  # 删除用户连接信息

    def update_activity(self, user_id):
        """更新用户最后活动时间

        更新指定用户的最后活动时间戳，用于跟踪用户活动状态。

        参数:
            user_id (int): 用户ID

        返回:
            无返回值
        """
        with self._lock:  # 使用线程锁保护共享资源
            if user_id in self._connections:
                # 更新最后活动时间为当前时间
                self._connections[user_id]['last_activity'] = time.time()

    def check_connection_timeout(self, user_id):
        """检查连接是否超时

        检查指定用户的连接是否已超过设定的超时时间。

        参数:
            user_id (int): 用户ID

        返回:
            bool: 如果连接已超时返回True，否则返回False
        """
        with self._lock:  # 使用线程锁保护共享资源
            if user_id in self._connections:
                # 获取用户最后活动时间
                last_activity = self._connections[user_id]['last_activity']
                # 检查是否超过超时时间
                return (time.time() - last_activity) > self.connection_timeout
            return False  # 用户不在连接字典中，视为未超时

    def handle_connection_error(self, user_id):
        """处理连接错误

        处理指定用户的连接错误，增加重试计数，并根据重试次数决定是否断开连接。

        参数:
            user_id (int): 用户ID

        返回:
            bool: 如果可以继续重试返回True，否则返回False
        """
        with self._lock:  # 使用线程锁保护共享资源
            if user_id in self._connections:
                # 获取连接信息
                conn_info = self._connections[user_id]
                # 增加重试计数
                conn_info['retry_count'] += 1

                # 检查是否超过最大重试次数
                if conn_info['retry_count'] > self.max_retries:
                    # 记录警告日志
                    current_app.logger.warning(f"用户 {user_id} 连接重试次数超过限制，断开连接")
                    # 注销连接
                    self.unregister_connection(user_id)
                    # 断开Socket.IO连接
                    disconnect()
                    return False

                # 等待重试延迟时间
                time.sleep(self.retry_delay)
                # 记录重试信息
                current_app.logger.info(f"用户 {user_id} 正在进行第 {conn_info['retry_count']} 次重连")
                return True  # 可以继续重试
            return False  # 用户不在连接字典中，无法重试

def websocket_error_handler(f):
    """WebSocket错误处理装饰器

    用于包装WebSocket事件处理函数，捕获和处理执行过程中的异常。
    当发生异常时，尝试使用WebSocket管理器的错误处理机制进行重试，
    如果重试失败或无法重试，则返回错误状态。

    参数:
        f (function): 要装饰的WebSocket事件处理函数

    返回:
        function: 包装后的函数，具有错误处理能力

    示例:
        @socketio.on('connect')
        @websocket_error_handler
        def handle_connect(data=None):
            # 处理连接事件的代码
    """
    @wraps(f)  # 保留原函数的元数据
    def wrapped(*args, **kwargs):
        try:
            # 调用原函数
            return f(*args, **kwargs)
        except Exception as e:
            # 记录错误日志
            current_app.logger.error(f"WebSocket错误: {str(e)}")
            # 检查应用是否有WebSocket管理器
            if hasattr(current_app, 'websocket_manager'):
                # 尝试从关键字参数中获取用户ID
                user_id = kwargs.get('user_id')
                # 如果有用户ID，尝试使用WebSocket管理器处理连接错误
                if user_id and current_app.websocket_manager.handle_connection_error(user_id):
                    # 返回重试状态
                    return {'status': 'retry', 'message': '连接错误，正在重试'}
            # 无法重试，返回错误状态
            return {'status': 'error', 'message': '连接错误'}
    return wrapped

def init_websocket_manager(app):
    """初始化WebSocket管理器

    为Flask应用创建并初始化WebSocket管理器实例，并将其附加到应用对象上。
    这使得WebSocket管理器可以在整个应用中通过current_app.websocket_manager访问。

    参数:
        app (Flask): Flask应用实例

    返回:
        WebSocketManager: 创建的WebSocket管理器实例

    示例:
        from flask import Flask
        app = Flask(__name__)
        websocket_manager = init_websocket_manager(app)
    """
    # 创建WebSocket管理器实例
    app.websocket_manager = WebSocketManager()
    # 返回创建的实例
    return app.websocket_manager