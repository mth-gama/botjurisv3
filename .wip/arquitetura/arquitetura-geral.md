# Arquitetura Geral - Documentação

## Visão Geral
O BotJuris é uma aplicação FastAPI que implementa um sistema de atendimento automatizado via WhatsApp, utilizando IA para responder mensagens de forma contextualizada e inteligente.

## Arquitetura em Camadas

### 1. Camada de Apresentação (API Layer)
**Diretório:** `app/routers/`
- **webhook.py:** Endpoint principal para receber mensagens
- **health.py:** Health check e métricas do sistema

**Responsabilidades:**
- Receber requisições HTTP
- Validação de entrada (Pydantic)
- Serialização de respostas
- Tratamento de erros HTTP

### 2. Camada de Serviços (Service Layer)
**Diretório:** `app/service/`
- **process.py:** Processamento principal de mensagens
- **llm_response.py:** Integração com LLM
- **queue_manager.py:** Gerenciamento de filas
- **evolution_api.py:** Integração com Evolution API
- **send_message.py:** Envio de mensagens
- **crypto.py:** Criptografia de dados sensíveis
- **sanitize.py:** Sanitização de dados

**Responsabilidades:**
- Lógica de negócio principal
- Orquestração de processos
- Integração com serviços externos
- Gerenciamento de estado

### 3. Camada de Dados (Data Layer)
**Diretório:** `app/database/`
- **models.py:** Modelos SQLAlchemy
- **repositories/:** Repositórios de dados
- **manipulations/:** Operações de negócio
- **connection.py:** Gerenciamento de conexões

**Responsabilidades:**
- Persistência de dados
- Queries otimizadas
- Transações de banco de dados
- Cache de dados

### 4. Camada de Infraestrutura (Infrastructure Layer)
**Diretório:** `app/core/`
- **config.py:** Configurações da aplicação
- **cache.py:** Configuração de cache Redis
- **logger_config.py:** Configuração de logs
- **queue_config.py:** Configuração de filas

**Responsabilidades:**
- Configuração de serviços externos
- Gerenciamento de dependências
- Configurações de ambiente
- Inicialização de recursos

## Fluxo de Dados

### 1. Fluxo de Mensagem Recebida
```
WhatsApp User → Evolution API → Webhook Endpoint → Queue Manager → Worker → Process Service → LLM Service → Evolution API → WhatsApp User
```

### 2. Fluxo Detalhado
1. **Recebimento:** Mensagem chega via webhook do Evolution
2. **Validação:** Payload validado com Pydantic schemas
3. **Enfileiramento:** Mensagem armazenada no Redis
4. **Processamento:** Worker consome mensagem da fila
5. **Identificação:** Busca IA pelo número de telefone
6. **Contexto:** Recupera histórico do lead
7. **IA:** Gera resposta contextualizada
8. **Envio:** Envia resposta via Evolution API
9. **Atualização:** Atualiza histórico do lead

## Componentes Principais

### 1. Sistema de Filas (Queue Manager)
**Arquitetura:** Redis + Circuit Breaker + Dead Letter Queue
**Propósito:** Processamento assíncrono e confiável
**Características:**
- Retry automático com backoff exponencial
- Circuit breaker para proteção contra falhas
- Dead letter queue para mensagens problemáticas
- Distributed lock para prevenir duplicação

### 2. Sistema de Cache
**Tecnologia:** Redis
**Propósito:** Performance e redução de custos
**Estratégias:**
- Cache de respostas da IA
- Cache de informações de leads
- TTL configurável por tipo de dado

### 3. Sistema de Logs
**Tecnologia:** Python logging + JSON
**Propósito:** Observabilidade e debugging
**Características:**
- Logs estruturados em JSON
- Níveis configuráveis (DEBUG, INFO, WARNING, ERROR)
- Rotação automática de arquivos
- Integração com sistemas de monitoramento

## Padrões de Design

### 1. Repository Pattern
```python
class IARepository:
    def get_by_phone(self, phone: str) -> Optional[IA]:
        # Implementação
        
    def create(self, ia_data: dict) -> IA:
        # Implementação
```

### 2. Service Layer Pattern
```python
class ProcessService:
    def process_webhook_data(self, data: dict) -> None:
        # Orquestração do processamento
        
class LLMService:
    def generate_response(self, message: str, history: list) -> str:
        # Integração com LLM
```

### 3. Dependency Injection
```python
def get_settings() -> Settings:
    # Singleton pattern para configurações
    
def get_redis_client() -> Redis:
    # Gerenciamento de conexões Redis
```

### 4. Circuit Breaker Pattern
```python
class CircuitBreaker:
    def call(self, func: Callable, *args, **kwargs):
        # Implementação de circuit breaker
```

## Segurança

### 1. Autenticação e Autorização
- **Webhook Secret:** Validação de assinatura de webhooks
- **API Keys:** Autenticação em serviços externos
- **Rate Limiting:** Previne abuso do sistema

### 2. Criptografia
- **Dados em Repouso:** Credenciais criptografadas no banco
- **Dados em Trânsito:** HTTPS/TLS para todas as comunicações
- **Algoritmo:** Fernet (AES 128-bit CBC)

### 3. Validação e Sanitização
- **Input Validation:** Pydantic schemas para validação
- **Data Sanitization:** Remoção de dados sensíveis dos logs
- **SQL Injection:** Proteção via ORM e prepared statements

## Escalabilidade

### 1. Horizontal Scaling
- **Stateless Design:** Aplicação sem estado (stateless)
- **Shared Cache:** Redis compartilhado entre instâncias
- **Database Connection Pooling:** Pool de conexões otimizado

### 2. Vertical Scaling
- **Async Processing:** Processamento assíncrono de mensagens
- **Connection Pooling:** Reutilização de conexões
- **Resource Management:** Gerenciamento eficiente de recursos

### 3. Load Balancing
- **Health Checks:** Endpoints para verificação de saúde
- **Graceful Shutdown:** Finalização ordenada de processos
- **Circuit Breaker:** Proteção contra sobrecarga

## Monitoramento e Observabilidade

### 1. Métricas
- **Business Metrics:** Mensagens processadas, taxa de sucesso
- **Technical Metrics:** Tempo de resposta, uso de recursos
- **Error Metrics:** Taxa de erro, tipos de erro

### 2. Logs
- **Structured Logging:** Logs em formato JSON
- **Log Levels:** DEBUG, INFO, WARNING, ERROR
- **Log Aggregation:** Centralização de logs

### 3. Health Checks
- **Application Health:** Status da aplicação
- **Dependency Health:** Status de dependências externas
- **Custom Health Checks:** Verificações específicas

## Configuração e Deployment

### 1. Environment Configuration
```python
class Settings(BaseSettings):
    ENVIRONMENT: Literal["development", "staging", "production"]
    DEBUG: bool
    # Outras configurações...
```

### 2. Containerização
- **Docker:** Containerização da aplicação
- **Docker Compose:** Orquestração local
- **Health Checks:** Verificações de saúde nos containers

### 3. Deployment Patterns
- **Blue-Green Deployment:** Deployment com zero downtime
- **Rolling Updates:** Atualizações graduais
- **Rollback Strategy:** Estratégia de rollback automático

## Integrações Externas

### 1. Evolution API
**Propósito:** Envio e recebimento de mensagens WhatsApp
**Características:**
- Retry automático com backoff
- Validação de assinatura
- Suporte a múltiplos tipos de mídia

### 2. OpenAI API
**Propósito:** Geração de respostas inteligentes
**Características:**
- Cache de respostas
- Suporte a GPT-4 e GPT-4 Vision
- Transcrição com Whisper

### 3. Redis
**Propósito:** Cache e sistema de filas
**Características:**
- Cache distribuído
- Sistema de filas confiável
- Locks distribuídos

## Padrões de Erro e Resiliência

### 1. Retry Patterns
- **Exponential Backoff:** Backoff exponencial para retries
- **Circuit Breaker:** Proteção contra falhas em cascata
- **Timeout Management:** Timeouts configuráveis

### 2. Error Handling
- **Graceful Degradation:** Degradação graciosa do serviço
- **Fallback Strategies:** Estratégias de fallback
- **Error Propagation:** Propagação adequada de erros

### 3. Recovery Strategies
- **Automatic Recovery:** Recuperação automática de falhas
- **Manual Recovery:** Procedimentos de recuperação manual
- **Data Consistency:** Consistência de dados em caso de falha