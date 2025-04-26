"""
论坛API模块

本模块提供论坛相关的RESTful API接口，包括：
1. 获取最新主题
2. 获取主题列表（支持分页和分类筛选）
3. 创建新主题
4. 获取主题下的帖子列表
5. 创建主题回复

所有API返回标准化的JSON响应，使用app.utils.response中的工具函数。
错误处理采用统一的异常捕获和日志记录机制。
"""

from flask import request, current_app
from . import api_bp
from app.models import ForumTopic, ForumPost
from app import db
from flask_login import current_user, login_required
from app.utils.response import api_success, api_error

@api_bp.route('/forum/latest_topics', methods=['GET'])
def get_latest_topics():
    """获取最新论坛主题API

    返回按最后活动时间排序的最新论坛主题列表。

    Query参数:
        limit (int, optional): 返回的主题数量，默认为5

    Returns:
        JSON: 包含最新主题列表的标准成功响应
        {
            "success": true,
            "message": "操作成功",
            "data": {
                "topics": [
                    {
                        "id": 1,
                        "title": "主题标题",
                        "category": "分类",
                        "user_id": 1,
                        "username": "用户名",
                        "created_at": "2023-01-01 12:00:00",
                        "last_activity": "2023-01-01 12:00:00",
                        "post_count": 10,
                        "is_pinned": false,
                        "is_closed": false
                    },
                    ...
                ]
            }
        }

    错误响应:
        500: 服务器内部错误
    """
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
    """获取论坛主题列表API

    返回分页的论坛主题列表，支持按分类筛选。
    结果按置顶状态和最后活动时间排序。

    Query参数:
        page (int, optional): 页码，默认为1
        per_page (int, optional): 每页数量，默认为20
        category (str, optional): 按分类筛选

    Returns:
        JSON: 包含主题列表和分页信息的标准成功响应
        {
            "success": true,
            "message": "操作成功",
            "data": {
                "topics": [
                    {
                        "id": 1,
                        "title": "主题标题",
                        "category": "分类",
                        "user_id": 1,
                        "username": "用户名",
                        "created_at": "2023-01-01 12:00:00",
                        "last_activity": "2023-01-01 12:00:00",
                        "post_count": 10,
                        "is_pinned": false,
                        "is_closed": false
                    },
                    ...
                ],
                "total": 100,
                "pages": 5,
                "current_page": 1
            }
        }

    错误响应:
        500: 服务器内部错误
    """
    try:
        # 获取分页和筛选参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        category = request.args.get('category')

        # 构建查询
        query = ForumTopic.query

        # 如果提供了分类参数，添加分类筛选
        if category:
            query = query.filter_by(category=category)

        # 执行分页查询，按置顶状态和最后活动时间排序
        pagination = query.order_by(ForumTopic.is_pinned.desc(),
                                    ForumTopic.last_activity.desc()).paginate(
            page=page, per_page=per_page, error_out=False)

        # 获取当前页的主题列表
        topics = pagination.items

        # 构建响应结果
        result = {
            'topics': [topic.to_dict() for topic in topics],  # 将每个主题转换为字典格式
            'total': pagination.total,  # 总主题数
            'pages': pagination.pages,  # 总页数
            'current_page': page  # 当前页码
        }

        # 返回成功响应
        return api_success(result)
    except Exception as e:
        # 记录错误日志
        current_app.logger.error(f"获取论坛主题列表出错：{str(e)}")
        # 返回错误响应
        return api_error("获取论坛主题列表失败")

@api_bp.route('/forum/topics', methods=['POST'])
@login_required
def create_topic():
    """创建论坛主题API

    创建新的论坛主题和第一个帖子。
    需要用户登录。

    请求体(JSON):
        {
            "title": "主题标题",  // 必填
            "content": "主题内容", // 必填
            "category": "分类"    // 可选，默认为"讨论"
        }

    Returns:
        JSON: 包含新创建主题信息的标准成功响应
        {
            "success": true,
            "message": "主题创建成功",
            "data": {
                "id": 1,
                "title": "主题标题",
                "category": "分类",
                "user_id": 1,
                "username": "用户名",
                "created_at": "2023-01-01 12:00:00",
                "last_activity": "2023-01-01 12:00:00",
                "post_count": 1,
                "is_pinned": false,
                "is_closed": false
            }
        }

    错误响应:
        400: 请求数据无效或必填字段缺失
        401: 用户未登录
        500: 服务器内部错误
    """
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
    """获取主题下的帖子列表API

    返回指定主题下的帖子列表，支持分页。
    结果按创建时间升序排序，即最早的帖子在前。

    路由: /forum/topics/<topic_id>/posts
    方法: GET
    权限: 无需登录

    Args:
        topic_id (int): 主题ID

    Query参数:
        page (int, optional): 页码，默认为1
        per_page (int, optional): 每页数量，默认为20

    Returns:
        JSON: 包含主题信息、帖子列表和分页信息的标准成功响应
        {
            "success": true,
            "message": "操作成功",
            "data": {
                "topic": {
                    "id": 1,
                    "title": "主题标题",
                    "category": "分类",
                    "user_id": 1,
                    "username": "用户名",
                    "created_at": "2023-01-01 12:00:00",
                    "last_activity": "2023-01-01 12:00:00",
                    "post_count": 10,
                    "is_pinned": false,
                    "is_closed": false
                },
                "posts": [
                    {
                        "id": 1,
                        "topic_id": 1,
                        "user_id": 1,
                        "username": "用户名",
                        "content": "帖子内容",
                        "created_at": "2023-01-01 12:00:00",
                        "parent_id": null,
                        "reply_to_user_id": null
                    },
                    ...
                ],
                "total": 10,
                "pages": 1,
                "current_page": 1
            }
        }

    错误响应:
        404: 主题不存在
        500: 服务器内部错误
    """
    try:
        # 获取主题，如果不存在则返回404错误
        topic = ForumTopic.query.get_or_404(topic_id)

        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # 查询主题下的帖子，按创建时间升序排序
        pagination = ForumPost.query.filter_by(topic_id=topic_id).order_by(
            ForumPost.created_at.asc()).paginate(
            page=page, per_page=per_page, error_out=False)

        # 获取当前页的帖子列表
        posts = pagination.items

        # 构建响应结果
        result = {
            'topic': topic.to_dict(),  # 主题信息
            'posts': [post.to_dict() for post in posts],  # 帖子列表
            'total': pagination.total,  # 总帖子数
            'pages': pagination.pages,  # 总页数
            'current_page': page  # 当前页码
        }

        # 返回成功响应
        return api_success(result)
    except Exception as e:
        # 记录错误日志
        current_app.logger.error(f"获取主题帖子列表出错：{str(e)}")
        # 返回错误响应
        return api_error("获取主题帖子列表失败")

@api_bp.route('/forum/topics/<int:topic_id>/posts', methods=['POST'])
@login_required
def create_post(topic_id):
    """创建主题回复API

    在指定主题下创建新的回复帖子。
    需要用户登录。
    同时会更新主题的最后活动时间。

    路由: /forum/topics/<topic_id>/posts
    方法: POST
    权限: 需要用户登录

    Args:
        topic_id (int): 主题ID

    请求体(JSON):
        {
            "content": "回复内容",  // 必填
            "parent_id": 1,        // 可选，回复的父帖子ID
            "reply_to_user_id": 2  // 可选，回复的目标用户ID
        }

    Returns:
        JSON: 包含新创建帖子信息的标准成功响应
        {
            "success": true,
            "message": "回复成功",
            "data": {
                "id": 2,
                "topic_id": 1,
                "user_id": 1,
                "username": "用户名",
                "content": "回复内容",
                "created_at": "2023-01-01 12:30:00",
                "parent_id": 1,
                "reply_to_user_id": 2
            }
        }

    错误响应:
        400: 回复内容为空
        401: 用户未登录
        404: 主题不存在
        500: 服务器内部错误
    """
    try:
        # 获取主题，如果不存在则返回404错误
        topic = ForumTopic.query.get_or_404(topic_id)

        # 获取请求数据
        data = request.get_json()

        # 验证回复内容
        if not data or not data.get('content'):
            return api_error("回复内容不能为空")

        # 创建新帖子
        post = ForumPost(
            topic_id=topic_id,
            user_id=current_user.id,
            content=data['content'],
            # 如果提供了父帖子ID和回复目标用户ID，则设置这些字段
            parent_id=data.get('parent_id'),
            reply_to_user_id=data.get('reply_to_user_id')
        )

        # 更新主题最后活动时间为帖子创建时间
        topic.last_activity = post.created_at

        # 将新帖子添加到数据库
        db.session.add(post)
        # 提交事务
        db.session.commit()

        # 返回成功响应，包含新创建的帖子信息
        return api_success(post.to_dict(), "回复成功")
    except Exception as e:
        # 发生异常时回滚事务
        db.session.rollback()
        # 记录错误日志
        current_app.logger.error(f"创建主题回复出错：{str(e)}")
        # 返回错误响应
        return api_error("创建主题回复失败")
