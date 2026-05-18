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

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}

import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Путь к скомпилированному фронтенду
frontend_dist_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist")

if os.path.exists(frontend_dist_path):
    # Раздаем папку с ассетами (JS, CSS, картинки)
    assets_path = os.path.join(frontend_dist_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    # Для всех остальных путей отдаем index.html (React Router на клиенте)
    @app.get("/{catchall:path}")
    async def serve_spa(catchall: str):
        # Если запрошен конкретный файл, отдаем его
        file_path = os.path.join(frontend_dist_path, catchall)
        if catchall and os.path.isfile(file_path):
            return FileResponse(file_path)
        # Иначе отдаем index.html для роутинга на стороне клиента (React SPA)
        return FileResponse(os.path.join(frontend_dist_path, "index.html"))
else:
    @app.get("/")
    async def root():
        return {"message": "Welcome to D&D Helper API"}

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug,
    )

