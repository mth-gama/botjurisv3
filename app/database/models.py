from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, Index
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import func
from sqlalchemy.orm import relationship, declarative_base
from app.service.crypto import decrypt_data

Base = declarative_base()

class IA(Base):
    __tablename__ = "ias"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, unique=True)
    phone_number = Column(String(20), nullable=False, unique=True)
    status = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    prompts = relationship("Prompt", back_populates="ia", lazy="selectin")
    ia_config = relationship("IAConfig", back_populates="ia", uselist=False, lazy="joined")
    leads = relationship("Lead", back_populates="ia", lazy="selectin")

    @property
    def active_prompts(self):
        active = [p for p in self.prompts if p.is_active]
        return active[0] if active else None

Index("idx_ia_phone_status", IA.phone_number, IA.status)


class IAConfig(Base):
    __tablename__ = "ia_config"
    id = Column(Integer, primary_key=True, index=True)
    ia_id = Column(Integer, ForeignKey("ias.id"), nullable=False, index=True)
    channel = Column(String(50), nullable=False)
    ai_api = Column(String(100), nullable=False)
    encrypted_credentials = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    ia = relationship("IA", back_populates="ia_config", lazy="joined")

    @property
    def credentials(self):
        return decrypt_data(self.encrypted_credentials)


class Prompt(Base):
    __tablename__ = "prompts"
    id = Column(Integer, primary_key=True, index=True)
    ia_id = Column(Integer, ForeignKey("ias.id"), nullable=False, index=True)
    prompt_text = Column(String, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    ia = relationship("IA", back_populates="prompts", lazy="selectin")


class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    ia_id = Column(Integer, ForeignKey("ias.id"), nullable=False, index=True)
    name = Column(String(120))
    phone = Column(String(20), index=True)
    message = Column(MutableList.as_mutable(JSON), nullable=False)
    resume = Column(String)
    bloqueado = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    ia = relationship("IA", back_populates="leads", lazy="joined")
