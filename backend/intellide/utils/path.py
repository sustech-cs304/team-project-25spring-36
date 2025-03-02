import os.path
import posixpath
from typing import Tuple, Iterator

from pathvalidate import is_valid_filepath


def path_normalize(
        path: str,
) -> str:
    """
    验证并规范化文件路径

    参数:
    - path: 要验证和规范化的文件路径

    返回:
    - 规范化后的文件路径，如果路径无效则返回 None
    """
    # 验证文件路径
    if not is_valid_filepath(path, platform="linux"):
        raise ValueError("Invalid path")
    # 规范化文件路径
    return posixpath.normpath(path)


def path_prefix(
        path: str,
) -> str:
    """
    获取文件路径的父目录

    参数:
    - path: 文件路径

    返回:
    - 父目录路径，如果父目录是根目录则返回空字符串
    """
    path = path_normalize(path)
    dirname = posixpath.dirname(path)
    if dirname == "/":
        return ""
    else:
        return dirname


def path_dir_base_name(
        path: str,
) -> Tuple[str, str]:
    """
    分割文件路径为目录和文件名

    参数:
    - path: 文件路径

    返回:
    - 目录和文件名的元组
    """
    path = path_normalize(path)
    idx = path.rfind("/")
    return (
        path[:idx],
        path[idx + 1:],
    )

def path_base_name(
        path:str,
) -> str:
    """
    获取文件路径的文件名

    参数:
    - path: 文件路径

    返回:
    - 文件名
    """
    path = path_normalize(path)
    return posixpath.basename(path)


def path_iterate_parents(
        path: str,
) -> Iterator[str]:
    """
    迭代文件路径的所有父目录

    参数:
    - path: 文件路径

    返回:
    - 父目录路径的迭代器
    """
    path = path_normalize(path)
    while path:
        yield path
        idx = path.rfind("/")
        if idx == -1:
            return
        path = path[:idx]


def path_parts(
        path: str,
        index: int,
) -> str:
    """
    提取路径中的第 index 个目

    参数:
    - path: 文件路径
    - index: 目录索引（从 0 开始）

    返回:
    - 目录名

    异常:
    - RuntimeError: 如果索引超出范围
    """
    path = path_normalize(path)
    parts = [p for p in path.split("/") if p]
    if not (0 <= index < len(parts)):
        raise RuntimeError(f"Index {index} is out of range for path '{path}'")
    return parts[index]

def path_parts_first_n(
        path:str,
        n:int,
) -> str:
    """
    提取路径中的前 n 个目录

    参数:
    - path: 文件路径
    - n: 目录数量

    返回:
    - 目录名
    """
    path = path_normalize(path)
    parts = [p for p in path.split("/") if p]
    if not (0 < n < len(parts)):
        raise RuntimeError(f"Index {n} is out of range for path '{path}'")
    return "/" + "/".join(parts[:n])