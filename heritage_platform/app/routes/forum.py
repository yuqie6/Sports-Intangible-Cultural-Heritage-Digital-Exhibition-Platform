from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from app import db
from app.models import ForumTopic, ForumPost
from app.forms.forum import TopicForm, PostForm
from app.utils.decorators import admin_required
from sqlalchemy.exc import SQLAlchemyError

forum_bp = Blueprint('forum', __name__)

@forum_bp.route('/')
def index():
    """论坛首页"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category')
    
    query = ForumTopic.query
    
    if category:
        query = query.filter_by(category=category)
        
    # 按置顶和最后活动时间排序
    pagination = query.order_by(
        ForumTopic.is_pinned.desc(), 
        ForumTopic.last_activity.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    
    topics = pagination.items
    
    # 获取所有分类
    categories = db.session.query(ForumTopic.category).distinct().all()
    categories = [c[0] for c in categories]
    
    return render_template('forum/index.html', 
                           topics=topics, 
                           pagination=pagination,
                           categories=categories,
                           current_category=category)

@forum_bp.route('/topic/<int:id>', methods=['GET', 'POST'])
def topic(id):
    """主题详情页"""
    topic = ForumTopic.query.get_or_404(id)
    
    # 增加浏览次数
    topic.views += 1
    db.session.commit()
    
    # 回复表单
    form = PostForm()
    
    if form.validate_on_submit() and current_user.is_authenticated:
        if topic.is_closed and not current_user.is_admin:
            flash('此主题已关闭，无法回复', 'warning')
            return redirect(url_for('forum.topic', id=id))
            
        try:
            post = ForumPost(
                topic_id=id,
                user_id=current_user.id,
                content=form.content.data
            )
            
            # 更新主题最后活动时间
            topic.last_activity = post.created_at
            
            db.session.add(post)
            db.session.commit()
            
            flash('回复发布成功', 'success')
            return redirect(url_for('forum.topic', id=id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"发布回复失败: {str(e)}")
            flash('发布回复失败，请稍后重试', 'danger')
    
    # 获取帖子列表
    page = request.args.get('page', 1, type=int)
    posts_pagination = ForumPost.query.filter_by(topic_id=id).order_by(
        ForumPost.created_at.asc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('forum/topic.html', 
                           topic=topic,
                           posts=posts_pagination.items,
                           pagination=posts_pagination,
                           form=form)

@forum_bp.route('/create_topic', methods=['GET', 'POST'])
@login_required
def create_topic():
    """创建主题页面"""
    form = TopicForm()
    
    if form.validate_on_submit():
        try:
            topic = ForumTopic(
                title=form.title.data,
                category=form.category.data,
                user_id=current_user.id
            )
            
            db.session.add(topic)
            db.session.flush()  # 获取topic.id
            
            # 创建第一个帖子
            first_post = ForumPost(
                topic_id=topic.id,
                user_id=current_user.id,
                content=form.content.data
            )
            
            db.session.add(first_post)
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
    """置顶/取消置顶主题"""
    topic = ForumTopic.query.get_or_404(id)
    
    try:
        topic.is_pinned = not topic.is_pinned
        db.session.commit()
        
        if topic.is_pinned:
            flash('主题已置顶', 'success')
        else:
            flash('已取消置顶', 'success')
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"置顶操作失败: {str(e)}")
        flash('操作失败，请稍后重试', 'danger')
        
    return redirect(url_for('forum.topic', id=id))

@forum_bp.route('/close_topic/<int:id>', methods=['POST'])
@login_required
@admin_required
def close_topic(id):
    """关闭/打开主题"""
    topic = ForumTopic.query.get_or_404(id)
    
    try:
        topic.is_closed = not topic.is_closed
        db.session.commit()
        
        if topic.is_closed:
            flash('主题已关闭', 'success')
        else:
            flash('主题已打开', 'success')
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"关闭操作失败: {str(e)}")
        flash('操作失败，请稍后重试', 'danger')
        
    return redirect(url_for('forum.topic', id=id))
