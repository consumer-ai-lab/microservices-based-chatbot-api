from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from .redis_manager import get_redis_manager, Message, MessageRole
from .chat_summary_manager import get_chat_summary_manager, Model, Query
from pydantic import BaseModel

app = FastAPI(root_path="/api/chat")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ApiQuery(BaseModel):
    user_id: str
    thread_id: str
    model: Model
    question: str

    def id(self) -> str:
        return f"{self.user_id}/{self.thread_id}"

class QaQuery(BaseModel):
    model: Model
    question: str
    summary: str

@app.get("/")
def root():
    return {"message": "hello from query_preprocessing_service"}


@app.post("/generate")
def get_ai_message(query: ApiQuery):
    chat_manager = get_redis_manager(query.id())
    chat_history = chat_manager.get_messages()
    summary_manager = get_chat_summary_manager(query.model, temperature=0.2)

    summary = summary_manager.summarize_chats(
        history=chat_history
    )

    qa_query = QaQuery(**(query.dict() | {"summary": summary}))
    if not summary_manager.check_if_fine(qa_query):
        return { "error": "not related to medical stuff" }

    try:
        response = requests.post(
            "http://qa-service:8000/get-ai-response", json=qa_query.dict()
        )
        response.raise_for_status()
        ai_response = response.json()
    except requests.exceptions.RequestException as e:
        chat_manager.add_message(Message(role=MessageRole.user, content=query.question))
        return {"error": f"Request to qa_service failed: {e}"}
    else:
        chat_manager.add_message(Message(role=MessageRole.user, content=query.question))
        chat_manager.add_message(Message(role=MessageRole.assistant, content=ai_response.get("ai_response")))
        return {"ai_response": ai_response.get("ai_response")}
