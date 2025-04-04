/**
 * 通用的通知相关函数
 */

// 固定元素检测与调整
document.addEventListener('DOMContentLoaded', function() {
    // 检查页面上的固定计时器等元素
    function checkFixedElements() {
        // 寻找页面上可能的计时器元素
        const timeElements = document.querySelectorAll('.time-display, .countdown-timer, .auto-save-timer, [id*="timer"], [class*="timer"]');
        
        if (timeElements.length > 0) {
            console.log('检测到计时器元素：', timeElements.length, '个');
            
            // 调整每个检测到的计时器元素
            timeElements.forEach(element => {
                // 获取计算样式
                const style = window.getComputedStyle(element);
                
                // 检查是否为固定定位或绝对定位
                if (style.position === 'fixed' || style.position === 'absolute') {
                    console.log('处理固定位置元素:', element);
                    
                    // 调整z-index确保不会覆盖通知栏
                    if (!element.style.zIndex || parseInt(element.style.zIndex) >= 9000) {
                        element.style.zIndex = '1000';
                    }
                    
                    // 如果元素在右下角，移动它以避免与通知区域重叠
                    if ((style.bottom === '0px' || parseInt(style.bottom) < 100) && 
                        (style.right === '0px' || parseInt(style.right) < 100)) {
                        element.style.bottom = '120px';
                    }
                }
            });
        }
    }
    
    // 页面加载时运行一次
    checkFixedElements();
    
    // 每10秒检查一次，捕获可能动态添加的元素
    setInterval(checkFixedElements, 10000);
});

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
