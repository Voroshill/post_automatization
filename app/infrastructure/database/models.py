from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Boolean
from sqlalchemy.ext.declarative import declarative_base
from app.domain.entities.user import UserStatus

Base = declarative_base()


class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String, unique=True, index=True, nullable=False)
    firstname = Column(String, nullable=False)
    secondname = Column(String, nullable=False)
    thirdname = Column(String, nullable=True)
    company = Column(String, nullable=False)
    department = Column(String, nullable=False)
    otdel = Column(String, nullable=False)
    appointment = Column(String, nullable=False)
    mobile_phone = Column(String, nullable=True)
    work_phone = Column(String, nullable=True)
    current_location_id = Column(String, nullable=False)
    boss_id = Column(String, nullable=True)
    birth_date = Column(String, nullable=True)
    object_date_vihod = Column(String, nullable=True)
    dismissal_date = Column(String, nullable=True)
    worktype_id = Column(String, nullable=True)
    is_engineer = Column(Integer, nullable=True)
    o_id = Column(String, nullable=True)
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING)
    upload_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_update = Column(Boolean, default=False, nullable=False)
