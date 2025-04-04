/**
 * WebSocket连接和事件处理
 * 
 * 这个文件提供与服务器的WebSocket连接功能，用于实时通信，包括：
 * - 私信接收与发送
 * - 通知接收
 * - 论坛帖子更新
 * - 群组消息
 */

// WebSocketClient命名空间
const WebSocketClient = (function() {

// WebSocket连接状态
let socket = null;
let isConnected = false;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 3000; // 3秒

// 用于存储回调函数的对象
const eventHandlers = {
    'connect': [],
    'disconnect': [],
    'reconnect': [],
    'error': [],
    'new_notification': [],
    'new_private_message': [],
    'sent_private_message': [],
    'new_group_message': [],
    'new_forum_post': [],
    'message_deleted': []
};

/**
 * 初始化WebSocket连接
 */
function initWebSocket() {
    if (typeof io === 'undefined') {
        console.error('Socket.IO库未加载');
        return;
    }

    // 如果已经连接，则不重复连接
    if (isConnected && socket) {
        return;
    }

    try {
        // 获取CSRF令牌
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        
        // 创建Socket.IO连接，增加配置选项
        socket = io({
            path: '/socket.io',
            transports: ['websocket', 'polling'], // 优先使用WebSocket，备用长轮询
            reconnection: true,                    // 启用自动重连
            reconnectionDelay: 1000,              // 重连延迟
            reconnectionAttempts: 5,              // 重连尝试次数
            timeout: 20000,                        // 连接超时时间
            withCredentials: true,                 // 启用跨域凭证
            auth: csrfToken ? { csrf_token: csrfToken } : {} // 添加CSRF令牌
        });

        // 连接建立事件
        socket.on('connect', function() {
            console.log('WebSocket连接已建立');
            isConnected = true;
            reconnectAttempts = 0;
            
            // 自动加入个人通知房间
            socket.emit('join_notification_room');
            
            // 触发所有连接事件的回调
            triggerEventHandlers('connect');
        });

        // 连接错误事件
        socket.on('connect_error', function(error) {
            console.error('WebSocket连接错误:', error);
            isConnected = false;
            
            // 触发所有错误事件的回调
            triggerEventHandlers('error', error);
            
            // 尝试重连
            attemptReconnect();
        });

        // 断开连接事件
        socket.on('disconnect', function(reason) {
            console.log('WebSocket连接已断开:', reason);
            isConnected = false;
            
            // 触发所有断开连接事件的回调
            triggerEventHandlers('disconnect', reason);
            
            // 如果不是客户端主动断开，则尝试重连
            if (reason !== 'io client disconnect') {
                attemptReconnect();
            }
        });

        // 收到新通知事件
        socket.on('new_notification', function(data) {
            console.log('收到新通知:', data);
            triggerEventHandlers('new_notification', data);
        });

        // 收到新私信事件
        socket.on('new_private_message', function(data) {
            console.log('收到新私信:', data);
            triggerEventHandlers('new_private_message', data);
        });

        // 发送私信成功事件
        socket.on('sent_private_message', function(data) {
            console.log('私信发送成功:', data);
            triggerEventHandlers('sent_private_message', data);
        });

        // 收到新群组消息事件
        socket.on('new_group_message', function(data) {
            console.log('收到新群组消息:', data);
            triggerEventHandlers('new_group_message', data);
        });

        // 收到新论坛帖子事件
        socket.on('new_forum_post', function(data) {
            console.log('收到新论坛帖子:', data);
            triggerEventHandlers('new_forum_post', data);
        });

        // 消息被删除事件
        socket.on('message_deleted', function(data) {
            console.log('消息已被删除:', data);
            triggerEventHandlers('message_deleted', data);
        });

        // 添加额外的错误处理
        socket.on('error', function(error) {
            console.error('WebSocket错误:', error);
            triggerEventHandlers('error', error);
        });

        // 处理重连事件
        socket.io.on("reconnect_attempt", (attempt) => {
            console.log(`Socket.IO尝试重连 (${attempt})`);
        });

        socket.io.on("reconnect", (attempt) => {
            console.log(`Socket.IO重连成功，尝试次数: ${attempt}`);
            triggerEventHandlers('reconnect', attempt);
        });

        socket.io.on("reconnect_error", (error) => {
            console.error('Socket.IO重连错误:', error);
        });

        socket.io.on("reconnect_failed", () => {
            console.error('Socket.IO重连失败，达到最大尝试次数');
        });

    } catch (e) {
        console.error('初始化WebSocket时出错:', e);
        // 触发所有错误事件的回调
        triggerEventHandlers('error', e);
    }
}

/**
 * 尝试重新连接WebSocket
 */
function attemptReconnect() {
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
        console.error('达到最大重连次数，停止重连');
        return;
    }

    reconnectAttempts++;
    console.log(`尝试重连 (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`);
    
    // 触发重连事件
    triggerEventHandlers('reconnect', reconnectAttempts);
    
    // 延迟一段时间后重连
    setTimeout(function() {
        if (!isConnected) {
            initWebSocket();
        }
    }, RECONNECT_DELAY);
}

/**
 * 加入群组聊天室
 * @param {number} groupId 群组ID
 */
function joinGroup(groupId) {
    if (!isConnected || !socket) {
        console.error('WebSocket未连接，无法加入群组');
        return;
    }

    socket.emit('join_group', { group_id: groupId }, function(response) {
        if (response && response.status === 'success') {
            console.log('成功加入群组:', groupId);
        } else {
            console.error('加入群组失败:', response ? response.message : '未知错误');
        }
    });
}

/**
 * 离开群组聊天室
 * @param {number} groupId 群组ID
 */
function leaveGroup(groupId) {
    if (!isConnected || !socket) {
        console.error('WebSocket未连接，无法离开群组');
        return;
    }

    socket.emit('leave_group', { group_id: groupId }, function(response) {
        if (response && response.status === 'success') {
            console.log('成功离开群组:', groupId);
        } else {
            console.error('离开群组失败:', response ? response.message : '未知错误');
        }
    });
}

/**
 * 加入论坛主题
 * @param {number} topicId 主题ID
 */
function joinTopic(topicId) {
    if (!isConnected || !socket) {
        console.error('WebSocket未连接，无法加入论坛主题');
        return;
    }

    socket.emit('join_topic', { topic_id: topicId }, function(response) {
        if (response && response.status === 'success') {
            console.log('成功加入论坛主题:', topicId);
        } else {
            console.error('加入论坛主题失败:', response ? response.message : '未知错误');
        }
    });
}

/**
 * 离开论坛主题
 * @param {number} topicId 主题ID
 */
function leaveTopic(topicId) {
    if (!isConnected || !socket) {
        console.error('WebSocket未连接，无法离开论坛主题');
        return;
    }

    socket.emit('leave_topic', { topic_id: topicId }, function(response) {
        if (response && response.status === 'success') {
            console.log('成功离开论坛主题:', topicId);
        } else {
            console.error('离开论坛主题失败:', response ? response.message : '未知错误');
        }
    });
}

/**
 * 发送群组消息
 * @param {number} groupId 群组ID
 * @param {string} content 消息内容
 * @param {function} callback 回调函数
 */
function sendGroupMessage(groupId, content, callback) {
    if (!isConnected || !socket) {
        console.error('WebSocket未连接，无法发送群组消息');
        if (callback) callback({ status: 'error', message: 'WebSocket未连接' });
        return;
    }

    socket.emit('send_group_message', { 
        group_id: groupId, 
        content: content 
    }, function(response) {
        if (callback) callback(response);
    });
}

/**
 * 发送私信
 * @param {number} receiverId 接收者ID
 * @param {string} content 消息内容
 * @param {function} callback 回调函数
 */
function sendPrivateMessage(receiverId, content, callback) {
    if (!isConnected || !socket) {
        console.error('WebSocket未连接，无法发送私信');
        if (callback) callback({ status: 'error', message: 'WebSocket未连接' });
        return;
    }

    socket.emit('send_private_message', { 
        receiver_id: receiverId, 
        content: content 
    }, function(response) {
        if (callback) callback(response);
    });
}

/**
 * 标记消息为已读
 * @param {number} messageId 消息ID
 * @param {function} callback 回调函数
 */
function markMessageRead(messageId, callback) {
    if (!isConnected || !socket) {
        console.error('WebSocket未连接，无法标记消息为已读');
        if (callback) callback({ status: 'error', message: 'WebSocket未连接' });
        return;
    }

    socket.emit('mark_message_read', { 
        message_id: messageId 
    }, function(response) {
        if (callback) callback(response);
    });
}

/**
 * 发表评论
 * @param {number} topicId 主题ID
 * @param {string} content 评论内容
 * @param {number} parentId 父评论ID
 * @param {number} replyToUserId 回复用户ID
 * @param {function} callback 回调函数
 */
function postComment(topicId, content, parentId, replyToUserId, callback) {
    if (!isConnected || !socket) {
        console.error('WebSocket未连接，无法发表评论');
        if (callback) callback({ status: 'error', message: 'WebSocket未连接' });
        return;
    }

    socket.emit('post_comment', {
        topic_id: topicId,
        content: content,
        parent_id: parentId || null,
        reply_to_user_id: replyToUserId || null
    }, function(response) {
        if (callback) callback(response);
    });
}

/**
 * 注册事件处理器
 * @param {string} event 事件名称
 * @param {function} handler 处理函数
 */
function onEvent(event, handler) {
    if (typeof handler !== 'function') {
        console.error('事件处理器必须是函数');
        return;
    }
    
    if (eventHandlers[event]) {
        // 清除该事件的所有现有处理函数，避免重复注册
        console.log(`清除事件 ${event} 的现有处理函数，重新注册`);
        eventHandlers[event] = [];
        eventHandlers[event].push(handler);
    } else {
        console.error('未知事件类型:', event);
    }
}

/**
 * 触发所有事件处理器
 * @param {string} event 事件名称
 * @param {*} data 事件数据
 */
function triggerEventHandlers(event, data) {
    if (eventHandlers[event]) {
        eventHandlers[event].forEach((handler, index) => {
            try {
                handler(data);
            } catch (e) {
                console.error(`执行${event}事件处理器 #${index + 1} 时出错:`, e);
            }
        });
    }
}

// 提供公共API
return {
    init: initWebSocket,
    joinGroup: joinGroup,
    leaveGroup: leaveGroup,
    joinTopic: joinTopic,
    leaveTopic: leaveTopic,
    sendGroupMessage: sendGroupMessage,
    sendPrivateMessage: sendPrivateMessage,
    markMessageRead: markMessageRead,
    postComment: postComment,
    onEvent: onEvent,
    getStatus: function() {
        return {
            connected: isConnected,
            reconnectAttempts: reconnectAttempts
        };
    }
};

})();

// 页面加载时自动初始化WebSocket
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM加载完成，初始化WebSocket...');
    WebSocketClient.init();
});