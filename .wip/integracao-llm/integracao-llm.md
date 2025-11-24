# Integração LLM - Documentação

## Visão Geral
A integração com Large Language Models (LLM) é o coração inteligente do BotJuris, responsável por gerar respostas contextuais e resumos de conversas usando OpenAI GPT models.

## Arquitetura da Integração

### Componentes Principais
1. **IAresponse:** Classe principal para geração de respostas
2. **ConversationChain:** Gerenciamento de contexto conversacional
3. **ConversationBufferWindowMemory:** Memória de conversas com limite de janela
4. **Cache Service:** Armazenamento de respostas para performance
5. **OpenAI Integration:** Integração com API da OpenAI

## Modelos de IA Utilizados

### GPT Models
- **Modelo Padrão:** `gpt-4o-mini` (configurável via `MODEL_DEFAULT`)
- **Análise de Imagem:** `gpt-4o` (configurável via `MODEL_ANALYZE_IMAGE`)
- **Transcrição de Áudio:** `whisper-1`

### Configurações
```python
MODEL_DEFAULT = "gpt-4o-mini"
MODEL_ANALYZE_IMAGE = "gpt-4o"
```

## Classe IAresponse

### Construtor
```python
def __init__(self, api_key: str, ia_model: str, system_prompt: str, resume_lead: str = ""):
    self.api_key = api_key
    self.ia_model = ia_model
    self.system_prompt = system_prompt
    self.resume_lead = resume_lead
```

### Métodos Principais

#### 1. generate_response()
**Propósito:** Gera resposta conversacional com contexto histórico

**Parâmetros:**
- `message_lead: str` - Mensagem do usuário
- `history_message: list` - Histórico de mensagens

**Retorno:** String com resposta gerada

**Implementação:**
```python
def generate_response(self, message_lead: str, history_message: list = []) -> str:
    chat = ChatOpenAI(model=self.ia_model, api_key=self.api_key)
    memory = ConversationBufferWindowMemory(k=20)  # Últimas 20 mensagens
    review_template = PromptTemplate.from_template(self.system_prompt)
    
    conversation = ConversationChain(
        llm=chat, memory=memory, prompt=review_template
    )
    
    # Alimenta memória com histórico
    for msg in history_message:
        if msg["role"] == "user":
            conversation.memory.chat_memory.add_user_message(msg.get("content"))
        elif msg["role"] == "assistant":
            conversation.memory.chat_memory.add_ai_message(msg.get("content"))
    
    return conversation.predict(input=message_lead)
```

#### 2. generate_resume()
**Propósito:** Gera resumo detalhado da conversa

**Parâmetros:**
- `history_message: list` - Histórico completo de mensagens

**Retorno:** String com resumo gerado

**Prompt de Resumo:**
```
Você é um assistente especializado em resumir conversas com leads. 
Extraia e organize:
1. Pontos-chave e necessidades do lead
2. Interesses e objeções identificadas  
3. Próximos passos sugeridos
4. Informações de contato relevantes
5. Requisitos específicos do lead
```

## Sistema de Cache

### Implementação
```python
def get_response_from_ai(user_message: str, user_id: str):
    cache_key = f"ia_response:{user_id}"
    
    # Tenta recuperar do cache
    cached = get_cache(cache_key)
    if cached:
        return cached["response"]
    
    # Gera nova resposta
    response = ia.generate_response(user_message)
    
    # Armazena no cache
    set_cache(cache_key, {"response": response})
    
    return response
```

### Benefícios
- **Performance:** Evita chamadas repetidas à API
- **Custo:** Reduz custos com API da OpenAI
- **Latência:** Respostas mais rápidas para mensagens idênticas

## Processamento de Mídias

### Análise de Imagem
**Fluxo:**
1. Recebe imagem via Evolution API
2. Converte para base64
3. Envia para GPT-4 Vision
4. Retorna descrição textual

**Prompt de Análise:**
```
Descreva detalhadamente o que você vê nesta imagem.
```

**Código:**
```python
def processar_imagem(instance: str, message_id: str, ia_infos) -> str:
    # Busca imagem da Evolution
    image_base64 = get_image_from_evolution(instance, message_id)
    
    # Envia para OpenAI Vision
    payload = {
        "model": "gpt-4o",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "Descreva detalhadamente..."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]
        }]
    }
    
    response = requests.post("https://api.openai.com/v1/chat/completions", json=payload)
    return response.json()["choices"][0]["message"]["content"]
```

### Transcrição de Áudio
**Fluxo:**
1. Recebe áudio via Evolution API
2. Converte OGG para MP3
3. Transcreve com Whisper
4. Retorna texto transcrito

**Código:**
```python
def processar_audio(instance: str, message_id: str, ia_infos) -> str:
    # Busca áudio da Evolution
    audio_base64 = get_audio_from_evolution(instance, message_id)
    
    # Salva e converte arquivo
    save_audio_file(audio_base64)
    convert_ogg_to_mp3()
    
    # Transcreve com Whisper
    with open("audio.mp3", "rb") as audio_file:
        response = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    
    return response.text
```

## Configuração de Prompts

### Prompts por IA
Cada IA no sistema pode ter múltiplos prompts, mas apenas um ativo por vez.

### Estrutura de Prompt
```python
class Prompt(Base):
    __tablename__ = "prompts"
    id = Column(Integer, primary_key=True)
    ia_id = Column(Integer, ForeignKey("ias.id"))
    prompt_text = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

### Prompt Ativo
```python
@property
def active_prompts(self):
    active = [p for p in self.prompts if p.is_active]
    return active[0] if active else None
```

## Integração com Fluxo Principal

### Processo Completo
1. **Recebimento:** Webhook recebe mensagem
2. **Identificação:** Busca IA pelo telefone
3. **Validação:** Verifica se IA está ativa
4. **Contexto:** Recupera histórico do lead
5. **Geração:** IA gera resposta com contexto
6. **Cache:** Armazena resposta se aplicável
7. **Envio:** Retorna resposta ao usuário

### Tratamento de Erros
```python
try:
    response = llm.generate_response(mensagem_texto, historico)
    if not response:
        raise Exception("IA não gerou resposta")
except Exception as ex:
    log.error(f"Erro ao gerar resposta: {ex}")
    # Fallback para mensagem padrão
    response = "Desculpe, não consegui processar sua mensagem."
```

## Configurações de API

### Variáveis de Ambiente
```bash
OPENAI_API_KEY=sk-sua-chave-api
MODEL_DEFAULT=gpt-4o-mini
MODEL_ANALYZE_IMAGE_OPENAI=gpt-4o
```

### Credenciais por IA
```python
# IAConfig contém credenciais encriptadas
@property
def credentials(self):
    return decrypt_data(self.encrypted_credentials)

# Uso na geração de resposta
api_key = ia_infos.ia_config.credentials.get("api_key")
ia_model = ia_infos.ia_config.credentials.get("ia_model", "")
```

## Monitoramento e Métricas

### Logs de IA
```
🧠 Gerando resumo (interações=25)
Resposta IA: [conteúdo da resposta]
Resumo IA: [conteúdo do resumo]
```

### Métricas Importantes
- **Tempo de resposta da IA:** Monitorado e logado
- **Taxa de sucesso:** Sucesso/falha nas chamadas
- **Tokens utilizados:** Para controle de custos
- **Cache hit ratio:** Efetividade do cache

## Segurança e Privacidade

### Proteções Implementadas
- **Criptografia:** Credenciais armazenadas encriptadas
- **Sanitização:** Dados de entrada sanitizados
- **Logs:** Informações sensíveis não são logadas
- **Rate Limiting:** Previne abuso da API

### Prompts de Segurança
```
5. **Privacidade e Segurança:** Garanta que todas as informações 
sensíveis sejam tratadas com a devida confidencialidade.
```

## Performance e Otimização

### Técnicas Utilizadas
1. **Cache de Respostas:** Reduz chamadas repetidas
2. **Janela de Memória:** Limita histórico para performance
3. **Timeout:** Previne travamentos
4. **Retry com Backoff:** Trata falhas temporárias
5. **Circuit Breaker:** Protege contra falhas em cascata