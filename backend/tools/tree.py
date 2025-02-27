import os

import pyperclip
from pathspec import PathSpec
from treelib import Tree


def load_gitignore_spec(
        gitignore_path: str,
) -> PathSpec:
    """
    加载 .gitignore 文件内容
    """
    with open(gitignore_path, "r") as fp:
        return PathSpec.from_lines('gitwildmatch', fp.readlines())


def is_ignored(
        gitignore_path: str,
        target_path: str,
        spec: PathSpec
) -> bool:
    """
    判断文件是否被 .gitignore 忽略
    """
    rel_path = os.path.relpath(target_path, os.path.dirname(gitignore_path))
    # rel_path = os.path.join('.',rel_path)
    print(gitignore_path, target_path, rel_path, spec.match_file(rel_path))
    return spec.match_file(rel_path)


def generate_tree(
        gitignore_path: str,
        root_path: str,
        spec: PathSpec,
) -> Tree:
    tree = Tree()
    # 创建根节点
    tree.create_node(os.path.basename(root_path), root_path)

    def add_nodes(
            path: str,
            parent: str,
    ):
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            # 如果该文件或目录被.gitignore忽略，则跳过
            if is_ignored(gitignore_path, item_path, spec):
                continue
            if os.path.isdir(item_path):
                tree.create_node(item, item_path, parent=parent)
                add_nodes(item_path, item_path)  # 递归
            else:
                tree.create_node(item, item_path, parent=parent)

    # 从根路径开始递归添加节点
    add_nodes(root_path, root_path)
    return tree


if __name__ == "__main__":
    GITIGNORE_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".gitignore"))
    ROOT_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

    result = str(generate_tree(GITIGNORE_PATH, ROOT_PATH, load_gitignore_spec(GITIGNORE_PATH)))
    pyperclip.copy(result)
    print(result)
