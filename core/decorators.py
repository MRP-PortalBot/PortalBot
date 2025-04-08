import functools
import inspect
import asyncio
from core.logging_module import get_log
from core.cache_state import bot_data_cache, cache_lock

_log = get_log(__name__)


def cache_updated(func):
    """
    Decorator to automatically update the bot_data_cache after a save or update method.
    Handles both async and sync functions.
    """

    if inspect.iscoroutinefunction(func):
        # Async version
        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            result = await func(self, *args, **kwargs)
            async with cache_lock:
                bot_data_cache[str(self.server_id)] = self
                _log.debug(
                    f"[Async] Updated bot_data_cache for server {self.server_id}"
                )
            return result

        return async_wrapper

    else:
        # Sync version
        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule cache update without blocking
                    loop.create_task(_async_cache_update(self))
                else:
                    # Safe for sync environments like Flask routes
                    bot_data_cache[str(self.server_id)] = self
                _log.debug(f"[Sync] Updated bot_data_cache for server {self.server_id}")
            except Exception as e:
                _log.error(f"Failed to update cache for server {self.server_id}: {e}")
            return result

        return sync_wrapper


async def _async_cache_update(instance):
    """
    Internal helper coroutine to perform async cache update for sync wrapper.
    """
    async with cache_lock:
        bot_data_cache[str(instance.server_id)] = instance
