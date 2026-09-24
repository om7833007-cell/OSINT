import asyncio
import random


class RateLimiter:
    """Per-key semaphore + exponential backoff retry wrapper.

    Every module call goes through here, keyed by module name, so no single
    data source gets hammered with unlimited concurrent requests.
    """

    def __init__(self, max_concurrent: int = 5):
        self._locks: dict[str, asyncio.Semaphore] = {}
        self._max_concurrent = max_concurrent

    def _get_lock(self, key: str) -> asyncio.Semaphore:
        if key not in self._locks:
            self._locks[key] = asyncio.Semaphore(self._max_concurrent)
        return self._locks[key]

    async def run(self, key: str, coro_fn, *args, retries: int = 3, **kwargs):
        lock = self._get_lock(key)
        async with lock:
            for attempt in range(retries):
                try:
                    return await coro_fn(*args, **kwargs)
                except Exception as exc:
                    if attempt == retries - 1:
                        return {"error": str(exc)}
                    backoff = (2 ** attempt) + random.random()
                    await asyncio.sleep(backoff)
