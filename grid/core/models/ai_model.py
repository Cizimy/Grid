from pydantic import BaseModel, Field

class AiModel(BaseModel):
    modelName: str = Field(...) # PK, Unique
    type: str = Field(...) # 'diffusion'など