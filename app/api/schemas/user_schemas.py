from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.domain.entities.user import UserStatus


# =============================================================================
# СХЕМЫ АУТЕНТИФИКАЦИИ
# =============================================================================

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    user: Optional[dict] = None


class AuthConfigResponse(BaseModel):
    auth_enabled: bool
    login_url: str


class AuthVerifyResponse(BaseModel):
    authenticated: bool
    user: Optional[dict] = None


class UserCreateRequest(BaseModel):
    unique: str
    firstname: str
    secondname: str
    thirdname: Optional[str] = None
    company: str
    Department: str
    Otdel: str
    appointment: str
    WorkPhone: Optional[str] = None
    current_location_id: str
    boss_id: Optional[str] = None
    BirthDate: Optional[str] = None
    object_date_vihod: Optional[str] = None
    dismissal_date: Optional[str] = None
    worktype_id: Optional[str] = None
    is_engeneer: Optional[int] = None
    o_id: Optional[str] = None
    UploadDate: datetime


class UserResponse(BaseModel):
    id: int
    unique_id: str
    firstname: str
    secondname: str
    thirdname: Optional[str] = None
    company: str
    department: str
    otdel: str
    appointment: str
    work_phone: Optional[str] = None
    current_location_id: str
    boss_id: Optional[str] = None
    birth_date: Optional[str] = None
    object_date_vihod: Optional[str] = None
    dismissal_date: Optional[str] = None
    worktype_id: Optional[str] = None
    is_engineer: Optional[int] = None
    o_id: Optional[str] = None
    status: UserStatus
    upload_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserStatusUpdate(BaseModel):
    status: UserStatus


class CursorPaginationInfo(BaseModel):
    next_cursor: Optional[str] = None
    has_more: bool
    total_loaded: int
    total_count: Optional[int] = None


class CursorPaginatedUsersResponse(BaseModel):
    users: List[UserResponse]
    pagination: CursorPaginationInfo


# Схемы для администрирования
class ChangePasswordRequest(BaseModel):
    username: str
    new_password: str


class ChangePhoneRequest(BaseModel):
    pager: str
    new_phone: str


class BlockUserCompleteRequest(BaseModel):
    unique_id: str


class AssignManagerRequest(BaseModel):
    employee_id: str
    manager_id: str


class TechnicalUserRequest(BaseModel):
    firstname: str
    secondname: str
    thirdname: Optional[str] = None
    company: str
    department: str
    appointment: str
    boss_id: Optional[str] = None
    current_location_id: str
    unique_id: str
    work_phone: Optional[str] = None
    technical: Optional[str] = None  # Добавляем поле technical как в PowerShell

class AdminResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class CreateObjectRequest(BaseModel):
    object_name: str

class UpdateTestAttributesRequest(BaseModel):
    pager: str
    test_type: str
