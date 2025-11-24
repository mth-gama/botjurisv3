# API WhatsApp - Documentação

## Visão Geral
A API WhatsApp é o ponto de entrada principal da aplicação BotJuris, responsável por receber webhooks do Evolution API e processar mensagens do WhatsApp de forma assíncrona.

## Endpoints Principais

### 1. Webhook Receiver
**Endpoint:** `POST /webhook`
**Descrição:** Recebe payloads do Evolution API contendo mensagens do WhatsApp
**Status HTTP:** 200 OK (sempre retorna 200 para confirmar recebimento)

#### Estrutura do Payload Recebido
```json
{
  "apikey": "string",
  "instance": "string",
  "sender": "string@whatsapp.net",
  "event": "string",
  "data": {
    "key": {
      "id": "string",
      "remoteJid": "string@s.whatsapp.net",
      "fromMe": boolean
    },
    "message": {
      "conversation": "string",
      "extendedTextMessage": {},
      "documentWithCaptionMessage": {},
      "imageMessage": {},
      "audioMessage": {}
    },
    "messageType": "string",
    "pushName": "string",
    "messageTimestamp": number
  }
}
```

#### Tipos de Mensagens Suportadas
- **Texto Simples:** `conversation`, `extendedTextMessage`
- **Imagem:** `imageMessage` (processada com IA para descrição)
- **Áudio:** `audioMessage` (transcrita com Whisper)
- **Documento:** `documentWithCaptionMessage`

#### Fluxo de Processamento
1. **Recebimento:** Endpoint recebe payload via POST
2. **Validação:** Payload é validado usando Pydantic (`WebhookPayload`)
3. **Sanitização:** Dados são sanitizados para segurança
4. **Enfileiramento:** Mensagem é enfileirada no Redis para processamento assíncrono
5. **Resposta:** Retorna confirmação de recebimento imediatamente

### 2. Health Check
**Endpoint:** `GET /health`
**Descrição:** Verifica status da aplicação e dependências
**Resposta:** Status de saúde do sistema, Redis, banco de dados

## Middlewares de Segurança

### Rate Limiting
- **Limite:** 10 requisições por minuto por IP
- **Implementação:** `RateLimitMiddleware`
- **Propósito:** Prevenir spam e sobrecarga do sistema

### Validação de Assinatura
- **Middleware:** `SignatureValidationMiddleware`
- **Propósito:** Validar autenticidade dos webhooks do Evolution
- **Secret:** Configurado via `WEBHOOK_SECRET` no .env

### Headers de Segurança
- **Middleware:** `SecurityHeadersMiddleware`
- **Headers adicionados:** X-Content-Type-Options, X-Frame-Options, etc.

## Configurações

### CORS
```python
allow_origins = [
    "https://evolution-api.com",
    "http://localhost:3000"
]
allow_credentials = True
allow_methods = ["*"]
allow_headers = ["*"]
```

### Variáveis de Ambiente Necessárias
```bash
# Evolution API
EVOLUTION_HOST=https://sua-instancia.evolution-api.com/
EVOLUTION_API_KEY=sua-api-key

# Segurança
WEBHOOK_SECRET=seu-webhook-secret
```

## Tratamento de Erros
- **Erros de Validação:** Retornam 422 com detalhes do erro
- **Erros de Processamento:** São logados e mensagem vai para DLQ (Dead Letter Queue)
- **Erros de API Externa:** Implementam retry automático com backoff exponencial

## Logs e Monitoramento
- **Nível de Log:** Configurável via ambiente (DEBUG, INFO, WARNING, ERROR)
- **Formato:** JSON estruturado para fácil análise
- **Métricas:** Total de mensagens processadas, taxa de erro, tempo de resposta