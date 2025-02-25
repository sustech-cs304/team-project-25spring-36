from fastapi import status
from fastapi.responses import JSONResponse
from typing import Dict, LiteralString


def ok(data: Dict = None, **kwargs) -> JSONResponse:
    """
    返回成功响应

    参数:
    - data: 返回的数据字典（可选）
    - kwargs: 其他附加内容（可选）

    返回:
    - JSONResponse: 包含状态为 "ok" 的响应
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "success",
            "code": status.HTTP_200_OK,
            "description": "OK",
            "data": data,
            **kwargs,
        },
    )


def bad_request(message: LiteralString = "N/A", **kwargs) -> JSONResponse:
    """
    返回错误请求响应

    参数:
    - message: 错误信息（可选）
    - kwargs: 其他附加内容（可选）

    返回:
    - JSONResponse: 包含状态为 "error" 和描述为 "Bad Request" 的响应
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "error",
            "code": status.HTTP_400_BAD_REQUEST,
            "description": "Bad Request",
            "message": message,
            **kwargs,
        },
    )


def forbidden(message: LiteralString = "N/A", **kwargs) -> JSONResponse:
    """
    返回禁止访问响应

    参数:
    - message: 错误信息（可选）
    - kwargs: 其他附加内容（可选）

    返回:
    - JSONResponse: 包含状态为 "error" 和描述为 "Forbidden" 的响应
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "error",
            "code": status.HTTP_403_FORBIDDEN,
            "description": "Forbidden",
            "message": message,
            **kwargs,
        },
    )


def internal_server_error(message: LiteralString = "N/A", **kwargs) -> JSONResponse:
    """
    返回服务器内部错误响应

    参数:
    - message: 错误信息（可选）
    - kwargs: 其他附加内容（可选）

    返回:
    - JSONResponse: 包含状态为 "error" 和描述为 "Internal Server Error" 的响应
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "error",
            "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "description": "Internal Server Error",
            "message": message,
            **kwargs,
        },
    )


def not_implemented(message: LiteralString = "N/A", **kwargs) -> JSONResponse:
    """
    返回未实现功能响应

    参数:
    - message: 错误信息（可选）
    - kwargs: 其他附加内容（可选）

    返回:
    - JSONResponse: 包含状态为 "error" 和描述为 "Not Implemented" 的响应
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "error",
            "code": status.HTTP_501_NOT_IMPLEMENTED,
            "description": "Not Implemented",
            "message": message,
            **kwargs,
        },
    )
