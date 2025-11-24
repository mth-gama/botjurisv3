# app/service/internal_queue.py

import json
import threading
import time
import os
from typing import Any, Dict, List, Optional
from collections import deque
from datetime import datetime

from app.core.logger_config import get_logger

log = get_logger()

class InternalQueue:
    """
    Fila interna em memória com persistência em arquivo.
    Usada como fallback quando Redis está indisponível.
    """
    
    def __init__(self, queue_name: str = "internal_queue", max_size: int = 1000):
        self.queue_name = queue_name
        self.max_size = max_size
        self.queue: deque = deque()
        self.dlq: deque = deque()
        self.lock = threading.Lock()
        self.persistence_file = f"data/{queue_name}.json"
        self.dlq_file = f"data/{queue_name}_dlq.json"
        self._ensure_data_dir()
        self._load_from_disk()
    
    def _ensure_data_dir(self):
        """Garante que o diretório data existe."""
        os.makedirs("data", exist_ok=True)
    
    def _load_from_disk(self):
        """Carrega fila do disco se existir."""
        try:
            if os.path.exists(self.persistence_file):
                with open(self.persistence_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.queue = deque(data)
                    log.info(f"📂 Fila interna carregada com {len(self.queue)} itens")
            
            if os.path.exists(self.dlq_file):
                with open(self.dlq_file, 'r', encoding='utf-8') as f:
                    dlq_data = json.load(f)
                    self.dlq = deque(dlq_data)
                    log.info(f"📂 DLQ interna carregada com {len(self.dlq)} itens")
        except Exception as e:
            log.error(f"❌ Erro ao carregar fila do disco: {e}")
    
    def _save_to_disk(self):
        """Persiste fila em disco."""
        try:
            with self.lock:
                with open(self.persistence_file, 'w', encoding='utf-8') as f:
                    json.dump(list(self.queue), f, ensure_ascii=False, indent=2)
                
                with open(self.dlq_file, 'w', encoding='utf-8') as f:
                    json.dump(list(self.dlq), f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.error(f"❌ Erro ao salvar fila em disco: {e}")
    
    def lpush(self, item: Dict[str, Any]) -> bool:
        """
        Adiciona item à esquerda da fila (como Redis LPUSH).
        """
        try:
            with self.lock:
                if len(self.queue) >= self.max_size:
                    log.warning(f"⚠️ Fila interna atingiu limite máximo ({self.max_size})")
                    return False
                
                self.queue.appendleft(item)
                self._save_to_disk()
                log.debug(f"📥 Item adicionado à fila interna (tamanho: {len(self.queue)})")
                return True
        except Exception as e:
            log.error(f"❌ Erro ao adicionar item à fila: {e}")
            return False
    
    def brpop(self, timeout: int = 5) -> Optional[tuple]:
        """
        Remove item da direita da fila (como Redis BRPOP).
        Retorna tupla (queue_name, item) ou None se timeout.
        """
        start_time = time.time()
        
        while True:
            try:
                with self.lock:
                    if self.queue:
                        item = self.queue.pop()
                        self._save_to_disk()
                        log.debug(f"📤 Item removido da fila interna (tamanho: {len(self.queue)})")
                        return (self.queue_name, json.dumps(item))
                
                # Verifica timeout
                if time.time() - start_time >= timeout:
                    return None
                
                # Pequena pausa para não consumir CPU
                time.sleep(0.1)
                
            except Exception as e:
                log.error(f"❌ Erro ao remover item da fila: {e}")
                return None
        
        return None
    
    def add_to_dlq(self, item: Dict[str, Any], error: str) -> bool:
        """
        Adiciona item à Dead Letter Queue interna.
        """
        try:
            with self.lock:
                item["error"] = error
                item["timestamp"] = datetime.now().isoformat()
                self.dlq.appendleft(item)
                self._save_to_disk()
                log.debug(f"☠️ Item adicionado à DLQ interna (tamanho: {len(self.dlq)})")
                return True
        except Exception as e:
            log.error(f"❌ Erro ao adicionar item à DLQ: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas da fila interna.
        """
        with self.lock:
            return {
                "queue_size": len(self.queue),
                "dlq_size": len(self.dlq),
                "max_size": self.max_size,
                "persistence_file": self.persistence_file,
                "dlq_file": self.dlq_file
            }
    
    def clear(self):
        """
        Limpa a fila e DLQ internas.
        """
        with self.lock:
            self.queue.clear()
            self.dlq.clear()
            self._save_to_disk()
            log.info("🗑️ Fila interna e DLQ limpas")


class InternalQueueManager:
    """
    Gerenciador de múltiplas filas internas.
    """
    
    def __init__(self):
        self.queues: Dict[str, InternalQueue] = {}
        self.lock = threading.Lock()
        self._stop_event = threading.Event()
    
    def get_queue(self, queue_name: str) -> InternalQueue:
        """
        Obtém ou cria uma fila interna.
        """
        with self.lock:
            if queue_name not in self.queues:
                self.queues[queue_name] = InternalQueue(queue_name)
            return self.queues[queue_name]
    
    def stop_all(self):
        """
        Para todas as filas internas.
        """
        self._stop_event.set()
        log.info("🛑 Todas as filas internas foram sinalizadas para parar")


# Singleton global
_internal_queue_manager = InternalQueueManager()

def get_internal_queue(queue_name: str = "queue:webhook") -> InternalQueue:
    """
    Obtém uma fila interna específica.
    """
    return _internal_queue_manager.get_queue(queue_name)