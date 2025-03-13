from intellide.cache import cache


async def startup():
    await cache.clear()
