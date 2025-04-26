from pydantic import BaseModel, Field

class Tag(BaseModel):
    tagName: str = Field(...) # PK, Unique, 'namespace:token'形式推奨