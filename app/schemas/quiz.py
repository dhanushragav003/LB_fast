from pydantic import BaseModel

class QuizRequest(BaseModel):
    text:str
    context:str
    size:int 

class summaryrequest(BaseModel):
    video_id:str
    lan:str = "en"