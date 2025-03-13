import json
from typing import Dict, Tuple, Any, Hashable

import redis

from intellide.config import CACHE_URL

_cache = redis.from_url(CACHE_URL)


def cache_set(
        key: str,
        value: Any,
        ttl: int,
):
    _cache.set(key, json.dumps(value), ex=ttl)


def cache_get(
        key: str,
) -> Any:
    value = _cache.get(key)
    if value:
        return json.loads(value)
    else:
        return None


# 统一断言 HTTP 响应码
def assert_code(
        response: Dict,
        expected_code: int,
):
    assert response["code"] == expected_code


def assert_dict(
        src: Dict,
        dst: Dict,
        keys: Tuple[Hashable, ...],
):
    for key in keys:
        assert src[key] == dst[key]
