from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.user import User, UserStatus


class UserRepository(ABC):
    @abstractmethod
    async def create_user(self, user_data: dict) -> User:
        """Создание нового пользователя"""
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        pass

    @abstractmethod
    async def update_status(self, user_id: int, status: UserStatus) -> Optional[User]:
        """Обновление статуса пользователя"""
        pass

    @abstractmethod
    async def get_all_users(self) -> List[User]:
        """Получение всех пользователей"""
        pass

    @abstractmethod
    async def get_pending_users_cursor(self, cursor: Optional[str] = None, limit: int = 20, search: Optional[str] = None, total_loaded: int = 0) -> dict:
        """Получение пользователей ожидающих одобрения с курсорной пагинацией"""
        pass

    @abstractmethod
    async def get_dismissed_users_cursor(self, cursor: Optional[str] = None, limit: int = 20, search: Optional[str] = None, total_loaded: int = 0) -> dict:
        """Получение уволенных пользователей с курсорной пагинацией"""
        pass

    @abstractmethod
    async def search_users_cursor(self, query: str, cursor: Optional[str] = None, limit: int = 20, total_loaded: int = 0) -> dict:
        """Поиск пользователей с курсорной пагинацией"""
        pass

    @abstractmethod
    async def get_all_users_cursor(self, cursor: Optional[str] = None, limit: int = 20, search: Optional[str] = None, status: Optional[UserStatus] = None, total_loaded: int = 0) -> dict:
        """Получение всех пользователей с курсорной пагинацией"""
        pass
