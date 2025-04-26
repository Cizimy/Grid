from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class User(BaseModel):
    userID: str = Field(...) # PK
    username: Optional[str] = None
    createdAt: datetime = Field(...)