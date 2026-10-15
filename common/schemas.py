from pydantic import BaseModel, Field


class VulnerabilityPrediction(BaseModel):
    is_vulnerable: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_summary: str