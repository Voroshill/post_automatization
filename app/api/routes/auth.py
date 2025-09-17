from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from typing import Optional
from app.core.config.settings import settings
from app.core.logging.logger import api_logger
from app.api.schemas.user_schemas import (
    LoginRequest, LoginResponse, AuthConfigResponse, AuthVerifyResponse
)
import hashlib
import secrets
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["authentication"])

active_sessions = {}


def generate_session_token() -> str:
    """Генерация токена сессии"""
    return secrets.token_urlsafe(32)


def hash_password(password: str) -> str:
    """Хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Проверка пароля"""
    return hash_password(password) == hashed


def get_session_token(request: Request) -> Optional[str]:
    """Получение токена сессии из cookies"""
    return request.cookies.get("session_token")


def verify_session(session_token: str) -> bool:
    """Проверка валидности сессии"""
    if not session_token:
        return False
    
    session_data = active_sessions.get(session_token)
    if not session_data:
        return False
    
    if datetime.now() > session_data["expires_at"]:
        del active_sessions[session_token]
        return False
    
    return True


@router.get("/config", response_model=AuthConfigResponse)
async def get_auth_config():
    """Получение конфигурации аутентификации"""
    try:
        api_logger.info("Запрос конфигурации аутентификации")
        
        return AuthConfigResponse(
            auth_enabled=True,
            login_url="/api/users/auth/login"
        )
    except Exception as e:
        api_logger.error(f"Ошибка получения конфигурации аутентификации: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сервера")


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, request: Request):
    """Вход в систему"""
    try:
        api_logger.info(f"Попытка входа пользователя: {login_data.username}")
        
        if (login_data.username == settings.admin_username and 
            login_data.password == settings.admin_password):
            
            session_token = generate_session_token()

            active_sessions[session_token] = {
                "username": login_data.username,
                "role": "admin",
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(hours=24)
            }
            
            response = JSONResponse(
                content=LoginResponse(
                    success=True,
                    message="Вход выполнен успешно",
                    user={
                        "username": login_data.username,
                        "role": "admin"
                    }
                ).dict()
            )
            

            response.set_cookie(
                key="session_token",
                value=session_token,
                httponly=True,
                secure=False,  
                samesite="lax",
                max_age=86400 
            )
            
            api_logger.info(f"Пользователь {login_data.username} успешно вошел в систему")
            return response
            
        else:
            api_logger.warning(f"Неудачная попытка входа: {login_data.username}")
            raise HTTPException(
                status_code=401,
                detail="Неверные учетные данные"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Ошибка входа в систему: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сервера")


@router.post("/logout")
async def logout(request: Request):
    """Выход из системы"""
    try:
        session_token = get_session_token(request)
        
        if session_token and session_token in active_sessions:
            del active_sessions[session_token]
            api_logger.info("Пользователь вышел из системы")
        
        response = JSONResponse(
            content={"success": True, "message": "Выход выполнен успешно"}
        )
        
        response.delete_cookie(key="session_token")
        
        return response
        
    except Exception as e:
        api_logger.error(f"Ошибка выхода из системы: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сервера")


@router.get("/verify", response_model=AuthVerifyResponse)
async def verify_auth(request: Request):
    """Проверка аутентификации"""
    try:
        session_token = get_session_token(request)
        
        if verify_session(session_token):
            session_data = active_sessions[session_token]
            return AuthVerifyResponse(
                authenticated=True,
                user={
                    "username": session_data["username"],
                    "role": session_data["role"]
                }
            )
        else:
            return AuthVerifyResponse(authenticated=False)
            
    except Exception as e:
        api_logger.error(f"Ошибка проверки аутентификации: {e}")
        return AuthVerifyResponse(authenticated=False)


def require_auth(request: Request):
    """Зависимость для проверки аутентификации"""
    session_token = get_session_token(request)
    
    if not verify_session(session_token):
        raise HTTPException(
            status_code=401,
            detail="Требуется аутентификация"
        )
    
    return active_sessions[session_token]


__all__ = ["router", "require_auth"]
