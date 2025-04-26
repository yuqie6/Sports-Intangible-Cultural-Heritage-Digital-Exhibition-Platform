"""
错误处理路由模块

本模块定义了应用的全局错误处理函数，包括：
- 404 页面未找到错误
- 403 禁止访问错误
- 400 错误请求错误
- 500 服务器内部错误

这些错误处理函数根据请求类型返回不同的响应：
- 对于普通页面请求，返回友好的错误页面
- 对于API请求，返回JSON格式的错误信息

通过统一的错误处理，提高了应用的用户体验和可维护性。
"""

from flask import Blueprint, render_template, jsonify, request, current_app
from app import db

errors_bp = Blueprint('errors', __name__)

@errors_bp.app_errorhandler(404)
def page_not_found(_):
    """处理404页面未找到错误

    当用户请求不存在的页面或资源时触发此错误处理函数。
    返回自定义的404错误页面，提供友好的用户体验。

    参数:
        _: 异常对象，未使用

    返回:
        tuple: 包含渲染后的错误页面和404状态码
    """
    return render_template('errors/404.html'), 404

@errors_bp.app_errorhandler(500)
def internal_server_error(_):
    """处理500服务器内部错误

    当服务器发生内部错误时触发此错误处理函数。
    回滚数据库会话以防止数据不一致，并返回自定义的500错误页面。

    参数:
        _: 异常对象，未使用

    返回:
        tuple: 包含渲染后的错误页面和500状态码
    """
    # 回滚数据库会话，防止因异常导致的数据不一致
    db.session.rollback()
    return render_template('errors/500.html'), 500

@errors_bp.app_errorhandler(403)
def forbidden(_):
    """处理403禁止访问错误

    当用户尝试访问没有权限的资源时触发此错误处理函数。
    返回自定义的403错误页面，提示用户权限不足。

    参数:
        _: 异常对象，未使用

    返回:
        tuple: 包含渲染后的错误页面和403状态码
    """
    return render_template('errors/403.html'), 403

# API错误处理函数
@errors_bp.app_errorhandler(400)
def handle_bad_request(e):
    """处理400错误请求错误

    根据请求类型返回不同的响应：
    - 对于图片上传API请求，返回符合CKEditor上传接口规范的JSON响应
    - 对于普通页面请求，返回自定义的400错误页面

    这种区分处理方式使得前端JavaScript和用户界面都能正确处理错误。

    参数:
        e: 异常对象，用于记录错误日志

    返回:
        JSON或HTML: 根据请求类型返回不同格式的错误响应
    """
    # 检查是否是图片上传API请求
    if request.path.startswith('/content/upload_image'):
        # 对API请求返回JSON格式响应
        current_app.logger.error(f"API 400错误: {str(e)}")
        # 返回符合CKEditor上传接口规范的JSON
        return jsonify({
            'uploaded': 0,  # 上传失败
            'error': {'message': '请求格式错误'}  # 错误消息
        }), 400
    # 对普通页面请求返回HTML错误页面
    return render_template('errors/400.html'), 400

@errors_bp.app_errorhandler(500)
def handle_internal_server_error(e):
    """处理500服务器内部错误（API版本）

    与普通的500错误处理函数类似，但专门处理API请求的错误。
    根据请求类型返回不同的响应：
    - 对于图片上传API请求，返回符合CKEditor上传接口规范的JSON响应
    - 对于普通页面请求，返回自定义的500错误页面

    参数:
        e: 异常对象，用于记录错误日志

    返回:
        JSON或HTML: 根据请求类型返回不同格式的错误响应
    """
    # 检查是否是图片上传API请求
    if request.path.startswith('/content/upload_image'):
        # 对API请求返回JSON格式响应
        current_app.logger.error(f"API 500错误: {str(e)}")
        # 返回符合CKEditor上传接口规范的JSON
        return jsonify({
            'uploaded': 0,  # 上传失败
            'error': {'message': '服务器内部错误'}  # 错误消息
        }), 500
    # 对普通页面请求返回HTML错误页面
    return render_template('errors/500.html'), 500
