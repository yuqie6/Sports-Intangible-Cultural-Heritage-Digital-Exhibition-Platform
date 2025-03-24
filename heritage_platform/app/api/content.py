from flask import jsonify, request, current_app
from . import api_bp
from app.models import Content, HeritageItem, Comment, Like, Favorite
from app import db
from flask_login import current_user, login_required
from app.utils.response import api_success, api_error
import traceback

@api_bp.route('/contents', methods=['GET'])
def get_contents():
    """获取内容列表API"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        heritage_id = request.args.get('heritage_id', type=int)
        content_type = request.args.get('content_type')
        
        query = Content.query
        
        if heritage_id:
            query = query.filter_by(heritage_id=heritage_id)
            
        if content_type:
            query = query.filter_by(content_type=content_type)
            
        pagination = query.order_by(Content.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False)
        
        items = pagination.items
        
        result = {
            'items': [item.to_dict() for item in items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }
        
        return api_success(result)
    except Exception as e:
        current_app.logger.error(f"获取内容列表出错：{str(e)}")
        return api_error("获取内容列表失败")

@api_bp.route('/contents/<int:id>', methods=['GET'])
def get_content(id):
    """获取内容详情API"""
    try:
        content = Content.query.get_or_404(id)
        return api_success(content.to_dict(include_comments=True))
    except Exception as e:
        current_app.logger.error(f"获取内容详情出错：{str(e)}")
        return api_error("获取内容详情失败")

@api_bp.route('/contents', methods=['POST'])
@login_required
def create_content():
    """创建内容API"""
    try:
        data = request.get_json()
        
        if not data:
            return api_error("无效的数据")
        
        # 基本验证
        if not data.get('title') or not data.get('heritage_id') or not data.get('content_type'):
            return api_error("标题、所属非遗项目和内容类型不能为空")
        
        # 检查非遗项目是否存在
        heritage = HeritageItem.query.get(data['heritage_id'])
        if not heritage:
            return api_error("所选非遗项目不存在")
            
        content = Content(
            title=data['title'],
            heritage_id=data['heritage_id'],
            user_id=current_user.id,
            content_type=data['content_type'],
            text_content=data.get('text_content', ''),
            file_path=data.get('file_path', '')
        )
        
        db.session.add(content)
        db.session.commit()
        
        return api_success(content.to_dict(), "内容创建成功")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建内容出错：{str(e)}")
        return api_error("创建内容失败")

@api_bp.route('/contents/<int:id>/like', methods=['POST'])
@login_required
def like_content(id):
    """点赞内容API"""
    try:
        content = Content.query.get_or_404(id)
        
        # 检查是否已点赞
        existing_like = Like.query.filter_by(
            user_id=current_user.id,
            content_id=id
        ).first()
        
        if existing_like:
            return api_error("您已经点赞过该内容")
            
        like = Like(user_id=current_user.id, content_id=id)
        db.session.add(like)
        db.session.commit()
        
        return api_success({"likes_count": content.likes.count()}, "点赞成功")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"点赞内容出错：{str(e)}")
        return api_error("点赞失败")

@api_bp.route('/contents/<int:id>/comments', methods=['POST'])
@login_required
def comment_content(id):
    """评论内容API"""
    try:
        content = Content.query.get_or_404(id)
        data = request.get_json()
        
        if not data or not data.get('text'):
            return api_error("评论内容不能为空")
            
        comment = Comment(
            user_id=current_user.id,
            content_id=id,
            text=data['text']
        )
        
        db.session.add(comment)
        db.session.commit()
        
        return api_success(comment.to_dict(), "评论成功")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"评论内容出错：{str(e)}")
        return api_error("评论失败")
