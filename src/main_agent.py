from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from src.app_config import app_config
from src.schema import (
    UserQuestion,
    MessageResponse,
)
from src.database_handler.qdrant_handler import QdrantHandler
from src.prompt import SYSEM_PROMPT
class ReactAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model=app_config.MODEL_NAME, temperature=0.9)
        self.qdrant_db = QdrantHandler()
        self.qdrant_db.connect_to_database()
        self.tools = [self.qdrant_db.search_similar_texts]
        self.agent = self.create_agent()

    def create_agent(self):
        return create_react_agent(
            self.llm,
            tools=self.tools,
            prompt=SYSEM_PROMPT,
        )

    def print_stream(self, inputs):
        message = None
        for s in self.agent.stream(inputs, stream_mode="values"):
            message = s["messages"][-1]
            if isinstance(message, tuple):
                print(message)
            else:
                message.pretty_print()
        return message.content if message else ""

    def process_question(self, user_question: UserQuestion) -> MessageResponse:
        messages = [{"role": "user", "content": user_question.question}]
        answer = self.print_stream({"messages": messages})
        return answer



# agent = ReactAgent()
# question = "What’s the heaviest load you’ll need to lift?"
# question = UserQuestion(question=question)
# print(agent.process_question(question))

