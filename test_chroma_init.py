"""
Тестовый скрипт для проверки инициализации всех векторных БД в OllamaClient
"""
from src.ollama import OllamaClient

if __name__ == "__main__":
    client = OllamaClient()
    print("\nПроверка инициализации векторных БД:")
    if not client.chroma_clients:
        print("❌ Не найдено ни одной векторной БД!")
    else:
        for db_type, db_client in client.chroma_clients.items():
            try:
                collections = db_client.list_collections()
                print(f"✅ {db_type}: найдено {len(collections)} коллекций")
                for coll in collections:
                    print(f"   - {coll.name}")
            except Exception as e:
                print(f"⚠️  Ошибка при доступе к {db_type}: {e}")
