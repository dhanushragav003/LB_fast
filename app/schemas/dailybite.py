from pydantic import BaseModel
from typing import Optional

class DailyBiteRequest(BaseModel):
    destination:str
    frequency:str
    time:str
    time_zone:str
    payload:dict
    '''
    {
       ulp_id:str,
       email:str,
    }
    '''

class Dailybite(BaseModel):
    send_to:str="gmail"
    payload:dict
    # {"email": "dhanushragav003@gmail.com", "ulp_id": 12, "url": "http://localhost:8000", "user_id": 28}


