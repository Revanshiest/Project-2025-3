from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import uuid4

from backend.ai.rag_orchestrator import RAGOrchestrator
from backend.api.dependencies import get_rag_orchestrator, get_chat_repo
from backend.repositories.chat_repository import ChatRepository

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])

class AIQueryRequest(BaseModel):
    question: str
    section_name: str = ""
    section_content: str = ""
    user_id: int = 1
    chat_id: Optional[str] = None

@router.get("/chats/{user_id}")
def get_user_chats(
    user_id: int,
    chat_repo: ChatRepository = Depends(get_chat_repo)
):
    """
    Получить все сохраненные сессии чатов для пользователя.
    """
    return chat_repo.get_by_user(user_id)

@router.get("/chats/{user_id}/{chat_id}")
def get_chat_session(
    user_id: int,
    chat_id: str,
    chat_repo: ChatRepository = Depends(get_chat_repo)
):
    """
    Получить конкретную сессию чата по ID.
    """
    session = chat_repo.get_by_id(user_id, chat_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия чата не найдена")
    return session

@router.post("/ask")
def ask_ai(
    request: AIQueryRequest,
    orchestrator: RAGOrchestrator = Depends(get_rag_orchestrator),
    chat_repo: ChatRepository = Depends(get_chat_repo)
):
    """
    Задать вопрос ИИ-помощнику. 
    Использует RAGOrchestrator (чистую архитектуру) для поиска информации и генерации.
    Также сохраняет историю запросов в ChatRepository.
    """
    # Вычисляем или создаем chat_id
    chat_id = request.chat_id
    if not chat_id:
        chat_id = f"chat_{uuid4().hex[:12]}"
        
    # Загружаем существующую сессию или создаем новую
    existing_session = chat_repo.get_by_id(request.user_id, chat_id)
    messages = existing_session.get("messages", []) if existing_session else []
    title = existing_session.get("title", request.question[:30] + "...") if existing_session else (request.question[:30] + "...")
    
    # Добавляем сообщение пользователя
    user_msg_id = f"msg_{uuid4().hex[:8]}"
    now = datetime.now().isoformat()
    messages.append({
        "id": user_msg_id,
        "sender": "user",
        "content": request.question,
        "timestamp": now
    })
    
    # Генерируем ответ
    answer = orchestrator.generate_response(
        user_message=request.question,
        section_name=request.section_name,
        section_content=request.section_content
    )
    
    if not answer:
        raise HTTPException(status_code=500, detail="Ошибка генерации ответа")
        
    # Добавляем ответ ассистента
    assistant_msg_id = f"msg_{uuid4().hex[:8]}"
    messages.append({
        "id": assistant_msg_id,
        "sender": "assistant",
        "content": answer,
        "timestamp": datetime.now().isoformat()
    })
    
    # Сохраняем сессию
    chat_repo.save_chat_session(
        user_id=request.user_id,
        chat_id=chat_id,
        title=title,
        messages=messages,
        is_active=True
    )
    
    return {
        "answer": answer,
        "chat_id": chat_id,
        "title": title
    }
