from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from app import db
from app.models import HeritageItem, Content
from app.forms.heritage import HeritageItemForm
from app.utils.decorators import teacher_required
from app.utils.file_handlers import save_file
from sqlalchemy.exc import SQLAlchemyError

# 创建蓝图，用于组织非遗项目相关的路由
heritage_bp = Blueprint('heritage', __name__)

@heritage_bp.route('/list')
def list():
    """非遗项目列表页
    
    展示所有非遗项目，支持分页和按分类筛选。
    页面包含项目卡片、分类筛选器和分页控件。
    
    URL参数:
        page (int): 当前页码，默认为1
        category (str): 筛选的项目分类，可选
        
    Returns:
        HTML: 渲染后的列表页面
    """
    # 获取页码参数，默认为第1页
    page = request.args.get('page', 1, type=int)
    # 获取分类筛选参数
    category = request.args.get('category')
    
    # 构建查询对象
    query = HeritageItem.query
    
    # 如果提供了分类参数，应用分类筛选
    if category:
        query = query.filter_by(category=category)
        
    # 执行分页查询，每页显示9个项目
    pagination = query.order_by(HeritageItem.created_at.desc()).paginate(
        page=page, per_page=9, error_out=False)
    
    # 获取当前页的项目列表
    items = pagination.items
    
    # 获取所有可用的分类，用于构建筛选器
    categories = db.session.query(HeritageItem.category).distinct().all()
    categories = [c[0] for c in categories]
    
    # 渲染模板，传入项目列表、分页对象、分类列表和当前选中的分类
    return render_template('heritage/list.html', 
                           items=items, 
                           pagination=pagination,
                           categories=categories,
                           current_category=category)

@heritage_bp.route('/detail/<int:id>')
def detail(id):
    """非遗项目详情页
    
    展示指定非遗项目的详细信息，包括基本资料和关联的不同类型内容。
    
    Args:
        id (int): 非遗项目ID
        
    Returns:
        HTML: 渲染后的详情页面
        
    Raises:
        404: 如果指定ID的项目不存在
    """
    # 获取指定ID的项目，如不存在则返回404错误
    item = HeritageItem.query.get_or_404(id)
    
    try:
        # 获取所有关联内容并按类型分组
        contents = item.contents
        # 将内容按类型分类为文章、视频、图片和多媒体
        articles = [c for c in contents if c.content_type == 'article']
        videos = [c for c in contents if c.content_type == 'video']
        images = [c for c in contents if c.content_type == 'image']
        multimedia = [c for c in contents if c.content_type == 'multimedia']
        
        # 记录内容获取成功的日志
        current_app.logger.info(f"Found contents for heritage {id}: {len(articles)} articles, {len(videos)} videos, {len(images)} images, {len(multimedia)} rich texts")
        
    except Exception as e:
        # 记录错误日志并设置空内容列表
        current_app.logger.error(f"Error fetching contents for heritage {id}: {str(e)}")
        articles, videos, images, multimedia = [], [], [], []
    
    # 渲染详情页模板，传入项目信息和不同类型的内容
    return render_template('heritage/detail.html', 
                           item=item,
                           articles=articles,
                           videos=videos,
                           images=images,
                           multimedia=multimedia)

@heritage_bp.route('/create', methods=['GET', 'POST'])
@login_required  # 需要用户登录
@teacher_required  # 需要教师权限
def create():
    """创建非遗项目页面
    
    提供表单用于创建新的非遗项目。
    仅限已登录的教师用户访问。
    支持上传封面图片。
    
    Methods:
        GET: 显示创建表单
        POST: 处理表单提交，创建新项目
        
    Returns:
        GET: 渲染创建表单页面
        POST成功: 重定向到新创建项目的详情页
        POST失败: 显示错误消息并重新渲染表单
    """
    # 创建表单实例
    form = HeritageItemForm()
    
    # 如果是POST请求且表单验证通过
    if form.validate_on_submit():
        try:
            # 处理封面图片上传
            cover_image = ''
            if form.cover_image.data:
                # 确保cover_image.data是文件对象而不是字符串
                if hasattr(form.cover_image.data, 'filename'):
                    # 保存上传的图片文件，返回存储路径
                    cover_image = save_file(form.cover_image.data, 'image')
                
            # 创建新的非遗项目实例
            heritage_item = HeritageItem(
                name=form.name.data,
                category=form.category.data,
                description=form.description.data,
                cover_image=cover_image,
                created_by=current_user.id  # 记录创建者ID
            )
            
            # 添加到数据库会话并提交
            db.session.add(heritage_item)
            db.session.commit()
            
            # 显示成功消息
            flash('非遗项目创建成功', 'success')
            # 重定向到新创建项目的详情页
            return redirect(url_for('heritage.detail', id=heritage_item.id))
        
        except Exception as e:
            # 发生错误时回滚数据库事务
            db.session.rollback()
            # 记录错误日志
            current_app.logger.error(f"创建非遗项目失败: {str(e)}")
            # 显示错误消息
            flash('创建非遗项目失败，请稍后重试', 'danger')
    
    # GET请求或表单验证失败时，渲染创建表单
    return render_template('heritage/create.html', form=form)

@heritage_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required  # 需要用户登录
@teacher_required  # 需要教师权限
def edit(id):
    """编辑非遗项目页面
    
    提供表单用于编辑现有的非遗项目。
    仅限项目创建者或管理员访问。
    支持更新封面图片。
    
    Args:
        id (int): 非遗项目ID
        
    Methods:
        GET: 显示编辑表单，预填充现有数据
        POST: 处理表单提交，更新项目
        
    Returns:
        GET: 渲染编辑表单页面
        POST成功: 重定向到项目详情页
        POST失败: 显示错误消息并重新渲染表单
        权限不足: 重定向到项目详情页并显示错误消息
        
    Raises:
        404: 如果指定ID的项目不存在
    """
    # 获取指定ID的项目，如不存在则返回404错误
    heritage_item = HeritageItem.query.get_or_404(id)
    
    # 权限检查：只有创建者或管理员可以编辑
    if heritage_item.created_by != current_user.id and not current_user.is_admin:
        flash('您没有权限编辑此项目', 'danger')
        return redirect(url_for('heritage.detail', id=id))
        
    # 创建表单实例，预填充现有数据
    form = HeritageItemForm(obj=heritage_item)
    
    # 如果是POST请求且表单验证通过
    if form.validate_on_submit():
        try:
            # 更新项目基本信息
            heritage_item.name = form.name.data
            heritage_item.category = form.category.data
            heritage_item.description = form.description.data
            
            # 处理封面图片更新
            if form.cover_image.data:
                # 确保cover_image.data是文件对象而不是字符串
                if hasattr(form.cover_image.data, 'filename'):
                    # 保存新上传的图片文件
                    cover_image = save_file(form.cover_image.data, 'image')
                    if cover_image:
                        heritage_item.cover_image = cover_image
                    
            # 提交数据库事务
            db.session.commit()
            
            # 显示成功消息
            flash('非遗项目更新成功', 'success')
            # 重定向到更新后的项目详情页
            return redirect(url_for('heritage.detail', id=heritage_item.id))
        
        except Exception as e:
            # 发生错误时回滚数据库事务
            db.session.rollback()
            # 记录错误日志
            current_app.logger.error(f"更新非遗项目失败: {str(e)}")
            # 显示错误消息
            flash('更新非遗项目失败，请稍后重试', 'danger')
    
    # GET请求或表单验证失败时，渲染编辑表单
    return render_template('heritage/edit.html', form=form, item=heritage_item)

@heritage_bp.route('/delete/<int:id>', methods=['POST'])
@login_required  # 需要用户登录
@teacher_required  # 需要教师权限
def delete(id):
    """删除非遗项目
    
    删除指定的非遗项目及其关联内容（仅管理员可删除有关联内容的项目）。
    仅限项目创建者或管理员访问。
    
    Args:
        id (int): 非遗项目ID
        
    Methods:
        POST: 处理删除请求
        
    Returns:
        成功: 重定向到项目列表页并显示成功消息
        失败: 重定向到项目详情页并显示错误消息
        权限不足: 重定向到项目详情页并显示错误消息
        
    Raises:
        404: 如果指定ID的项目不存在
    """
    # 获取指定ID的项目，如不存在则返回404错误
    heritage_item = HeritageItem.query.get_or_404(id)
    
    # 权限检查：只有创建者或管理员可以删除
    if not (current_user.is_admin or heritage_item.created_by == current_user.id):
        flash('您没有权限删除此项目', 'danger')
        return redirect(url_for('heritage.detail', id=id))
        
    try:
        # 检查是否有关联的内容
        contents = Content.query.filter_by(heritage_id=id).all()
        
        # 非管理员用户不能删除有关联内容的项目
        if contents and not current_user.is_admin:
            flash('此项目下有关联内容，无法删除。请先删除所有关联内容或联系管理员', 'warning')
            return redirect(url_for('heritage.detail', id=id))
            
        # 管理员可以强制删除所有关联内容
        if current_user.is_admin and contents:
            for content in contents:
                db.session.delete(content)
                
        # 删除非遗项目
        db.session.delete(heritage_item)
        # 提交数据库事务
        db.session.commit()
        
        # 显示成功消息
        flash('非遗项目删除成功', 'success')
        # 重定向到项目列表页
        return redirect(url_for('heritage.list'))
        
    except Exception as e:
        # 发生错误时回滚数据库事务
        db.session.rollback()
        # 记录错误日志
        current_app.logger.error(f"删除非遗项目失败: {str(e)}")
        # 显示错误消息
        flash('删除非遗项目失败，请稍后重试', 'danger')
        # 重定向到项目详情页
        return redirect(url_for('heritage.detail', id=id))
