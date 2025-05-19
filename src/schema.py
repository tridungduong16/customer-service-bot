from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class MessageResponse(BaseModel):
    response: str

class InitializeMessageRequest(BaseModel):
    name: str


class AskResponse(BaseModel):
    response: str
    response_time: str


class AgentIdRequest(BaseModel):
    agent_id: int


class InitializeResponse(BaseModel):
    status: str
    message: str
    is_new: bool


class AgentNameRequest(BaseModel):
    agent_name: str


class UserThread(BaseModel):
    user_id: str
    thread_id: Optional[str]


class Message(BaseModel):
    role: str
    content: str


class UserThread(BaseModel):
    user_id: str
    thread_id: Optional[str] = "1234"
    agent_name: Optional[str] = "MISS CHINA AI"


class ConversationInfor(BaseModel):
    user_thread_infor: UserThread
    messages: List[Message]
    created_at: Optional[str] = None

