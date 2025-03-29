/**
 * 通用的通知相关函数
 */

// 更新未读通知数量的函数
function updateNotificationCount() {
    fetch('/api/notifications/unread-count')
        .then(response => {
            if (!response.ok) {
                if (response.status === 429) {
                    // 如果遇到频率限制,延迟重试
                    console.log('Rate limited, retrying in 5 seconds...');
                    setTimeout(updateNotificationCount, 5000);
                    return;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (!data) return; // 如果上面的代码返回了undefined(429情况),直接退出
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
        .catch(error => {
            console.error('Error:', error);
            // 出错时隐藏badge
            const badge = document.getElementById('notification-badge');
            if (badge) {
                badge.style.display = 'none';
            }
        });
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
    // 通知检查
    const notificationBadge = document.getElementById('notification-badge');
    if (notificationBadge) {
        updateNotificationCount();
        // 增加检查间隔到2分钟
        setInterval(updateNotificationCount, 120000);
    }

    // 如果存在趋势图canvas
    const activityTrendCanvas = document.getElementById('activityTrend');
    if (activityTrendCanvas) {
        // 从后端API获取用户活动数据
        fetch('/user/api/user-activity-stats')
            .then(response => response.json())
            .then(data => {
                const dates = data.dates;
                const datasets = [
                    {
                        label: '发布内容',
                        data: data.content_counts,
                        borderColor: 'rgb(13, 110, 253)',
                        backgroundColor: 'rgba(13, 110, 253, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: '发布主题',
                        data: data.topic_counts,
                        borderColor: 'rgb(25, 135, 84)',
                        backgroundColor: 'rgba(25, 135, 84, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: '论坛回复',
                        data: data.post_counts,
                        borderColor: 'rgb(255, 193, 7)',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        tension: 0.4,
                        fill: true
                    }
                ];

                new Chart(activityTrendCanvas, {
                    type: 'line',
                    data: {
                        labels: dates,
                        datasets: datasets
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'top',
                            },
                            title: {
                                display: false
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                grid: {
                                    borderDash: [2, 4]
                                }
                            },
                            x: {
                                grid: {
                                    display: false
                                }
                            }
                        },
                        interaction: {
                            intersect: false,
                            mode: 'index'
                        }
                    }
                });
            })
            .catch(error => console.error('Error fetching activity stats:', error));
    }
});
