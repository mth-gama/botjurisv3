# app/core/logger_config.py
import os
from loguru import logger
from app.core.config import Settings
from dotenv import load_dotenv
import inspect
import threading
import sys
import traceback


load_dotenv()

ambiente = os.getenv("ENVIROMENT", "prod")

def error_func(text:str) -> None:
    '''Função para exibição erros'''
    thread_id = threading.get_ident()
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback_details = traceback.extract_tb(exc_traceback)
    last_trace = traceback_details[-1] if traceback_details else None
    simple_traceback = f"{last_trace.filename}, line {last_trace.lineno}, in {last_trace.name}" if last_trace else "No traceback available"
    frame = inspect.currentframe().f_back
    func_name = frame.f_code.co_name
    location = func_name
    print(f"[{thread_id}] : Erro na função : [{location}]\n > {text}\n > {simple_traceback}")

def get_logger():
    settings = Settings()  # ← cria uma instância local de configuração

    if ambiente == "developer":
        logger.add(
            "logs/chatbot.log",
            rotation="10 MB",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
        )
        print("AMBIENTE DE DESENVOLVIMENTO ATIVADO")
    return logger
