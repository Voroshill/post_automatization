from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.domain.repositories.user_repository import UserRepository
from app.domain.entities.user import User, UserStatus
from app.infrastructure.database.models import UserModel
from app.core.logging.logger import db_logger
import base64

class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, db: Session):
        self.db = db
        db_logger.info("SQLAlchemyUserRepository инициализирован")

    async def create_user(self, user_data: dict) -> User:
        """Создание нового пользователя"""
        try:
            db_logger.info(f"Создание пользователя в БД: {user_data.get('unique_id', 'N/A')}")
            user_model = UserModel(**user_data)
            self.db.add(user_model)
            self.db.commit()
            self.db.refresh(user_model)
            user = User.model_validate(user_model)
            
            db_logger.info(f"Пользователь успешно создан в БД: ID={user.id}")
            return user
            
        except IntegrityError as e:
            db_logger.error(f"Ошибка целостности данных при создании пользователя: {e}")
            self.db.rollback()
            raise
        except Exception as e:
            db_logger.error(f"Ошибка создания пользователя в БД: {e}")
            self.db.rollback()
            raise

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        try:
            db_logger.debug(f"Запрос пользователя по ID: {user_id}")
            user_model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
            
            if user_model:
                user = User.model_validate(user_model)
                db_logger.debug(f"Пользователь найден: ID={user_id}")
                return user
            else:
                db_logger.warning(f"Пользователь не найден: ID={user_id}")
                return None
                
        except Exception as e:
            db_logger.error(f"Ошибка получения пользователя по ID {user_id}: {e}")
            raise

    async def update_status(self, user_id: int, status: UserStatus) -> Optional[User]:
        """Обновление статуса пользователя"""
        try:
            db_logger.info(f"Обновление статуса пользователя: ID={user_id}, статус={status}")
            
            user_model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
            if user_model:
                user_model.status = status
                self.db.commit()
                self.db.refresh(user_model)
                
                user = User.model_validate(user_model)
                db_logger.info(f"Статус пользователя обновлен: ID={user_id}, новый статус={status}")
                return user
            else:
                db_logger.warning(f"Пользователь не найден для обновления статуса: ID={user_id}")
                return None
                
        except Exception as e:
            db_logger.error(f"Ошибка обновления статуса пользователя {user_id}: {e}")
            self.db.rollback()
            raise

    async def get_all_users(self) -> List[User]:
        """Получение всех пользователей"""
        try:
            db_logger.info("Запрос всех пользователей из БД")
            user_models = self.db.query(UserModel).all()
            users = [User.model_validate(model) for model in user_models]
            db_logger.info(f"Получено {len(users)} пользователей из БД")
            return users
            
        except Exception as e:
            db_logger.error(f"Ошибка получения всех пользователей: {e}")
            raise

    def _encode_cursor(self, user_id: int) -> str:
        """Кодирование курсора"""
        return base64.b64encode(str(user_id).encode()).decode()

    def _decode_cursor(self, cursor: str) -> int:
        """Декодирование курсора"""
        try:
            return int(base64.b64decode(cursor.encode()).decode())
        except:
            return 0

    async def get_pending_users_cursor(self, cursor: Optional[str] = None, limit: int = 20, search: Optional[str] = None, total_loaded: int = 0) -> dict:
        """Получение пользователей ожидающих одобрения с курсорной пагинацией"""
        try:
            db_logger.info(f"Запрос pending пользователей: cursor={cursor}, limit={limit}, search={search}")
            
            count_query = self.db.query(UserModel).filter(UserModel.status == UserStatus.PENDING)
            if search:
                search_term = f"%{search}%"
                count_query = count_query.filter(
                    (UserModel.firstname.ilike(search_term)) |
                    (UserModel.secondname.ilike(search_term)) |
                    (UserModel.thirdname.ilike(search_term)) |
                    (UserModel.unique_id.ilike(search_term)) |
                    (UserModel.mobile_phone.ilike(search_term))
                )
            total_count = count_query.count()

            query = self.db.query(UserModel).filter(UserModel.status == UserStatus.PENDING)
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    (UserModel.firstname.ilike(search_term)) |
                    (UserModel.secondname.ilike(search_term)) |
                    (UserModel.thirdname.ilike(search_term)) |
                    (UserModel.unique_id.ilike(search_term)) |
                    (UserModel.mobile_phone.ilike(search_term))
                )
            if cursor:
                cursor_id = self._decode_cursor(cursor)
                query = query.filter(UserModel.id > cursor_id)
            query = query.order_by(UserModel.id.asc()).limit(limit + 1)
            user_models = query.all()
            has_more = len(user_models) > limit
            
            if has_more:
                user_models = user_models[:-1] 
            
            users = [User.model_validate(model) for model in user_models]
            next_cursor = None
            if users and has_more:
                next_cursor = self._encode_cursor(users[-1].id)
            
            db_logger.info(f"Получено {len(users)} pending пользователей, has_more={has_more}, total_count={total_count}")
            
            return {
                "users": users,
                "next_cursor": next_cursor,
                "has_more": has_more,
                "total_count": total_count
            }
            
        except Exception as e:
            db_logger.error(f"Ошибка получения pending пользователей: {e}")
            raise

    async def get_dismissed_users_cursor(self, cursor: Optional[str] = None, limit: int = 20, search: Optional[str] = None, total_loaded: int = 0) -> dict:
        """Получение уволенных пользователей с курсорной пагинацией"""
        try:
            db_logger.info(f"Запрос dismissed пользователей: cursor={cursor}, limit={limit}, search={search}")
            
            count_query = self.db.query(UserModel).filter(UserModel.status == UserStatus.DISMISSED)
            if search:
                search_term = f"%{search}%"
                count_query = count_query.filter(
                    (UserModel.firstname.ilike(search_term)) |
                    (UserModel.secondname.ilike(search_term)) |
                    (UserModel.thirdname.ilike(search_term)) |
                    (UserModel.unique_id.ilike(search_term)) |
                    (UserModel.mobile_phone.ilike(search_term))
                )
            total_count = count_query.count()

            query = self.db.query(UserModel).filter(UserModel.status == UserStatus.DISMISSED)
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    (UserModel.firstname.ilike(search_term)) |
                    (UserModel.secondname.ilike(search_term)) |
                    (UserModel.thirdname.ilike(search_term)) |
                    (UserModel.unique_id.ilike(search_term)) |
                    (UserModel.mobile_phone.ilike(search_term))
                )

            if cursor:
                cursor_id = self._decode_cursor(cursor)
                query = query.filter(UserModel.id > cursor_id)
            query = query.order_by(UserModel.id.asc()).limit(limit + 1)
            user_models = query.all()
            has_more = len(user_models) > limit
            
            if has_more:
                user_models = user_models[:-1] 
            
            users = [User.model_validate(model) for model in user_models]
            next_cursor = None
            if users and has_more:
                next_cursor = self._encode_cursor(users[-1].id)
            
            db_logger.info(f"Получено {len(users)} dismissed пользователей, has_more={has_more}, total_count={total_count}")
            
            return {
                "users": users,
                "next_cursor": next_cursor,
                "has_more": has_more,
                "total_count": total_count
            }
            
        except Exception as e:
            db_logger.error(f"Ошибка получения dismissed пользователей: {e}")
            raise

    async def search_users_cursor(self, query: str, cursor: Optional[str] = None, limit: int = 20, status: Optional[UserStatus] = None, total_loaded: int = 0) -> dict:
        """Поиск пользователей с курсорной пагинацией"""
        try:
            db_logger.info(f"Поиск пользователей: query='{query}', cursor={cursor}, limit={limit}, status={status}")

            count_query = self.db.query(UserModel).filter(
                (UserModel.firstname.ilike(f"%{query}%")) |
                (UserModel.secondname.ilike(f"%{query}%")) |
                (UserModel.thirdname.ilike(f"%{query}%")) |
                (UserModel.unique_id.ilike(f"%{query}%")) |
                (UserModel.mobile_phone.ilike(f"%{query}%"))
            )
            if status:
                count_query = count_query.filter(UserModel.status == status)
            total_count = count_query.count()
            
            search_term = f"%{query}%"
            db_query = self.db.query(UserModel).filter(
                (UserModel.firstname.ilike(search_term)) |
                (UserModel.secondname.ilike(search_term)) |
                (UserModel.thirdname.ilike(search_term)) |
                (UserModel.unique_id.ilike(search_term)) |
                (UserModel.mobile_phone.ilike(search_term))
            )
            if status:
                db_query = db_query.filter(UserModel.status == status)
            if cursor:
                cursor_id = self._decode_cursor(cursor)
                db_query = db_query.filter(UserModel.id > cursor_id)
            db_query = db_query.order_by(UserModel.id.asc()).limit(limit + 1)
            user_models = db_query.all()
            has_more = len(user_models) > limit
            
            if has_more:
                user_models = user_models[:-1] 
            
            users = [User.model_validate(model) for model in user_models]
            next_cursor = None
            if users and has_more:
                next_cursor = self._encode_cursor(users[-1].id)
            
            db_logger.info(f"Найдено {len(users)} пользователей по запросу '{query}', has_more={has_more}, total_count={total_count}")
            
            return {
                "users": users,
                "next_cursor": next_cursor,
                "has_more": has_more,
                "total_count": total_count
            }
            
        except Exception as e:
            db_logger.error(f"Ошибка поиска пользователей: {e}")
            raise

    async def get_all_users_cursor(self, cursor: Optional[str] = None, limit: int = 20, search: Optional[str] = None, status: Optional[UserStatus] = None, total_loaded: int = 0) -> dict:
        """Получение всех пользователей с курсорной пагинацией"""
        try:
            db_logger.info(f"Запрос всех пользователей: cursor={cursor}, limit={limit}, search={search}, status={status}")
            
            count_query = self.db.query(UserModel)
            if status:
                count_query = count_query.filter(UserModel.status == status)
            if search:
                search_term = f"%{search}%"
                count_query = count_query.filter(
                    (UserModel.firstname.ilike(search_term)) |
                    (UserModel.secondname.ilike(search_term)) |
                    (UserModel.thirdname.ilike(search_term)) |
                    (UserModel.unique_id.ilike(search_term)) |
                    (UserModel.mobile_phone.ilike(search_term))
                )
            total_count = count_query.count()
            
            query = self.db.query(UserModel)
            if status:
                query = query.filter(UserModel.status == status)
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    (UserModel.firstname.ilike(search_term)) |
                    (UserModel.secondname.ilike(search_term)) |
                    (UserModel.thirdname.ilike(search_term)) |
                    (UserModel.unique_id.ilike(search_term)) |
                    (UserModel.mobile_phone.ilike(search_term))
                )
            if cursor:
                cursor_id = self._decode_cursor(cursor)
                query = query.filter(UserModel.id > cursor_id)
            query = query.order_by(UserModel.id.asc()).limit(limit + 1)
            user_models = query.all()
            has_more = len(user_models) > limit
            
            if has_more:
                user_models = user_models[:-1] 
            
            users = [User.model_validate(model) for model in user_models]
            next_cursor = None
            if users and has_more:
                next_cursor = self._encode_cursor(users[-1].id)
            
            db_logger.info(f"Получено {len(users)} пользователей, has_more={has_more}, total_count={total_count}")
            
            return {
                "users": users,
                "next_cursor": next_cursor,
                "has_more": has_more,
                "total_count": total_count
            }
            
        except Exception as e:
            db_logger.error(f"Ошибка получения всех пользователей: {e}")
            raise
