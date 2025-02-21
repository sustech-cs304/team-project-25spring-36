def update_attrs(src: object, dst: object) -> None:
    """
    更新目标对象的属性

    参数:
    - src: 源对象
    - dst: 目标对象

    返回:
    - None
    """
    for key, val in vars(src).items():
        if val and hasattr(dst, key):
            setattr(dst, key, val)
