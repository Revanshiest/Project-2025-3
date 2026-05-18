from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn 
from backend.api.routers import reference, characters, ai
from backend.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_title,
    description="Backend API for D&D Helper Application",
    version=settings.app_version
)

# Настройка CORS (Cross-Origin Resource Sharing)
# Это механизм безопасности браузеров. Если фронтенд запущен на одном домене (например, my-dnd-front.com),
# а бекенд на другом (api-dnd.com), браузер заблокирует запросы, если мы явно не разрешим этот домен здесь.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

app.include_router(reference.router)
app.include_router(characters.router)
app.include_router(ai.router)

@app.get("/")
async def root():
    return {"message": "Welcome to D&D Helper API"}

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug,
    )

