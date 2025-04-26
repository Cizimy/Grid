from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class VibeImage(BaseModel):
    vibeID: str = Field(...) # PK
    imagePath: str = Field(...)
    vibeType: str = Field(...) # 'Generic', 'Parent', 'Child'
    encodedIE: float = Field(...)
    encodedVibePath: str = Field(...)
    notes: Optional[str] = None
    createdAt: datetime = Field(...)