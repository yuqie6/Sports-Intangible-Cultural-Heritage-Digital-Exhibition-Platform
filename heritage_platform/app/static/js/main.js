// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 自动关闭警告框
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000); // 5秒后自动关闭
    });
    
    // 为所有需要确认的操作添加确认对话框
    const confirmBtns = document.querySelectorAll('.btn-confirm');
    confirmBtns.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            if (!confirm('确定要执行此操作吗？')) {
                e.preventDefault();
            }
        });
    });
});

// 图片预览功能
function previewImage(input, previewId) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        
        reader.onload = function(e) {
            document.getElementById(previewId).src = e.target.result;
        }
        
        reader.readAsDataURL(input.files[0]);
    }
}
