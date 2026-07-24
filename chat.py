from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    question: str

@router.post("/chat")
def chat(request: ChatRequest):
    return {
        "question": request.question,
        "response": "AI module will answer this."
    }