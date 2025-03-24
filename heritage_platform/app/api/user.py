from flask import jsonify, request, current_app
from . import api_bp
from app.models import User, Content, Favorite
from app import db
from flask_login import current_user, login_required
from app.utils.response import api_success, api_error
from werkzeug.security import generate_password_hash
import traceback

@api_bp.route('/user/profile', methods=['GET'])
@login_required
def get_user_profile():
    """获取用户个人资料API"""
    try:
        user_data = {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'role': current_user.role,
            'avatar': current_user.avatar,
            'created_at': current_user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 获取用户统计信息
        from app.models import Comment, Like, Favorite, ForumTopic, ForumPost
        
        # 内容相关统计
        content_count = Content.query.filter_by(user_id=current_user.id).count()
        comment_count = Comment.query.filter_by(user_id=current_user.id).count()
        like_count = Like.query.filter_by(user_id=current_user.id).count()
        favorite_count = Favorite.query.filter_by(user_id=current_user.id).count()
        
        # 论坛相关统计
        topic_count = ForumTopic.query.filter_by(user_id=current_user.id).count()
        post_count = ForumPost.query.filter_by(user_id=current_user.id).count()
        
        # 合并统计数据
        stats = {
            'content_count': content_count,
            'comment_count': comment_count,
            'like_count': like_count,
            'favorite_count': favorite_count,
            'topic_count': topic_count,
            'post_count': post_count
        }
        
        user_data['stats'] = stats
        
        return api_success(user_data)
    except Exception as e:
        current_app.logger.error(f"获取用户资料出错：{str(e)}")
        return api_error("获取用户资料失败")

@api_bp.route('/user/contents', methods=['GET'])
@login_required
def get_user_contents():
    """获取用户发布的内容API"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        pagination = Content.query.filter_by(user_id=current_user.id).order_by(
            Content.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False)
        
        contents = pagination.items
        
        result = {
            'items': [content.to_dict() for content in contents],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }
        
        return api_success(result)
    except Exception as e:
        current_app.logger.error(f"获取用户内容出错：{str(e)}")
        return api_error("获取用户内容失败")

@api_bp.route('/user/favorites', methods=['GET'])
@login_required
def get_user_favorites():
    """获取用户收藏内容API"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 获取用户收藏的内容ID
        favorite_ids = db.session.query(Favorite.content_id).filter_by(
            user_id=current_user.id).all()
        favorite_ids = [f[0] for f in favorite_ids]
        
        # 查询这些内容
        if favorite_ids:
            pagination = Content.query.filter(Content.id.in_(favorite_ids)).order_by(
                Content.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False)
            
            contents = pagination.items
            
            result = {
                'items': [content.to_dict() for content in contents],
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page
            }
        else:
            result = {
                'items': [],
                'total': 0,
                'pages': 0,
                'current_page': page
            }
        
        return api_success(result)
    except Exception as e:
        current_app.logger.error(f"获取用户收藏出错：{str(e)}")
        return api_error("获取用户收藏失败")

@api_bp.route('/user/password', methods=['PUT'])
@login_required
def change_password():
    """修改密码API"""
    try:
        data = request.get_json()
        
        if not data:
            return api_error("无效的数据")
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return api_error("当前密码和新密码不能为空")
        
        # 验证当前密码
        if not current_user.verify_password(current_password):
            return api_error("当前密码不正确")
        
        # 更新密码
        current_user.password = new_password
        db.session.commit()
        
        return api_success(message="密码修改成功")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"修改密码出错：{str(e)}")
        return api_error("修改密码失败")
