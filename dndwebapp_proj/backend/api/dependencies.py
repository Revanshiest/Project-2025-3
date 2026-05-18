from backend.core.config import get_settings
from backend.repositories.data_repository import DataRepository
from backend.repositories.character_repository import CharacterRepository
from backend.repositories.chat_repository import ChatRepository
from backend.services.character_service import CharacterService
from backend.services.level_up_service import LevelUpService

# AI Сервисы
from backend.ai.ollama_client import OllamaLLMService, OllamaEmbeddingService
from backend.ai.chroma_repository import ChromaVectorRepository
from backend.ai.rag_orchestrator import RAGOrchestrator

settings = get_settings()

# Глобальные экземпляры сервисов для простоты и переиспользования
data_repo = DataRepository(data_path=settings.data_path)
char_repo = CharacterRepository(data_path=settings.data_path)
chat_repo = ChatRepository(data_path=settings.data_path)

# Сервисы теперь не имеют состояния и зависят только от нужных репозиториев
character_service = CharacterService()
level_up_service = LevelUpService(data_repo=data_repo)

def get_data_repo() -> DataRepository:
    return data_repo

def get_char_repo() -> CharacterRepository:
    return char_repo

def get_chat_repo() -> ChatRepository:
    return chat_repo

def get_character_service() -> CharacterService:
    return character_service
    
def get_level_up_service() -> LevelUpService:
    return level_up_service

# Настройка AI Сервисов (URL и модели из конфига)
llm_service = OllamaLLMService(
    base_url=settings.ollama_host,
    model=settings.ollama_llm_model,
)
embedding_service = OllamaEmbeddingService(
    base_url=settings.ollama_host,
    model=settings.ollama_embedding_model,
)
vector_repo = ChromaVectorRepository(
    db_path=settings.vector_db_path,
    embedding_service=embedding_service,
)

rag_orchestrator = RAGOrchestrator(
    llm_service=llm_service,
    embedding_service=embedding_service,
    vector_repository=vector_repo
)

def get_rag_orchestrator() -> RAGOrchestrator:
    return rag_orchestrator
