from flask import jsonify, request, current_app
from . import api_bp
from app.models import ForumTopic, ForumPost
from app import db
from flask_login import current_user, login_required
from app.utils.response import api_success, api_error
import traceback

@api_bp.route('/forum/latest_topics', methods=['GET'])
def get_latest_topics():
    """获取最新论坛主题API"""
    try:
        limit = request.args.get('limit', 5, type=int)
        topics = ForumTopic.query.order_by(
            ForumTopic.last_activity.desc()).limit(limit).all()
        
        return api_success({
            'topics': [topic.to_dict() for topic in topics]
        })
    except Exception as e:
        current_app.logger.error(f"获取最新主题出错：{str(e)}")
        return api_error("获取最新主题失败")

@api_bp.route('/forum/topics', methods=['GET'])
def get_topics():
    """获取论坛主题列表API"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        category = request.args.get('category')
        
        query = ForumTopic.query
        
        if category:
            query = query.filter_by(category=category)
            
        pagination = query.order_by(ForumTopic.is_pinned.desc(), 
                                    ForumTopic.last_activity.desc()).paginate(
            page=page, per_page=per_page, error_out=False)
        
        topics = pagination.items
        
        result = {
            'topics': [topic.to_dict() for topic in topics],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }
        
        return api_success(result)
    except Exception as e:
        current_app.logger.error(f"获取论坛主题列表出错：{str(e)}")
        return api_error("获取论坛主题列表失败")

@api_bp.route('/forum/topics', methods=['POST'])
@login_required
def create_topic():
    """创建论坛主题API"""
    try:
        data = request.get_json()
        
        if not data:
            return api_error("无效的数据")
        
        # 基本验证
        if not data.get('title') or not data.get('content'):
            return api_error("标题和内容不能为空")
            
        topic = ForumTopic(
            title=data['title'],
            category=data.get('category', '讨论'),
            user_id=current_user.id
        )
        
        db.session.add(topic)
        db.session.flush()  # 获取topic.id
        
        # 创建第一个帖子
        first_post = ForumPost(
            topic_id=topic.id,
            user_id=current_user.id,
            content=data['content']
        )
        
        db.session.add(first_post)
        db.session.commit()
        
        return api_success(topic.to_dict(), "主题创建成功")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建论坛主题出错：{str(e)}")
        return api_error("创建论坛主题失败")

@api_bp.route('/forum/topics/<int:topic_id>/posts', methods=['GET'])
def get_topic_posts(topic_id):
    """获取主题下的帖子列表API"""
    try:
        topic = ForumTopic.query.get_or_404(topic_id)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        pagination = ForumPost.query.filter_by(topic_id=topic_id).order_by(
            ForumPost.created_at.asc()).paginate(
            page=page, per_page=per_page, error_out=False)
        
        posts = pagination.items
        
        result = {
            'topic': topic.to_dict(),
            'posts': [post.to_dict() for post in posts],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }
        
        return api_success(result)
    except Exception as e:
        current_app.logger.error(f"获取主题帖子列表出错：{str(e)}")
        return api_error("获取主题帖子列表失败")

@api_bp.route('/forum/topics/<int:topic_id>/posts', methods=['POST'])
@login_required
def create_post(topic_id):
    """创建主题回复API"""
    try:
        topic = ForumTopic.query.get_or_404(topic_id)
        data = request.get_json()
        
        if not data or not data.get('content'):
            return api_error("回复内容不能为空")
            
        post = ForumPost(
            topic_id=topic_id,
            user_id=current_user.id,
            content=data['content']
        )
        
        # 更新主题最后活动时间
        topic.last_activity = post.created_at
        
        db.session.add(post)
        db.session.commit()
        
        return api_success(post.to_dict(), "回复成功")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建主题回复出错：{str(e)}")
        return api_error("创建主题回复失败")
