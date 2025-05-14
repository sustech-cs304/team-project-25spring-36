import os

import pyperclip
from pathspec import PathSpec
from treelib import Tree


def load_gitignore_spec(
    root_path: str,
) -> PathSpec:
    """
    加载 .gitignore 文件内容
    """
    with open(os.path.join(root_path, ".gitignore"), "r") as fp:
        return PathSpec.from_lines("gitwildmatch", fp.readlines())


def is_ignored(root_path: str, target_path: str, spec: PathSpec) -> bool:
    """
    判断文件是否被 .gitignore 忽略
    """
    rel_path = os.path.relpath(target_path, root_path)
    return spec.match_file(rel_path)


def generate_tree(
    root_path: str,
    spec: PathSpec,
) -> Tree:
    """
    生成目录树
    """

    def add_nodes(_path: str, _parent: str, _spec: PathSpec):
        for item in os.listdir(_path):
            item_path = os.path.join(_path, item)
            # 如果该文件或目录被.gitignore忽略，则跳过
            if is_ignored(root_path, item_path, spec):
                continue
            if os.path.isdir(item_path):
                tree.create_node(item, item_path, parent=_parent)
                add_nodes(item_path, item_path, _spec)  # 递归
            else:
                tree.create_node(item, item_path, parent=_parent)

    tree = Tree()
    # 创建根节点
    tree.create_node(os.path.basename(root_path), root_path)
    # 从根路径开始递归添加节点
    add_nodes(root_path, root_path, spec)
    return tree


if __name__ == "__main__":
    ROOT_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

    result = str(generate_tree(ROOT_PATH, load_gitignore_spec(ROOT_PATH)))
    pyperclip.copy(result)
    print(result)
