import os
import uuid
import traceback
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import current_user, login_required
from app import db, csrf
from app.models import Content, HeritageItem, Comment, Like, Favorite, ContentImage
from app.forms.content import ContentForm, CommentForm
from app.utils.file_handlers import ALLOWED_IMAGE_EXTENSIONS, allowed_file, save_file
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_

content_bp = Blueprint('content', __name__)

@content_bp.route('/list')
def list():
    """内容列表页"""
    page = request.args.get('page', 1, type=int)
    content_type = request.args.get('type')
    heritage_id = request.args.get('heritage_id', type=int)
    search_query = request.args.get('q', '')  # 获取搜索关键词
    per_page = 12
    
    try:
        # 使用查询构建器并加载关联的用户信息和heritage项目
        query = Content.query.options(db.joinedload(Content.heritage)).join(Content.author)
        
        # 应用搜索过滤
        if search_query:
            query = query.filter(or_(
                Content.title.ilike(f'%{search_query}%'),
                Content.text_content.ilike(f'%{search_query}%'),
                Content.rich_content.ilike(f'%{search_query}%')
            ))
            current_app.logger.info(f"处理搜索请求: '{search_query}'")
        
        if content_type:
            query = query.filter(Content.content_type == content_type)
            
        if heritage_id:
            query = query.filter(Content.heritage_id == heritage_id)
            
        # 应用排序并进行分页
        pagination = query.order_by(Content.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False)
        
        items = pagination.items
        
    except Exception as e:
        current_app.logger.error(f"内容列表查询错误: {str(e)}")
        # 降级处理：返回空列表
        items = []
        pagination = None
    
    # 获取所有非遗项目供筛选用
    try:
        heritage_items = HeritageItem.query.all()
    except Exception as e:
        current_app.logger.error(f"获取非遗项目列表错误: {str(e)}")
        heritage_items = []
    
    return render_template('content/list.html', 
                           items=items, 
                           pagination=pagination,
                           heritage_items=heritage_items,
                           current_type=content_type,
                           current_heritage_id=heritage_id,
                           search_query=search_query)  # 传递搜索关键词到模板

@content_bp.route('/detail/<int:id>', methods=['GET', 'POST'])
def detail(id):
    """内容详情页"""
    content = Content.query.options(db.joinedload(Content.heritage)).get_or_404(id)
    
    # 更新浏览量
    content.views += 1
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"更新浏览量失败: {str(e)}")
        db.session.rollback()
    
    # 评论表单
    form = CommentForm()
    
    if form.validate_on_submit() and current_user.is_authenticated:
        try:
            comment = Comment(
                user_id=current_user.id,
                content_id=id,
                text=form.text.data
            )
            
            db.session.add(comment)
            
            # 如果评论者不是内容作者本人，发送通知
            if current_user.id != content.user_id:
                from app.routes.notification import send_notification
                content_msg = f"{current_user.username} 评论了你的内容 \"{content.title}\""
                send_notification(
                    user_id=content.user_id,
                    content=content_msg,
                    notification_type='reply',
                    link=url_for('content.detail', id=id),
                    sender_id=current_user.id
                )
            
            db.session.commit()
            flash('评论发布成功', 'success')
            return redirect(url_for('content.detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"发布评论失败: {str(e)}")
            flash('发布评论失败，请稍后重试', 'danger')
    
    # 获取顶级评论列表（不包括回复）
    page = request.args.get('page', 1, type=int)
    comments_pagination = Comment.query.filter_by(
        content_id=id,
        parent_id=None
    ).order_by(Comment.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # 检查当前用户是否已点赞
    has_liked = False
    if current_user.is_authenticated:
        has_liked = Like.query.filter_by(
            user_id=current_user.id, 
            content_id=id
        ).first() is not None
    
    # 检查当前用户是否已收藏
    has_favorited = False
    if current_user.is_authenticated:
        has_favorited = Favorite.query.filter_by(
            user_id=current_user.id, 
            content_id=id
        ).first() is not None
    
    # 获取相关内容推荐 - 相同非遗项目且相同类型的内容，排除当前内容
    related_contents = Content.query.filter(
        Content.heritage_id == content.heritage_id,
        Content.content_type == content.content_type,
        Content.id != content.id
    ).order_by(db.func.random()).limit(4).all()

    # 如果不足4个，补充相同非遗项目的内容
    if len(related_contents) < 4:
        additional = Content.query.filter(
            Content.heritage_id == content.heritage_id,
            Content.id != content.id,
            Content.id.notin_([c.id for c in related_contents])
        ).order_by(db.func.random()).limit(4 - len(related_contents)).all()
        related_contents.extend(additional)

    # 如果仍不足4个，补充随机内容
    if len(related_contents) < 4:
        additional = Content.query.filter(
            Content.id != content.id,
            Content.id.notin_([c.id for c in related_contents])
        ).order_by(db.func.random()).limit(4 - len(related_contents)).all()
        related_contents.extend(additional)

    return render_template('content/detail.html', 
                           content=content,
                           form=form,
                           comments=comments_pagination.items,
                           pagination=comments_pagination,
                           has_liked=has_liked,
                           has_favorited=has_favorited,
                           related_contents=related_contents)

@content_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """编辑内容页面"""
    content = Content.query.get_or_404(id)
    
    # 检查权限：只有作者或管理员可以编辑
    if current_user.id != content.user_id and not current_user.is_admin:
        flash('无权编辑此内容', 'danger')
        return redirect(url_for('content.detail', id=id))
        
    form = ContentForm(obj=content)
    
    # 动态加载非遗项目选项
    form.heritage_id.choices = [(h.id, h.name) for h in HeritageItem.query.all()]
    
    if form.validate_on_submit():
        try:
            content.title = form.title.data
            content.heritage_id = form.heritage_id.data
            content.content_type = form.content_type.data
            
            # 处理封面图片（适用于所有内容类型）
            # 注意：只在用户选择了新封面图片时才处理上传
            if hasattr(form.cover_image.data, 'filename') and form.cover_image.data.filename:
                current_app.logger.info(f"处理封面图片上传: {form.cover_image.data.filename}")
                cover_path = save_file(form.cover_image.data, 'image')
                if cover_path:
                    current_app.logger.info(f"封面图片上传成功，路径: {cover_path}")
                    content.cover_image = cover_path
                else:
                    current_app.logger.error("封面图片上传失败")
                    flash('封面图片上传失败', 'danger')
                    return render_template('content/edit.html', form=form, content=content)
            
            # 根据内容类型处理不同字段
            if form.content_type.data == 'article':
                content.text_content = form.text_content.data
                # 清除其他类型的内容字段
                content.rich_content = ''
                content.file_path = ''
            elif form.content_type.data == 'multimedia':
                content.rich_content = form.rich_content.data
                # 清除其他类型的内容字段
                content.text_content = ''
                content.file_path = ''
            elif form.content_type.data == 'image':
                # 处理多图片上传
                if form.file.data and hasattr(form.file.data, 'filename') and form.file.data.filename:
                    # 处理单个文件上传（兼容旧版表单）
                    current_app.logger.info(f"处理单个图片上传: {form.file.data.filename}")
                    file_path = save_file(form.file.data, 'image')
                    if file_path:
                        current_app.logger.info(f"图片上传成功，路径: {file_path}")
                        # 创建图片记录
                        image = ContentImage(
                            content_id=content.id,
                            file_path=file_path,
                            caption=''
                        )
                        db.session.add(image)
                    else:
                        current_app.logger.error(f"图片上传失败: {form.file.data.filename}")
                        flash(f'图片上传失败: {form.file.data.filename}', 'danger')
                        # 不要在这里返回，让用户可以继续保存其他内容
                
                # 处理多图片上传
                if form.multiple_images.data and hasattr(form.multiple_images.data, '__iter__'):
                    for file in form.multiple_images.data:
                        if hasattr(file, 'filename') and file.filename:
                            current_app.logger.info(f"处理多图片上传: {file.filename}")
                            file_path = save_file(file, 'image')
                            if file_path:
                                current_app.logger.info(f"图片上传成功，路径: {file_path}")
                                # 创建图片记录
                                image = ContentImage(
                                    content_id=content.id,
                                    file_path=file_path,
                                    caption=''  # 可以从form.image_captions.data中解析，如果需要
                                )
                                db.session.add(image)
                            else:
                                current_app.logger.error(f"图片上传失败: {file.filename}")
                                flash(f'图片上传失败: {file.filename}', 'danger')
                                # 不要在这里返回，让用户可以继续保存其他内容
                # 清除其他类型的内容字段
                content.text_content = ''
                content.rich_content = ''
            elif form.content_type.data == 'video':
                # 清除其他类型的内容字段
                content.text_content = ''
                content.rich_content = ''
                
                # 只有当用户上传了新文件时才处理文件上传
                if form.file.data and hasattr(form.file.data, 'filename') and form.file.data.filename:
                    current_app.logger.info(f"处理文件上传: {form.file.data.filename}")
                    file_path = save_file(form.file.data, 'video')
                    if file_path:
                        current_app.logger.info(f"文件上传成功，路径: {file_path}")
                        content.file_path = file_path
                    else:
                        current_app.logger.error("文件上传失败")
                        flash('文件上传失败', 'danger')
                        return render_template('content/edit.html', form=form, content=content)
            
            db.session.commit()
            current_app.logger.info(f"内容更新成功：ID={content.id}, 标题={content.title}")
            
            flash('内容更新成功', 'success')
            return redirect(url_for('content.detail', id=content.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新内容失败: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            flash('更新内容失败，请稍后重试', 'danger')
    
    # 预填表单数据
    if not form.is_submitted():
        # 根据内容类型预设表单值
        if content.content_type == 'article':
            form.text_content.data = content.text_content
        elif content.content_type == 'multimedia':
            form.rich_content.data = content.rich_content
    
    return render_template('content/edit.html', form=form, content=content)

@content_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建内容页面"""
    form = ContentForm()
    
    # 动态加载非遗项目选项
    form.heritage_id.choices = [(h.id, h.name) for h in HeritageItem.query.all()]
    
    if form.validate_on_submit():
        try:
            content = Content(
                title=form.title.data,
                heritage_id=form.heritage_id.data,
                user_id=current_user.id,
                content_type=form.content_type.data
            )
            
            # 处理封面图片（适用于所有内容类型）
            if form.cover_image.data and form.cover_image.data.filename:
                current_app.logger.info(f"处理封面图片上传: {form.cover_image.data.filename}")
                cover_path = save_file(form.cover_image.data, 'image')
                if cover_path:
                    current_app.logger.info(f"封面图片上传成功，路径: {cover_path}")
                    content.cover_image = cover_path
                else:
                    current_app.logger.error("封面图片上传失败")
                    flash('封面图片上传失败', 'danger')
                    # 保留原有封面图片
                    # 不要在这里返回，让用户可以继续保存其他内容
            
            # 根据内容类型处理不同字段
            if form.content_type.data == 'article':
                content.text_content = form.text_content.data
            elif form.content_type.data == 'multimedia':
                content.rich_content = form.rich_content.data
            elif form.content_type.data == 'image':
                # 先保存内容对象以获取ID
                db.session.add(content)
                db.session.flush()
                
                # 处理单个文件上传（兼容旧版表单）
                if form.file.data and hasattr(form.file.data, 'filename') and form.file.data.filename:
                    current_app.logger.info(f"处理单个图片上传: {form.file.data.filename}")
                    file_path = save_file(form.file.data, 'image')
                    if file_path:
                        current_app.logger.info(f"图片上传成功，路径: {file_path}")
                        # 创建图片记录
                        image = ContentImage(
                            content_id=content.id,
                            file_path=file_path,
                            caption=''
                        )
                        db.session.add(image)
                    else:
                        current_app.logger.error(f"图片上传失败: {form.file.data.filename}")
                        flash(f'图片上传失败: {form.file.data.filename}', 'danger')
                        # 不要在这里返回，让用户可以继续保存其他内容
                
                # 处理多图片上传
                if form.multiple_images.data and hasattr(form.multiple_images.data, '__iter__'):
                    for file in form.multiple_images.data:
                        if hasattr(file, 'filename') and file.filename:
                            current_app.logger.info(f"处理多图片上传: {file.filename}")
                            file_path = save_file(file, 'image')
                            if file_path:
                                current_app.logger.info(f"图片上传成功，路径: {file_path}")
                                # 创建图片记录
                                image = ContentImage(
                                    content_id=content.id,
                                    file_path=file_path,
                                    caption=''  # 可以从form.image_captions.data中解析，如果需要
                                )
                                db.session.add(image)
                            else:
                                current_app.logger.error(f"图片上传失败: {file.filename}")
                                db.session.rollback()
                                flash(f'图片上传失败: {file.filename}', 'danger')
                                # 不要在这里返回，让用户可以继续保存其他内容
                elif not form.file.data or not hasattr(form.file.data, 'filename') or not form.file.data.filename:
                    current_app.logger.warning(f"未检测到图片上传")
            elif form.content_type.data == 'video':
                if form.file.data:
                    current_app.logger.info(f"处理视频上传: {form.file.data.filename}")
                    file_path = save_file(form.file.data, 'video')
                    if file_path:
                        current_app.logger.info(f"视频上传成功，路径: {file_path}")
                        content.file_path = file_path
                    else:
                        current_app.logger.error("视频上传失败")
                        flash('视频上传失败', 'danger')
                        return render_template('content/create.html', form=form)
                else:
                    current_app.logger.warning(f"未检测到视频上传")
            
            db.session.add(content)
            db.session.commit()
            current_app.logger.info(f"内容创建成功：ID={content.id}, 标题={content.title}")
            
            flash('内容创建成功', 'success')
            return redirect(url_for('content.detail', id=content.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建内容失败: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            flash('创建内容失败，请稍后重试', 'danger')
    
    return render_template('content/create.html', form=form)

# 添加图片上传API端点，并豁免CSRF保护
@content_bp.route('/upload_cover', methods=['POST'])
@login_required
@csrf.exempt
def upload_cover():
    """封面图片上传处理"""
    try:
        current_app.logger.info("收到封面图片上传请求")
        
        # 检查请求中是否包含文件
        if 'cover_image' not in request.files:
            current_app.logger.warning("请求中没有'cover_image'文件")
            return jsonify({
                'success': False,
                'error': '没有文件上传'
            })
        
        file = request.files['cover_image']
        if file.filename == '':
            current_app.logger.warning("上传了空文件名")
            return jsonify({
                'success': False,
                'error': '未选择文件'
            })
        
        # 检查文件类型
        if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
            current_app.logger.warning(f"不支持的文件类型: {file.filename}")
            return jsonify({
                'success': False,
                'error': '不支持的文件类型，请上传jpg, jpeg, png或gif格式'
            })
        
        # 重置文件指针位置
        file.seek(0)
        
        # 使用统一的文件处理函数保存
        file_path = save_file(file, 'image')
        if not file_path:
            return jsonify({
                'success': False,
                'error': '文件保存失败'
            })
        
        # 构建URL
        url = url_for('static', filename=file_path)
        
        return jsonify({
            'success': True,
            'url': url,
            'fileName': file.filename
        })
        
    except Exception as e:
        current_app.logger.error(f"封面图片上传失败: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@content_bp.route('/upload_image', methods=['POST'])
@login_required
@csrf.exempt   # 添加CSRF豁免
def upload_image():
    """富文本编辑器的图片上传处理"""
    try:
        current_app.logger.info("收到文件上传请求")
        
        # 检查请求中是否包含文件
        if 'upload' not in request.files:
            current_app.logger.warning("请求中没有'upload'文件")
            return jsonify({
                'uploaded': 0,
                'error': {'message': '没有文件上传'}
            })
        
        file = request.files['upload']
        if file.filename == '':
            current_app.logger.warning("上传了空文件名")
            return jsonify({
                'uploaded': 0,
                'error': {'message': '未选择文件'}
            })
        
        # 记录请求信息用于调试
        current_app.logger.info(f"文件名: {file.filename}")
        current_app.logger.info(f"Content-Type: {file.content_type}")
        
        # 检查文件类型
        if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
            current_app.logger.warning(f"不支持的文件类型: {file.filename}")
            return jsonify({
                'uploaded': 0,
                'error': {'message': '不支持的文件类型，请上传jpg, jpeg, png或gif格式'}
            })
        
        # 重置文件指针位置，确保能正确读取文件内容
        file.seek(0)
        
        try:
            # 创建上传目录
            upload_path = os.path.join(
                current_app.root_path, 
                'static', 'uploads', 'images'
            )
            current_app.logger.info(f"上传路径: {upload_path}")
            os.makedirs(upload_path, exist_ok=True)
            
            # 创建安全的文件名
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(upload_path, unique_filename)
            
            # 直接保存文件
            file.save(file_path)
            current_app.logger.info(f"文件保存到: {file_path}")
            
            # 构建绝对URL路径（确保以/static/开头）
            url = url_for('static', filename=f"uploads/images/{unique_filename}")
            
            # 记录生成的URL
            current_app.logger.info(f"生成的图片URL: {url}")
            
            # 确认文件已成功保存
            if os.path.exists(file_path):
                current_app.logger.info(f"文件确认存在: {file_path}")
                # 返回CKEditor需要的格式
                return jsonify({
                    'uploaded': 1,
                    'fileName': filename,
                    'url': url  # 绝对URL路径，以/static/开头
                })
            else:
                current_app.logger.error(f"文件保存后不存在: {file_path}")
                return jsonify({
                    'uploaded': 0, 
                    'error': {'message': '文件保存失败，请稍后重试'}
                })
                
        except Exception as e:
            current_app.logger.error(f"处理上传图片时出错: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            return jsonify({
                'uploaded': 0,
                'error': {'message': f'上传处理失败: {str(e)}'}
            })
    
    except Exception as e:
        current_app.logger.error(f"图片上传过程中发生未处理的错误: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'uploaded': 0,
            'error': {'message': f'服务器错误: {str(e)}'}
        })

@content_bp.route('/like/<int:id>', methods=['POST'])
@login_required
def like(id):
    """点赞内容"""
    content = Content.query.get_or_404(id)
    
    # 检查是否已点赞
    existing_like = Like.query.filter_by(
        user_id=current_user.id,
        content_id=id
    ).first()
    
    try:
        if existing_like:
            # 取消点赞
            db.session.delete(existing_like)
            message = '取消点赞成功'
        else:
            # 添加点赞
            like = Like(user_id=current_user.id, content_id=id)
            db.session.add(like)
            message = '点赞成功'
            
            # 如果点赞者不是内容作者本人，发送通知
            if current_user.id != content.user_id:
                from app.routes.notification import send_notification
                content_msg = f"{current_user.username} 点赞了你的内容\"{content.title}\""
                send_notification(
                    user_id=content.user_id,
                    content=content_msg,
                    notification_type='like',
                    link=url_for('content.detail', id=id),
                    sender_id=current_user.id
                )
            
        db.session.commit()
        flash(message, 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"点赞操作失败: {str(e)}")
        flash('操作失败，请稍后重试', 'danger')
        
    return redirect(url_for('content.detail', id=id))

@content_bp.route('/delete_image/<int:id>', methods=['POST'])
@login_required
def delete_image(id):
    """删除内容中的单张图片"""
    image = ContentImage.query.get_or_404(id)
    content = Content.query.get_or_404(image.content_id)
    
    # 检查权限：只有作者或管理员可以删除
    if current_user.id != content.user_id and not current_user.is_admin:
        return jsonify({
            'success': False,
            'message': '无权删除此图片'
        }), 403
    
    try:
        # 删除物理文件
        image_path = os.path.join(
            current_app.root_path,
            'static',
            image.file_path.replace('/static/', '')
        )
        if os.path.exists(image_path):
            os.remove(image_path)
        
        # 删除数据库记录
        db.session.delete(image)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '图片删除成功'
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除图片失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '删除失败，请稍后重试'
        }), 500

@content_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """删除内容"""
    content = Content.query.get_or_404(id)
    
    # 检查权限：只有作者或管理员可以删除
    if current_user.id != content.user_id and not current_user.is_admin:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': '无权删除此内容'}), 403
        else:
            flash('无权删除此内容', 'danger')
            return redirect(url_for('content.list'))
    
    try:
        # 删除关联文件
        if content.cover_image:
            try:
                # 修复路径处理，避免重复的static前缀
                cover_path = os.path.join(
                    current_app.root_path, 
                    'static', 
                    content.cover_image.replace('/static/', '')
                )
                if os.path.exists(cover_path):
                    os.remove(cover_path)
            except Exception as e:
                current_app.logger.error(f"删除封面图片失败: {str(e)}")
        
        if content.file_path:
            try:
                # 修复路径处理，避免重复的static前缀
                file_path = os.path.join(
                    current_app.root_path,
                    'static',
                    content.file_path.replace('/static/', '')
                )
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                current_app.logger.error(f"删除内容文件失败: {str(e)}")
        
        # 删除相关图片文件
        for image in content.images:
            try:
                image_path = os.path.join(
                    current_app.root_path,
                    'static',
                    image.file_path.replace('/static/', '')
                )
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                current_app.logger.error(f"删除图片文件失败: {str(e)}")
        
        # 删除关联数据
        Comment.query.filter_by(content_id=id).delete()
        Like.query.filter_by(content_id=id).delete()
        Favorite.query.filter_by(content_id=id).delete()
        
        # 删除内容
        db.session.delete(content)
        db.session.commit()
        
        # 处理AJAX请求
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': '内容删除成功'})
            
        flash('内容删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除内容失败: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        
        # 处理AJAX请求
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': '删除内容失败，请稍后重试'}), 500
            
        flash('删除内容失败，请稍后重试', 'danger')
    
    # 检查请求来源，如果来自my_contents页面，则返回到该页面
    referrer = request.referrer
    if referrer and 'my_contents' in referrer:
        return redirect(url_for('user.my_contents'))
    
    # 否则返回内容列表页
    return redirect(url_for('content.list'))

@content_bp.route('/reply_comment/<int:content_id>/<int:comment_id>', methods=['POST'])
@login_required
def reply_comment(content_id, comment_id):
    """回复评论"""
    content = Content.query.get_or_404(content_id)
    parent_comment = Comment.query.get_or_404(comment_id)
    form = CommentForm()
    
    if form.validate_on_submit():
        try:
            reply = Comment(
                user_id=current_user.id,
                content_id=content_id,
                text=form.text.data,
                parent_id=comment_id,
                reply_to_user_id=parent_comment.user_id
            )
            
            db.session.add(reply)
            
            # 发送通知给被回复的用户（如果回复者不是被回复者本人）
            if current_user.id != parent_comment.user_id:
                from app.routes.notification import send_notification
                content_msg = f"{current_user.username} 回复了你在内容 \"{content.title}\" 中的评论"
                send_notification(
                    user_id=parent_comment.user_id,
                    content=content_msg,
                    notification_type='reply',
                    link=url_for('content.detail', id=content_id),
                    sender_id=current_user.id
                )
            
            db.session.commit()
            flash('回复发布成功', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"发布回复失败: {str(e)}")
            flash('发布回复失败，请稍后重试', 'danger')
    
    return redirect(url_for('content.detail', id=content_id))

@content_bp.route('/favorite/<int:id>', methods=['POST'])
@login_required
def favorite(id):
    """收藏内容"""
    content = Content.query.get_or_404(id)
    
    # 检查是否已收藏
    existing_favorite = Favorite.query.filter_by(
        user_id=current_user.id,
        content_id=id
    ).first()
    
    try:
        if existing_favorite:
            # 取消收藏
            db.session.delete(existing_favorite)
            message = '取消收藏成功'
        else:
            # 添加收藏
            favorite = Favorite(user_id=current_user.id, content_id=id)
            db.session.add(favorite)
            message = '收藏成功'
            
        db.session.commit()
        flash(message, 'success')
        
        # 检查请求来源，如果来自 Referer 头包含 my_favorites，则返回到收藏页面
        referrer = request.referrer
        if referrer and 'my_favorites' in referrer:
            return redirect(url_for('user.my_favorites'))
        
        # 处理AJAX请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': True, 'message': message})
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"收藏操作失败: {str(e)}")
        flash('操作失败，请稍后重试', 'danger')
        
        # 如果是AJAX请求，返回错误JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'message': '操作失败，请稍后重试'})
            
    return redirect(url_for('content.detail', id=id))
