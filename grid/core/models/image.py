from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class GeneratedImage(BaseModel):
    imageID: str = Field(...) # PK
    imagePath: str = Field(...)
    seed: int = Field(...)
    actualParameters: Dict[str, Any] = Field(...) # Map型はDictで表現
    actualPromptPositive: str = Field(...)
    actualPromptNegative: Optional[str] = None
    rating: int = Field(default=0) # 0-5
    eagleItemID: Optional[str] = None
    generationStatus: str = Field(...) # 'pending', 'processing', 'success', 'error'
    errorMessage: Optional[str] = None
    isVibeCandidate: bool = Field(default=False) # 将来拡張だがMVP設計書にあるため含める