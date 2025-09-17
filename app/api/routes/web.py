from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter(tags=["web"])


@router.get("/", response_class=FileResponse)
async def dashboard():
    """Главная страница - Vue.js приложение"""
    return FileResponse("static/index.html")
