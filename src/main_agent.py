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
from src.prompts.general import GENERAL_AGENT_SYSTEM_PROMPT
from src.prompts.gama import CREATE_CONTENT_GAMA_PROMPT
from src.prompts.cz import CZ_PROMPT
from src.schema.celeb import (
    AgentProfile,
    UserQuestion,
    UserThread,
    ConversationInfor,
    Message,
    MessageResponse,
)
# from src.tools.image_processing import ImageProcessingAgent
from src.utils import load_agent_api_key, get_account_id_from_twitter_url
from src.tools import data_scraping, travel
from src.database_handler.qdrant_handler import QdrantHandler
from src.tools.content import ContentCreator
from src.tools.twitter import TwitterXMediaClient
from src.tools.mcp_tool import CallMCP


class ReactAgent:
    def __init__(self, name, database_handler, memory_handler, mcp_config_path=None):
        self.name = name
        self.database_handler = database_handler
        self.memory_handler = memory_handler
        self.mcp_config_path = mcp_config_path

        self.agent_profile = None
        self.account_id = None
        self.content_creator = None
        self.image_processing_agent = None
        self.qdrant = None
        self.twitter_api = None

        self.tools = None
        self.system_prompt = None
        self.model = None
        self.agent = None
        self.llm = None
        self.question = None

    async def async_init(self):
        await self._load_agent_profile()
        self.system_prompt = self.format_system_prompt()
        self.tools = await self.initialize_tools()
        self.model = ChatOpenAI(model=app_config.MODEL_NAME, temperature=0.9)
        self.llm = self.model
        self.agent = self.create_agent()

    async def _load_agent_profile(self):
        if self.name == "Changpeng Zhao AI":
            self.qdrant = QdrantHandler()
            self.qdrant.connect_to_database()
            self.collection_name = "cz_memory"
            self.twitter_api = TwitterXMediaClient(
                client_id=app_config.CZ_X_CLIENT_ID,
                client_secret=app_config.CZ_X_CLIENT_SECRET,
                consumer_key=app_config.CZ_X_API_KEY,
                consumer_secret=app_config.CZ_X_API_SECRET_KEY,
                access_token=app_config.CZ_X_ACCESS_TOKEN,
                access_token_secret=app_config.CZ_X_ACCESS_TOKEN_SECRET,
            )
        elif self.name == "GAMA AI":
            self.twitter_api = TwitterXMediaClient(
                client_id=app_config.GAMA_X_CLIENT_ID,
                client_secret=app_config.GAMA_X_CLIENT_SECRET,
                consumer_key=app_config.GAMA_X_API_KEY,
                consumer_secret=app_config.GAMA_X_API_SECRET_KEY,
                access_token=app_config.GAMA_X_ACCESS_TOKEN,
                access_token_secret=app_config.GAMA_X_ACCESS_TOKEN_SECRET,
            )
        elif self.name == "ARNOLD AI":
            self.twitter_api = TwitterXMediaClient(
                client_id=app_config.ARNOLD_X_CLIENT_ID,
                client_secret=app_config.ARNOLD_X_CLIENT_SECRET,
                consumer_key=app_config.ARNOLD_X_API_KEY,
                consumer_secret=app_config.ARNOLD_X_API_SECRET_KEY,
                access_token=app_config.ARNOLD_X_ACCESS_TOKEN,
                access_token_secret=app_config.ARNOLD_X_ACCESS_TOKEN_SECRET,
            )
        elif self.name == "CASANOVA AI":
            self.twitter_api = TwitterXMediaClient(
                client_id=app_config.CASANOVA_X_CLIENT_ID,
                client_secret=app_config.CASANOVA_X_CLIENT_SECRET,
                consumer_key=app_config.CASANOVA_X_API_KEY,
                consumer_secret=app_config.CASANOVA_X_API_SECRET_KEY,
                access_token=app_config.CASANOVA_X_ACCESS_TOKEN,
                access_token_secret=app_config.CASANOVA_X_ACCESS_TOKEN_SECRET,
            )

        # self.image_processing_agent = ImageProcessingAgent()

        raw_profile = self.database_handler.get_one_agent_profile(app_config.TABLE_NAME, self.name)
        self.agent_profile = AgentProfile(**self.database_handler.unflatten_agent_profile(raw_profile))
        self.account_id = get_account_id_from_twitter_url(self.agent_profile.social.twitter)
        self.content_creator = ContentCreator(self.agent_profile.identity.agentName)

    def format_system_prompt(self):
        if self.agent_profile.identity.agentName == "Changpeng Zhao AI":
            return CZ_PROMPT

        identity = self.agent_profile.identity
        behavior = self.agent_profile.behavior
        rules = " ".join(self.agent_profile.rules)

        return GENERAL_AGENT_SYSTEM_PROMPT.format(
            name=identity.agentName,
            bio=identity.bio,
            lore=identity.lore,
            topic=behavior.topic,
            personality_traits=", ".join(behavior.personality_traits),
            formal_casual=behavior.communication_style.formal_casual,
            serious_humorous=behavior.communication_style.serious_humorous,
            concise_detailed=behavior.communication_style.concise_detailed,
            neutral_opinionated=behavior.communication_style.neutral_opinionated,
            rules=rules,
        )

    async def initialize_tools(self):
        tools = []

        if self.mcp_config_path:
            try:
                print(self.mcp_config_path)
                mcp_client = CallMCP(self.mcp_config_path)
                mcp_tools = await mcp_client.get_tools()
                tools.extend(mcp_tools)
            except Exception as e:
                print(f"⚠️ Failed to load MCP tools: {e}")

        name = self.agent_profile.identity.agentName
        if name == "Changpeng Zhao AI":
            tools += [
                data_scraping.tool,
                self.qdrant.search_similar_texts,
                self.content_creator.cz_create_content,
                self.twitter_api.upload_png,
                self.twitter_api.create_tweet_with_media,
            ]
        elif name == "GAMA AI":
            tools += [
                self.content_creator.create_travel_content,
                data_scraping.tool,
                travel.TravelHotelSearch.search_hotels,
                travel.TravelHotelSearch.search_flights,
                self.twitter_api.upload_png,
                self.twitter_api.create_tweet_with_media,
            ]
        elif name == "ARNOLD AI":
            tools += [
                self.content_creator.arnold_create_content,
                data_scraping.tool,
                self.twitter_api.upload_png,
                self.twitter_api.create_tweet_with_media,
            ]
        elif name == "CASANOVA AI":
            tools += [
                self.content_creator.casanova_create_content,
                data_scraping.tool,
                self.twitter_api.upload_png,
                self.twitter_api.create_tweet_with_media,
            ]
        elif name == "MISS CHINA AI":
            tools += [
                # self.image_processing_agent.skin_analysis_image,
                self.content_creator.general_create_content,
                data_scraping.tool,
            ]
        else:
            tools += [data_scraping.tool]

        return tools

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
        async for s in self.agent.astream(inputs, stream_mode="values"):
            message = s["messages"][-1]
            if isinstance(message, tuple):
                print(message)
            else:
                message.pretty_print()
        return message.content if message else ""


    async def process_question(self, user_question: UserQuestion) -> MessageResponse:
        self.question = user_question.question

        # If this is a sync method, remove await
        messages = self._get_chat_history(user_question.user_thread)
        messages.append({"role": "user", "content": user_question.question})

        # Use the async version of print_stream
        answer = await self.print_stream({"messages": messages})

        # If this is a sync method, remove await
        self._save_conversation(user_question.user_thread, user_question.question, answer)

        return answer


    # async def process_question(self, user_question: UserQuestion) -> MessageResponse:
    #     self.question = user_question.question
        
    #     # Get chat history (update to async if needed)
    #     messages = self._get_chat_history(user_question.user_thread)
    #     messages.append({"role": "user", "content": user_question.question})
        
    #     # Stream response from the LLM
    #     answer_chunks = []
    #     async for chunk in self.llm.astream({"messages": messages}):
    #         answer_chunks.append(chunk.content)  # Assuming chunk has `.content`

    #     full_answer = "".join(answer_chunks)

    #     # Save the full conversation (update to async if needed)
    #     await self._save_conversation(
    #         user_question.user_thread, user_question.question, full_answer
    #     )

    #     return full_answer

        # return MessageResponse(answer=full_answer)

    async def process_question_async(self, user_question: UserQuestion) -> MessageResponse:
        self.question = user_question.question
        messages = self._get_chat_history(user_question.user_thread)
        messages.append({"role": "user", "content": user_question.question})

        result = await self.agent.ainvoke({"messages": messages})
        answer = result['messages'][-1].content

        self._save_conversation(user_question.user_thread, user_question.question, answer)
        return answer



    def process_question_stream(self, user_question: UserQuestion):
        self.question = user_question.question
        messages = self._get_chat_history(user_question.user_thread)
        messages.append({"role": "user", "content": user_question.question})
        for s in self.agent.stream({"messages": messages}, stream_mode="values"):
            message = s["messages"][-1]
            if isinstance(message, HumanMessage):
                yield {"type": "human", "content": message.content}
            elif isinstance(message, AIMessage):
                yield {"type": "ai", "content": message.content, "tool_calls": getattr(message, "tool_calls", None)}
            elif isinstance(message, ToolMessage):
                yield {"type": "tool", "content": message.content, "name": message.name, "tool_calls": getattr(message, "tool_calls", None)}
            else:
                yield {"type": "unknown", "content": str(message)}

        self._save_conversation(user_question.user_thread, user_question.question, message.content)
