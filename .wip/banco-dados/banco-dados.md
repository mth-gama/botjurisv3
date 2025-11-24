# Banco de Dados - Documentação

## Visão Geral
O banco de dados do BotJuris utiliza PostgreSQL com SQLAlchemy ORM, implementando um modelo de dados otimizado para gerenciamento de IAs conversacionais, leads e suas interações.

## Modelos de Dados

### 1. IA (Inteligência Artificial)
**Tabela:** `ias`
**Descrição:** Configuração das IAs que respondem mensagens

```sql
CREATE TABLE ias (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL UNIQUE,
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    status BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ia_phone_status ON ias(phone_number, status);
```

**Campos:**
- `id`: Identificador único
- `name`: Nome da IA
- `phone_number`: Número de telefone associado
- `status`: Ativa (true) ou inativa (false)
- `created_at`: Data de criação
- `updated_at`: Última atualização

**Relacionamentos:**
- Um para muitos com `Prompts`
- Um para um com `IAConfig`
- Um para muitos com `Leads`

### 2. IAConfig (Configuração da IA)
**Tabela:** `ia_config`
**Descrição:** Configurações técnicas da IA (API, credenciais)

```sql
CREATE TABLE ia_config (
    id SERIAL PRIMARY KEY,
    ia_id INTEGER NOT NULL REFERENCES ias(id),
    channel VARCHAR(50) NOT NULL,
    ai_api VARCHAR(100) NOT NULL,
    encrypted_credentials TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ia_config_ia_id ON ia_config(ia_id);
```

**Campos:**
- `id`: Identificador único
- `ia_id`: FK para tabela `ias`
- `channel`: Canal de comunicação (WhatsApp, etc.)
- `ai_api`: API de IA utilizada (OpenAI, etc.)
- `encrypted_credentials`: Credenciais criptografadas
- `created_at`: Data de criação
- `updated_at`: Última atualização

**Propriedades:**
```python
@property
def credentials(self):
    return decrypt_data(self.encrypted_credentials)
```

### 3. Prompt
**Tabela:** `prompts`
**Descrição:** Prompts de sistema para cada IA

```sql
CREATE TABLE prompts (
    id SERIAL PRIMARY KEY,
    ia_id INTEGER NOT NULL REFERENCES ias(id),
    prompt_text TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_prompts_ia_id ON prompts(ia_id);
CREATE INDEX idx_prompts_is_active ON prompts(is_active);
```

**Campos:**
- `id`: Identificador único
- `ia_id`: FK para tabela `ias`
- `prompt_text`: Texto do prompt do sistema
- `is_active`: Prompt ativo (true) ou inativo (false)
- `created_at`: Data de criação
- `updated_at`: Última atualização

**Regras de Negócio:**
- Cada IA pode ter múltiplos prompts
- Apenas um prompt pode estar ativo por IA
- Prompt ativo é usado para geração de respostas

### 4. Lead
**Tabela:** `leads`
**Descrição:** Usuários que interagem com as IAs

```sql
CREATE TABLE leads (
    id SERIAL PRIMARY KEY,
    ia_id INTEGER NOT NULL REFERENCES ias(id),
    name VARCHAR(120),
    phone VARCHAR(20) NOT NULL UNIQUE,
    message JSON NOT NULL,
    resume TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_leads_ia_id ON leads(ia_id);
CREATE INDEX idx_leads_phone ON leads(phone);
```

**Campos:**
- `id`: Identificador único
- `ia_id`: FK para tabela `ias` (IA que o lead interage)
- `name`: Nome do lead
- `phone`: Número de telefone (único)
- `message`: Histórico de mensagens (JSON array)
- `resume`: Resumo da conversa
- `created_at`: Data de criação
- `updated_at`: Última atualização

**Estrutura do Campo `message`:**
```json
[
  {
    "role": "user",
    "name": "João",
    "content": "Olá, preciso de ajuda jurídica"
  },
  {
    "role": "assistant", 
    "content": "Olá! Sou a assistente jurídica do BotJuris. Como posso ajudar?"
  }
]
```

## Índices e Performance

### Índices Criados
1. **idx_ia_phone_status:** Otimiza busca de IA por telefone e status
2. **idx_ia_config_ia_id:** Acelera joins com configurações
3. **idx_prompts_ia_id + is_active:** Rápida busca de prompt ativo
4. **idx_leads_phone:** Busca eficiente de leads por telefone

### Otimizações
- Uso de `lazy="selectin"` e `lazy="joined"` para queries otimizadas
- Índices em campos frequentemente consultados
- JSON mutável para histórico de mensagens

## Operações de Banco de Dados

### Manipulações Principais

#### 1. IA Manipulations (`ia_manipulations`)
```python
# Buscar IA por telefone
ia_infos = ia_manipulations.filter_ia(phone_number)

# Verificar se IA está ativa
if ia_infos and ia_infos.status:
    # Processar mensagem
```

#### 2. Lead Manipulations (`lead_manipulations`)
```python
# Buscar ou criar lead
lead_db = lead_manipulations.filter_lead(phone, message_data)

# Criar novo lead
lead_db = lead_manipulations.new_lead(ia_id, phone, name, messages)

# Atualizar lead
success = lead_manipulations.update_lead(lead_id, message_data, resume)
```

### Queries e Repositórios

#### Estrutura de Queries (`queries.py`)
- Queries SQL otimizadas para operações específicas
- Uso de prepared statements para segurança
- Índices aproveitados em filtros complexos

#### Repositórios (`repositories/`)
- `ia_repository.py`: Operações de CRUD para IAs
- `lead_repository.py`: Operações de CRUD para Leads
- Abstração entre modelo de dados e lógica de negócio

## Segurança

### Criptografia
- **Credenciais:** Armazenadas criptografadas com Fernet
- **Chave de Criptografia:** Configurada via `FERNET_KEY` no .env
- **Algoritmo:** AES 128-bit em modo CBC

```python
def encrypt_data(data: dict) -> str:
    f = Fernet(settings.FERNET_KEY)
    encrypted = f.encrypt(json.dumps(data).encode())
    return base64.b64encode(encrypted).decode()

def decrypt_data(encrypted_data: str) -> dict:
    f = Fernet(settings.FERNET_KEY)
    decrypted = f.decrypt(base64.b64decode(encrypted_data))
    return json.loads(decrypted.decode())
```

### Sanitização
- Dados de entrada são sanitizados antes de persistir
- Proteção contra SQL injection via SQLAlchemy ORM
- Validação de tipos via Pydantic schemas

## Backup e Recuperação

### Estratégia de Backup
- Backups automáticos do PostgreSQL
- Retenção configurável (diário, semanal, mensal)
- Testes regulares de restauração

### Recuperação de Desastres
- Replicação para standby (se configurado)
- Scripts de restauração automatizados
- Documentação de procedimentos de recuperação

## Monitoramento e Manutenção

### Queries de Monitoramento
```sql
-- Total de leads por IA
SELECT ia_id, COUNT(*) as total_leads 
FROM leads 
GROUP BY ia_id;

-- IAs ativas
SELECT * FROM ias WHERE status = true;

-- Leads mais recentes
SELECT * FROM leads 
ORDER BY updated_at DESC 
LIMIT 10;
```

### Manutenção Regular
- Análise de performance de queries
- Reindexação periódica
- Vacuum e análise de estatísticas
- Limpeza de dados antigos (se aplicável)

## Migrações e Versionamento

### Sistema de Migrações
- Uso de Alembic para versionamento de schema
- Migrações são versionadas e reversíveis
- Ambientes (dev, staging, prod) sincronizados

### Procedimentos de Migração
1. Backup do banco antes da migração
2. Teste em ambiente de staging
3. Aplicação em produção com rollback preparado
4. Validação pós-migração

## Configurações de Conexão

### PostgreSQL
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/botjuris
```

### Pool de Conexões
- Tamanho do pool: 10 (configurável)
- Timeout de conexão: 30 segundos
- Reciclagem de conexões: 3600 segundos