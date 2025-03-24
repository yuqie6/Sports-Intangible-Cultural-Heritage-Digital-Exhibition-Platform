from flask import jsonify

def api_success(data=None, message="操作成功"):
    """标准API成功响应"""
    response = {
        "success": True,
        "message": message
    }
    
    if data is not None:
        response["data"] = data
        
    return jsonify(response)

def api_error(message="操作失败", code=400):
    """标准API错误响应"""
    response = {
        "success": False,
        "message": message
    }
    
    return jsonify(response), code
