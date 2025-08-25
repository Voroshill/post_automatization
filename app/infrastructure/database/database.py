from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config.settings import settings
from app.core.logging.logger import db_logger


engine = create_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

async def init_db():
    """Инициализация базы данных"""
    try:
        from app.infrastructure.database.models import Base
        Base.metadata.create_all(bind=engine)
        db_logger.info(f"Инициализирован движок БД: {settings.database_url}")
    except Exception as e:
        db_logger.error(f"Ошибка инициализации БД: {e}")
        raise

def get_db():
    """Генератор сессий базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
