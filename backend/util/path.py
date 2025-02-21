import posixpath
from pathvalidate import is_valid_filepath


def path_normalize(path: str) -> str:
    """
    验证并规范化文件路径

    参数:
    - path: 要验证和规范化的文件路径

    返回:
    - 规范化后的文件路径，如果路径无效则返回 None
    """
    # 验证文件路径
    if not is_valid_filepath(path, platform="linux"):
        return None
    # 规范化文件路径
    return posixpath.normpath(path)


def path_prefix(entry_path: str) -> str:
    """
    获取文件路径的父目录

    参数:
    - entry_path: 文件路径

    返回:
    - 父目录路径，如果父目录是根目录则返回空字符串
    """
    dirname = posixpath.dirname(entry_path)
    if dirname == "/":
        return ""
    else:
        return dirname
