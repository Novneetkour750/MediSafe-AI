from fastapi import APIRouter, Depends

from dependencies import get_medicine_service
from models.schemas import ChatResponse, FollowUpRequest, ChatRequest
from services.medicine_service import MedicineService

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, service: MedicineService = Depends(get_medicine_service)):
    reply = service.answer_chat_question(request.question)
    return ChatResponse(reply=reply)


@router.post("/followup", response_model=ChatResponse)
def followup(request: FollowUpRequest, service: MedicineService = Depends(get_medicine_service)):
    context = request.context.model_dump(exclude_none=True)
    reply = service.answer_followup_question(context, request.question)
    return ChatResponse(reply=reply)
