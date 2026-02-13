from pydantic import BaseModel, Field
from typing import List, Optional

class BiteEmail(BaseModel):
    email_subject: str
    introduction: str
    core_concept: str
    detailed_explanation: str
    code_example: Optional[str] = None
    code_explanation:  Optional[List[str]]= Field(..., min_length=1)
    key_takeaways: List[str] = Field(..., min_length=1)
    summary: str