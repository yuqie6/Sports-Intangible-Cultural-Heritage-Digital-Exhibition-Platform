from app.models import HeritageItem, ForumTopic
from flask_login import current_user
from flask import current_app

def common_data():
    """向所有模板提供通用数据的上下文处理器
    
    优化点:
    1. 使用明确的异常类型替代空捕获
    2. 记录错误到日志而不是静默失败
    3. 减少不必要的查询
    """
    # 存储上下文数据
    context_data = {
        'nav_heritage_categories': [],
        'nav_forum_categories': [],
        'user_favorite_count': 0
    }
    
    # 获取头部导航菜单的非遗分类
    try:
        categories = HeritageItem.query.with_entities(
            HeritageItem.category).distinct().limit(5).all()
        context_data['nav_heritage_categories'] = [c[0] for c in categories]
    except Exception as e:
        current_app.logger.error(f"获取非遗分类失败: {str(e)}")
    
    # 获取论坛分类
    try:
        forum_categories = ForumTopic.query.with_entities(
            ForumTopic.category).distinct().limit(5).all()
        context_data['nav_forum_categories'] = [c[0] for c in forum_categories]
    except Exception as e:
        current_app.logger.error(f"获取论坛分类失败: {str(e)}")
    
    # 用户收藏数量 - 只有在用户已登录时才查询
    if current_user.is_authenticated:
        try:
            from app.models import Favorite
            context_data['user_favorite_count'] = Favorite.query.filter_by(
                user_id=current_user.id).count()
        except Exception as e:
            current_app.logger.error(f"获取用户收藏数量失败: {str(e)}")
    
    return context_data
