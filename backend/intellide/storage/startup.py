import aiofiles.os

from intellide.config import STORAGE_PATH


async def startup():
    """
    异步创建存储目录（如果不存在）
    """
    await aiofiles.os.makedirs(STORAGE_PATH, exist_ok=True)
