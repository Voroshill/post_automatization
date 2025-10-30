from typing import List, Union
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.infrastructure.database.database import get_db
from app.infrastructure.database.user_repository_impl import SQLAlchemyUserRepository
from app.domain.services.user_service import UserService
from app.api.schemas.user_schemas import UserCreateRequest, UserResponse
from app.domain.entities.user import UserStatus
from datetime import datetime
from app.core.config.settings import settings
from app.core.logging.logger import api_logger
from pydantic import BaseModel

router = APIRouter(prefix="/oneC", tags=["1C Integration"])


class OneCUserData(BaseModel):
    """Схема для данных пользователя от 1C"""
    unique: str
    firstname: str
    secondname: str
    thirdname: str = None
    company: str
    Department: str
    Otdel: str
    appointment: str
    WorkPhone: str = None
    current_location_id: str
    boss_id: str = None
    BirthDate: str = None
    object_date_vihod: str = None
    dismissal_date: str = None
    worktype_id: str = None
    is_engeneer: int = None
    o_id: str = None
    UploadDate: str
    status: str = "Работает"


class ErrorResponse(BaseModel):
    """Схема для ответа с ошибкой"""
    success: bool = False
    error_type: str
    message: str
    details: str = None


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    repository = SQLAlchemyUserRepository(db)
    return UserService(repository)


@router.post("/receive")
async def receive_user_data(
    data: Union[OneCUserData, List[OneCUserData]],
    db: Session = Depends(get_db)
):
    """
    Получение данных пользователя или массива пользователей от 1C
    """
    try:
        api_logger.info("Получен запрос от 1C")
        
        repository = SQLAlchemyUserRepository(db)
        user_service = UserService(repository)
        
        def transform_1c_data(user_data):
            """Преобразует данные от 1C в формат нашей БД"""
            return {
                "unique_id": user_data.unique,
                "firstname": user_data.firstname,
                "secondname": user_data.secondname,
                "thirdname": user_data.thirdname,
                "company": user_data.company,
                "department": user_data.Department,
                "otdel": user_data.Otdel,
                "appointment": user_data.appointment,
                "work_phone": user_data.WorkPhone,
                "current_location_id": user_data.current_location_id,
                "boss_id": user_data.boss_id,
                "birth_date": user_data.BirthDate,
                "object_date_vihod": user_data.object_date_vihod,
                "dismissal_date": user_data.dismissal_date,
                "worktype_id": user_data.worktype_id,
                "is_engineer": user_data.is_engeneer,
                "o_id": user_data.o_id,
                "upload_date": datetime.fromisoformat(user_data.UploadDate.replace('Z', '+00:00')) if user_data.UploadDate else datetime.now(),
                "status": UserStatus.PENDING if user_data.status == 'Работает' else UserStatus.DISMISSED if user_data.status == 'Уволен' else UserStatus.PENDING
            }
        
        if isinstance(data, list):
            api_logger.info(f"Получен массив из {len(data)} пользователей от 1C")
            
            created_users = []
            failed_users = []
            
            for i, user_data in enumerate(data):
                try:
                    transformed_data = transform_1c_data(user_data)
                    user = await user_service.create_user(transformed_data)
                    created_users.append({
                        "unique_id": user.unique_id,
                        "user_id": user.id,
                        "status": "created"
                    })
                    api_logger.info(f"Пользователь {i+1}/{len(data)} создан: {user.unique_id}")
                    
                except IntegrityError as e:
                    if "UNIQUE constraint failed: users.unique_id" in str(e):
                        error_msg = f"Сотрудник с табельным номером {user_data.unique} уже существует в системе"
                    else:
                        error_msg = f"Ошибка данных для сотрудника {user_data.unique}: некорректная информация"
                    
                    failed_users.append({
                        "unique_id": user_data.unique,
                        "error": error_msg,
                        "status": "failed"
                    })
                    api_logger.warning(f"Пользователь {i+1}/{len(data)} уже существует: {user_data.unique}")
                    
                except Exception as e:
                    failed_users.append({
                        "unique_id": user_data.unique,
                        "error": f"Ошибка создания сотрудника {user_data.unique}: {str(e)}",
                        "status": "failed"
                    })
                    api_logger.error(f"Ошибка создания пользователя {i+1}/{len(data)}: {e}")
            
            api_logger.info(f"Batch обработка завершена: {len(created_users)} создано, {len(failed_users)} ошибок")
            
            return {
                "success": True,
                "message": f"Обработка завершена: {len(created_users)} создано, {len(failed_users)} ошибок",
                "total_received": len(data),
                "created": len(created_users),
                "failed": len(failed_users),
                "created_users": created_users,
                "failed_users": failed_users
            }
            
        else:
            api_logger.info(f"Получены данные пользователя: {data.unique}")
            
            try:
                transformed_data = transform_1c_data(data)
                user = await user_service.create_user(transformed_data)
                
                api_logger.info(f"Пользователь успешно создан от 1C: {user.id}")
                
                return {
                    "success": True,
                    "message": "Сотрудник успешно добавлен в систему",
                    "user_id": user.id
                }
                
            except IntegrityError as e:
                if "UNIQUE constraint failed: users.unique_id" in str(e):
                    error_msg = f"Сотрудник с табельным номером {data.unique} уже существует в системе"
                else:
                    error_msg = f"Ошибка данных: некорректная информация о сотруднике"
                
                api_logger.warning(f"Пользователь уже существует: {data.unique}")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "error_type": "duplicate_user",
                        "message": error_msg,
                        "details": f"Попробуйте использовать другой табельный номер или обновите существующую запись"
                    }
                )
        
    except HTTPException:
        raise
    except IntegrityError as e:
        api_logger.error(f"Ошибка целостности данных от 1C: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error_type": "integrity_error",
                "message": "Ошибка данных: некорректная информация о сотруднике",
                "details": "Проверьте правильность всех обязательных полей"
            }
        )
    except Exception as e:
        # Проверяем, не является ли это IntegrityError
        if "UNIQUE constraint failed" in str(e) or "IntegrityError" in str(e):
            api_logger.error(f"Ошибка целостности данных от 1C: {e}")
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error_type": "integrity_error",
                    "message": "Ошибка данных: некорректная информация о сотруднике",
                    "details": "Проверьте правильность всех обязательных полей"
                }
            )
        else:
            api_logger.error(f"Ошибка получения данных от 1C: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error_type": "server_error",
                    "message": "Внутренняя ошибка сервера",
                    "details": "Попробуйте повторить операцию позже"
                }
            )


@router.get("/status")
async def get_integration_status():
    """
    Проверка статуса интеграции с 1C
    """
    try:
        api_logger.info("Запрос статуса интеграции с 1C")
        
        status = {
            "success": True,
            "status": "active",
            "endpoint": settings.onec_endpoint,
            "allowed_origins": settings.onec_allowed_origins,
            "message": "1C интеграция работает"
        }
        
        api_logger.info("Статус интеграции с 1C: активен")
        return status
        
    except Exception as e:
        api_logger.error(f"Ошибка получения статуса интеграции с 1C: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "server_error",
                "message": "Ошибка получения статуса интеграции",
                "details": str(e)
            }
        )
