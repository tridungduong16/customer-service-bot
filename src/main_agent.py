import os
import yaml
import json
from datetime import datetime
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.app_config import app_config
from src.schema.celeb import (
    AgentProfile,
    UserQuestion,
    UserThread,
    ConversationInfor,
    Message,
    MessageResponse,
)
from src.tools import data_scraping, travel
from src.database_handler.qdrant_handler import QdrantHandler

class ReactAgent:
    def __init__(self):
        self.model = ChatOpenAI(model=app_config.MODEL_NAME, temperature=0.9)
        self.llm = self.model
        self.agent = self.create_agent()

    def create_agent(self):
        return create_react_agent(
            self.model,
            tools=self.tools,
            prompt=self.system_prompt,
        )

    def _get_chat_history(self, user_thread: UserThread):
        chat_history = self.memory_handler.retrieve_conversation(user_thread)
        if not chat_history or "messages" not in chat_history:
            return []
        messages = chat_history["messages"]
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages[-6:]
        ]

    def _save_conversation(self, user_thread: UserThread, question: str, answer: str):
        conversation = ConversationInfor(
            user_thread_infor=user_thread,
            messages=[
                Message(role="user", content=question),
                Message(role="assistant", content=answer),
            ],
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        )
        self.memory_handler.insert_or_update_conversation(conversation)


    async def print_stream(self, inputs):
        message = None
        async for s in self.agent.stream(inputs, stream_mode="values"):
            message = s["messages"][-1]
            if isinstance(message, tuple):
                print(message)
            else:
                message.pretty_print()
        return message.content if message else ""

    def process_question(self, user_question: UserQuestion) -> MessageResponse:
        messages = self._get_chat_history(user_question.user_thread)
        messages.append({"role": "user", "content": user_question.question})
        answer = self.print_stream({"messages": messages})
        self._save_conversation(user_question.user_thread, user_question.question, answer)
        return answer



