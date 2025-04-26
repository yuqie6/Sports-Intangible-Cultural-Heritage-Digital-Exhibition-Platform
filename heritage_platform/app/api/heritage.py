"""
非物质文化遗产项目API模块

本模块提供与非物质文化遗产项目相关的RESTful API接口，包括：
- 获取非遗项目列表（支持分页和分类筛选）
- 获取单个非遗项目详情
- 创建新的非遗项目（仅限教师用户）

这些API接口支持前端与后端的数据交互，为用户提供非遗项目的浏览和管理功能。
"""

from flask import request, current_app
from . import api_bp  # 导入API蓝图
from app.models import HeritageItem  # 导入非遗项目模型
from app import db  # 导入数据库实例
from flask_login import current_user, login_required  # 导入用户认证相关功能
from app.utils.decorators import teacher_required  # 导入教师权限装饰器
from app.utils.response import api_success, api_error  # 导入API响应工具函数
import traceback  # 导入异常追踪模块

@api_bp.route('/heritage_items', methods=['GET'])
def get_heritage_items():
    """获取非遗项目列表API

    提供分页和分类筛选功能的非遗项目列表查询接口。

    URL参数:
        page (int, 可选): 当前页码，默认为1
        per_page (int, 可选): 每页项目数量，默认为10
        category (str, 可选): 按项目分类筛选

    返回:
        JSON: 包含项目列表、总数、总页数和当前页码的响应
        {
            "success": true,
            "data": {
                "items": [...],  # 项目列表，每个项目为字典格式
                "total": 100,    # 总项目数
                "pages": 10,     # 总页数
                "current_page": 1 # 当前页码
            },
            "message": "success"
        }
    """
    try:
        # 从请求参数中获取分页和筛选条件
        page = request.args.get('page', 1, type=int)  # 获取页码，默认为第1页
        per_page = request.args.get('per_page', 10, type=int)  # 获取每页数量，默认为10条
        category = request.args.get('category')  # 获取分类筛选条件

        # 构建查询对象
        query = HeritageItem.query

        # 如果提供了分类参数，添加分类筛选条件
        if category:
            query = query.filter_by(category=category)

        # 执行分页查询，按创建时间降序排序
        pagination = query.order_by(HeritageItem.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False)

        # 获取当前页的项目列表
        items = pagination.items

        # 构建响应结果
        result = {
            'items': [item.to_dict() for item in items],  # 将每个项目转换为字典格式
            'total': pagination.total,  # 总项目数
            'pages': pagination.pages,  # 总页数
            'current_page': page  # 当前页码
        }

        # 返回成功响应
        return api_success(result)
    except Exception as e:
        # 记录错误日志
        current_app.logger.error(f"获取非遗项目列表出错：{str(e)}")
        current_app.logger.error(traceback.format_exc())  # 记录完整的异常堆栈
        # 返回错误响应
        return api_error("获取非遗项目列表失败")

@api_bp.route('/heritage_items/<int:id>', methods=['GET'])
def get_heritage_item(id):
    """获取非遗项目详情API

    根据项目ID获取单个非遗项目的详细信息，包括关联的内容列表。

    URL参数:
        id (int): 非遗项目ID，作为URL路径的一部分

    返回:
        JSON: 包含项目详细信息的响应
        {
            "success": true,
            "data": {
                "id": 1,
                "name": "项目名称",
                "category": "项目分类",
                "description": "项目描述",
                "cover_image": "封面图片路径",
                "created_at": "创建时间",
                "created_by": "创建者ID",
                "contents": [...]  # 关联的内容列表
            },
            "message": "success"
        }
    """
    try:
        # 查询项目，如果不存在则返回404错误
        item = HeritageItem.query.get_or_404(id)
        # 返回项目详情，包括关联的内容
        return api_success(item.to_dict(include_contents=True))
    except Exception as e:
        # 记录错误日志
        current_app.logger.error(f"获取非遗项目详情出错：{str(e)}")
        # 返回错误响应
        return api_error("获取非遗项目详情失败")

@api_bp.route('/heritage_items', methods=['POST'])
@login_required  # 要求用户登录
@teacher_required  # 要求用户具有教师权限
def create_heritage_item():
    """创建非遗项目API

    创建新的非遗项目，仅限已登录的教师用户使用。

    请求体:
        JSON对象，包含以下字段:
        {
            "name": "项目名称",  # 必填
            "category": "项目分类",  # 必填
            "description": "项目描述",  # 可选
            "cover_image": "封面图片路径"  # 可选
        }

    返回:
        JSON: 包含新创建项目信息的响应
        {
            "success": true,
            "data": {
                "id": 1,
                "name": "项目名称",
                ...
            },
            "message": "非遗项目创建成功"
        }
    """
    try:
        # 获取请求中的JSON数据
        data = request.get_json()

        # 验证数据是否存在
        if not data:
            return api_error("无效的数据")

        # 验证必填字段
        if not data.get('name') or not data.get('category'):
            return api_error("项目名称和分类不能为空")

        # 创建新的非遗项目实例
        item = HeritageItem(
            name=data['name'],  # 项目名称
            category=data['category'],  # 项目分类
            description=data.get('description', ''),  # 项目描述，可选
            cover_image=data.get('cover_image', ''),  # 封面图片，可选
            created_by=current_user.id  # 创建者ID，当前登录用户
        )

        # 将新项目添加到数据库会话
        db.session.add(item)
        # 提交事务
        db.session.commit()

        # 返回成功响应，包含新创建的项目信息
        return api_success(item.to_dict(), "非遗项目创建成功")
    except Exception as e:
        # 发生异常时回滚事务
        db.session.rollback()
        # 记录错误日志
        current_app.logger.error(f"创建非遗项目出错：{str(e)}")
        # 返回错误响应
        return api_error("创建非遗项目失败")
