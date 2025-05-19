import asyncio

# Global bot data cache
bot_data_cache = {}

# Lock to protect the cache
cache_lock = asyncio.Lock()
