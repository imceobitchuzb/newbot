from typing import Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str = "SAT MASTER API"
    version: str = "0.1.0"
    database: Optional[str] = None
