from typing import List, Optional, Dict, Any
from app.domain.repositories.user_repository import UserRepository
from app.domain.entities.user import User, UserStatus
from app.infrastructure.external.ldap_service import LDAPService
from app.infrastructure.external.exchange_service import ExchangeService
from app.core.logging.logger import app_logger
from app.api.schemas.user_schemas import CursorPaginatedUsersResponse, CursorPaginationInfo
from app.core.config.settings import settings
from sqlalchemy.exc import IntegrityError


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.ldap_service = LDAPService()
        self.exchange_service = ExchangeService(self.ldap_service)
        
        app_logger.info("UserService инициализирован с LDAP сервисом")
    
    async def create_user(self, user_data: dict) -> User:
        """Создание нового пользователя"""
        try:
            app_logger.info(f"Создание пользователя: {user_data.get('unique_id', 'N/A')}")
            user = await self.user_repository.create_user(user_data)
            app_logger.info(f"Пользователь создан успешно, ID: {user.id}")
            return user
        except IntegrityError as e:
            app_logger.error(f"Ошибка целостности данных при создании пользователя: {e}")
            raise
        except Exception as e:
            app_logger.error(f"Ошибка создания пользователя: {e}")
            raise
    
    async def get_pending_users(self) -> List[User]:
        return await self.user_repository.get_all_pending()
    
    async def get_dismissed_users(self) -> List[User]:
        return await self.user_repository.get_all_dismissed()
    
    async def search_users(self, query: str) -> List[User]:
        return await self.user_repository.search_users(query)
    
    async def approve_user(self, user_id: int) -> Optional[User]:
        """Одобрение пользователя и создание в AD"""
        try:
            app_logger.info(f"Одобрение пользователя ID: {user_id}")
            user = await self.user_repository.get_user_by_id(user_id)
            if not user:
                app_logger.warning(f"Пользователь с ID {user_id} не найден")
                return None

            result = await self._execute_creation_scripts(user)
            if result["success"]:
                await self.user_repository.update_status(user_id, UserStatus.APPROVED)
                app_logger.info(f"Пользователь {user_id} успешно одобрен и создан в AD")
                return await self.user_repository.get_user_by_id(user_id)
            else:
                app_logger.error(f"Ошибка создания пользователя {user_id} в AD: {result['stderr']}")
                return None
        except Exception as e:
            app_logger.error(f"Ошибка одобрения пользователя {user_id}: {e}")
            raise
    
    async def reject_user(self, user_id: int) -> Optional[User]:
        """Отклонение пользователя"""
        try:
            app_logger.info(f"Отклонение пользователя ID: {user_id}")
            await self.user_repository.update_status(user_id, UserStatus.REJECTED)
            app_logger.info(f"Пользователь {user_id} успешно отклонен")
            return await self.user_repository.get_user_by_id(user_id)
        except Exception as e:
            app_logger.error(f"Ошибка отклонения пользователя {user_id}: {e}")
            raise
    
    async def dismiss_user(self, user_id: int) -> Optional[User]:
        """Увольнение пользователя"""
        try:
            app_logger.info(f"Увольнение пользователя ID: {user_id}")
            user = await self.user_repository.get_user_by_id(user_id)
            if not user:
                app_logger.warning(f"Пользователь с ID {user_id} не найден")
                return None

            await self.user_repository.update_status(user_id, UserStatus.DISMISSED)
            app_logger.info(f"Статус пользователя {user_id} обновлен на DISMISSED")
            
            result = await self.ldap_service.block_user(user.unique_id)
            if result["success"]:
                app_logger.info(f"Пользователь {user_id} успешно уволен и заблокирован в AD")
                return await self.user_repository.get_user_by_id(user_id)
            else:
                await self.user_repository.update_status(user_id, user.status)
                app_logger.error(f"Ошибка блокировки пользователя {user_id} в AD: {result['stderr']}")
                return None
        except Exception as e:
            app_logger.error(f"Ошибка увольнения пользователя {user_id}: {e}")
            raise
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        return await self.user_repository.get_user_by_id(user_id)
    
    async def get_all_users(self) -> List[User]:
        """Получение всех пользователей без пагинации"""
        try:
            app_logger.info("Запрос всех пользователей без пагинации")
            users = await self.user_repository.get_all_users()
            app_logger.info(f"Получено {len(users)} пользователей")
            return users
        except Exception as e:
            app_logger.error(f"Ошибка получения всех пользователей: {e}")
            raise

    async def _execute_creation_scripts(self, user: User) -> Dict[str, Any]:
        """Выполнение скриптов создания пользователя в AD (точно как в PowerShell)"""
        try:
            app_logger.info(f"Выполнение скриптов создания пользователя: {user.unique_id}")
            
            user_data = {
                'unique_id': user.unique_id,
                'firstname': user.firstname,
                'secondname': user.secondname,
                'thirdname': user.thirdname,
                'company': user.company,
                'department': user.otdel,  # Передаем отдел как department (как в PowerShell)
                'appointment': user.appointment,
                'work_phone': user.work_phone,
                'current_location_id': user.current_location_id,
                'boss_id': user.boss_id,
                'is_engineer': user.is_engineer,
                # Флаг technical для паритета со скриптами: 'technical' если is_engineer == 1
                'technical': 'technical' if user.is_engineer == 1 else ''
            }
            
            ad_result = await self.ldap_service.create_user_in_ad(user_data)
            
            if not ad_result["success"]:
                app_logger.error(f"Ошибка создания пользователя в AD: {ad_result['stderr']}")
                return ad_result
            
            sam_account_name = ad_result.get("sam_account_name")
            app_logger.info(f"Пользователь {sam_account_name} успешно создан в AD")
            
            user_principal_name = ad_result.get("user_principal_name")
            mailbox_result = await self.exchange_service.create_mailbox(sam_account_name, user_principal_name)
            if not mailbox_result["success"]:
                app_logger.warning(f"Ошибка создания почтового ящика: {mailbox_result['stderr']}")
            
            # Отправка email с таймаутом - не блокируем approve если email зависнет
            import asyncio
            try:
                confirmation_result = await asyncio.wait_for(
                    self.exchange_service.send_confirmation_email(user_data, sam_account_name),
                    timeout=25.0
                )
                if not confirmation_result["success"]:
                    app_logger.warning(f"Ошибка отправки подтверждения: {confirmation_result.get('stderr', 'Unknown error')}")
            except asyncio.TimeoutError:
                app_logger.warning(f"Таймаут отправки подтверждения для {sam_account_name} (превышено 25 секунд)")
                confirmation_result = {"success": False, "stderr": "Email send timeout"}
            except Exception as e:
                app_logger.warning(f"Исключение при отправке подтверждения: {e}")
                confirmation_result = {"success": False, "stderr": str(e)}
            
            try:
                welcome_result = await asyncio.wait_for(
                    self.exchange_service.send_welcome_email(user_data, sam_account_name),
                    timeout=25.0
                )
                if not welcome_result["success"]:
                    app_logger.warning(f"Ошибка отправки приветственного письма: {welcome_result.get('stderr', 'Unknown error')}")
            except asyncio.TimeoutError:
                app_logger.warning(f"Таймаут отправки приветственного письма для {sam_account_name} (превышено 25 секунд)")
                welcome_result = {"success": False, "stderr": "Email send timeout"}
            except Exception as e:
                app_logger.warning(f"Исключение при отправке приветственного письма: {e}")
                welcome_result = {"success": False, "stderr": str(e)}
            
            return {
                "success": True,
                "stdout": f"User {sam_account_name} created successfully with all services",
                "ad_result": ad_result,
                "mailbox_result": mailbox_result,
                "confirmation_result": confirmation_result,
                "welcome_result": welcome_result
            }
            
        except Exception as e:
            app_logger.error(f"Исключение при выполнении скриптов создания: {e}")
            return {"success": False, "stderr": str(e)}
    
    def _create_cursor_pagination_info(self, next_cursor: Optional[str], has_more: bool, total_loaded: int) -> CursorPaginationInfo:
        """Создание информации о курсорной пагинации"""
        return CursorPaginationInfo(
            next_cursor=next_cursor,
            has_more=has_more,
            total_loaded=total_loaded
        )
    
    async def get_pending_users_cursor(self, cursor: Optional[str] = None, limit: int = 20, search: Optional[str] = None, total_loaded: int = 0):
        """Получение пользователей ожидающих одобрения с курсорной пагинацией"""
        try:
            app_logger.info(f"Запрос pending пользователей: cursor={cursor}, limit={limit}, search={search}")
            result = await self.user_repository.get_pending_users_cursor(cursor, limit, search, total_loaded)
            app_logger.info(f"Получено {len(result['users'])} pending пользователей")
            return result
        except Exception as e:
            app_logger.error(f"Ошибка получения pending пользователей: {e}")
            raise
    
    async def get_dismissed_users_cursor(self, cursor: Optional[str] = None, limit: int = 20, search: Optional[str] = None, total_loaded: int = 0):
        """Получение уволенных пользователей с курсорной пагинацией"""
        try:
            app_logger.info(f"Запрос dismissed пользователей: cursor={cursor}, limit={limit}, search={search}")
            result = await self.user_repository.get_dismissed_users_cursor(cursor, limit, search, total_loaded)
            app_logger.info(f"Получено {len(result['users'])} dismissed пользователей")
            return result
        except Exception as e:
            app_logger.error(f"Ошибка получения dismissed пользователей: {e}")
            raise

    async def search_users_cursor(self, query: str, cursor: Optional[str] = None, limit: int = 20, status: Optional[UserStatus] = None, total_loaded: int = 0):
        """Поиск пользователей с курсорной пагинацией"""
        try:
            app_logger.info(f"Поиск пользователей: query='{query}', cursor={cursor}, limit={limit}, status={status}")
            result = await self.user_repository.search_users_cursor(query, cursor, limit, status, total_loaded)
            app_logger.info(f"Найдено {len(result['users'])} пользователей по запросу '{query}'")
            return result
        except Exception as e:
            app_logger.error(f"Ошибка поиска пользователей: {e}")
            raise

    async def get_all_users_cursor(self, cursor: Optional[str] = None, limit: int = 20, search: Optional[str] = None, status: Optional[UserStatus] = None, total_loaded: int = 0):
        """Получение всех пользователей с курсорной пагинацией"""
        try:
            app_logger.info(f"Запрос всех пользователей: cursor={cursor}, limit={limit}, search={search}, status={status}")
            result = await self.user_repository.get_all_users_cursor(cursor, limit, search, status, total_loaded)
            app_logger.info(f"Получено {len(result['users'])} пользователей")
            return result
        except Exception as e:
            app_logger.error(f"Ошибка получения всех пользователей: {e}")
            raise


    async def change_password(self, username: str, new_password: str) -> dict:
        """Смена пароля пользователя в AD"""
        try:
            app_logger.info(f"Смена пароля для пользователя: {username}")
            
            result = await self.ldap_service.change_password(username, new_password)
            
            if not result.get("success", False):
                error_msg = result.get("stderr", "Неизвестная ошибка")
                app_logger.error(f"Ошибка смены пароля для пользователя {username}: {error_msg}")
                raise Exception(f"Ошибка смены пароля: {error_msg}")
            
            app_logger.info(f"Пароль для пользователя {username} успешно изменен")
            return result
        except Exception as e:
            app_logger.error(f"Ошибка смены пароля для пользователя {username}: {e}")
            raise

    async def change_phone_number(self, pager: str, new_phone: str) -> dict:
        """Смена номера телефона пользователя в AD"""
        try:
            app_logger.info(f"Смена номера телефона для пользователя: {pager}")
            
            result = await self.ldap_service.change_phone_number(pager, new_phone)
            
            if not result.get("success", False):
                error_msg = result.get("stderr", "Неизвестная ошибка")
                app_logger.error(f"Ошибка смены номера телефона для пользователя {pager}: {error_msg}")
                raise Exception(f"Ошибка смены номера телефона: {error_msg}")
            
            app_logger.info(f"Номер телефона для пользователя {pager} успешно обновлен")
            return result
        except Exception as e:
            app_logger.error(f"Ошибка смены номера телефона для пользователя {pager}: {e}")
            raise

    async def export_users_from_ad(self) -> dict:
        """Экспорт всех пользователей из Active Directory"""
        try:
            app_logger.info("Экспорт пользователей из AD")
            
            result = await self.ldap_service.export_users_from_ad()
            
            if not result.get("success", False):
                error_msg = result.get("stderr", "Неизвестная ошибка")
                app_logger.error(f"Ошибка экспорта пользователей из AD: {error_msg}")
                raise Exception(f"Ошибка экспорта пользователей из AD: {error_msg}")
            
            app_logger.info("Пользователи успешно экспортированы из AD")
            return result
        except Exception as e:
            app_logger.error(f"Ошибка экспорта пользователей из AD: {e}")
            raise

    async def block_user_complete(self, unique_id: str) -> dict:
        """Полная блокировка пользователя с удалением из групп и перемещением в OU "Уволенные сотрудники" """
        try:
            app_logger.info(f"Полная блокировка пользователя: {unique_id}")
            
            result = await self.ldap_service.block_user_complete(unique_id)
            
            if not result.get("success", False):
                error_msg = result.get("stderr", "Неизвестная ошибка")
                app_logger.error(f"Ошибка полной блокировки пользователя {unique_id}: {error_msg}")
                raise Exception(f"Ошибка полной блокировки пользователя: {error_msg}")
            
            app_logger.info(f"Пользователь {unique_id} полностью заблокирован")
            return result
        except Exception as e:
            app_logger.error(f"Ошибка полной блокировки пользователя {unique_id}: {e}")
            raise

    async def assign_manager(self, employee_id: str, manager_id: str) -> dict:
        """Назначение менеджера для пользователя"""
        try:
            app_logger.info(f"Назначение менеджера {manager_id} для пользователя {employee_id}")
            
            result = await self.ldap_service.assign_manager(employee_id, manager_id)
            
            if not result.get("success", False):
                error_msg = result.get("stderr", "Неизвестная ошибка")
                app_logger.error(f"Ошибка назначения менеджера {manager_id} для пользователя {employee_id}: {error_msg}")
                raise Exception(f"Ошибка назначения менеджера: {error_msg}")
            
            app_logger.info(f"Менеджер {manager_id} успешно назначен для пользователя {employee_id}")
            return result
        except Exception as e:
            app_logger.error(f"Ошибка назначения менеджера {manager_id} для пользователя {employee_id}: {e}")
            raise

    async def create_technical_user(self, user_data: dict) -> User:
        """Создание технического пользователя"""
        try:
            app_logger.info(f"Создание технического пользователя: {user_data.get('unique_id', 'N/A')}")

            user_data["technical"] = "technical"
            
            user = await self.user_repository.create_user(user_data)
            app_logger.info(f"Технический пользователь создан успешно, ID: {user.id}")
            return user
        except IntegrityError as e:
            app_logger.error(f"Ошибка целостности данных при создании технического пользователя: {e}")
            raise
        except Exception as e:
            app_logger.error(f"Ошибка создания технического пользователя: {e}")
            raise

    async def create_new_object(self, object_name: str) -> Dict[str, Any]:
        """Создание нового объекта (папок и групп AD)"""
        try:
            app_logger.info(f"Создание нового объекта через UserService: {object_name}")
            result = await self.ldap_service.create_new_object(object_name)
            return result
        except Exception as e:
            app_logger.error(f"Ошибка создания объекта в UserService: {e}")
            return {"success": False, "stderr": str(e)}

    async def update_test_attributes(self, pager: str, test_type: str) -> Dict[str, Any]:
        """Обновление тестовых атрибутов пользователя"""
        try:
            app_logger.info(f"Обновление тестовых атрибутов через UserService: {pager}, тип: {test_type}")
            result = await self.ldap_service.update_test_attributes(pager, test_type)
            return result
        except Exception as e:
            app_logger.error(f"Ошибка обновления тестовых атрибутов в UserService: {e}")
            return {"success": False, "stderr": str(e)}
