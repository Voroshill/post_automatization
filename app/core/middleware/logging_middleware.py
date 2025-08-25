import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging.logger import api_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        api_logger.info(f"Запрос: {request.method} {request.url.path} - IP: {request.client.host}")
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        api_logger.info(f"Ответ: {request.method} {request.url.path} - Статус: {response.status_code} - Время: {process_time:.3f}с")
        
        return response
