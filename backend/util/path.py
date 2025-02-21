import posixpath
from pathvalidate import is_valid_filepath


def path_normalize(path: str) -> str:
    # 验证文件路径
    if not is_valid_filepath(entry_path, platform="linux"):
        return None
    # 规范化文件路径
    entry_path = posixpath.normpath(entry_path)


def path_prefix(entry_path: str) -> str:
    dirname = posixpath.dirname(entry_path)
    if dirname == "/":
        return ""
    else:
        return dirname
