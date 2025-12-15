# app/middleware/security.py
import hmac
import hashlib
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logger_config import get_logger
from app.core.config import get_settings

log = get_logger()
settings = get_settings()


class SignatureValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware para validar assinatura HMAC-SHA256 do webhook Evolution.
    
    A Evolution API envia um header 'X-Signature' com o hash SHA256 do body,
    usando a WEBHOOK_SECRET como chave.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.secret = settings.WEBHOOK_SECRET
        
        if not self.secret:
            log.warning(
                "⚠️ WEBHOOK_SECRET não configurado no .env! "
                "Validação de assinatura será DESABILITADA (inseguro em produção)"
            )

    async def dispatch(self, request: Request, call_next):
        # Aplica validação apenas na rota /webhook
        if request.url.path == "/webhook":
            
            # Se secret não está configurado, apenas loga warning e permite
            if not self.secret:
                log.warning("🔓 Requisição sem validação de assinatura (WEBHOOK_SECRET ausente)")
                response = await call_next(request)
                return response
            
            # Busca assinatura no header
            signature = request.headers.get("X-Signature")
            #if not signature:
            #    log.warning("🚫 Header X-Signature ausente no webhook")
            #    raise HTTPException(
            #        status_code=401,
            #        detail="Missing X-Signature header"
            #    )
            
            # Lê o body da requisição
            body = await request.body()
            
            # Calcula assinatura esperada
            computed_signature = hmac.new(
                self.secret.encode("utf-8"),
                body,
                hashlib.sha256
            ).hexdigest()
            
            # Compara de forma segura (evita timing attacks)
            if not hmac.compare_digest(computed_signature, signature):
                log.error(
                    f"🚫 Assinatura inválida! "
                    f"Esperado: {computed_signature[:10]}... | "
                    f"Recebido: {signature[:10]}..."
                )
                raise HTTPException(
                    status_code=403,
                    detail="Invalid webhook signature"
                )
            
            log.debug("✅ Assinatura do webhook validada com sucesso")
        
        response = await call_next(request)
        return response