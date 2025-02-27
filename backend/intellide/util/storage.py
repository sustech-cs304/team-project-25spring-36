import asyncio
import mimetypes
import os

import aiofiles
import aiofiles.os
from fastapi.responses import FileResponse

from intellide.config import STORAGE_PATH


def get_storage_path(storage_name: str) -> str:
    """
    获取存储路径

    参数:
    - storage_name: 存储名称

    返回:
    - 完整的存储路径
    """
    return os.path.join(STORAGE_PATH, storage_name)


async def async_write_file(
        storage_name: str,
        content: bytes,
) -> None:
    """
    异步写入文件

    参数:
    - storage_name: 存储名称
    - content: 文件内容
    """
    async with aiofiles.open(get_storage_path(storage_name), "wb") as fp:
        await fp.write(content)


async def get_file_response(
        storage_name: str,
        file_name: str,
) -> FileResponse:
    """
    获取文件响应

    参数:
    - storage_name: 存储名称
    - file_name: 文件名称

    返回:
    - 文件响应
    """
    # 使用 mimetypes.guess_type 来获取文件的 MIME 类型
    media_type, _ = mimetypes.guess_type(file_name)
    if media_type is None:
        media_type = "application/octet-stream"
    # 返回文件
    return FileResponse(
        get_storage_path(storage_name),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={file_name}"}
    )


async def _startup():
    """
    异步创建存储目录（如果不存在）
    """
    await aiofiles.os.makedirs(STORAGE_PATH, exist_ok=True)


# 调度 _startup 函数运行
asyncio.create_task(_startup())
