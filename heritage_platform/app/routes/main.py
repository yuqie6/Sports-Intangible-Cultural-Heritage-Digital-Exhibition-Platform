from flask import Blueprint, render_template, request, current_app
from app.models import HeritageItem, Content
from sqlalchemy.exc import SQLAlchemyError
import os
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """主页"""
    # 调试信息：检查用户认证状态
    current_app.logger.info(f"当前用户认证状态: {current_user.is_authenticated}")
    if current_user.is_authenticated:
        current_app.logger.info(f"当前登录用户: {current_user.username}, 角色: {current_user.role}")

    # 尝试从数据库获取数据，添加错误处理
    try:
        # 获取精选非遗项目
        featured_items = HeritageItem.query.order_by(HeritageItem.created_at.desc()).limit(6).all()
        # 获取最新内容
        latest_contents = Content.query.order_by(Content.created_at.desc()).limit(8).all()
    except SQLAlchemyError as e:
        current_app.logger.error(f"数据库查询错误: {e}")
        featured_items = []
        latest_contents = []

    return render_template('main/index.html',
                           featured_items=featured_items,
                           latest_contents=latest_contents,
                           debug_auth=current_user.is_authenticated)

@main_bp.route('/about')
def about():
    """关于页面"""
    return render_template('main/about.html')

@main_bp.route('/privacy-policy')
def privacy_policy():
    """隐私政策页面"""
    return render_template('main/privacy_policy.html')

@main_bp.route('/terms-of-service')
def terms_of_service():
    """使用条款页面"""
    return render_template('main/terms_of_service.html')

@main_bp.route('/sitemap')
def sitemap():
    """网站地图页面"""
    return render_template('main/sitemap.html')

@main_bp.route('/technical-doc')
def technical_doc():
    """技术文档页面"""
    try:
        with open(os.path.join(current_app.root_path, '..', '技术报告.md'), 'r', encoding='utf-8') as f:
            content = f.read()
        return render_template('main/technical_doc.html', content=content)
    except Exception as e:
        current_app.logger.error(f"读取技术文档错误: {e}")
        return render_template('main/technical_doc.html', content="技术文档加载失败")
