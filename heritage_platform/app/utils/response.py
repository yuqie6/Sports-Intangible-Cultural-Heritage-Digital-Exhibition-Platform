"""
API响应工具模块

本模块提供了一组用于生成标准化API响应的工具函数，确保所有API接口返回一致的响应格式。
主要功能包括：
1. 成功响应：返回带有数据的成功响应
2. 错误响应：返回带有错误信息的失败响应
3. 分页列表响应：返回带有分页信息的数据列表
4. 特定类型错误响应：如验证错误、资源未找到、未授权访问等

标准响应格式：
{
    "success": true/false,
    "message": "操作结果描述",
    "data": {...}  // 可选，仅在成功响应中包含
    "error_code": "ERROR_CODE"  // 可选，仅在错误响应中包含
    "details": {...}  // 可选，仅在错误响应中包含
}
"""

from flask import jsonify
from typing import Optional, Any, Dict, Union
from http import HTTPStatus

def api_success(data: Optional[Any] = None, message: str = "操作成功", status_code: int = HTTPStatus.OK) -> tuple:
    """标准API成功响应

    生成一个标准格式的API成功响应，包含成功标志、消息和可选的数据。

    Args:
        data: 响应数据，可以是任何可JSON序列化的对象，如字典、列表等
        message: 成功消息，描述操作结果
        status_code: HTTP状态码，默认为200 OK

    Returns:
        tuple: 包含JSON响应和HTTP状态码的元组，格式为(jsonify(response), status_code)

    示例:
        return api_success({"user_id": 1, "username": "admin"}, "用户创建成功")
        # 返回: ({"success": true, "message": "用户创建成功", "data": {"user_id": 1, "username": "admin"}}, 200)
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

    生成一个标准格式的API错误响应，包含错误标志、错误消息、可选的错误代码和详细信息。

    Args:
        message: 错误消息，描述错误原因
        status_code: HTTP状态码，默认为400 BAD_REQUEST
        error_code: 自定义错误代码，用于客户端识别特定错误类型
        details: 详细错误信息，可包含字段错误、调试信息等

    Returns:
        tuple: 包含JSON响应和HTTP状态码的元组，格式为(jsonify(response), status_code)

    示例:
        return api_error(
            message="用户名已存在",
            status_code=HTTPStatus.CONFLICT,
            error_code="USER_EXISTS",
            details={"field": "username", "value": "admin"}
        )
        # 返回: ({"success": false, "message": "用户名已存在",
        #         "error_code": "USER_EXISTS",
        #         "details": {"field": "username", "value": "admin"}}, 409)
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

    生成一个标准格式的分页数据列表响应，包含数据项和分页信息。
    适用于所有需要分页的API接口，确保分页格式一致。

    Args:
        items: 当前页的数据列表，通常是模型对象转换后的字典列表
        total: 总记录数，用于计算总页数
        page: 当前页码，从1开始
        per_page: 每页记录数，用于计算总页数
        message: 响应消息，描述操作结果

    Returns:
        tuple: 包含JSON响应和HTTP状态码的元组

    响应格式:
    {
        "success": true,
        "message": "获取列表成功",
        "data": {
            "items": [...],  // 当前页数据
            "pagination": {
                "total": 100,  // 总记录数
                "page": 1,     // 当前页码
                "per_page": 10, // 每页记录数
                "pages": 10     // 总页数
            }
        }
    }

    示例:
        items = [user.to_dict() for user in users]
        return api_list_response(items, total=100, page=1, per_page=10)
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
