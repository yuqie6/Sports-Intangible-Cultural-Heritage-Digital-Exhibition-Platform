from app.models import HeritageItem, ForumTopic
from flask_login import current_user

def common_data():
    """向所有模板提供通用数据的上下文处理器"""
    # 获取头部导航菜单的非遗分类
    categories = []
    try:
        categories = HeritageItem.query.with_entities(
            HeritageItem.category).distinct().limit(5).all()
        categories = [c[0] for c in categories]
    except:
        pass
    
    # 获取论坛分类
    forum_categories = []
    try:
        forum_categories = ForumTopic.query.with_entities(
            ForumTopic.category).distinct().limit(5).all()
        forum_categories = [c[0] for c in forum_categories]
    except:
        pass
    
    # 用户收藏数量
    favorite_count = 0
    if current_user.is_authenticated:
        try:
            from app.models import Favorite
            favorite_count = Favorite.query.filter_by(user_id=current_user.id).count()
        except:
            pass
    
    return {
        'nav_heritage_categories': categories,
        'nav_forum_categories': forum_categories,
        'user_favorite_count': favorite_count
    }
