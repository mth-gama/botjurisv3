# app/service/queue_manager.py

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Dict, Optional, Callable

import redis

from app.core.logger_config import get_logger
from app.core.distributed_lock import DistributedLock, get_redis_client
from app.service.process import process_webhook_data  # garante que esse nome está correto


log = get_logger()

# ======================================================
# 🔧 Configurações básicas
# ======================================================

QUEUE_KEY = "queue:webhook"
QUEUE_DLQ_KEY = "queue:webhook:dlq"   # Dead Letter Queue

DEFAULT_TIMEOUT_SECONDS = 30
REDIS_RECONNECT_DELAY = 5  # segundos

MAX_RETRIES = 5
MAX_BACKOFF_SECONDS = 30  # limite do backoff exponencial

_redis_client: Optional[redis.Redis] = None
_stop_event = threading.Event()
_worker_thread: Optional[threading.Thread] = None


def get_redis() -> redis.Redis:
    """Retorna client Redis, com tentativa de reconexão simples."""
    global _redis_client
    if _redis_client is None:
        _redis_client = get_redis_client()
    return _redis_client


# ======================================================
# 🧠 Circuit Breaker
# ======================================================

class CircuitBreaker:
    """
    Implementação simples de Circuit Breaker.

    Estados:
      - CLOSED: tudo normal
      - OPEN: falhas em excesso, chamadas são bloqueadas
      - HALF_OPEN: período de teste depois do timeout
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        half_open_successes: int = 1,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_successes = half_open_successes

        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self._half_open_success_count = 0

    def _can_attempt(self) -> bool:
        if self.state == "CLOSED":
            return True

        if self.state == "OPEN":
            assert self.last_failure_time is not None
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                # Tenta meia abertura
                self.state = "HALF_OPEN"
                log.warning("🟡 CircuitBreaker em HALF_OPEN (teste de recuperação)")
                return True
            else:
                return False

        if self.state == "HALF_OPEN":
            # Permite algumas tentativas limitadas
            return True

        return False

    def _on_success(self) -> None:
        if self.state in ("HALF_OPEN", "OPEN"):
            self._half_open_success_count += 1
            if self._half_open_success_count >= self.half_open_successes:
                log.info("🟢 CircuitBreaker retornou para CLOSED")
                self.state = "CLOSED"
                self.failure_count = 0
                self.last_failure_time = None
                self._half_open_success_count = 0
        else:
            self.failure_count = 0

    def _on_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        log.warning(f"⚠️ CircuitBreaker falha #{self.failure_count} (estado={self.state})")

        if self.failure_count >= self.failure_threshold and self.state != "OPEN":
            self.state = "OPEN"
            log.error("🔴 CircuitBreaker em estado OPEN — novas chamadas serão bloqueadas.")

    def call(self, func: Callable, *args, **kwargs):
        """
        Executa `func` respeitando o estado do circuit breaker.
        Lança RuntimeError se o circuito estiver OPEN.
        """
        if not self._can_attempt():
            raise RuntimeError("CircuitBreaker OPEN — chamada bloqueada")

        try:
            result = func(*args, **kwargs)
        except Exception:
            self._on_failure()
            raise
        else:
            self._on_success()
            return result


circuit_breaker = CircuitBreaker()


# ======================================================
# ⏱ Timeout helper
# ======================================================

def run_with_timeout(
    func: Callable,
    timeout: int,
    *args,
    **kwargs,
):
    """Executa função em thread separada com timeout."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except FuturesTimeoutError:
            log.error(f"⏱ Timeout ao executar função {func.__name__}")
            raise TimeoutError(f"Timeout de {timeout}s excedido em {func.__name__}")


# ======================================================
# 🔁 Funções de fila
# ======================================================

def enqueue_webhook(payload: Dict[str, Any]) -> None:
    """
    Enfileira um payload de webhook no Redis para processamento assíncrono.

    Wrap de mensagem:
    {
        "payload": { ...payload original do Evolution... },
        "retry": 0
    }
    """
    client = get_redis()
    wrapper = {
        "payload": payload,
        "retry": 0,
    }
    raw = json.dumps(wrapper, ensure_ascii=False)
    client.lpush(QUEUE_KEY, raw)
    log.debug("📥 Payload enfileirado na queue de webhooks")
    


def _extract_lead_phone(payload: Dict[str, Any]) -> Optional[str]:
    """
    Tenta extrair o telefone do lead do payload bruto.
    Ajuste esse caminho se a estrutura mudar.
    """
    try:
        remote_jid = payload["data"]["key"]["remoteJid"]
        return remote_jid.split("@")[0]
    except Exception:
        return None


def _handle_failure(wrapper: Dict[str, Any], error: Exception) -> None:
    """
    Gerencia falha no processamento de uma mensagem:
      - Incrementa contador de retry
      - Aplica backoff exponencial
      - Reenfileira ou envia para DLQ
    """
    client = get_redis()
    retry = wrapper.get("retry", 0)
    retry += 1
    wrapper["retry"] = retry

    payload = wrapper.get("payload", {})
    lead_phone = _extract_lead_phone(payload)

    if retry > MAX_RETRIES:
        # Envia para DLQ
        client.lpush(QUEUE_DLQ_KEY, json.dumps(wrapper, ensure_ascii=False))
        log.error(
            f"☠ Mensagem enviada para DLQ após {retry - 1} tentativas. "
            f"lead_phone={lead_phone}, erro={error}"
        )
        return

    # Calcula backoff exponencial (1, 2, 4, 8, 16, ...), limitado
    backoff = min(2 ** (retry - 1), MAX_BACKOFF_SECONDS)
    log.warning(
        f"🔁 Falha ao processar mensagem (tentativa {retry}/{MAX_RETRIES}). "
        f"Novo retry em ~{backoff}s. lead_phone={lead_phone}, erro={error}"
    )

    # Espera antes de reenfileirar (simples, mas efetivo)
    time.sleep(backoff)

    client.lpush(QUEUE_KEY, json.dumps(wrapper, ensure_ascii=False))


def _process_item(raw: str) -> None:
    """
    Processa um item individual da fila:
      - Decodifica wrapper (payload + retry)
      - Extrai telefone
      - Adquire lock distribuído por telefone
      - Chama process_webhook_data com circuit breaker + timeout
      - Em caso de erro, delega para _handle_failure (retry/DLQ)
    """
    wrapper = json.loads(raw)
    payload = wrapper.get("payload", {})

    lead_phone = _extract_lead_phone(payload)
    lock_name = f"lock:lead:{lead_phone}" if lead_phone else None

    def _do_process():
        # usa a função que você já tem em app.service.process
        process_webhook_data(payload)

    try:
        if lock_name:
            # Lock distribuído por telefone
            client = get_redis()
            with DistributedLock(client, lock_name, ttl=60, blocking_timeout=10):
                circuit_breaker.call(run_with_timeout, _do_process, DEFAULT_TIMEOUT_SECONDS)
        else:
            # Sem telefone — processa mesmo assim, mas loga
            log.warning("📵 Não foi possível extrair lead_phone para lock distribuído.")
            circuit_breaker.call(run_with_timeout, _do_process, DEFAULT_TIMEOUT_SECONDS)

    except Exception as ex:
        # Falha no processamento da função (timeout, erro da IA, erro de regra, etc.)
        _handle_failure(wrapper, ex)


def worker_loop() -> None:
    """
    Loop principal do worker:
      - Consome itens da fila Redis (BRPOP)
      - Processa com segurança
      - Respeita graceful shutdown via _stop_event
    """
    log.info("🚀 Worker de queue iniciado")

    while not _stop_event.is_set():
        try:
            client = get_redis()
            item = client.brpop(QUEUE_KEY, timeout=5)  # (queue, value)

            if item is None:
                # timeout do BRPOP — volta pro loop, checa se deve encerrar
                continue

            _, raw = item
            try:
                _process_item(raw)
            except Exception as ex:
                # Em princípio, qualquer erro tratado dentro de _process_item
                # não deveria chegar aqui, mas mantemos como fallback.
                log.error(f"❌ Erro inesperado ao processar item da fila: {ex}", exc_info=True)

        except (redis.ConnectionError, redis.TimeoutError) as ex:
            log.error(f"🔌 Erro de conexão com Redis: {ex}")
            time.sleep(REDIS_RECONNECT_DELAY)
        except Exception as ex:
            log.error(f"❌ Erro inesperado no worker_loop: {ex}", exc_info=True)

    log.info("🛑 Worker de queue finalizado (graceful shutdown concluído)")


# ======================================================
# 📴 Controle de start/stop (graceful shutdown)
# ======================================================

def start_worker(in_background: bool = True) -> None:
    """
    Inicia o worker que consome a fila de webhooks.
    Se in_background=True, roda em thread separada.
    """
    global _worker_thread

    if _worker_thread and _worker_thread.is_alive():
        log.warning("⚠️ Worker já está em execução.")
        return

    _stop_event.clear()

    if in_background:
        _worker_thread = threading.Thread(target=worker_loop, daemon=True)
        _worker_thread.start()
        log.info("👷 Worker iniciado em thread de background.")
    else:
        # Útil para testes
        worker_loop()


def stop_worker() -> None:
    """
    Solicita parada graciosa do worker e aguarda a thread finalizar.
    """
    global _worker_thread

    log.info("🛑 Solicitação de graceful shutdown do worker recebida.")
    _stop_event.set()

    if _worker_thread:
        _worker_thread.join(timeout=10)

    log.info("✅ Worker finalizado.")
