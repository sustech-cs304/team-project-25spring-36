from typing import Dict, List


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
