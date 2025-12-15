from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.cache import init_cache

# ============================================================
# 🌎 Seleção dinâmica do ambiente
# ============================================================
from app.core.config import get_settings
from app.core.logger_config import get_logger
from app.middleware.error_handler import register_exception_handlers
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security import SignatureValidationMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routers import webhook
from app.routers.health import router as health_router
from app.service.queue_manager import start_worker, stop_worker

settings = get_settings()

log = get_logger()


# ============================================================
# 🔄 Lifespan (melhor que on_event)
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🔵 Startup
    log.info(f"🚀 {settings.APP_NAME} iniciado com sucesso!")
    log.info(f"🌍 Ambiente: {settings.ENVIRONMENT}")

    init_cache()  # inicia Redis cache
    start_worker(True)  # inicia queue worker em background

    yield

    # 🔴 Shutdown
    log.info("🛑 Encerrando aplicação com graceful shutdown...")
    stop_worker()  # encerra worker de forma segura
    log.info("✔ Worker finalizado.")
    log.info("🔴 Aplicação encerrada com segurança.")


# ============================================================
# 🏗️ Criação da aplicação
# ============================================================
app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)


# ============================================================
# 🧱 Middlewares globais
# ============================================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://evolution-api.com",  # ajuste para o domínio real
        "http://localhost:3000",  # para desenvolvimento
        "https://evolution-evolution-api.i35x3k.easypanel.host/"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Headers de segurança (antes de tudo que gera resposta)
#app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting
#app.add_middleware(RateLimitMiddleware, max_requests=10, window_seconds=60)

# Validação de assinatura do Evolution
#app.add_middleware(SignatureValidationMiddleware)

# Exceptions globais
#register_exception_handlers(app)


# ============================================================
# 🛣️ Rotas
# ============================================================
app.include_router(webhook.router)
#app.include_router(health_router)
