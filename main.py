from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from app.core.config.settings import settings
from app.api.routes import users, onec, web
from app.infrastructure.database.database import init_db
from app.core.logging.logger import log_application_startup, unified_logger
from app.core.middleware.logging_middleware import LoggingMiddleware

app = FastAPI(title="User Management System", version="1.0.0")

log_application_startup()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(onec.router, prefix="/api/onec", tags=["onec"])
app.include_router(web.router, tags=["web"])


app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")

@app.on_event("startup")
async def startup_event():
    """Событие запуска приложения"""
    await init_db()
    unified_logger.app_logger.info("База данных инициализирована успешно")
    unified_logger.app_logger.info("Приложение User Management System запущено")
    unified_logger.app_logger.info(f"Домен: {settings.domain}")
    unified_logger.app_logger.info(f"API Base URL: {settings.api_base_url}")

@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {"status": "healthy", "timestamp": "2025-08-25T13:00:00Z"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None  
    )
