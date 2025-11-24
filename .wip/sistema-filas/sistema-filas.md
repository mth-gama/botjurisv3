# Sistema de Filas - Documentação

## Visão Geral
O sistema de filas do BotJuris é responsável pelo processamento assíncrono de mensagens do WhatsApp, garantindo confiabilidade, escalabilidade e resiliência através de um sistema baseado em Redis com Circuit Breaker e Dead Letter Queue.

## Arquitetura do Sistema de Filas

### Componentes Principais
1. **Redis:** Armazenamento das filas e locks distribuídos
2. **Worker Thread:** Processa mensagens em background
3. **Circuit Breaker:** Protege contra falhas em cascata
4. **Distributed Lock:** Previne processamento duplicado
5. **Dead Letter Queue (DLQ):** Armazena mensagens que falharam após múltiplas tentativas

### Filas Utilizadas
- **queue:webhook:** Fila principal para processamento de webhooks
- **queue:webhook:dlq:** Dead Letter Queue para mensagens falhadas

## Fluxo de Processamento

### 1. Enfileiramento (`enqueue_webhook`)
```python
def enqueue_webhook(payload: Dict[str, Any]) -> None:
    wrapper = {
        "payload": payload,
        "retry": 0,
    }
    client.lpush(QUEUE_KEY, json.dumps(wrapper))
```

### 2. Consumo (`worker_loop`)
```python
def worker_loop() -> None:
    while not _stop_event.is_set():
        item = client.brpop(QUEUE_KEY, timeout=5)
        if item:
            _process_item(raw)
```

### 3. Processamento Individual (`_process_item`)
1. **Extração de dados:** Telefone do lead e dados do payload
2. **Lock distribuído:** Previne concorrência para o mesmo lead
3. **Circuit Breaker:** Protege contra falhas
4. **Timeout:** Limita tempo de execução (30 segundos)
5. **Processamento:** Chama `process_webhook_data`

## Circuit Breaker

### Estados
- **CLOSED:** Funcionamento normal
- **OPEN:** Falhas em excesso, chamadas bloqueadas
- **HALF_OPEN:** Período de teste após timeout

### Configurações
```python
failure_threshold = 5      # Falhas para abrir circuito
recovery_timeout = 30     # Segundos para tentar recuperação
half_open_successes = 1   # Sucessos para fechar circuito
```

### Comportamento
- Monitora falhas consecutivas
- Abre circuito após limite de falhas
- Tenta recuperação após timeout
- Fecha circuito após sucessos no estado HALF_OPEN

## Sistema de Retry com Backoff Exponencial

### Configurações
```python
MAX_RETRIES = 5              # Máximo de tentativas
MAX_BACKOFF_SECONDS = 30     # Limite do backoff
```

### Algoritmo
1. **Tentativa 1:** Sem delay
2. **Tentativa 2:** 1 segundo
3. **Tentativa 3:** 2 segundos
4. **Tentativa 4:** 4 segundos
5. **Tentativa 5:** 8 segundos
6. **Tentativa 6:** 16 segundos
7. **DLQ:** Após exceder MAX_RETRIES

### Exemplo de Backoff
```
Retry 1: 0s (imediatamente)
Retry 2: 1s
Retry 3: 2s  
Retry 4: 4s
Retry 5: 8s
Retry 6: 16s
DLQ: Após 5 tentativas
```

## Distributed Lock

### Implementação
- Baseado em Redis com TTL (Time To Live)
- Previne processamento duplicado do mesmo lead
- Timeout configurável (padrão: 60 segundos)

### Uso
```python
lock_name = f"lock:lead:{lead_phone}"
with DistributedLock(client, lock_name, ttl=60, blocking_timeout=10):
    # Processamento protegido
    process_webhook_data(payload)
```

## Dead Letter Queue (DLQ)

### Propósito
- Armazena mensagens que falharam após múltiplas tentativas
- Permite análise e reprocessamento manual
- Evita perda de dados importantes

### Estrutura
```json
{
  "payload": { ...payload original... },
  "retry": 6,  // Número de tentativas realizadas
  "error": "...mensagem de erro...",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Configurações do Worker

### Timeout de Processamento
```python
DEFAULT_TIMEOUT_SECONDS = 30
```

### Reconexão Redis
```python
REDIS_RECONNECT_DELAY = 5  # segundos
```

### Controle de Concorrência
- Worker único por aplicação (Singleton)
- Thread dedicada para processamento
- Graceful shutdown implementado

## Monitoramento e Observabilidade

### Métricas Coletadas
- Total de mensagens processadas
- Taxa de sucesso/falha
- Tempo médio de processamento
- Número de mensagens na DLQ
- Estado do Circuit Breaker

### Logs
```
📥 Payload enfileirado na queue de webhooks
🔁 Falha ao processar mensagem (tentativa 3/5)
☠ Mensagem enviada para DLQ após 5 tentativas
🟢 CircuitBreaker retornou para CLOSED
🔴 CircuitBreaker em estado OPEN
```

## Graceful Shutdown

### Implementação
```python
def stop_worker() -> None:
    _stop_event.set()  # Sinaliza parada
    _worker_thread.join(timeout=10)  # Aguarda finalização
```

### Comportamento
1. Sinaliza parada via `_stop_event`
2. Aguarda processamento atual finalizar (timeout: 10s)
3. Não aceita novas mensagens
4. Mantém integridade dos dados

## Segurança e Confiabilidade

### Proteções Implementadas
- **Timeout:** Previne travamentos infinitos
- **Circuit Breaker:** Protege contra falhas em cascata
- **Distributed Lock:** Evita race conditions
- **DLQ:** Garante que nenhuma mensagem seja perdida
- **Validação:** Sanitização de dados antes do processamento

### Boas Práticas
- Processamento idempotente quando possível
- Logs estruturados para debugging
- Métricas para monitoramento
- Tratamento robusto de erros
- Recuperação automática de falhas