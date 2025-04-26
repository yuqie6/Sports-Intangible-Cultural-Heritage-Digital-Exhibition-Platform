"""
模板上下文处理器模块

本模块提供Flask模板上下文处理器，用于向所有模板注入通用数据。
这些数据在应用的所有页面中都可用，包括：
- 导航栏中显示的非遗项目分类
- 导航栏中显示的论坛分类
- 当前登录用户的收藏数量

通过上下文处理器提供这些数据，可以避免在每个视图函数中重复查询，
提高代码复用性和应用性能。
"""

from app.models import HeritageItem, ForumTopic  # 导入非遗项目和论坛主题模型
from flask_login import current_user  # 获取当前登录用户
from flask import current_app  # 获取当前应用实例，用于日志记录

def common_data():
    """向所有模板提供通用数据的上下文处理器

    此函数作为Flask上下文处理器注册，会在每个请求处理过程中被调用，
    返回的字典将被合并到所有模板的上下文中，使这些数据在所有模板中可用。

    包含的数据:
        - nav_heritage_categories: 用于导航栏的非遗项目分类列表
        - nav_forum_categories: 用于导航栏的论坛分类列表
        - user_favorite_count: 当前登录用户的收藏数量(未登录时为0)

    优化点:
        1. 使用明确的异常类型替代空捕获
        2. 记录错误到日志而不是静默失败
        3. 减少不必要的查询
        4. 考虑使用缓存减少数据库查询

    返回:
        dict: 包含通用数据的字典，将被合并到所有模板的上下文中
    """
    # 初始化上下文数据字典，设置默认值
    context_data = {
        'nav_heritage_categories': [],  # 导航栏显示的非遗分类
        'nav_forum_categories': [],     # 导航栏显示的论坛分类
        'user_favorite_count': 0        # 用户收藏数量，默认为0
    }

    # 获取头部导航菜单的非遗分类
    # 使用distinct()查询不同的分类，并限制最多返回5个
    try:
        # 使用with_entities优化查询，只获取需要的category字段
        categories = HeritageItem.query.with_entities(
            HeritageItem.category).distinct().limit(5).all()
        # 将查询结果转换为简单的列表
        context_data['nav_heritage_categories'] = [c[0] for c in categories]
    except Exception as e:
        # 记录错误日志，但不中断处理流程
        current_app.logger.error(f"获取非遗分类失败: {str(e)}")

    # 获取论坛分类
    # 同样使用distinct()查询不同的分类，并限制最多返回5个
    try:
        # 使用with_entities优化查询，只获取需要的category字段
        forum_categories = ForumTopic.query.with_entities(
            ForumTopic.category).distinct().limit(5).all()
        # 将查询结果转换为简单的列表
        context_data['nav_forum_categories'] = [c[0] for c in forum_categories]
    except Exception as e:
        # 记录错误日志，但不中断处理流程
        current_app.logger.error(f"获取论坛分类失败: {str(e)}")

    # 用户收藏数量 - 只有在用户已登录时才查询
    # 这样可以避免对未登录用户进行不必要的数据库查询
    if current_user.is_authenticated:
        try:
            # 延迟导入Favorite模型，避免循环导入问题
            from app.models import Favorite
            # 查询当前用户的收藏数量
            context_data['user_favorite_count'] = Favorite.query.filter_by(
                user_id=current_user.id).count()
        except Exception as e:
            # 记录错误日志，但不中断处理流程
            current_app.logger.error(f"获取用户收藏数量失败: {str(e)}")

    # 返回包含所有通用数据的字典
    return context_data
