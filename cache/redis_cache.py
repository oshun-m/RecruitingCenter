# cache/redis_cache.py
from __future__ import annotations

import json
from typing import Any, Dict

from redis import Redis
from redis.exceptions import RedisError, ConnectionError


class RedisCache:
    def __init__(self, cfg: Dict[str, Any]):
        self.ttl_minutes = cfg.get("ttl_minutes", 15)
        self._cfg = {k: v for k, v in cfg.items() if k != "ttl_minutes"}
        self._conn: Redis | None = None

    @property
    def conn(self) -> Redis | None:
        if self._conn is None:
            try:
                self._conn = Redis(**self._cfg)
                self._conn.ping()
            except (RedisError, ConnectionError) as e:
                print(f"[RedisCache] connection error: {e}")
                self._conn = None
        return self._conn

    # --------- базовые операции ---------

    def get_value(self, name: str):
        """Получить значение по ключу (JSON -> Python)"""
        if self.conn is None:
            return None
        try:
            raw = self.conn.get(name)
            if raw is None:
                return None
            return json.loads(raw)
        except (RedisError, ConnectionError, json.JSONDecodeError) as e:
            print(f"[RedisCache] fallback(get): {e}")
            return None

    def set_value(self, name: str, value, ttl: int | None = None):
        if self.conn is None:
            return
        try:
            raw = json.dumps(value, ensure_ascii=False)
            ex_seconds = ttl if ttl is not None else self.ttl_minutes * 60
            self.conn.set(name, raw, ex=ex_seconds)
        except (RedisError, ConnectionError) as e:
            print(f"[RedisCache] fallback(set): {e}")
            return
    def delete(self, name: str):
        """Удалить ключ"""
        if self.conn is None:
            return
        try:
            self.conn.delete(name)
        except (RedisError, ConnectionError) as e:
            print(f"[RedisCache] fallback(delete): {e}")
            return
