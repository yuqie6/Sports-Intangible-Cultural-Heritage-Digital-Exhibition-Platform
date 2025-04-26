"""
用户相关API模块

本模块提供与用户相关的RESTful API接口，包括：
- 获取用户个人资料和统计信息
- 获取用户发布的内容列表
- 获取用户收藏的内容列表
- 修改用户密码

这些API接口需要用户登录后才能访问，用于支持用户中心和个人资料页面的功能。
"""

from flask import request, current_app
from . import api_bp  # 导入API蓝图
from app.models import Content, Favorite  # 导入用户相关模型
from app import db  # 导入数据库实例
from flask_login import current_user, login_required  # 导入用户认证相关功能
from app.utils.response import api_success, api_error  # 导入API响应工具函数

@api_bp.route('/user/profile', methods=['GET'])
@login_required  # 要求用户登录
def get_user_profile():
    """获取用户个人资料API

    获取当前登录用户的个人资料和各类统计信息，包括基本信息和活动统计。
    需要用户登录才能访问。

    返回:
        JSON: 包含用户资料和统计信息的响应
        {
            "success": true,
            "data": {
                "id": 1,
                "username": "用户名",
                "email": "用户邮箱",
                "role": "用户角色",
                "avatar": "头像路径",
                "created_at": "注册时间",
                "stats": {
                    "content_count": 10,  # 发布内容数
                    "comment_count": 20,  # 评论数
                    "like_count": 30,     # 点赞数
                    "favorite_count": 5,  # 收藏数
                    "topic_count": 3,     # 发布话题数
                    "post_count": 15      # 论坛回复数
                }
            },
            "message": "success"
        }
    """
    try:
        # 构建用户基本信息字典
        user_data = {
            'id': current_user.id,  # 用户ID
            'username': current_user.username,  # 用户名
            'email': current_user.email,  # 邮箱
            'role': current_user.role,  # 角色（学生/教师/管理员）
            'avatar': current_user.avatar,  # 头像路径
            'created_at': current_user.created_at.strftime('%Y-%m-%d %H:%M:%S')  # 格式化注册时间
        }

        # 导入需要用于统计的模型类
        from app.models import Comment, Like, Favorite, ForumTopic, ForumPost

        # 计算内容相关统计数据
        content_count = Content.query.filter_by(user_id=current_user.id).count()  # 发布内容数
        comment_count = Comment.query.filter_by(user_id=current_user.id).count()  # 评论数
        like_count = Like.query.filter_by(user_id=current_user.id).count()  # 点赞数
        favorite_count = Favorite.query.filter_by(user_id=current_user.id).count()  # 收藏数

        # 计算论坛相关统计数据
        topic_count = ForumTopic.query.filter_by(user_id=current_user.id).count()  # 发布话题数
        post_count = ForumPost.query.filter_by(user_id=current_user.id).count()  # 论坛回复数

        # 将所有统计数据合并到一个字典中
        stats = {
            'content_count': content_count,
            'comment_count': comment_count,
            'like_count': like_count,
            'favorite_count': favorite_count,
            'topic_count': topic_count,
            'post_count': post_count
        }

        # 将统计数据添加到用户信息中
        user_data['stats'] = stats

        # 返回成功响应
        return api_success(user_data)
    except Exception as e:
        # 记录错误日志
        current_app.logger.error(f"获取用户资料出错：{str(e)}")
        # 返回错误响应
        return api_error("获取用户资料失败")

@api_bp.route('/user/contents', methods=['GET'])
@login_required  # 要求用户登录
def get_user_contents():
    """获取用户发布的内容API

    获取当前登录用户发布的所有内容列表，支持分页。
    需要用户登录才能访问。

    URL参数:
        page (int, 可选): 当前页码，默认为1
        per_page (int, 可选): 每页内容数量，默认为10

    返回:
        JSON: 包含用户发布内容列表的分页响应
        {
            "success": true,
            "data": {
                "items": [...],  # 内容列表，每个内容为字典格式
                "total": 25,     # 总内容数
                "pages": 3,      # 总页数
                "current_page": 1 # 当前页码
            },
            "message": "success"
        }
    """
    try:
        # 从请求参数中获取分页信息
        page = request.args.get('page', 1, type=int)  # 获取页码，默认为第1页
        per_page = request.args.get('per_page', 10, type=int)  # 获取每页数量，默认为10条

        # 查询当前用户发布的内容，按创建时间降序排序
        pagination = Content.query.filter_by(user_id=current_user.id).order_by(
            Content.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False)

        # 获取当前页的内容列表
        contents = pagination.items

        # 构建响应结果
        result = {
            'items': [content.to_dict() for content in contents],  # 将每个内容转换为字典格式
            'total': pagination.total,  # 总内容数
            'pages': pagination.pages,  # 总页数
            'current_page': page  # 当前页码
        }

        # 返回成功响应
        return api_success(result)
    except Exception as e:
        # 记录错误日志
        current_app.logger.error(f"获取用户内容出错：{str(e)}")
        # 返回错误响应
        return api_error("获取用户内容失败")

@api_bp.route('/user/favorites', methods=['GET'])
@login_required  # 要求用户登录
def get_user_favorites():
    """获取用户收藏内容API

    获取当前登录用户收藏的所有内容列表，支持分页。
    需要用户登录才能访问。

    URL参数:
        page (int, 可选): 当前页码，默认为1
        per_page (int, 可选): 每页内容数量，默认为10

    返回:
        JSON: 包含用户收藏内容列表的分页响应
        {
            "success": true,
            "data": {
                "items": [...],  # 收藏内容列表，每个内容为字典格式
                "total": 15,     # 总收藏数
                "pages": 2,      # 总页数
                "current_page": 1 # 当前页码
            },
            "message": "success"
        }
    """
    try:
        # 从请求参数中获取分页信息
        page = request.args.get('page', 1, type=int)  # 获取页码，默认为第1页
        per_page = request.args.get('per_page', 10, type=int)  # 获取每页数量，默认为10条

        # 首先获取用户收藏的所有内容ID
        favorite_ids = db.session.query(Favorite.content_id).filter_by(
            user_id=current_user.id).all()
        # 将查询结果转换为ID列表
        favorite_ids = [f[0] for f in favorite_ids]

        # 如果有收藏内容，则查询这些内容的详细信息
        if favorite_ids:
            # 使用ID列表查询内容，按创建时间降序排序
            pagination = Content.query.filter(Content.id.in_(favorite_ids)).order_by(
                Content.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False)

            # 获取当前页的内容列表
            contents = pagination.items

            # 构建响应结果
            result = {
                'items': [content.to_dict() for content in contents],  # 将每个内容转换为字典格式
                'total': pagination.total,  # 总收藏数
                'pages': pagination.pages,  # 总页数
                'current_page': page  # 当前页码
            }
        else:
            # 如果没有收藏内容，返回空列表
            result = {
                'items': [],
                'total': 0,
                'pages': 0,
                'current_page': page
            }

        # 返回成功响应
        return api_success(result)
    except Exception as e:
        # 记录错误日志
        current_app.logger.error(f"获取用户收藏出错：{str(e)}")
        # 返回错误响应
        return api_error("获取用户收藏失败")

@api_bp.route('/user/password', methods=['PUT'])
@login_required  # 要求用户登录
def change_password():
    """修改密码API

    允许当前登录用户修改自己的密码。
    需要用户登录才能访问。

    请求体:
        JSON对象，包含以下字段:
        {
            "current_password": "当前密码",  # 必填
            "new_password": "新密码"         # 必填
        }

    返回:
        JSON: 操作结果响应
        {
            "success": true,
            "data": null,
            "message": "密码修改成功"
        }
    """
    try:
        # 获取请求中的JSON数据
        data = request.get_json()

        # 验证数据是否存在
        if not data:
            return api_error("无效的数据")

        # 获取当前密码和新密码
        current_password = data.get('current_password')  # 当前密码
        new_password = data.get('new_password')  # 新密码

        # 验证密码字段是否为空
        if not current_password or not new_password:
            return api_error("当前密码和新密码不能为空")

        # 验证当前密码是否正确
        if not current_user.verify_password(current_password):
            return api_error("当前密码不正确")

        # 更新用户密码
        # 注意：这里使用了User模型中的password属性setter，它会自动处理密码哈希
        current_user.password = new_password
        # 提交事务
        db.session.commit()

        # 返回成功响应
        return api_success(message="密码修改成功")
    except Exception as e:
        # 发生异常时回滚事务
        db.session.rollback()
        # 记录错误日志
        current_app.logger.error(f"修改密码出错：{str(e)}")
        # 返回错误响应
        return api_error("修改密码失败")
