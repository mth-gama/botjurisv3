# app/service/test_fallback.py

"""
Script de teste para verificar o funcionamento do sistema de fallback.
Testa cenários com Redis disponível e indisponível.
"""

import json
import time
import threading
from queue_manager import enqueue_webhook, get_queue_stats, start_worker, stop_worker

def test_message():
    """Retorna uma mensagem de teste."""
    return {
        "event": "messages.upsert",
        "instance": "test-instance",
        "data": {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "test-message-id"
            },
            "message": {
                "conversation": "Mensagem de teste para fallback"
            },
            "messageTimestamp": int(time.time())
        }
    }

def test_with_redis_available():
    """Testa com Redis disponível."""
    print("\n=== Teste 1: Redis Disponível ===")
    
    # Enfileira mensagem
    message = test_message()
    enqueue_webhook(message)
    print("✅ Mensagem enfileirada com sucesso")
    
    # Verifica estatísticas
    stats = get_queue_stats()
    print(f"📊 Estatísticas: {json.dumps(stats, indent=2)}")
    
    time.sleep(2)

def test_with_redis_unavailable():
    """Testa com Redis indisponível (simulado)."""
    print("\n=== Teste 2: Redis Indisponível (Simulado) ===")
    
    # Força uso da fila interna
    from queue_manager import _use_internal_queue
    import queue_manager
    
    # Simula Redis indisponível
    original_use_internal = queue_manager._use_internal_queue
    queue_manager._use_internal_queue = True
    
    try:
        # Enfileira mensagem
        message = test_message()
        enqueue_webhook(message)
        print("✅ Mensagem enfileirada na fila interna com sucesso")
        
        # Verifica estatísticas
        stats = get_queue_stats()
        print(f"📊 Estatísticas: {json.dumps(stats, indent=2)}")
        
        time.sleep(2)
        
    finally:
        # Restaura estado original
        queue_manager._use_internal_queue = original_use_internal

def test_worker_processing():
    """Testa o processamento pelo worker."""
    print("\n=== Teste 3: Processamento pelo Worker ===")
    
    # Inicia worker
    start_worker(in_background=True)
    print("👷 Worker iniciado")
    
    # Enfileira algumas mensagens
    for i in range(3):
        message = test_message()
        message["data"]["message"]["conversation"] = f"Mensagem de teste {i+1}"
        enqueue_webhook(message)
        print(f"📤 Mensagem {i+1} enfileirada")
    
    # Aguarda processamento
    print("⏳ Aguardando processamento...")
    time.sleep(10)
    
    # Verifica estatísticas finais
    stats = get_queue_stats()
    print(f"📊 Estatísticas finais: {json.dumps(stats, indent=2)}")
    
    # Para worker
    stop_worker()
    print("🛑 Worker finalizado")

def main():
    """Executa todos os testes."""
    print("🧪 Iniciando testes do sistema de fallback")
    
    try:
        test_with_redis_available()
        test_with_redis_unavailable()
        test_worker_processing()
        
        print("\n✅ Todos os testes concluídos com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()