from typing import Dict, List, TypeVar, Generic

T = TypeVar('T')


# 统一断言 HTTP 响应码
def assert_code(
        response: Dict,
        expected_code: int,
):
    assert response["code"] == expected_code


def assert_dict(
        src: Dict,
        dst: Dict,
        keys: List[str],
):
    for key in keys:
        assert src[key] == dst[key]


class Ref(Generic[T]):
    def __init__(self, val: T = None):
        self.val = val

    def __str__(self):
        return self.val

    def get(self):
        return self.val

    def set(self, val: T):
        self.val = val
