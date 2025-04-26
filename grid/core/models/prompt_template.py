from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class PromptTemplate(BaseModel):
    templateID: str = Field(...) # PK
    name: str = Field(...)
    description: Optional[str] = None
    contentPositive: str = Field(...)
    contentNegative: Optional[str] = None
    createdAt: datetime = Field(...)