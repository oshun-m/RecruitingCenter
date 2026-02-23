# decorators/redis.py
import inspect
from functools import wraps
from typing import Callable, Union

from flask import current_app
from cache.redis_cache import RedisCache


def fetch_from_cache(
    cache_name: str,
    cache_config: Union[dict, Callable[[], dict]],
    ttl: int | None = None,
):
    def decorator(func):
        sig = inspect.signature(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            app = current_app
            cache: RedisCache = app.extensions.get("redis_cache")
            if cache is None:
                cfg = cache_config() if callable(cache_config) else cache_config
                cache = app.extensions["redis_cache"] = RedisCache(cfg)

            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            try:
                key = cache_name.format(**bound.arguments)
            except KeyError:
                key = cache_name

            cached = cache.get_value(key)
            if cached is not None:
                return cached

            result = func(*args, **kwargs)
            cache.set_value(key, result, ttl)
            return result

        return wrapper

    return decorator
