from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ParameterSet(BaseModel):
    setID: str = Field(...) # PK
    name: str = Field(...)
    description: Optional[str] = None
    parameters: str = Field(...) # JSON文字列として扱う
    createdAt: datetime = Field(...)