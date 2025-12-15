from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal

PHONE_REGEX = r"^\d{10,15}@(s\.whatsapp\.net|lid)$"  # ex.: 5571999999999@s.whatsapp.net

class ApiBaseModel(BaseModel):
    """Base com helpers p/ dump/loads consistentes."""
    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict):
        return cls.model_validate(data)

class Timestamped(ApiBaseModel):
    received_at: datetime = Field(default_factory=datetime.utcnow)

MessageType = Literal[
    "conversation",
    "extendedTextMessage",
    "imageMessage",
    "audioMessage",
    "documentWithCaptionMessage",
]