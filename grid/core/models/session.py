from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class GenerationSession(BaseModel):
    sessionID: str = Field(...) # PK, UUIDv7推奨
    name: Optional[str] = None
    timestamp: datetime = Field(...)
    baseParameters: str = Field(...) # JSON文字列として扱う
    basePromptPositive: str = Field(...)
    basePromptNegative: Optional[str] = None
    notes: Optional[str] = None
    overallStatus: str = Field(...) # 'pending', 'running', 'completed', 'partially_failed', 'failed'