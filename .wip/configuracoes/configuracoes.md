# Configurações - Documentação

## Visão Geral
As configurações do BotJuris são gerenciadas através de variáveis de ambiente e Pydantic Settings, garantindo validação de tipos, valores padrão e documentação automática.

## Configurações Principais

### 1. Configurações da Aplicação
```python
APP_NAME: str = "BotJuris"
ENVIRONMENT: Literal["development", "staging", "production"] = "development"
DEBUG: bool = False
```

**Descrição:**
- `APP_NAME`: Nome da aplicação para logs e identificação
- `ENVIRONMENT`: Ambiente de execução (afeta logs e comportamento)
- `DEBUG`: Modo debug (logs mais detalhados)

### 2. Configurações do Banco de Dados
```python
DATABASE_URL: str  # Obrigatório
```

**Formato:**
```
postgresql://usuario:senha@host:porta/database
```

**Exemplo:**
```bash
DATABASE_URL=postgresql://botjuris:senha123@localhost:5432/botjuris_db
```

### 3. Configurações do Redis
```python
REDIS_URL: str = "redis://localhost:6379/0"
REDIS_HOST: str = "localhost"
REDIS_PORT: int = 6379
REDIS_DB: int = 0
REDIS_PASSWORD: str | None = None
```

**Opções de Configuração:**
- **URL Completa:** `REDIS_URL` (preferencial)
- **Componentes Separados:** `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`

**Exemplos:**
```bash
# Opção 1: URL completa
REDIS_URL=redis://localhost:6379/0

# Opção 2: Componentes separados (com senha)
REDIS_HOST=redis.example.com
REDIS_PORT=6380
REDIS_DB=1
REDIS_PASSWORD=senha_redis_segura
```

### 4. Configurações da Evolution API
```python
EVOLUTION_HOST: str  # Obrigatório - deve terminar com /
EVOLUTION_API_KEY: str  # Obrigatório - mínimo 10 caracteres
```

**Exemplo:**
```bash
EVOLUTION_HOST=https://evolution-api.com/
EVOLUTION_API_KEY=evolution_api_key_12345
```

**Validação Automática:**
- URL é automaticamente ajustada para terminar com `/`
- API key deve ter no mínimo 10 caracteres

### 5. Configurações da OpenAI
```python
OPENAI_API_KEY: str  # Obrigatório - mínimo 20 caracteres
MODEL_DEFAULT: str = "gpt-4o-mini"
MODEL_ANALYZE_IMAGE: str = "gpt-4o"
```

**Exemplo:**
```bash
OPENAI_API_KEY=sk-openai_api_key_muito_longo_aqui
MODEL_DEFAULT=gpt-4o-mini
MODEL_ANALYZE_IMAGE=gpt-4o
```

### 6. Configurações de Segurança
```python
FERNET_KEY: str  # Obrigatório - exatamente 44 caracteres base64
WEBHOOK_SECRET: str | None = None  # Opcional
```

**Fernet Key:**
- Deve ter exatamente 44 caracteres em base64
- Usada para criptografar credenciais sensíveis
- Pode ser gerada com:
```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Copie este valor
```

**Webhook Secret:**
- Usado para validar assinaturas de webhooks
- Se não fornecido, validação é desabilitada

### 7. Configurações de Rate Limiting
```python
RATE_LIMIT_REQUESTS: int = 10
RATE_LIMIT_WINDOW: int = 60
```

**Descrição:**
- `RATE_LIMIT_REQUESTS`: Número máximo de requisições
- `RATE_LIMIT_WINDOW`: Janela de tempo em segundos
- Padrão: 10 requisições por minuto

## Arquivo de Configuração (.env)

### Exemplo Completo (.env)
```bash
# =====================================================
# Configurações da Aplicação
# =====================================================
APP_NAME=BotJuris
ENVIRONMENT=development
DEBUG=false

# =====================================================
# Banco de Dados
# =====================================================
DATABASE_URL=postgresql://botjuris:senha123@localhost:5432/botjuris_db

# =====================================================
# Redis (Cache e Filas)
# =====================================================
REDIS_URL=redis://localhost:6379/0
# Ou componentes separados:
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_DB=0
# REDIS_PASSWORD=

# =====================================================
# Evolution API (WhatsApp)
# =====================================================
EVOLUTION_HOST=https://evolution-api.com/
EVOLUTION_API_KEY=sua_chave_api_aqui

# =====================================================
# OpenAI (IA)
# =====================================================
OPENAI_API_KEY=sk-sua_chave_openai_aqui
MODEL_DEFAULT=gpt-4o-mini
MODEL_ANALYZE_IMAGE=gpt-4o

# =====================================================
# Segurança
# =====================================================
FERNET_KEY=sua_chave_fernet_de_44_caracteres_aqui_xxxxxxxxxxxx
WEBHOOK_SECRET=seu_webhook_secret_opcional

# =====================================================
# Rate Limiting
# =====================================================
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW=60
```

### Arquivo .env.example
```bash
# Copie este arquivo para .env e ajuste os valores

# Banco de Dados (Obrigatório)
DATABASE_URL=postgresql://usuario:senha@host:porta/database

# Redis
REDIS_URL=redis://localhost:6379/0

# Evolution API (Obrigatório)
EVOLUTION_HOST=https://sua-instancia.evolution-api.com/
EVOLUTION_API_KEY=sua-api-key-aqui

# OpenAI (Obrigatório)
OPENAI_API_KEY=sk-sua-chave-openai-aqui

# Segurança (Obrigatório)
FERNET_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx=  # 44 caracteres base64
```

## Validações Automáticas

### Validações de Campo
1. **EVOLUTION_HOST:** Garante que termina com `/`
2. **ENVIRONMENT:** Deve ser um dos valores permitidos
3. **API Keys:** Tamanho mínimo válido
4. **FERNET_KEY:** Exatamente 44 caracteres base64

### Validações de Sistema
- Arquivo `.env` deve existir e ser legível
- Variáveis obrigatórias devem estar presentes
- Formato das URLs deve ser válido

## Helpers e Propriedades

### Métodos Úteis
```python
@property
def is_production(self) -> bool:
    return self.ENVIRONMENT == "production"

@property  
def is_development(self) -> bool:
    return self.ENVIRONMENT == "development"

def get_redis_url_with_password(self) -> str:
    # Constrói URL com senha se existir
```

### Uso nas Configurações
```python
from app.core.config import get_settings

settings = get_settings()

if settings.is_production:
    # Configurações específicas de produção
    log_level = "INFO"
else:
    # Configurações de desenvolvimento
    log_level = "DEBUG"
```

## Configurações por Ambiente

### Desenvolvimento
```bash
ENVIRONMENT=development
DEBUG=true
REDIS_URL=redis://localhost:6379/0
```

### Staging
```bash
ENVIRONMENT=staging
DEBUG=false
REDIS_URL=redis://staging-redis:6379/0
RATE_LIMIT_REQUESTS=20
```

### Produção
```bash
ENVIRONMENT=production
DEBUG=false
REDIS_URL=redis://prod-redis-cluster:6379/0
RATE_LIMIT_REQUESTS=50
```

## Segurança das Configurações

### Boas Práticas
1. **Nunca commite o arquivo .env real**
2. **Use .env.example como template**
3. **Gire chaves de API regularmente**
4. **Use secrets management em produção**
5. **Valide configurações em startup**

### Gerando Fernet Key
```python
# Script para gerar chave Fernet
from cryptography.fernet import Fernet
import secrets

# Gera chave Fernet
derived_key = Fernet.generate_key()
print(f"FERNET_KEY={derived_key.decode()}")

# Ou use openssl (Linux/Mac)
# openssl rand -base64 32
```

## Troubleshooting

### Problemas Comuns

#### 1. "FERNET_KEY inválida"
**Causa:** Chave não tem 44 caracteres ou não é base64 válido
**Solução:** Gere uma nova chave com o script acima

#### 2. "DATABASE_URL não encontrada"
**Causa:** Variável obrigatória não está no .env
**Solução:** Adicione a variável ao arquivo .env

#### 3. "EVOLUTION_HOST deve terminar com /"
**Causa:** URL não termina com barra
**Solução:** A aplicação adiciona automaticamente, mas é bom corrigir

#### 4. "API Key muito curta"
**Causa:** Chave não atende ao tamanho mínimo
**Solução:** Verifique se a chave está completa e correta

### Debug de Configurações
```python
# Verificar todas as configurações
from app.core.config import get_settings

settings = get_settings()
print(f"Ambiente: {settings.ENVIRONMENT}")
print(f"Debug: {settings.DEBUG}")
print(f"App Name: {settings.APP_NAME}")
# ... outras configurações
```

## Testes de Configuração

### Testando Conexões
```bash
# Testar PostgreSQL
python -c "from app.database.connection import test_connection; test_connection()"

# Testar Redis  
python -c "from app.core.cache import test_cache; test_cache()"

# Testar Evolution API
python -c "from app.apis.evolution import test_connection; test_connection()"
```

### Validação de Configurações
```bash
# Valida todas as configurações
python -c "from app.core.config import get_settings; get_settings()"
```