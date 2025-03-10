from intellide.cache.cache import cache


async def startup():
    await cache.clear()
