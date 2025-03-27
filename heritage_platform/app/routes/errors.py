from flask import Blueprint, render_template, jsonify, request, current_app
from app import db

errors_bp = Blueprint('errors', __name__)

@errors_bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@errors_bp.app_errorhandler(500)
def internal_server_error(e):
    db.session.rollback()
    return render_template('errors/500.html'), 500

@errors_bp.app_errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

# API错误处理函数
@errors_bp.app_errorhandler(400)
def handle_bad_request(e):
    """处理400错误"""
    if request.path.startswith('/content/upload_image'):
        # 对API请求返回JSON
        current_app.logger.error(f"API 400错误: {str(e)}")
        return jsonify({
            'uploaded': 0,
            'error': {'message': '请求格式错误'}
        }), 400
    return render_template('errors/400.html'), 400

@errors_bp.app_errorhandler(500)
def handle_internal_server_error(e):
    """处理500错误"""
    if request.path.startswith('/content/upload_image'):
        # 对API请求返回JSON
        current_app.logger.error(f"API 500错误: {str(e)}")
        return jsonify({
            'uploaded': 0,
            'error': {'message': '服务器内部错误'}
        }), 500
    return render_template('errors/500.html'), 500
