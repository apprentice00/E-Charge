from flask import jsonify
from typing import Any, Dict, Optional

def success_response(message: str = "操作成功", data: Any = None, code: int = 200) -> Dict[str, Any]:
    """
    创建成功响应
    
    Args:
        message: 响应消息
        data: 响应数据
        code: 状态码
        
    Returns:
        标准化的成功响应
    """
    response = {
        "success": True,
        "code": code,
        "message": message
    }
    
    if data is not None:
        response["data"] = data
    
    return jsonify(response)

def error_response(message: str = "操作失败", code: int = 400, data: Any = None) -> Dict[str, Any]:
    """
    创建错误响应
    
    Args:
        message: 错误消息
        code: 错误码
        data: 附加数据
        
    Returns:
        标准化的错误响应
    """
    response = {
        "success": False,
        "code": code,
        "message": message
    }
    
    if data is not None:
        response["data"] = data
    
    return jsonify(response), code

def validation_error_response(errors: Dict[str, str]) -> Dict[str, Any]:
    """
    创建验证错误响应
    
    Args:
        errors: 字段验证错误字典
        
    Returns:
        验证错误响应
    """
    return error_response(
        message="数据验证失败",
        code=422,
        data={"validation_errors": errors}
    )

def unauthorized_response(message: str = "未授权访问") -> Dict[str, Any]:
    """
    创建未授权响应
    
    Args:
        message: 错误消息
        
    Returns:
        未授权响应
    """
    return error_response(message=message, code=401)

def forbidden_response(message: str = "权限不足") -> Dict[str, Any]:
    """
    创建禁止访问响应
    
    Args:
        message: 错误消息
        
    Returns:
        禁止访问响应
    """
    return error_response(message=message, code=403)

def not_found_response(message: str = "资源不存在") -> Dict[str, Any]:
    """
    创建资源不存在响应
    
    Args:
        message: 错误消息
        
    Returns:
        资源不存在响应
    """
    return error_response(message=message, code=404)

def server_error_response(message: str = "服务器内部错误") -> Dict[str, Any]:
    """
    创建服务器错误响应
    
    Args:
        message: 错误消息
        
    Returns:
        服务器错误响应
    """
    return error_response(message=message, code=500) 