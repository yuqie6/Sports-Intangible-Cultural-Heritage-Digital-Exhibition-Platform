from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import ForumTopic, ForumPost, User
from app.forms.forum import TopicForm, PostForm
from app.utils.decorators import admin_required
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

forum_bp = Blueprint('forum', __name__)

@forum_bp.route('/api/latest_topics')
def latest_topics():
    """获取最新论坛主题API"""
    limit = request.args.get('limit', 5, type=int)
    
    # 查询最新主题
    topics = db.session.query(
        ForumTopic,
        User.username.label('creator_name')
    ).outerjoin(User, ForumTopic.user_id == User.id
    ).order_by(
        ForumTopic.last_activity.desc()
    ).limit(limit).all()
    
    # 格式化数据
    result = []
    for topic, creator_name in topics:
        result.append({
            'id': topic.id,
            'title': topic.title,
            'category': topic.category,
            'creator': creator_name or "未知用户",
            'post_count': topic.post_count,
            'last_activity': topic.last_activity.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify(result)

@forum_bp.route('/')
def index():
    """论坛首页 - 优化数据库查询"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category')
    
    # 使用JOIN查询一次性获取主题和创建者信息
    query = db.session.query(
        ForumTopic, 
        User.username.label('creator_name')
    ).outerjoin(User, ForumTopic.user_id == User.id)
    
    if category:
        query = query.filter(ForumTopic.category == category)
        
    # 按置顶和最后活动时间排序
    query = query.order_by(
        ForumTopic.is_pinned.desc(), 
        ForumTopic.last_activity.desc()
    )
    
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    
    # 简化数据处理
    topic_data = []
    for topic_obj, creator_name in pagination.items:
        topic_data.append({
            'id': topic_obj.id,
            'title': topic_obj.title,
            'category': topic_obj.category,
            'creator': creator_name or "未知用户",
            'is_pinned': topic_obj.is_pinned,
            'is_closed': topic_obj.is_closed,
            'post_count': topic_obj.post_count,
            'views': topic_obj.views,
            'created_at': topic_obj.created_at,
            'last_activity': topic_obj.last_activity
        })
    
    # 获取所有分类 - 使用distinct优化
    categories = db.session.query(ForumTopic.category).distinct().all()
    categories = [c[0] for c in categories]
    
    return render_template('forum/index.html', 
                           topics=topic_data, 
                           pagination=pagination,
                           categories=categories,
                           current_category=category)

@forum_bp.route('/topic/<int:id>', methods=['GET', 'POST'])
def topic(id):
    """主题详情页 - 优化数据库查询"""
    topic = ForumTopic.query.get_or_404(id)
    
    # 增加浏览次数 - 避免每次访问都重新查询
    topic.views += 1
    
    # 回复表单
    form = PostForm()
    
    if form.validate_on_submit() and current_user.is_authenticated:
        try:
            if topic.is_closed and not current_user.is_admin:
                flash('该主题已关闭，无法回复', 'warning')
                return redirect(url_for('forum.topic', id=id))
                
            post = ForumPost(
                topic_id=id,
                user_id=current_user.id,
                content=form.content.data
            )
            db.session.add(post)
            
            # 更新主题最后活动时间，不直接修改post_count属性
            topic.last_activity = post.created_at
            
            db.session.commit()
            flash('回复成功', 'success')
            return redirect(url_for('forum.topic', id=id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"发表回复失败: {str(e)}")
            flash('发表回复失败，请稍后重试', 'danger')
    
    # 获取帖子列表 - 优化为一次性JOIN查询
    page = request.args.get('page', 1, type=int)
    posts_query = db.session.query(
        ForumPost,
        User.username.label('author_name'),
        User.avatar.label('author_avatar')
    ).outerjoin(User, ForumPost.user_id == User.id).filter(ForumPost.topic_id == id).order_by(
        ForumPost.created_at.asc())
    
    posts_pagination = posts_query.paginate(page=page, per_page=20, error_out=False)
    
    # 获取主题创建者信息
    creator = User.query.get(topic.user_id)
    topic_data = {
        'id': topic.id,
        'title': topic.title,
        'category': topic.category,
        'is_pinned': topic.is_pinned,
        'is_closed': topic.is_closed,
        'views': topic.views,
        'post_count': topic.post_count,
        'created_at': topic.created_at,
        'last_activity': topic.last_activity,
        'creator': creator.username if creator else "未知用户"
    }
    
    # 简化帖子数据处理
    posts_with_authors = []
    for post, author_name, author_avatar in posts_pagination.items:
        posts_with_authors.append({
            'id': post.id,
            'content': post.content,
            'created_at': post.created_at,
            'updated_at': post.updated_at,
            'author': author_name or "未知用户",
            'author_avatar': author_avatar
        })
    
    # 提交数据库更改
    db.session.commit()
    
    return render_template('forum/topic.html', 
                           topic=topic_data,
                           posts=posts_with_authors,
                           pagination=posts_pagination,
                           form=form)

@forum_bp.route('/create_topic', methods=['GET', 'POST'])
@login_required
def create_topic():
    """创建主题页面"""
    form = TopicForm()
    
    if form.validate_on_submit():
        try:
            # 首先创建主题（不包含content字段）
            topic = ForumTopic(
                title=form.title.data,
                category=form.category.data,
                user_id=current_user.id
            )
            
            # 添加主题并提交以获取ID
            db.session.add(topic)
            db.session.flush()  # 获取ID但不提交事务
            
            # 使用主题ID创建第一个帖子
            first_post = ForumPost(
                topic_id=topic.id,
                user_id=current_user.id,
                content=form.content.data
            )
            db.session.add(first_post)
            
            # 最后提交所有更改
            db.session.commit()
            
            flash('主题创建成功', 'success')
            return redirect(url_for('forum.topic', id=topic.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建主题失败: {str(e)}")
            flash('创建主题失败，请稍后重试', 'danger')
    
    return render_template('forum/create_topic.html', form=form)

@forum_bp.route('/pin_topic/<int:id>', methods=['POST'])
@login_required
@admin_required
def pin_topic(id):
    """置顶或取消置顶主题"""
    topic = ForumTopic.query.get_or_404(id)
    try:
        topic.is_pinned = not topic.is_pinned
        db.session.commit()
        flash('主题状态更新成功', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新主题置顶状态失败: {str(e)}")
        flash('操作失败，请稍后重试', 'danger')
    return redirect(url_for('forum.topic', id=id))

@forum_bp.route('/close_topic/<int:id>', methods=['POST'])
@login_required
@admin_required
def close_topic(id):
    """关闭或打开主题"""
    topic = ForumTopic.query.get_or_404(id)
    try:
        topic.is_closed = not topic.is_closed
        db.session.commit()
        flash('主题状态更新成功', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新主题关闭状态失败: {str(e)}")
        flash('操作失败，请稍后重试', 'danger')
    return redirect(url_for('forum.topic', id=id))

@forum_bp.route('/delete_topic/<int:id>', methods=['POST'])
@login_required
def delete_topic(id):
    """删除主题 - 允许作者或管理员删除主题"""
    topic = ForumTopic.query.get_or_404(id)
    
    # 检查是否有权限删除（管理员或作者）
    if not (current_user.is_admin or topic.user_id == current_user.id):
        flash('您没有权限删除此主题', 'danger')
        return redirect(url_for('forum.topic', id=id))
    
    try:
        # 先删除主题下的所有帖子
        ForumPost.query.filter_by(topic_id=id).delete()
        
        # 再删除主题
        db.session.delete(topic)
        db.session.commit()
        
        flash('主题删除成功', 'success')
        return redirect(url_for('forum.index'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除主题失败: {str(e)}")
        flash('删除主题失败，请稍后重试', 'danger')
        return redirect(url_for('forum.topic', id=id))

@forum_bp.route('/delete_post/<int:id>', methods=['POST'])
@login_required
def delete_post(id):
    """删除帖子回复 - 允许作者或管理员删除回复"""
    post = ForumPost.query.get_or_404(id)
    topic_id = post.topic_id
    
    # 检查是否有权限删除（管理员或作者）
    if not (current_user.is_admin or post.user_id == current_user.id):
        flash('您没有权限删除此回复', 'danger')
        return redirect(url_for('forum.topic', id=topic_id))
    
    # 不允许删除主题的首个帖子（第一条回复）
    first_post = ForumPost.query.filter_by(topic_id=topic_id).order_by(ForumPost.created_at.asc()).first()
    if first_post and first_post.id == post.id:
        flash('不能删除主题的第一条回复，请删除整个主题', 'warning')
        return redirect(url_for('forum.topic', id=topic_id))
    
    try:
        db.session.delete(post)
        
        # 更新主题的回复计数（依赖于触发器或手动更新）
        topic = ForumTopic.query.get(topic_id)
        if topic:
            # 减少回复计数，依赖于post_count字段的维护逻辑
            pass
            
        db.session.commit()
        flash('回复删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除回复失败: {str(e)}")
        flash('删除回复失败，请稍后重试', 'danger')
    
    return redirect(url_for('forum.topic', id=topic_id))
