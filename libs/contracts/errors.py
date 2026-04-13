from pydantic import BaseModel
from typing import Optional

class ErrorDetail(BaseModel):
    error_type: str 
    message: str
    traceback: Optional[str] = None
    is_recoverable: bool = True
