# app/schemas/webhook.py
from pydantic import Field, constr

from typing import Optional, Dict, Any
from .common import ApiBaseModel, Timestamped, MessageType, PHONE_REGEX

class WebhookMessage(ApiBaseModel):
    conversation: Optional[str] = None
    extendedTextMessage: Optional[Dict[str, Any]] = None
    documentWithCaptionMessage: Optional[Dict[str, Any]] = None
    imageMessage: Optional[Dict[str, Any]] = None
    audioMessage: Optional[Dict[str, Any]] = None

class WebhookKey(ApiBaseModel):
    id: constr(min_length=5)  # id precisa ter pelo menos 5 chars
    remoteJidAlt: constr(pattern=PHONE_REGEX)
    remoteJid: Optional[str]
    fromMe: Optional[bool] = None

class WebhookData(ApiBaseModel):
    key: WebhookKey
    message: WebhookMessage
    messageType: MessageType
    pushName: Optional[constr(min_length=1, max_length=120)] = "Usuário"
    messageTimestamp: Optional[int] = None  # epoch

class WebhookPayload(Timestamped):
    """Envelope do Evolution"""
    apikey: Optional[str] = None
    instance: constr(min_length=1)
    sender: constr(pattern=r"^\d{10,15}@s\.whatsapp\.net$")
    event: Optional[str] = None
    data: WebhookData
