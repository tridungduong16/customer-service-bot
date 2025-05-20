from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class MessageResponse(BaseModel):
    response: str

class InitializeMessageRequest(BaseModel):
    name: str


class UserQuestion(BaseModel):
    question: str

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


class Message(BaseModel):
    role: str
    content: str

