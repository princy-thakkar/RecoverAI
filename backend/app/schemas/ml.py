from pydantic import BaseModel, Field


class RecoveryPredictionRequest(BaseModel):
    amount: float = Field(gt=0)
    previous_attempts: int = Field(default=0, ge=0)
    failed_attempts: int = Field(default=0, ge=0)
    payment_method: str = Field(min_length=1)