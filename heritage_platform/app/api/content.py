"""
内容API模块

本模块提供内容相关的RESTful API接口，包括：
1. 获取内容列表（支持分页和筛选）
2. 获取内容详情
3. 创建新内容
4. 点赞内容
5. 评论内容

所有API返回标准化的JSON响应，使用app.utils.response中的工具函数。
错误处理采用统一的异常捕获和日志记录机制。
"""

from flask import jsonify, request, current_app
from . import api_bp
from app.models import Content, HeritageItem, Comment, Like, Favorite
from app import db
from flask_login import current_user, login_required
from app.utils.response import api_success, api_error
import traceback

@api_bp.route('/contents', methods=['GET'])
def get_contents():
    """获取内容列表API

    返回分页的内容列表，支持按非遗项目ID和内容类型筛选。

    路由: /contents
    方法: GET
    权限: 无需登录

    Query参数:
        page (int, optional): 页码，默认为1
        per_page (int, optional): 每页数量，默认为10
        heritage_id (int, optional): 按非遗项目ID筛选
        content_type (str, optional): 按内容类型筛选，可选值为article/video/image/multimedia

    Returns:
        JSON: 包含内容列表和分页信息的标准成功响应
        {
            "success": true,
            "message": "操作成功",
            "data": {
                "items": [
                    {
                        "id": 1,
                        "title": "内容标题",
                        "heritage_id": 1,
                        "heritage_name": "非遗项目名称",
                        "user_id": 1,
                        "author": "作者名",
                        "content_type": "article",
                        "created_at": "2023-01-01 12:00:00",
                        "views": 100,
                        "comments_count": 10,
                        "likes_count": 20
                    },
                    ...
                ],
                "total": 100,
                "pages": 10,
                "current_page": 1
            }
        }

    错误响应:
        500: 服务器内部错误
    """
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
    """获取内容详情API

    返回指定ID的内容详情，包括最近的评论。
    同时增加内容的浏览量计数。

    路由: /contents/<id>
    方法: GET
    权限: 无需登录

    Args:
        id (int): 内容ID

    Returns:
        JSON: 包含内容详情的标准成功响应
        {
            "success": true,
            "message": "操作成功",
            "data": {
                "id": 1,
                "title": "内容标题",
                "heritage_id": 1,
                "heritage_name": "非遗项目名称",
                "user_id": 1,
                "author": "作者名",
                "content_type": "article",
                "text_content": "内容文本",
                "file_path": "文件路径",
                "rich_content": "富文本内容",
                "created_at": "2023-01-01 12:00:00",
                "updated_at": "2023-01-01 12:00:00",
                "views": 101,
                "comments_count": 10,
                "likes_count": 20,
                "recent_comments": [
                    {
                        "id": 1,
                        "user_id": 2,
                        "author": "评论者名",
                        "text": "评论内容",
                        "created_at": "2023-01-01 12:30:00"
                    },
                    ...
                ]
            }
        }

    错误响应:
        404: 内容不存在
        500: 服务器内部错误
    """
    try:
        content = Content.query.get_or_404(id)
        return api_success(content.to_dict(include_comments=True))
    except Exception as e:
        current_app.logger.error(f"获取内容详情出错：{str(e)}")
        return api_error("获取内容详情失败")

@api_bp.route('/contents', methods=['POST'])
@login_required
def create_content():
    """创建内容API

    创建新的内容，需要用户登录。
    支持多种内容类型，如文章、视频、图片和多媒体。

    路由: /contents
    方法: POST
    权限: 需要用户登录

    请求体(JSON):
        {
            "title": "内容标题",  // 必填
            "heritage_id": 1,    // 必填，关联的非遗项目ID
            "content_type": "article", // 必填，内容类型，可选值为article/video/image/multimedia
            "text_content": "内容文本", // 可选，文本内容
            "file_path": "文件路径",   // 可选，文件路径
            "rich_content": "富文本内容" // 可选，富文本内容
        }

    Returns:
        JSON: 包含新创建内容信息的标准成功响应
        {
            "success": true,
            "message": "内容创建成功",
            "data": {
                "id": 1,
                "title": "内容标题",
                "heritage_id": 1,
                "heritage_name": "非遗项目名称",
                "user_id": 1,
                "author": "作者名",
                "content_type": "article",
                "created_at": "2023-01-01 12:00:00",
                "views": 0,
                "comments_count": 0,
                "likes_count": 0
            }
        }

    错误响应:
        400: 请求数据无效或必填字段缺失
        401: 用户未登录
        404: 关联的非遗项目不存在
        500: 服务器内部错误
    """
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
    """点赞内容API

    为指定ID的内容添加点赞，需要用户登录。
    每个用户只能对同一内容点赞一次。

    路由: /contents/<id>/like
    方法: POST
    权限: 需要用户登录

    Args:
        id (int): 内容ID

    Returns:
        JSON: 包含点赞结果的标准成功响应
        {
            "success": true,
            "message": "点赞成功",
            "data": {
                "likes_count": 21  // 点赞后的总点赞数
            }
        }

    错误响应:
        400: 已经点赞过该内容
        401: 用户未登录
        404: 内容不存在
        500: 服务器内部错误
    """
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
    """评论内容API

    为指定ID的内容添加评论，需要用户登录。
    支持纯文本评论，不支持富文本或HTML。

    路由: /contents/<id>/comments
    方法: POST
    权限: 需要用户登录

    Args:
        id (int): 内容ID

    请求体(JSON):
        {
            "text": "评论内容"  // 必填，评论文本
        }

    Returns:
        JSON: 包含新创建评论信息的标准成功响应
        {
            "success": true,
            "message": "评论成功",
            "data": {
                "id": 1,
                "user_id": 1,
                "author": "评论者名",
                "content_id": 1,
                "text": "评论内容",
                "created_at": "2023-01-01 12:00:00",
                "is_reply": false
            }
        }

    错误响应:
        400: 评论内容为空
        401: 用户未登录
        404: 内容不存在
        500: 服务器内部错误
    """
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
