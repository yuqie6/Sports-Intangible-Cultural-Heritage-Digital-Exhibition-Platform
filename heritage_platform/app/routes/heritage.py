from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from app import db
from app.models import HeritageItem, Content
from app.forms.heritage import HeritageItemForm
from app.utils.decorators import teacher_required
from app.utils.file_handlers import save_file
from sqlalchemy.exc import SQLAlchemyError

heritage_bp = Blueprint('heritage', __name__)

@heritage_bp.route('/list')
def list():
    """非遗项目列表页"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category')
    
    query = HeritageItem.query
    
    if category:
        query = query.filter_by(category=category)
        
    pagination = query.order_by(HeritageItem.created_at.desc()).paginate(
        page=page, per_page=9, error_out=False)
    
    items = pagination.items
    
    # 获取所有可用的分类
    categories = db.session.query(HeritageItem.category).distinct().all()
    categories = [c[0] for c in categories]
    
    return render_template('heritage/list.html', 
                           items=items, 
                           pagination=pagination,
                           categories=categories,
                           current_category=category)

@heritage_bp.route('/detail/<int:id>')
def detail(id):
    """非遗项目详情页"""
    item = HeritageItem.query.get_or_404(id)
    
    # 获取相关内容
    contents = Content.query.filter_by(heritage_id=id).order_by(Content.created_at.desc()).all()
    
    # 按类型分组内容
    articles = [c for c in contents if c.content_type == 'article']
    videos = [c for c in contents if c.content_type == 'video']
    images = [c for c in contents if c.content_type == 'image']
    
    return render_template('heritage/detail.html', 
                           item=item,
                           articles=articles,
                           videos=videos,
                           images=images)

@heritage_bp.route('/create', methods=['GET', 'POST'])
@login_required
@teacher_required
def create():
    """创建非遗项目页面"""
    form = HeritageItemForm()
    
    if form.validate_on_submit():
        try:
            # 处理封面图片上传
            cover_image = ''
            if form.cover_image.data:
                cover_image = save_file(form.cover_image.data, 'image')
                
            heritage_item = HeritageItem(
                name=form.name.data,
                category=form.category.data,
                description=form.description.data,
                cover_image=cover_image,
                created_by=current_user.id
            )
            
            db.session.add(heritage_item)
            db.session.commit()
            
            flash('非遗项目创建成功', 'success')
            return redirect(url_for('heritage.detail', id=heritage_item.id))
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建非遗项目失败: {str(e)}")
            flash('创建非遗项目失败，请稍后重试', 'danger')
    
    return render_template('heritage/create.html', form=form)

@heritage_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit(id):
    """编辑非遗项目页面"""
    heritage_item = HeritageItem.query.get_or_404(id)
    
    # 只有创建者或管理员可以编辑
    if heritage_item.created_by != current_user.id and not current_user.is_admin:
        flash('您没有权限编辑此项目', 'danger')
        return redirect(url_for('heritage.detail', id=id))
        
    form = HeritageItemForm(obj=heritage_item)
    
    if form.validate_on_submit():
        try:
            heritage_item.name = form.name.data
            heritage_item.category = form.category.data
            heritage_item.description = form.description.data
            
            # 处理封面图片上传
            if form.cover_image.data:
                cover_image = save_file(form.cover_image.data, 'image')
                if cover_image:
                    heritage_item.cover_image = cover_image
                    
            db.session.commit()
            
            flash('非遗项目更新成功', 'success')
            return redirect(url_for('heritage.detail', id=heritage_item.id))
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新非遗项目失败: {str(e)}")
            flash('更新非遗项目失败，请稍后重试', 'danger')
    
    return render_template('heritage/edit.html', form=form, item=heritage_item)
