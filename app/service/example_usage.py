# Exemplo de uso do sistema de filas com fallback

from app.service.queue_manager import enqueue_webhook, get_queue_stats, start_worker, stop_worker
import time

# Exemplo de payload de webhook
def create_test_payload():
    return {
        "event": "messages.upsert",
        "instance": "botjuris-instance",
        "data": {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "test-message-123"
            },
            "message": {
                "conversation": "Olá, preciso de ajuda jurídica!"
            },
            "messageTimestamp": int(time.time())
        }
    }

def main():
    print("🚀 Iniciando sistema de filas com fallback")
    
    # Inicia o worker em background
    start_worker(in_background=True)
    print("✅ Worker iniciado")
    
    # Enfileira mensagens de teste
    for i in range(5):
        payload = create_test_payload()
        payload["data"]["message"]["conversation"] = f"Mensagem de teste {i+1}"
        
        try:
            enqueue_webhook(payload)
            print(f"📤 Mensagem {i+1} enfileirada com sucesso")
        except Exception as e:
            print(f"❌ Erro ao enfileirar mensagem {i+1}: {e}")
        
        time.sleep(0.5)
    
    # Verifica estatísticas
    print("\n📊 Estatísticas das filas:")
    stats = get_queue_stats()
    print(f"Usando fila interna: {stats['using_internal_queue']}")
    print(f"Redis conectado: {stats['redis_connected']}")
    
    if stats['internal_queue_stats']:
        internal_stats = stats['internal_queue_stats']
        print(f"Tamanho da fila interna: {internal_stats['queue_size']}")
        print(f"Tamanho da DLQ interna: {internal_stats['dlq_size']}")
    
    # Aguarda processamento
    print("\n⏳ Aguardando processamento...")
    time.sleep(10)
    
    # Verifica estatísticas finais
    final_stats = get_queue_stats()
    print("\n📊 Estatísticas finais:")
    print(f"Fila interna: {final_stats['internal_queue_stats']['queue_size']} itens")
    print(f"DLQ interna: {final_stats['internal_queue_stats']['dlq_size']} itens")
    
    # Para o worker
    stop_worker()
    print("\n🛑 Worker finalizado")

if __name__ == "__main__":
    main()