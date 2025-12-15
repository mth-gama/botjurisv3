# app/service/sanitize.py
from typing import Any
import json

def sanitize_text(texto: str | None, max_len: int = 5000) -> str:
    """
    Sanitiza texto removendo caracteres de controle e normalizando espaços.

    Args:
        texto: Texto a ser sanitizado
        max_len: Tamanho máximo do texto

    Returns:
        Texto sanitizado
    """
    if not texto:
        return ""

    # Remove caracteres de controle (exceto quebras de linha)
    texto = "".join(ch for ch in texto if ch.isprintable() or ch in ["\n", "\r", "\t"])

    # Normaliza espaços (múltiplos espaços → um espaço)
    texto = " ".join(texto.split())

    # Remove espaços nas extremidades
    texto = texto.strip()

    # Limita tamanho
    if len(texto) > max_len:
        texto = texto[:max_len]

    return texto


def sanitize_dict(data: dict) -> dict:
    """
    Sanitiza recursivamente um dicionário.

    Args:
        data: Dicionário a ser sanitizado

    Returns:
        Dicionário sanitizado
    """
    if not isinstance(data, dict):
        return data

    sanitized: dict[str, Any] = {}  # ✅ ÚNICA MUDANÇA AQUI
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_text(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_text(item) if isinstance(item, str) else item for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized


encrypted_str = {}
print(type(encrypted_str))

print(isinstance(encrypted_str, list))
if isinstance(encrypted_str, dict):
    print("é dicionario")

encrypted_str = []