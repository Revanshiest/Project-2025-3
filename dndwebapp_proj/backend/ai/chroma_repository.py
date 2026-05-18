import logging
import chromadb
from pathlib import Path
from typing import List, Dict, Optional
from backend.ai.interfaces import VectorRepository, EmbeddingService
from backend.ai.ollama_client import OllamaEmbeddingFunction

logger = logging.getLogger(__name__)


class ChromaVectorRepository(VectorRepository):
    """
    Реализация векторного репозитория для работы с ChromaDB.
    Взаимодействует с базой данных и выполняет запросы поиска (Single Responsibility).
    """
    def __init__(
        self,
        db_path: str,
        embedding_service: EmbeddingService,
        preferred_collections: Optional[Dict[str, str]] = None,
    ):
        self.db_path = Path(db_path)
        self.embedding_service = embedding_service
        # Маппинг section_type -> preferred_collection_name (OCP)
        self.preferred_collections = preferred_collections or {
            "races": "dnd_races",
        }
        self.chroma_clients: Dict[str, chromadb.PersistentClient] = {}
        self._init_chroma_clients()

    def _init_chroma_clients(self) -> None:
        """Автоматически инициализирует все найденные Chroma PersistentClient в VectorDB"""
        if not self.db_path.exists():
            logger.warning("Папка VectorDB не найдена: %s", self.db_path)
            return
        for subdir in self.db_path.iterdir():
            if subdir.is_dir() and (subdir / "chroma.sqlite3").exists():
                try:
                    db_name = subdir.name.replace("chroma_", "")
                    self.chroma_clients[db_name] = chromadb.PersistentClient(path=str(subdir))
                    logger.info("Найдена векторная БД: %s -> %s", db_name, subdir)
                except Exception as e:
                    logger.error(
                        "Ошибка инициализации Chroma клиента %s: %s", subdir.name, e
                    )

    def list_clients(self) -> List[str]:
        return list(self.chroma_clients.keys())

    def _find_collection(
        self, db_client: chromadb.PersistentClient, section_type: str
    ) -> Optional[chromadb.Collection]:
        """
        Находит подходящую коллекцию в клиенте ChromaDB.
        Сначала проверяет preferred_collections (конфигурируемый маппинг),
        затем fallback на первую доступную коллекцию.
        """
        collections = db_client.list_collections()

        # Проверяем приоритетную коллекцию из маппинга (OCP)
        preferred_name = self.preferred_collections.get(section_type)
        if preferred_name:
            for coll in collections:
                if coll.name == preferred_name:
                    try:
                        collection = db_client.get_collection(name=preferred_name)
                        logger.debug(
                            "Используем приоритетную коллекцию '%s' для '%s'",
                            preferred_name, section_type,
                        )
                        return collection
                    except Exception:
                        continue

        # Fallback — первая доступная коллекция
        for coll in collections:
            try:
                collection = db_client.get_collection(name=coll.name)
                logger.debug(
                    "Используем коллекцию '%s' для '%s'", coll.name, section_type
                )
                return collection
            except Exception:
                continue

        return None

    def _execute_query(
        self,
        collection: chromadb.Collection,
        query: str,
        query_embedding: List[float],
        section_type: str,
    ) -> str:
        """Выполняет запрос к коллекции и формирует контекст."""
        count = 0
        try:
            count = collection.count()
            logger.debug("Коллекция '%s': %d документов", section_type, count)
            if count == 0:
                logger.warning("Коллекция '%s' пустая", section_type)
                return ""
        except Exception as e:
            logger.warning("Не удалось проверить количество документов: %s", e)

        n_results = min(5, count) if count > 0 else 5

        results = None
        try:
            results = collection.query(query_texts=[query], n_results=n_results)
        except Exception as e1:
            try:
                results = collection.query(
                    query_embeddings=[query_embedding], n_results=n_results
                )
            except Exception as e2:
                logger.error("Ошибка при запросе к коллекции: %s, %s", e1, e2)
                return ""

        if results and results.get("documents") and len(results["documents"]) > 0:
            context_parts = [doc for doc in results["documents"][0] if doc]
            rag_context = "\n\n---\n\n".join(context_parts)
            logger.debug(
                "RAG контекст для '%s' (запрос: '%s'): найдено %d документов",
                section_type, query, len(context_parts),
            )
            return rag_context

        logger.warning(
            "RAG не нашёл документы для '%s' (запрос: '%s')", section_type, query
        )
        return ""

    def retrieve_context(
        self, 
        query: str, 
        section_type: str, 
        query_embedding: List[float]
    ) -> str:
        try:
            db_client = self.chroma_clients.get(section_type)
            if not db_client:
                logger.warning("Нет клиента для типа: %s", section_type)
                return ""

            collection = self._find_collection(db_client, section_type)
            if not collection:
                logger.warning("Нет коллекций в БД %s", section_type)
                return ""

            return self._execute_query(
                collection, query, query_embedding, section_type
            )
        except Exception as e:
            logger.error("Ошибка при поиске в Chroma: %s", e)
            return ""
