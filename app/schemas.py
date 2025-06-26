from pydantic import BaseModel
from datetime import date, datetime

class TrendDataBase(BaseModel):
    date: date
    keyword: str
    score: int
    isPartial: bool  

class TrendDataCreate(TrendDataBase):
    pass

class TrendDataResponse(TrendDataBase):
    id: int
    date_queried: datetime

    class Config:
        from_attributes = True 