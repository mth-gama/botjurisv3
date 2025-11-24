# BotJuris - Documentação Geral do Projeto

## Visão Geral do Sistema

O BotJuris é uma aplicação FastAPI que implementa um sistema de atendimento automatizado via WhatsApp, utilizando inteligência artificial para fornecer respostas contextuais e inteligentes a mensagens de usuários.

### Objetivo Principal
Automatizar o atendimento ao cliente via WhatsApp, permitindo que empresas e profissionais configurem IAs personalizadas para responder mensagens de forma contextualizada e eficiente.

## Arquitetura do Sistema

### Tecnologias Utilizadas
- **Backend:** FastAPI (Python)
- **Banco de Dados:** PostgreSQL com SQLAlchemy
- **Cache/Filas:** Redis
- **IA:** OpenAI GPT (GPT-4, GPT-4 Vision, Whisper)
- **WhatsApp:** Evolution API
- **Containerização:** Docker

### Componentes Principais
1. **API de Webhooks:** Recebe mensagens do WhatsApp
2. **Sistema de Filas:** Processamento assíncrono com Redis
3. **Integração LLM:** Geração inteligente de respostas
4. **Banco de Dados:** Persistência de leads e configurações
5. **Cache:** Otimização de performance

## Funcionalidades Principais

### 1. Recebimento de Mensagens
- **Webhook Endpoint:** Recebe mensagens via Evolution API
- **Validação:** Validação de payloads com Pydantic
- **Segurança:** Rate limiting e validação de assinatura
- **Tipos Suportados:** Texto, imagem, áudio, documentos

### 2. Processamento Inteligente
- **Análise de Contexto:** Usa histórico de conversas
- **IA Personalizada:** Cada IA tem seu próprio prompt
- **Processamento de Mídia:** Imagens (GPT-4 Vision) e áudios (Whisper)
- **Resumos Automáticos:** Gera resumos periódicos das conversas

### 3. Gestão de Leads
- **Identificação Única:** Por número de telefone
- **Histórico Completo:** Todas as mensagens armazenadas
- **Contexto Persistente:** Conversas continuam onde pararam
- **Resumos Inteligentes:** IA gera resumos das conversas

### 4. Sistema de Filas Confiável
- **Processamento Assíncrono:** Não bloqueia o webhook
- **Retry Automático:** Backoff exponencial para falhas
- **Circuit Breaker:** Protege contra falhas em cascata
- **Dead Letter Queue:** Mensagens problemáticas são salvas

## Fluxo de Funcionamento

### 1. Mensagem Recebida
```
Usuário WhatsApp → Evolution API → Webhook BotJuris → Fila Redis
```

### 2. Processamento
```
Worker Redis → Process Service → IA Service → Evolution API → Usuário WhatsApp
```

### 3. Armazenamento
```
Lead Service → Database → Histórico Atualizado → Cache Redis
```

## Estrutura de Diretórios

```
app/
├── apis/                    # Integrações com APIs externas
├── core/                    # Configurações e utilidades core
├── database/                # Modelos e operações de banco
├── middleware/              # Middlewares da aplicação
├── routers/                 # Rotas da API
├── schemas/                 # Validações Pydantic
├── service/                 # Lógica de negócio
├── tasks/                   # Tarefas assíncronas
└── workers/                 # Workers de processamento

tests/                       # Testes unitários e de integração
```

## Configuração e Instalação

### Requisitos
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Evolution API
- OpenAI API Key

### Instalação
1. Clone o repositório
2. Configure o ambiente virtual
3. Instale as dependências
4. Configure o banco de dados
5. Configure as variáveis de ambiente
6. Execute as migrações
7. Inicie a aplicação

### Variáveis de Ambiente Principais
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `EVOLUTION_HOST`: Evolution API endpoint
- `EVOLUTION_API_KEY`: Evolution API key
- `OPENAI_API_KEY`: OpenAI API key
- `FERNET_KEY`: Encryption key (44 chars)

## Segurança

### Medidas Implementadas
- **Criptografia:** Credenciais criptografadas no banco
- **Validação:** Validação rigorosa de entradas
- **Rate Limiting:** Previne abuso do sistema
- **Webhook Validation:** Verifica autenticidade dos webhooks
- **Data Sanitization:** Remove dados sensíveis dos logs

### Conformidade
- LGPD: Dados pessoais tratados com consentimento
- Criptografia: Todos os dados sensíveis criptografados
- Logs: Informações sensíveis não são logadas

## Monitoramento e Observabilidade

### Logs
- Estruturados em formato JSON
- Níveis configuráveis (DEBUG, INFO, WARNING, ERROR)
- Rotação automática de arquivos

### Métricas
- Mensagens processadas por minuto
- Taxa de sucesso/falha
- Tempo médio de resposta
- Uso de recursos do sistema

### Health Checks
- Endpoint `/health` para verificação de saúde
- Verificação de dependências externas
- Status em tempo real da aplicação

## Escalabilidade

### Horizontal
- Aplicação stateless
- Cache distribuído com Redis
- Banco de dados com replicação

### Vertical
- Processamento assíncrono
- Pool de conexões otimizado
- Cache inteligente de respostas

## Manutenção e Suporte

### Backup
- Backups automáticos do PostgreSQL
- Backup de configurações
- Procedimentos de restauração documentados

### Updates
- Deploy com zero downtime
- Rollback automático em caso de falha
- Migrações de banco versionadas

### Troubleshooting
- Logs detalhados para debugging
- Documentação de problemas comuns
- Procedimentos de recuperação

## Casos de Uso

### 1. Escritórios de Advocacia
- Atendimento inicial de clientes
- Triagem de casos jurídicos
- Agendamento de consultas
- Respostas a perguntas frequentes

### 2. Consultorias
- Qualificação de leads
- Agendamento de reuniões
- Envio de materiais informativos
- Suporte ao cliente

### 3. Serviços Profissionais
- Atendimento 24/7
- Captação de clientes
- Automação de processos
- Integração com CRMs

## Vantagens do Sistema

### Para Empresas
- **Disponibilidade 24/7:** Atendimento constante
- **Escalabilidade:** Atende múltiplos clientes simultaneamente
- **Personalização:** IAs configuráveis por necessidade
- **Custo-benefício:** Reduz custos com atendimento

### Para Clientes
- **Resposta Imediata:** Sem tempo de espera
- **Contexto:** Mantém histórico da conversa
- **Disponibilidade:** Sempre disponível
- **Qualidade:** Respostas consistentes e precisas

## Roadmap e Futuras Implementações

### Funcionalidades Planejadas
- **Multi-idioma:** Suporte a múltiplos idiomas
- **Analytics Avançado:** Dashboards e relatórios
- **Integração CRM:** Conexão com sistemas CRM
- **IA Multimodal:** Processamento avançado de mídias
- **Voice:** Suporte a chamadas de voz

### Melhorias de Performance
- **Cache Inteligente:** Algoritmos de cache mais eficientes
- **Processamento Paralelo:** Maior paralelização de tarefas
- **Otimização de Queries:** Queries de banco otimizadas
- **CDN:** Distribuição global de conteúdo

## Documentação Adicional

### Documentações por Funcionalidade
- [API WhatsApp](api-whatsapp/api-whatsapp.md)
- [Sistema de Filas](sistema-filas/sistema-filas.md)
- [Integração LLM](integracao-llm/integracao-llm.md)
- [Banco de Dados](banco-dados/banco-dados.md)
- [Arquitetura Geral](arquitetura/arquitetura-geral.md)
- [Configurações](configuracoes/configuracoes.md)

### Links Úteis
- [Repositório do Projeto](https://github.com/seu-repo/botjuris)
- [Documentação Evolution API](https://doc.evolution-api.com)
- [Documentação OpenAI](https://platform.openai.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com)

## Suporte e Contribuições

### Suporte Técnico
- Issues no GitHub
- Documentação técnica completa
- Comunidade de desenvolvedores

### Contribuições
- Pull requests bem-vindos
- Guidelines de contribuição
- Code review process
- Testes obrigatórios

---

**BotJuris - Transformando atendimento via WhatsApp com Inteligência Artificial**