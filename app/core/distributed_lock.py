# app/core/distributed_lock.py

import os
import time
import uuid
from contextlib import AbstractContextManager
from typing import Optional

import redis

from app.core.logger_config import get_logger


log = get_logger()


def get_redis_client() -> redis.Redis:
    """
    Retorna um cliente Redis síncrono.
    Ajuste o REDIS_URL no .env se necessário.
    """
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return redis.Redis.from_url(url, decode_responses=True)


class DistributedLock(AbstractContextManager):
    """
    Implementação simples de lock distribuído usando Redis.

    - Usa SET NX com TTL para adquirir o lock.
    - Usa um token único por lock para liberar com segurança.
    - Pode ser usado como context manager:

        with DistributedLock(redis_client, "lock:lead:5511999999999"):
            # código crítico

    """

    def __init__(
        self,
        name: str,
        ttl: int = 30,
        blocking_timeout: Optional[float] = 10.0,
    ) -> None:
        self.redis = get_redis_client()
        self.name = name
        self.ttl = ttl
        self.blocking_timeout = blocking_timeout
        self._token: Optional[str] = None
        self._acquired = False

    @property
    def acquired(self) -> bool:
        return self._acquired

    def acquire(self) -> bool:
        """
        Tenta adquirir o lock dentro do blocking_timeout.
        Retorna True se conseguiu, False se não.
        """
        token = str(uuid.uuid4())
        end_time = time.time() + (self.blocking_timeout or 0)

        while True:
            # Tenta adquirir o lock
            if self.redis.set(self.name, token, nx=True, ex=self.ttl):
                self._token = token
                self._acquired = True
                log.debug(f"🔒 Lock adquirido: {self.name}")
                return True

            if self.blocking_timeout is None:
                # Não bloqueante: tenta uma vez só
                return False

            if time.time() > end_time:
                log.warning(f"⏱ Timeout ao tentar adquirir lock: {self.name}")
                return False

            time.sleep(0.05)  # pequena espera antes de tentar de novo

    def release(self) -> None:
        """
        Libera o lock somente se o token ainda é o mesmo.
        Evita liberar lock adquirido por outro processo.
        """
        if not self._acquired or not self._token:
            return

        # Script Lua para garantir liberação atômica
        lua_script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        """

        try:
            self.redis.eval(lua_script, 1, self.name, self._token)
            log.debug(f"🔓 Lock liberado: {self.name}")
        except Exception as ex:
            log.error(f"❌ Erro ao liberar lock {self.name}: {ex}", exc_info=True)
        finally:
            self._acquired = False
            self._token = None

    # Context manager
    def __enter__(self) -> "DistributedLock":
        ok = self.acquire()
        if not ok:
            raise TimeoutError(f"Não foi possível adquirir o lock: {self.name}")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()

