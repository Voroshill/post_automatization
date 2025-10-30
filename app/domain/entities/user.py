from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class UserStatus(str, Enum):
    PENDING = "pending"
    CREATING = "creating"  # В процессе создания учетных записей
    APPROVED = "approved"
    REJECTED = "rejected"
    DISMISSED = "dismissed" 


class User(BaseModel):
    id: Optional[int] = None
    unique_id: str  # pager ID из 1С
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
    status: UserStatus = UserStatus.PENDING
    upload_date: datetime
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    class Config:
        from_attributes = True
