from flask import jsonify, request, current_app
from . import api_bp
from app.models import HeritageItem
from app import db
from flask_login import current_user, login_required
from app.utils.decorators import teacher_required
from app.utils.response import api_success, api_error
import traceback

@api_bp.route('/heritage_items', methods=['GET'])
def get_heritage_items():
    """获取非遗项目列表API"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        category = request.args.get('category')
        
        query = HeritageItem.query
        
        if category:
            query = query.filter_by(category=category)
            
        pagination = query.order_by(HeritageItem.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False)
        
        items = pagination.items
        
        result = {
            'items': [item.to_dict() for item in items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }
        
        return api_success(result)
    except Exception as e:
        current_app.logger.error(f"获取非遗项目列表出错：{str(e)}")
        current_app.logger.error(traceback.format_exc())
        return api_error("获取非遗项目列表失败")

@api_bp.route('/heritage_items/<int:id>', methods=['GET'])
def get_heritage_item(id):
    """获取非遗项目详情API"""
    try:
        item = HeritageItem.query.get_or_404(id)
        return api_success(item.to_dict(include_contents=True))
    except Exception as e:
        current_app.logger.error(f"获取非遗项目详情出错：{str(e)}")
        return api_error("获取非遗项目详情失败")

@api_bp.route('/heritage_items', methods=['POST'])
@login_required
@teacher_required
def create_heritage_item():
    """创建非遗项目API"""
    try:
        data = request.get_json()
        
        if not data:
            return api_error("无效的数据")
        
        # 基本验证
        if not data.get('name') or not data.get('category'):
            return api_error("项目名称和分类不能为空")
            
        item = HeritageItem(
            name=data['name'],
            category=data['category'],
            description=data.get('description', ''),
            cover_image=data.get('cover_image', ''),
            created_by=current_user.id
        )
        
        db.session.add(item)
        db.session.commit()
        
        return api_success(item.to_dict(), "非遗项目创建成功")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建非遗项目出错：{str(e)}")
        return api_error("创建非遗项目失败")
