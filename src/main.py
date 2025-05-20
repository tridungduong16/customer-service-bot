import json
import sys
import time

import psutil
import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from src.app_config import app_config
from pydantic import BaseModel
from fastapi import Body
from fastapi import Query
from pydantic import BaseModel
from src.main_agent import ReactAgent
from src.schema import UserQuestion, MessageResponse

app = FastAPI()
agent = ReactAgent()
# question = "What’s the heaviest load you’ll need to lift?"
# question = UserQuestion(question=question)
# print(agent.process_question(question))

@app.get("/")
async def root():
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    return {"message": "AI Agent platform is running v1!", "datetime": current_time}


@app.post("/ask")
async def ask(request: UserQuestion):
    try:
        ans = agent.process_question(request)
        agent_response = {
            "response": ans,
        }
        return MessageResponse(**agent_response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7888, reload=True)
