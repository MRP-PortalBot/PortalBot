import functools
import inspect
import asyncio
from core.logging_module import get_log
from core.common import bot_data_cache, cache_lock

_log = get_log(__name__)


def cache_updated(func):
    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            result = await func(self, *args, **kwargs)
            async with cache_lock:
                bot_data_cache[self.server_id] = self
                _log.debug(
                    f"[Async] Updated bot_data_cache for server {self.server_id}"
                )
            return result

        return async_wrapper
    else:

        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    coro = cache_lock.__aenter__()
                    loop.create_task(coro)
                    bot_data_cache[self.server_id] = self
                    loop.create_task(cache_lock.__aexit__(None, None, None))
                else:
                    bot_data_cache[self.server_id] = self
                _log.debug(f"[Sync] Updated bot_data_cache for server {self.server_id}")
            except Exception as e:
                _log.error(f"Failed to update cache for server {self.server_id}: {e}")
            return result

        return sync_wrapper
