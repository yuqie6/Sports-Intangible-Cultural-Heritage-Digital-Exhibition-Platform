from flask import current_app
from flask_socketio import disconnect
from functools import wraps
import time
from threading import Lock

class WebSocketManager:
    def __init__(self):
        self._connections = {}
        self._lock = Lock()
        self.max_retries = 3
        self.retry_delay = 1  # 重试延迟（秒）
        self.connection_timeout = 30  # 连接超时时间（秒）

    def register_connection(self, user_id, session_id):
        """注册新的WebSocket连接"""
        with self._lock:
            self._connections[user_id] = {
                'session_id': session_id,
                'connected_at': time.time(),
                'retry_count': 0,
                'last_activity': time.time()
            }

    def unregister_connection(self, user_id):
        """注销WebSocket连接"""
        with self._lock:
            if user_id in self._connections:
                del self._connections[user_id]

    def update_activity(self, user_id):
        """更新用户最后活动时间"""
        with self._lock:
            if user_id in self._connections:
                self._connections[user_id]['last_activity'] = time.time()

    def check_connection_timeout(self, user_id):
        """检查连接是否超时"""
        with self._lock:
            if user_id in self._connections:
                last_activity = self._connections[user_id]['last_activity']
                return (time.time() - last_activity) > self.connection_timeout
            return False

    def handle_connection_error(self, user_id):
        """处理连接错误"""
        with self._lock:
            if user_id in self._connections:
                conn_info = self._connections[user_id]
                conn_info['retry_count'] += 1
                
                if conn_info['retry_count'] > self.max_retries:
                    current_app.logger.warning(f"用户 {user_id} 连接重试次数超过限制，断开连接")
                    self.unregister_connection(user_id)
                    disconnect()
                    return False
                
                time.sleep(self.retry_delay)
                current_app.logger.info(f"用户 {user_id} 正在进行第 {conn_info['retry_count']} 次重连")
                return True
            return False

def websocket_error_handler(f):
    """WebSocket错误处理装饰器"""
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"WebSocket错误: {str(e)}")
            if hasattr(current_app, 'websocket_manager'):
                user_id = kwargs.get('user_id')
                if user_id and current_app.websocket_manager.handle_connection_error(user_id):
                    return {'status': 'retry', 'message': '连接错误，正在重试'}
            return {'status': 'error', 'message': '连接错误'}
    return wrapped

def init_websocket_manager(app):
    """初始化WebSocket管理器"""
    app.websocket_manager = WebSocketManager()
    return app.websocket_manager