from flask import jsonify
from typing import Optional, Any, Dict, Union
from http import HTTPStatus

def api_success(data: Optional[Any] = None, message: str = "操作成功", status_code: int = HTTPStatus.OK) -> tuple:
    """标准API成功响应
    
    Args:
        data: 响应数据
        message: 成功消息
        status_code: HTTP状态码
    """
    response = {
        "success": True,
        "message": message
    }
    
    if data is not None:
        response["data"] = data
        
    return jsonify(response), status_code

def api_error(
    message: str = "操作失败",
    status_code: int = HTTPStatus.BAD_REQUEST,
    error_code: Optional[str] = None,
    details: Optional[Dict] = None
) -> tuple:
    """标准API错误响应
    
    Args:
        message: 错误消息
        status_code: HTTP状态码
        error_code: 自定义错误代码
        details: 详细错误信息
    """
    response = {
        "success": False,
        "message": message
    }
    
    if error_code:
        response["error_code"] = error_code
        
    if details:
        response["details"] = details
    
    return jsonify(response), status_code

def api_list_response(
    items: list,
    total: int,
    page: int,
    per_page: int,
    message: str = "获取列表成功"
) -> tuple:
    """分页列表响应
    
    Args:
        items: 当前页的数据列表
        total: 总记录数
        page: 当前页码
        per_page: 每页记录数
        message: 响应消息
    """
    response = {
        "success": True,
        "message": message,
        "data": {
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page
            }
        }
    }
    
    return jsonify(response), HTTPStatus.OK

def api_validation_error(errors: Dict[str, list]) -> tuple:
    """表单验证错误响应
    
    Args:
        errors: 字段错误信息字典
    """
    return api_error(
        message="输入验证失败",
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        error_code="VALIDATION_ERROR",
        details={"fields": errors}
    )

def api_not_found(resource: str = "资源", message: Optional[str] = None) -> tuple:
    """资源未找到响应
    
    Args:
        resource: 资源名称
        message: 自定义消息
    """
    return api_error(
        message=message or f"{resource}不存在",
        status_code=HTTPStatus.NOT_FOUND,
        error_code="NOT_FOUND"
    )

def api_unauthorized(message: str = "未授权访问") -> tuple:
    """未授权访问响应"""
    return api_error(
        message=message,
        status_code=HTTPStatus.UNAUTHORIZED,
        error_code="UNAUTHORIZED"
    )

def api_forbidden(message: str = "没有操作权限") -> tuple:
    """禁止访问响应"""
    return api_error(
        message=message,
        status_code=HTTPStatus.FORBIDDEN,
        error_code="FORBIDDEN"
    )
