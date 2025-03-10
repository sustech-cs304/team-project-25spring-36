from aiocache import Cache

from intellide.config import CACHE_URL

cache = Cache.from_url(CACHE_URL)
