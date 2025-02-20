from fastapi import status
from fastapi.responses import JSONResponse


def ok(data: dict = None, **kwargs) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "ok",
            "description": "OK",
            "data": data,
            **kwargs,
        },
    )


def bad_request(message: str = "N/A", **kwargs) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "error",
            "description": "Bad Request",
            "message": message,
            **kwargs,
        },
    )


def forbidden(message: str = "N/A", **kwargs) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "error",
            "description": "Forbidden",
            "message": message,
            **kwargs,
        },
    )


def internal_server_error(message: str = "N/A", **kwargs) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "error",
            "description": "Internal Server Error",
            "message": message,
            **kwargs,
        },
    )


def not_implement(message: str = "N/A", **kwargs) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "error",
            "description": "Not Implement",
            "message": message,
            **kwargs,
        },
    )
