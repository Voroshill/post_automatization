from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.infrastructure.database.database import get_db
from app.infrastructure.database.user_repository_impl import SQLAlchemyUserRepository
from app.domain.services.user_service import UserService
from app.domain.services.export_service import ExportService
from app.api.schemas.user_schemas import (
    UserResponse, UserCreateRequest, CursorPaginatedUsersResponse, CursorPaginationInfo,
    ChangePasswordRequest, ChangePhoneRequest, BlockUserCompleteRequest, 
    AssignManagerRequest, TechnicalUserRequest, AdminResponse, CreateObjectRequest, UpdateTestAttributesRequest
)
from app.domain.entities.user import UserStatus
from app.core.logging.logger import api_logger
from datetime import datetime
import io
from app.core.config.settings import settings

router = APIRouter(tags=["users"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    repository = SQLAlchemyUserRepository(db)
    return UserService(repository)


def get_export_service() -> ExportService:
    return ExportService()


def user_to_response(user) -> UserResponse:
    """Конвертирует User в UserResponse"""
    return UserResponse(
        id=user.id,
        unique_id=user.unique_id,
        firstname=user.firstname,
        secondname=user.secondname,
        thirdname=user.thirdname,
        company=user.company,
        department=user.department,
        otdel=user.otdel,
        appointment=user.appointment,
        mobile_phone=user.mobile_phone,
        work_phone=user.work_phone,
        current_location_id=user.current_location_id,
        boss_id=user.boss_id,
        birth_date=user.birth_date,
        object_date_vihod=user.object_date_vihod,
        dismissal_date=user.dismissal_date,
        worktype_id=user.worktype_id,
        is_engineer=user.is_engineer,
        o_id=user.o_id,
        status=user.status,
        upload_date=user.upload_date or datetime.now(),
        created_at=user.created_at or datetime.now(),
        updated_at=user.updated_at or datetime.now()
    )


@router.post("/manual", response_model=UserResponse)
async def create_user_manually(
    user_data: UserCreateRequest,
    user_service: UserService = Depends(get_user_service)
):
    """
    Ручное создание пользователя администратором
    """
    try:
        api_logger.info(f"Ручное создание пользователя: {user_data.unique}")
        
        user_dict = user_data.model_dump()
        # Разрешаем как PascalCase, так и snake_case ключи из фронтенда
        user_dict["unique_id"] = user_dict.pop("unique", user_dict.get("unique_id"))
        user_dict["department"] = user_dict.pop("Department", user_dict.get("department"))
        user_dict["otdel"] = user_dict.pop("Otdel", user_dict.get("otdel"))
        user_dict["mobile_phone"] = user_dict.pop("MobilePhone", user_dict.get("mobile_phone"))
        user_dict["work_phone"] = user_dict.pop("WorkPhone", user_dict.get("work_phone"))
        user_dict["birth_date"] = user_dict.pop("BirthDate", user_dict.get("birth_date"))
        user_dict["upload_date"] = user_dict.pop("UploadDate", user_dict.get("upload_date"))
        # Принимаем technical/is_engeneer/is_engineer и маппим в is_engineer = 0/1
        raw_technical = user_dict.pop("technical", user_dict.pop("Technical", None))
        is_engeneer_value = user_dict.pop("is_engeneer", user_dict.pop("is_engineer", ''))
        # Нормализуем значение
        normalized = None
        if raw_technical is not None:
            # technical может быть True/False или строкой ('technical','true','1')
            if isinstance(raw_technical, bool):
                normalized = 1 if raw_technical else 0
            elif str(raw_technical).strip().lower() in ['technical', 'true', '1', 'yes']:
                normalized = 1
            elif str(raw_technical).strip().lower() in ['false', '0', 'no', '']:
                normalized = 0
        if normalized is None:
            if is_engeneer_value in ['0', '']:
                normalized = 0
            elif is_engeneer_value == '1':
                normalized = 1
        user_dict["is_engineer"] = normalized if normalized is not None else None
        
        user_dict["status"] = UserStatus.PENDING
        
        user = await user_service.create_user(user_dict)
        
        
        api_logger.info(f"Пользователь {user.id} успешно создан вручную")
        return user_to_response(user)
        
    except IntegrityError as e:
        if "UNIQUE constraint failed: users.unique_id" in str(e):
            error_msg = f"Сотрудник с табельным номером {user_data.unique} уже существует в системе"
        else:
            error_msg = f"Ошибка данных: некорректная информация о сотруднике"
        
        api_logger.error(f"Ошибка ручного создания пользователя: {error_msg}")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error_type": "duplicate_user",
                "message": error_msg,
                "details": "Попробуйте использовать другой табельный номер или обновите существующую запись"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Ошибка ручного создания пользователя: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "server_error",
                "message": "Внутренняя ошибка сервера",
                "details": "Попробуйте повторить операцию позже"
            }
        )


@router.get("/ous", response_model=List[str])
async def get_available_ous(
    user_service: UserService = Depends(get_user_service)
):
    """
    Получение списка доступных организационных единиц (OU) из Active Directory
    """
    try:
        api_logger.info("Запрос списка доступных OU")
        ous = await user_service.ldap_service.list_available_ous()
        api_logger.info(f"Получено {len(ous)} OU")
        return ous
    except Exception as e:
        api_logger.error(f"Ошибка получения списка OU: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "ldap_error",
                "message": "Ошибка получения списка организационных единиц",
                "details": str(e)
            }
        )


@router.get("/pending", response_model=CursorPaginatedUsersResponse)
async def get_pending_users(
    cursor: Optional[str] = Query(None, description="Курсор для пагинации"),
    limit: int = Query(20, ge=1, le=100, description="Количество записей"),
    search: Optional[str] = Query(None, description="Поисковый запрос"),
    total_loaded: int = Query(0, ge=0, description="Общее количество загруженных записей"),
    user_service: UserService = Depends(get_user_service)
):
    try:
        api_logger.info(f"Запрос pending пользователей: cursor={cursor}, limit={limit}, search={search}")
        result = await user_service.get_pending_users_cursor(cursor, limit, search, total_loaded)
        
        users_response = [user_to_response(user) for user in result['users']]
        pagination = CursorPaginationInfo(
            next_cursor=result['next_cursor'],
            has_more=result['has_more'],
            total_loaded=total_loaded + len(users_response),
            total_count=result.get('total_count')
        )
        
        return CursorPaginatedUsersResponse(users=users_response, pagination=pagination)
    except Exception as e:
        api_logger.error(f"Ошибка получения pending пользователей: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "database_error",
                "message": "Ошибка получения данных",
                "details": "Не удалось загрузить список сотрудников. Попробуйте обновить страницу"
            }
        )


@router.get("/dismissed", response_model=CursorPaginatedUsersResponse)
async def get_dismissed_users(
    cursor: Optional[str] = Query(None, description="Курсор для пагинации"),
    limit: int = Query(20, ge=1, le=100, description="Количество записей"),
    search: Optional[str] = Query(None, description="Поисковый запрос"),
    total_loaded: int = Query(0, ge=0, description="Общее количество загруженных записей"),
    user_service: UserService = Depends(get_user_service)
):
    try:
        api_logger.info(f"Запрос dismissed пользователей: cursor={cursor}, limit={limit}, search={search}")
        result = await user_service.get_dismissed_users_cursor(cursor, limit, search, total_loaded)
        
        users_response = [user_to_response(user) for user in result['users']]
        pagination = CursorPaginationInfo(
            next_cursor=result['next_cursor'],
            has_more=result['has_more'],
            total_loaded=total_loaded + len(users_response),
            total_count=result.get('total_count')
        )
        
        return CursorPaginatedUsersResponse(users=users_response, pagination=pagination)
    except Exception as e:
        api_logger.error(f"Ошибка получения dismissed пользователей: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "database_error",
                "message": "Ошибка получения данных",
                "details": "Не удалось загрузить список уволенных сотрудников. Попробуйте обновить страницу"
            }
        )


@router.get("/search", response_model=CursorPaginatedUsersResponse)
async def search_users(
    query: str = Query(..., description="Поисковый запрос"),
    cursor: Optional[str] = Query(None, description="Курсор для пагинации"),
    limit: int = Query(20, ge=1, le=100, description="Количество записей"),
    status: Optional[UserStatus] = Query(None, description="Фильтр по статусу"),
    total_loaded: int = Query(0, ge=0, description="Общее количество загруженных записей"),
    user_service: UserService = Depends(get_user_service)
):
    try:
        api_logger.info(f"Поиск пользователей: query='{query}', cursor={cursor}, limit={limit}, status={status}")
        result = await user_service.search_users_cursor(query, cursor, limit, status, total_loaded)
        
        users_response = [user_to_response(user) for user in result['users']]
        pagination = CursorPaginationInfo(
            next_cursor=result['next_cursor'],
            has_more=result['has_more'],
            total_loaded=total_loaded + len(users_response),
            total_count=result.get('total_count')
        )
        
        return CursorPaginatedUsersResponse(users=users_response, pagination=pagination)
    except Exception as e:
        api_logger.error(f"Ошибка поиска пользователей: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "search_error",
                "message": "Ошибка поиска",
                "details": "Не удалось выполнить поиск. Попробуйте изменить поисковый запрос"
            }
        )


@router.get("/", response_model=CursorPaginatedUsersResponse)
async def get_all_users(
    cursor: Optional[str] = Query(None, description="Курсор для пагинации"),
    limit: int = Query(20, ge=1, le=100, description="Количество записей"),
    search: Optional[str] = Query(None, description="Поисковый запрос"),
    status: Optional[UserStatus] = Query(None, description="Фильтр по статусу"),
    total_loaded: int = Query(0, ge=0, description="Общее количество загруженных записей"),
    user_service: UserService = Depends(get_user_service)
):
    try:
        api_logger.info(f"Запрос всех пользователей: cursor={cursor}, limit={limit}, search={search}, status={status}")
        result = await user_service.get_all_users_cursor(cursor, limit, search, status, total_loaded)
        
        users_response = [user_to_response(user) for user in result['users']]
        pagination = CursorPaginationInfo(
            next_cursor=result['next_cursor'],
            has_more=result['has_more'],
            total_loaded=total_loaded + len(users_response),
            total_count=result.get('total_count')
        )
        
        return CursorPaginatedUsersResponse(users=users_response, pagination=pagination)
    except Exception as e:
        api_logger.error(f"Ошибка получения всех пользователей: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "database_error",
                "message": "Ошибка получения данных",
                "details": "Не удалось загрузить список сотрудников. Попробуйте обновить страницу"
            }
        )


@router.get("/export/xlsx")
async def export_users_to_xlsx(
    status: Optional[UserStatus] = Query(None, description="Фильтр по статусу"),
    search: Optional[str] = Query(None, description="Поисковый запрос"),
    user_service: UserService = Depends(get_user_service),
    export_service: ExportService = Depends(get_export_service)
):
    """
    Экспорт пользователей в XLSX файл
    """
    try:
        api_logger.info(f"Запрос экспорта в XLSX: status={status}, search={search}")
        
        users = await user_service.get_all_users()
        
        if status:
            users = [u for u in users if u.status == status]
            api_logger.info(f"Применен фильтр по статусу: {status}, осталось {len(users)} пользователей")
        
        if search:
            users = [u for u in users if search.lower() in 
                    f"{u.firstname} {u.secondname} {u.thirdname or ''} {u.unique_id}".lower()]
            api_logger.info(f"Применен поисковый фильтр: '{search}', осталось {len(users)} пользователей")
        
        excel_data = export_service.export_users_to_xlsx(users, status.value if status else None)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        status_suffix = f"_{status.value}" if status else ""
        filename = f"users_export{status_suffix}_{timestamp}.xlsx"
        
        api_logger.info(f"Экспорт завершен успешно: {filename}, {len(users)} пользователей")
        
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        api_logger.error(f"Ошибка экспорта в XLSX: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "export_error",
                "message": "Ошибка экспорта",
                "details": "Не удалось создать файл Excel. Попробуйте повторить операцию позже"
            }
        )


@router.put("/{user_id}/approve", response_model=UserResponse)
async def approve_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    try:
        api_logger.info(f"Запрос одобрения пользователя ID: {user_id}")
        
        user = await user_service.user_repository.get_user_by_id(user_id)
        if not user:
            api_logger.warning(f"Пользователь с ID {user_id} не найден")
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error_type": "user_not_found",
                    "message": "Сотрудник не найден",
                    "details": f"Сотрудник с ID {user_id} не существует в системе"
                }
            )
        
        # Устанавливаем статус "В процессе создания"
        await user_service.user_repository.update_status(user_id, UserStatus.CREATING)
        api_logger.info(f"Статус пользователя {user_id} обновлен на CREATING")
        
        # Ждем результат создания учетных записей с таймаутом
        import asyncio
        
        try:
            result = await asyncio.wait_for(
                user_service._execute_creation_scripts(user),
                timeout=45  
            )
            
            if not result["success"]:
                # Откатываем статус при ошибке
                await user_service.user_repository.update_status(user_id, UserStatus.PENDING)
                api_logger.error(f"Ошибка создания учетных записей для пользователя {user_id}: {result.get('stderr', 'Неизвестная ошибка')}")
                
                # Возвращаем ошибку клиенту
                raise HTTPException(
                    status_code=500,
                    detail={
                        "success": False,
                        "error_type": "creation_failed",
                        "message": "Ошибка создания учетных записей",
                        "details": result.get('stderr', 'Не удалось создать учетные записи в Active Directory')
                    }
                )
            else:
                # Успешно создано - переводим в APPROVED
                await user_service.user_repository.update_status(user_id, UserStatus.APPROVED)
                api_logger.info(f"Учетные записи для пользователя {user_id} созданы успешно")
                
        except asyncio.TimeoutError:
            # Таймаут - откатываем статус
            await user_service.user_repository.update_status(user_id, UserStatus.PENDING)
            api_logger.error(f"Таймаут создания учетных записей для пользователя {user_id} (превышено 45 секунд)")
            
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error_type": "timeout",
                    "message": "Таймаут создания учетных записей",
                    "details": "Процесс создания учетных записей занял слишком много времени (более 45 секунд). Попробуйте повторить операцию позже"
                }
            )
        
        api_logger.info(f"Пользователь {user_id} успешно одобрен и создан в AD")
        updated_user = await user_service.user_repository.get_user_by_id(user_id)
        return user_to_response(updated_user)
            
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Ошибка одобрения пользователя {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "approval_error",
                "message": "Ошибка одобрения сотрудника",
                "details": "Не удалось одобрить сотрудника. Попробуйте повторить операцию позже"
            }
        )


@router.get("/{user_id}/status")
async def get_user_status(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """Получение статуса пользователя для отслеживания создания учетных записей"""
    try:
        user = await user_service.user_repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        return {
            "user_id": user_id,
            "status": user.status,
            "message": _get_status_message(user.status)
        }
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Ошибка получения статуса пользователя {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статуса")


def _get_status_message(status: UserStatus) -> str:
    """Получение сообщения для статуса"""
    messages = {
        UserStatus.PENDING: "Ожидает одобрения",
        UserStatus.CREATING: "Создание учетных записей...",
        UserStatus.APPROVED: "Успешно создан",
        UserStatus.REJECTED: "Отклонен",
        UserStatus.DISMISSED: "Уволен"
    }
    return messages.get(status, "Неизвестный статус")


@router.put("/{user_id}/reject", response_model=UserResponse)
async def reject_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    try:
        api_logger.info(f"Запрос отклонения пользователя ID: {user_id}")
        user = await user_service.reject_user(user_id)
        if not user:
            api_logger.warning(f"Пользователь с ID {user_id} не найден")
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error_type": "user_not_found",
                    "message": "Сотрудник не найден",
                    "details": f"Сотрудник с ID {user_id} не существует в системе"
                }
            )
        
        api_logger.info(f"Пользователь {user_id} успешно отклонен")
        return user_to_response(user)
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Ошибка отклонения пользователя {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "rejection_error",
                "message": "Ошибка отклонения сотрудника",
                "details": "Не удалось отклонить сотрудника. Попробуйте повторить операцию позже"
            }
        )


@router.put("/{user_id}/dismiss", response_model=UserResponse)
async def dismiss_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    try:
        api_logger.info(f"Запрос увольнения пользователя ID: {user_id}")
        
        user = await user_service.user_repository.get_user_by_id(user_id)
        if not user:
            api_logger.warning(f"Пользователь с ID {user_id} не найден")
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error_type": "user_not_found",
                    "message": "Сотрудник не найден",
                    "details": f"Сотрудник с ID {user_id} не существует в системе"
                }
            )
        
        await user_service.user_repository.update_status(user_id, UserStatus.DISMISSED)
        api_logger.info(f"Статус пользователя {user_id} обновлен на DISMISSED")
        
        result = await user_service.ldap_service.block_user(user.unique_id)
        
        if result["success"]:
            api_logger.info(f"Пользователь {user_id} успешно уволен и заблокирован в AD")
            updated_user = await user_service.user_repository.get_user_by_id(user_id)
            return user_to_response(updated_user)
        else:
            await user_service.user_repository.update_status(user_id, user.status)
            api_logger.error(f"Ошибка блокировки пользователя {user_id} в AD: {result['stderr']}")
            
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error_type": "ad_block_failed",
                    "message": "Сотрудник уволен, но произошла ошибка при блокировке в Active Directory",
                    "details": f"Ошибка: {result['stderr']}. Попробуйте заблокировать сотрудника вручную в AD или обратитесь к системному администратору"
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Ошибка увольнения пользователя {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "dismissal_error",
                "message": "Ошибка увольнения сотрудника",
                "details": "Не удалось уволить сотрудника. Попробуйте повторить операцию позже"
            }
        )


@router.put("/admin/change-password", response_model=AdminResponse)
async def change_password(
    request: ChangePasswordRequest,
    user_service: UserService = Depends(get_user_service)
):
    """
    Смена пароля пользователя в AD
    """
    try:
        api_logger.info(f"Запрос смены пароля для пользователя: {request.username}")
        
        result = await user_service.change_password(request.username, request.new_password)
        
        api_logger.info(f"Пароль для пользователя {request.username} успешно изменен")
        return AdminResponse(
            success=True,
            message=f"Пароль для пользователя {request.username} успешно изменен",
            details=result
        )
        
    except Exception as e:
        api_logger.error(f"Ошибка смены пароля для пользователя {request.username}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "password_change_error",
                "message": "Ошибка смены пароля",
                "details": f"Не удалось изменить пароль для пользователя {request.username}: {str(e)}"
            }
        )


@router.put("/admin/change-phone", response_model=AdminResponse)
async def change_phone_number(
    request: ChangePhoneRequest,
    user_service: UserService = Depends(get_user_service)
):
    """
    Смена номера телефона пользователя в AD
    """
    try:
        api_logger.info(f"Запрос смены номера телефона для пользователя: {request.pager}")
        
        result = await user_service.change_phone_number(request.pager, request.new_phone)
        
        api_logger.info(f"Номер телефона для пользователя {request.pager} успешно обновлен")
        return AdminResponse(
            success=True,
            message=f"Номер телефона для пользователя {request.pager} успешно обновлен",
            details=result
        )
        
    except Exception as e:
        api_logger.error(f"Ошибка смены номера телефона для пользователя {request.pager}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "phone_change_error",
                "message": "Ошибка смены номера телефона",
                "details": f"Не удалось изменить номер телефона для пользователя {request.pager}: {str(e)}"
            }
        )


@router.post("/admin/export-ad", response_model=AdminResponse)
async def export_users_from_ad(
    user_service: UserService = Depends(get_user_service)
):
    """
    Экспорт всех пользователей из Active Directory
    """
    try:
        api_logger.info("Запрос экспорта пользователей из AD")
        
        result = await user_service.export_users_from_ad()
        
        api_logger.info("Пользователи успешно экспортированы из AD")
        return AdminResponse(
            success=True,
            message="Пользователи успешно экспортированы из Active Directory",
            details=result
        )
        
    except Exception as e:
        api_logger.error(f"Ошибка экспорта пользователей из AD: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "export_error",
                "message": "Ошибка экспорта пользователей",
                "details": f"Не удалось экспортировать пользователей из AD: {str(e)}"
            }
        )


@router.put("/admin/block-complete", response_model=AdminResponse)
async def block_user_complete(
    request: BlockUserCompleteRequest,
    user_service: UserService = Depends(get_user_service)
):
    """
    Полная блокировка пользователя с удалением из групп и перемещением в OU "Уволенные сотрудники"
    """
    try:
        api_logger.info(f"Запрос полной блокировки пользователя: {request.unique_id}")
        
        result = await user_service.block_user_complete(request.unique_id)
        
        api_logger.info(f"Пользователь {request.unique_id} полностью заблокирован")
        return AdminResponse(
            success=True,
            message=f"Пользователь {request.unique_id} полностью заблокирован",
            details=result
        )
        
    except Exception as e:
        api_logger.error(f"Ошибка полной блокировки пользователя {request.unique_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "block_complete_error",
                "message": "Ошибка полной блокировки пользователя",
                "details": f"Не удалось полностью заблокировать пользователя {request.unique_id}: {str(e)}"
            }
        )


@router.put("/admin/assign-manager", response_model=AdminResponse)
async def assign_manager(
    request: AssignManagerRequest,
    user_service: UserService = Depends(get_user_service)
):
    """
    Назначение менеджера для пользователя
    """
    try:
        api_logger.info(f"Запрос назначения менеджера {request.manager_id} для пользователя {request.employee_id}")
        
        result = await user_service.assign_manager(request.employee_id, request.manager_id)
        
        api_logger.info(f"Менеджер {request.manager_id} успешно назначен для пользователя {request.employee_id}")
        return AdminResponse(
            success=True,
            message=f"Менеджер {request.manager_id} успешно назначен для пользователя {request.employee_id}",
            details=result
        )
        
    except Exception as e:
        api_logger.error(f"Ошибка назначения менеджера {request.manager_id} для пользователя {request.employee_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "manager_assignment_error",
                "message": "Ошибка назначения менеджера",
                "details": f"Не удалось назначить менеджера {request.manager_id} для пользователя {request.employee_id}: {str(e)}"
            }
        )


@router.post("/admin/technical", response_model=UserResponse)
async def create_technical_user(
    user_data: TechnicalUserRequest,
    user_service: UserService = Depends(get_user_service)
):
    """
    Создание технического пользователя
    """
    try:
        api_logger.info(f"Запрос создания технического пользователя: {user_data.username}")
        
        user_dict = user_data.model_dump()
        user_dict["unique_id"] = user_dict.pop("username")
        user_dict["firstname"] = user_dict["username"]
        user_dict["secondname"] = "Технический"
        user_dict["thirdname"] = "Пользователь"
        user_dict["company"] = "STI"
        user_dict["department"] = "IT"
        user_dict["otdel"] = "Техподдержка"
        user_dict["appointment"] = user_dict.get("description", "Техническая учетная запись")
        user_dict["current_location_id"] = "1"
        user_dict["status"] = UserStatus.PENDING
        user_dict["upload_date"] = datetime.now()
        
        user = await user_service.create_technical_user(user_dict)
        
        api_logger.info(f"Технический пользователь {user.id} успешно создан")
        return user_to_response(user)
        
    except IntegrityError as e:
        if "UNIQUE constraint failed: users.unique_id" in str(e):
            error_msg = f"Технический пользователь с именем {user_data.username} уже существует"
        else:
            error_msg = f"Ошибка данных: некорректная информация о техническом пользователе"
        
        api_logger.error(f"Ошибка создания технического пользователя: {error_msg}")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error_type": "duplicate_technical_user",
                "message": error_msg,
                "details": "Попробуйте использовать другое имя пользователя"
            }
        )
    except Exception as e:
        api_logger.error(f"Ошибка создания технического пользователя: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "technical_user_creation_error",
                "message": "Ошибка создания технического пользователя",
                "details": "Попробуйте повторить операцию позже"
            }
        )


@router.post("/admin/create-object", response_model=AdminResponse)
async def create_new_object(
    request: CreateObjectRequest,
    user_service: UserService = Depends(get_user_service)
):
    """
    Создание нового объекта (папок и групп AD)
    """
    try:
        api_logger.info(f"Создание нового объекта: {request.object_name}")
        
        result = await user_service.create_new_object(request.object_name)
        
        if result["success"]:
            api_logger.info(f"Объект {request.object_name} успешно создан")
            return AdminResponse(
                success=True,
                message=f"Объект {request.object_name} успешно создан",
                data=result
            )
        else:
            api_logger.error(f"Ошибка создания объекта: {result.get('stderr', 'Unknown error')}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error_type": "object_creation_error",
                    "message": "Ошибка создания объекта",
                    "details": result.get('stderr', 'Unknown error')
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Ошибка создания объекта: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "object_creation_error",
                "message": "Ошибка создания объекта",
                "details": "Попробуйте повторить операцию позже"
            }
        )


@router.post("/admin/update-test-attributes", response_model=AdminResponse)
async def update_test_attributes(
    request: UpdateTestAttributesRequest,
    user_service: UserService = Depends(get_user_service)
):
    """
    Обновление тестовых атрибутов пользователя
    """
    try:
        api_logger.info(f"Обновление тестовых атрибутов: {request.pager}, тип: {request.test_type}")
        
        result = await user_service.update_test_attributes(request.pager, request.test_type)
        
        if result["success"]:
            api_logger.info(f"Тестовые атрибуты успешно обновлены для {request.pager}")
            return AdminResponse(
                success=True,
                message=f"Тестовые атрибуты успешно обновлены",
                data=result
            )
        else:
            api_logger.error(f"Ошибка обновления тестовых атрибутов: {result.get('stderr', 'Unknown error')}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error_type": "test_attributes_update_error",
                    "message": "Ошибка обновления тестовых атрибутов",
                    "details": result.get('stderr', 'Unknown error')
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Ошибка обновления тестовых атрибутов: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "test_attributes_update_error",
                "message": "Ошибка обновления тестовых атрибутов",
                "details": "Попробуйте повторить операцию позже"
            }
        )


@router.get("/auth-config")
async def get_auth_config():
    """
    Получение конфигурации аутентификации для фронтенда
    """
    try:
        api_logger.info("Запрос конфигурации аутентификации")
        
        return {
            "success": True,
            "auth_enabled": True,
            "message": "Аутентификация настроена"
        }
        
    except Exception as e:
        api_logger.error(f"Ошибка получения конфигурации аутентификации: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "auth_config_error",
                "message": "Ошибка получения конфигурации аутентификации",
                "details": str(e)
            }
        )


from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/auth/login")
async def login_admin(
    login_data: LoginRequest,
    user_service: UserService = Depends(get_user_service)
):
    """
    Аутентификация администратора
    """
    try:
        api_logger.info(f"Попытка входа администратора: {login_data.username}")
        
        if login_data.username == settings.admin_username and login_data.password == settings.admin_password:
            api_logger.info(f"Успешный вход администратора: {login_data.username}")
            return {
                "success": True,
                "message": "Вход выполнен успешно",
                "user": {
                    "username": login_data.username,
                    "role": "admin"
                }
            }
        else:
            api_logger.warning(f"Неудачная попытка входа: {login_data.username}")
            raise HTTPException(
                status_code=401,
                detail={
                    "success": False,
                    "error_type": "invalid_credentials",
                    "message": "Неверное имя пользователя или пароль",
                    "details": "Проверьте правильность введенных данных"
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Ошибка аутентификации: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "auth_error",
                "message": "Ошибка аутентификации",
                "details": "Попробуйте повторить операцию позже"
            }
        )
