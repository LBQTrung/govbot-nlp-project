from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class Message(BaseModel):
    sender: str
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SentMessage(BaseModel):
    chat_id: str
    content: str

class ProductInformation(BaseModel):
    data: Dict[str, Any]

class ChatBase(BaseModel):
    name: str = ""
    productInformation: dict = {}
    messages: List[Message] = []
    status: str = "active"

class ChatCreate(ChatBase):
    pass

class ChatUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None

class ChatInDB(ChatBase):
    id: str = Field(alias="_id")
    userId: str
    createdAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True 