import json, pysnooper
from typing import Optional

from app.core.logger_config import get_logger

from ..connection import init_db
from ..models import Lead

log = get_logger()


def filter_lead(phone: str, message: dict) -> Optional[Lead]:
    db = init_db()
    if not db:
        raise Exception("Não consegui conectar com database")

    try:
        lead = db.query(Lead).filter(Lead.phone == phone).first()
        if not lead:
            log.info(f"Lead não localizado com esse telefone {phone}")
            return None

        historico = lead.message
        if not historico:
            historico = []

        historico.append(message)
        lead.message = historico
 
        db.commit()
        db.refresh(lead)
        log.info(f"Lead localizado e conversa atualizada: {lead.name} - {lead.phone}")

        return lead

    except Exception as ex:
        log.error(f"Erro ao filtrar lead: {ex}", exc_info=True)
        return None
    finally:
        db.close()


def update_lead(lead_id: int, message: list, resume: str) -> bool:
    db = init_db()
    if not db:
        raise Exception("Não consegui conectar com database")

    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            log.warning(f"Lead não localizado com esse ID {lead_id}")
            return False

        if resume:
            lead.resume = resume

        historico = lead.message
        if not historico:
            historico = []

        historico.append(message)
        lead.message = historico

        db.commit()
        db.refresh(lead)
        log.info(
            f"Lead localizado e conversa atualizada: {lead.name} - {lead.phone}"
        )  # ✅ MUDOU AQUI

        return True

    except Exception as ex:
        log.error(f"Erro ao atualizar lead: {ex}", exc_info=True)
        return False
    finally:
        db.close()

def normalize_json(value):
    """
    Garante que o valor é JSON-safe para Postgres JSON.
    """
    return json.loads(
        json.dumps(value, ensure_ascii=False, default=str)
    )


def new_lead(ia_id: int, phone: str, name: str, message: list) -> Optional[Lead]:
    db = init_db()
    if not db:
        print("Não consegui conectar com database")
        raise Exception("Não consegui conectar com database")

    try:
        print(f"Iniciando salvamento do lead {phone} no database")
        if isinstance(message, dict):
            print("mensagem estava em dicionario colocando em lista")
            message = [message]
        
        lead = Lead(ia_id=ia_id, phone=phone, name=name, message=message)
        db.add(lead)

        db.commit()

        db.refresh(lead)


        print(
            f"Novo Lead [id: {lead.id}, Nome: {lead.name}] da IA {lead.ia_id} adicionado com sucesso!"
        )

        return lead

    except Exception as ex:
        import traceback
        print("🔥 ERRO AO COMMITAR LEAD")
        print(f"Tipo do erro: {type(ex)}")
        if hasattr(ex, "orig"):
            print(f"Erro original do banco: {ex.orig}")
        traceback.print_exc()
        raise
    finally:
        db.close()
