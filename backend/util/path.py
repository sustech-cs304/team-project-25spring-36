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
    dirname = posixpath.dirname(path)
    if dirname == "/":
        return ""
    else:
        return dirname


def path_split_dir_file_name(
        path: str,
) -> Tuple[str, str]:
    """
    分割文件路径为目录和文件名

    参数:
    - path: 文件路径

    返回:
    - 目录和文件名的元组
    """
    idx = path.rfind("/")
    return (
        path[:idx],
        path[idx + 1:],
    )


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
    while path:
        yield path
        idx = path.rfind("/")
        if idx == -1:
            return
        path = path[:idx]
