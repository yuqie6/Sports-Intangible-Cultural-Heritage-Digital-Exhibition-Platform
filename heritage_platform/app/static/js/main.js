/**
 * 通用的通知相关函数
 */

// 更新未读通知数量的函数
function updateNotificationCount() {
    fetch('/api/notifications/unread-count')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('notification-badge');
            if (badge) {
                if (data.count > 0) {
                    badge.textContent = data.count;
                    badge.style.display = 'inline';
                } else {
                    badge.style.display = 'none';
                }
            }
        })
        .catch(error => console.error('Error:', error));
}

// 标记单个通知为已读
function markNotificationAsRead(notificationId) {
    fetch('/api/notifications/mark-read', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            notification_id: notificationId
        })
    })
    .then(response => {
        if (!response.ok) {
            console.error('Response status:', response.status);
            return response.text().then(text => {
                throw new Error(`Server responded with ${response.status}: ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.message) {
            // 更新UI
            const notification = document.getElementById(`notification-${notificationId}`);
            if (notification) {
                notification.classList.remove('list-group-item-primary');
                const button = notification.querySelector('button');
                if (button) button.remove();
            }
            // 更新未读计数
            updateNotificationCount();
        }
    })
    .catch(error => console.error('Error:', error));
}

// 标记所有通知为已读
function markAllNotificationsAsRead() {
    fetch('/api/notifications/mark-all-read', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            console.error('Response status:', response.status);
            return response.text().then(text => {
                throw new Error(`Server responded with ${response.status}: ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.message) {
            // 更新所有通知的UI
            document.querySelectorAll('.list-group-item').forEach(item => {
                item.classList.remove('list-group-item-primary');
                const button = item.querySelector('button');
                if (button) button.remove();
            });
            // 更新未读计数
            updateNotificationCount();
        }
    })
    .catch(error => console.error('Error:', error));
}

// 当页面加载完成时执行
document.addEventListener('DOMContentLoaded', function() {
    // 如果存在通知徽章元素，则启动定期检查
    const notificationBadge = document.getElementById('notification-badge');
    if (notificationBadge) {
        // 页面加载时先检查一次
        updateNotificationCount();
        // 每30秒检查一次新通知
        setInterval(updateNotificationCount, 30000);
    }
});
