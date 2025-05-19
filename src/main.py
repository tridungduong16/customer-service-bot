import json
import sys
import time

import psutil
import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional

from src.agent_manager import AgentManager
from src.agents.create_agent_profile import CreateAgentProfile
from src.agents.main_agent import ReactAgent
from src.app_config import app_config
from src.database_handler.agent_profile import AgentProfileDatabaseHandler
from src.database_handler.mongo_handler import MemoryHandler
from src.schema.celeb import (
    AgentIdRequest,
    AgentNameRequest,
    AgentProfile,
    AskResponse,
    CreatorIdRequest,
    InitializeMessageRequest,
    InitializeResponse,
    PaginatedResponse,
    PaginationRequest,
    TokenContractUpdate,
    UserQuestion,
    ResponseSkinAnalysisAPI,
    SkinAnalysisRequest,
    VerifyAgentInput,
)
from pydantic import BaseModel
from src.schema.celeb import UserThread
from fastapi import Body
from src.routers.analyse_skin import router as analyse_skin_router
from fastapi import Query
from pydantic import BaseModel
from src.schema.celeb import UserThread

class ChatHistoryRequest(BaseModel):
    thread_info: UserThread
    page: int = 1
    page_size: int = 5

app = FastAPI()


@app.get("/")
async def root():
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    return {"message": "AI Agent platform is running v1!", "datetime": current_time}


@app.post("/ask", response_model=AskResponse)
async def ask(request: UserQuestion) -> AskResponse:
    try:
        ans = await agent.process_question(request)
        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        print(ans)
        agent_response = {
            "response": ans,
            "response_time": f"{response_time}s",
        }
        return agent_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_handler.close_connection()
        memory_handler.close_connection()



@app.get("/list_agents")
async def list_agents():
    return {
        "agents": list(agent_manager.agents.keys()),
        "current_agent": agent_manager.current_agent,
    }


@app.on_event("startup")
async def startup_event():
    db_handler.connect_to_database()
    memory_handler.connect_to_database()
    agent = ReactAgent(
        name=name,
        database_handler=db_handler,
        memory_handler=memory_handler,
        mcp_config_path=mcp_config_path  # optional
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7888, reload=True)
