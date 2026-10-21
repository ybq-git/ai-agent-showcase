"""Redis cache with an in-memory fallback for local development and tests."""

import json
import threading
import time
import uuid
from contextlib import contextmanager

from app.config import settings


class InMemoryCache:
    def __init__(self) -> None:
        self._data: dict[str, tuple[str, float | None]] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> str | None:
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if expires_at is not None and expires_at < time.time():
                self._data.pop(key, None)
                return None
            return value

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        with self._lock:
            self._data[key] = (value, time.time() + ex if ex else None)

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def incr(self, key: str, amount: int = 1) -> int:
        with self._lock:
            current = self.get(key)
            try:
                value = int(current or 0)
            except (TypeError, ValueError):
                value = 0
            value += amount
            self.set(key, str(value))
            return value


class Cache:
    def __init__(self, url: str | None = None) -> None:
        self._redis = None
        self._fallback = InMemoryCache()
        self._fallback_lock = threading.Lock()
        url = settings.redis_url if url is None else url
        if url:
            try:
                import redis

                client = redis.Redis.from_url(
                    url,
                    decode_responses=True,
                    socket_connect_timeout=0.5,
                    socket_timeout=0.5,
                )
                client.ping()
                self._redis = client
            except Exception:
                self._redis = None

    @property
    def backend(self) -> str:
        return "redis" if self._redis is not None else "memory"

    def get(self, key: str) -> str | None:
        if self._redis is not None:
            try:
                return self._redis.get(key)
            except Exception:
                pass
        return self._fallback.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        if self._redis is not None:
            try:
                self._redis.set(key, value, ex=ex)
                return
            except Exception:
                pass
        self._fallback.set(key, value, ex)

    def delete(self, key: str) -> None:
        if self._redis is not None:
            try:
                self._redis.delete(key)
                return
            except Exception:
                pass
        self._fallback.delete(key)

    def incr(self, key: str, amount: int = 1) -> int:
        if self._redis is not None:
            try:
                return int(self._redis.incrby(key, amount))
            except Exception:
                pass
        return self._fallback.incr(key, amount)

    def get_json(self, key: str) -> dict | list | None:
        raw = self.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def set_json(self, key: str, value: dict | list, ex: int | None = None) -> None:
        self.set(key, json.dumps(value, ensure_ascii=False, default=str), ex=ex)

    def mutex(self, key: str, timeout: int = 5):
        return self._mutex(key, timeout)

    @contextmanager
    def _mutex(self, key: str, timeout: int = 5):
        if self._redis is None:
            with self._fallback_lock:
                yield
            return

        token = uuid.uuid4().hex
        acquired = False
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                acquired = bool(self._redis.set(key, token, nx=True, ex=timeout))
            except Exception:
                acquired = False
            if acquired:
                break
            time.sleep(0.02)
        try:
            yield
        finally:
            if acquired:
                try:
                    if self._redis.get(key) == token:
                        self._redis.delete(key)
                except Exception:
                    pass

    def get_or_set_json(self, key: str, ttl: int, loader) -> dict | list:
        cached = self.get_json(key)
        if cached is not None:
            return cached
        with self._mutex(f"lock:{key}"):
            cached = self.get_json(key)
            if cached is not None:
                return cached
            value = loader()
            self.set_json(key, value, ex=ttl)
            return value

    def bump_version(self, name: str) -> int:
        return self.incr(f"{name}:version")

    def version(self, name: str) -> str:
        return self.get(f"{name}:version") or "0"


cache = Cache()
