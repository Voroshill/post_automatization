import asyncio
import os
import subprocess
from typing import Dict, Any, Optional
from ldap3 import Server, Connection, ALL, NTLM, SUBTREE, MODIFY_REPLACE
from app.core.config.settings import settings
from app.core.logging.logger import ldap_logger


class LDAPService:
    def __init__(self):
        self.ad_domain = settings.ad_domain
        self.ad_server = settings.ad_server
        self.admin_username = settings.admin_username
        self.admin_password = settings.admin_password
        self.conn = None
        
        ldap_logger.info(f"LDAPService инициализирован. Сервер: {self.ad_server}")
        
        self.server = Server(self.ad_server, get_info=ALL)
        self.connection = None
    
    async def _get_connection(self) -> Connection:
        """Получение подключения к AD"""
        if not self.connection or not self.connection.bound:
            self.connection = Connection(
                self.server,
                user=f"{self.ad_domain}\\{self.admin_username}",
                password=self.admin_password,
                authentication=NTLM,
                auto_bind=True
            )
            
            if not self.connection.bound:
                raise Exception(f"Не удалось подключиться к AD: {self.connection.result}")
        
        return self.connection
    
    def translit(self, text: str) -> str:
        """Транслитерация русского текста в латиницу (точно как в PowerShell)"""
        translit_map = {
            'а': 'a', 'А': 'a', 'б': 'b', 'Б': 'b', 'в': 'v', 'В': 'v',
            'г': 'g', 'Г': 'g', 'д': 'd', 'Д': 'd', 'е': 'e', 'Е': 'e',
            'ё': 'e', 'Ё': 'e', 'ж': 'zh', 'Ж': 'zh', 'з': 'z', 'З': 'z',
            'и': 'i', 'И': 'i', 'й': 'i', 'Й': 'i', 'к': 'k', 'К': 'k',
            'л': 'l', 'Л': 'l', 'м': 'm', 'М': 'm', 'н': 'n', 'Н': 'n',
            'о': 'o', 'О': 'o', 'п': 'p', 'П': 'p', 'р': 'r', 'Р': 'r',
            'с': 's', 'С': 's', 'т': 't', 'Т': 't', 'у': 'u', 'У': 'u',
            'ф': 'f', 'Ф': 'f', 'х': 'h', 'Х': 'h', 'ц': 'ts', 'Ц': 'ts',
            'ч': 'ch', 'Ч': 'ch', 'ш': 'sh', 'Ш': 'sh', 'щ': 'sch', 'Щ': 'sch',
            'ъ': '', 'Ъ': '', 'ы': 'y', 'Ы': 'y', 'ь': '', 'Ь': '',
            'э': 'e', 'Э': 'e', 'ю': 'yu', 'Ю': 'yu', 'я': 'ya', 'Я': 'ya',
            ' ': '-'
        }
        
        result = ""
        for char in text:
            result += translit_map.get(char, char)
        return result
    
    def get_user_principal_name(self, sam_account_name: str, company: str) -> str:
        """Определение UserPrincipalName на основе компании (точно как в PowerShell)"""
        if any(keyword in company.upper() for keyword in ['STI', 'СТРОЙ', 'ТЕХНО', 'ИНЖЕНЕРИНГ']):
            return f"{sam_account_name}@st-ing.com"
        elif any(keyword in company.upper() for keyword in ['DTTERMO', 'ДТ']):
            return f"{sam_account_name}@dttermo.ru"
        else:
            return f"{sam_account_name}@st-ing.com"
    
    def find_ou(self, obj_name: str, department: str) -> str:
        """Определение OU в Active Directory (точно как в PowerShell)"""
        if 'прудный' in obj_name.lower():
            return "OU=Доп. офис Трёхпрудный,OU=Отдел управления проектами,OU=Технический департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        
        if 'лобня' in obj_name.lower():
            if 'логистик' in department.lower():
                return "OU=Отдел логистики и складского учета,OU=Коммерческий департамент,OU=DtTermo,DC=central,DC=st-ing,DC=com"
        
        if 'медовый' in obj_name.lower():
            if 'информац' in department.lower():
                return "OU=Отдел информационных технологий,OU=Департамент обеспечения,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            elif 'кадро' in department.lower():
                return "OU=Отдел кадров,OU=Департамент обеспечения,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            elif 'персона' in department.lower():
                return "OU=Отдел персонала,OU=Департамент обеспечения,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            elif 'управленческ' in department.lower():
                return "OU=Отдел управленческого учета,OU=Департамент обеспечения,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            elif 'проектир' in department.lower():
                return "OU=Отдел проектирования,OU=Департамент развития,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            elif 'ендерны' in department.lower():
                return "OU=Тендерный отдел,OU=Департамент развития,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            elif 'закупок' in department.lower():
                return "OU=Отдел закупок,OU=Коммерческий департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            elif 'логистик' in department.lower():
                return "OU=Отдел логистики и складского учета,OU=Коммерческий департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            elif 'снабже' in department.lower():
                return "OU=Отдел снабжения,OU=Коммерческий департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            elif 'труд' in department.lower():
                return "OU=Отдел охраны труда,OU=Технический департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            elif 'ПТО' in department.upper():
                return "OU=Отдел ПТО,OU=Технический департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            elif 'метный' in department.lower():
                return "OU=Сметный отдел,OU=Технический департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            elif 'ланово' in department.lower():
                return "OU=Планово экономический отдел,OU=Финансовый департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            elif 'ухгалтери' in department.lower():
                return "OU=Бухгалтерия,OU=Финансовый департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            elif 'азначе' in department.lower():
                return "OU=Казначейство,OU=Финансовый департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            elif 'ридически' in department.lower():
                return "OU=Юридический отдел,OU=Юридический департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            elif 'дминистративны' in department.lower():
                return "OU=Административный отдел,OU=Департамент обеспечения,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        
        construction_objects = ['емеров', 'амчатк', 'гнитогор', 'инько', 'ер К32', 'авидо', 'ктафар', 'ухарев', 'алент', 'рофлот', 'ON']
        if any(obj in obj_name for obj in construction_objects):
            return f"OU={obj_name},OU=Строительные объекты,OU=Отдел управления проектами,OU=Технический департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        
        return "OU=Пользователи,DC=central,DC=st-ing,DC=com"
    
    async def create_user_in_ad(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание пользователя в Active Directory через LDAP (точно как в PowerShell)"""
        try:
            ldap_logger.info(f"Создание пользователя в AD через LDAP: {user_data.get('unique_id', 'Unknown')}")
            
            conn = await self._get_connection()
            
            firstname_translit = self.translit(user_data.get('firstname', ''))
            secondname_translit = self.translit(user_data.get('secondname', ''))
            sam_account_name = f"{firstname_translit}.{secondname_translit}"
            
            user_principal_name = self.get_user_principal_name(sam_account_name, user_data.get('company', ''))
            
            if user_data.get('technical') == 'technical':
                ou = 'OU=Технические логины,DC=central,DC=st-ing,DC=com'
            else:
            ou = self.find_ou(user_data.get('current_location_id', ''), user_data.get('department', ''))
            
            display_name = f"{user_data.get('firstname', '')} {user_data.get('secondname', '')} {user_data.get('thirdname', '')}"
            user_dn = f"CN={display_name},{ou}"
            
            attributes = {
                'objectClass': ['top', 'person', 'organizationalPerson', 'user'],
                'sAMAccountName': sam_account_name,
                'userPrincipalName': user_principal_name,
                'givenName': user_data.get('firstname', ''),
                'sn': user_data.get('secondname', ''),
                'displayName': display_name,
                'mail': user_principal_name,
                'pager': user_data.get('unique_id', ''),
                'company': user_data.get('company', ''),
                'department': user_data.get('department', ''),
                'title': user_data.get('appointment', ''),
                'description': user_data.get('appointment', ''),
                'streetAddress': user_data.get('current_location_id', ''),
                'physicalDeliveryOfficeName': user_data.get('current_location_id', ''),
                'telephoneNumber': user_data.get('work_phone', ''),
                'city': user_data.get('current_location_id', ''), 
                'office': user_data.get('current_location_id', ''), 
                'userAccountControl': '512' 
            }
            
            success = conn.add(user_dn, attributes=attributes)
            
            if success:
                ldap_logger.info(f"Пользователь {sam_account_name} успешно создан в AD через LDAP")
                
                conn.extend.microsoft.modify_password(user_dn, settings.default_user_password)
                
                conn.modify(
                    user_dn,
                    {'pwdLastSet': [(MODIFY_REPLACE, ['0'])]} 
                )
                
                await self._add_user_to_groups(sam_account_name, user_data)
                
                if user_data.get('boss_id'):
                    await self._assign_manager(sam_account_name, user_data.get('boss_id'))
                
                return {
                    "success": True,
                    "sam_account_name": sam_account_name,
                    "user_principal_name": user_principal_name,
                    "default_password": settings.default_user_password,
                    "stdout": f"User {sam_account_name} created successfully via LDAP"
                }
            else:
                error_msg = f"Ошибка создания пользователя: {conn.result}"
                ldap_logger.error(error_msg)
                return {"success": False, "stderr": error_msg}
                
        except Exception as e:
            ldap_logger.error(f"Исключение при создании пользователя через LDAP: {e}")
            return {"success": False, "stderr": str(e)}
    
    async def _add_user_to_groups(self, sam_account_name: str, user_data: Dict[str, Any]):
        """Добавление пользователя в группы AD (точно как в PowerShell)"""
        try:
            conn = await self._get_connection()
            
            company = user_data.get('company', '')
            if any(keyword in company.upper() for keyword in ['СТРОЙ', 'ТЕХНО', 'ИНЖЕНЕРИНГ', 'STI', 'ТРОЙ']):
                conn.extend.microsoft.add_members_to_groups(
                    sam_account_name, 
                    'СтройТехноИнженеринг'
                )
            elif any(keyword in company.upper() for keyword in ['DTTERMO', 'ДТ']):
                conn.extend.microsoft.add_members_to_groups(
                    sam_account_name, 
                    'DttermoSign'
                )
            
            department = user_data.get('department', '')
            if department:
                conn.extend.microsoft.add_members_to_groups(
                    sam_account_name, 
                    department
                )
                
        except Exception as e:
            ldap_logger.warning(f"Ошибка добавления в группы: {e}")
    
    async def _assign_manager(self, sam_account_name: str, manager_id: str):
        """Назначение менеджера (как в PowerShell)"""
        try:
            conn = await self._get_connection()
            
            # Поиск менеджера по pager
            manager_filter = f"(pager={manager_id})"
            conn.search(
                'DC=central,DC=st-ing,DC=com',
                manager_filter,
                attributes=['distinguishedName']
            )
            
            if conn.entries:
                manager = conn.entries[0]
                manager_dn = manager.distinguishedName.value
                
                user_filter = f"(sAMAccountName={sam_account_name})"
                conn.search(
                    'DC=central,DC=st-ing,DC=com',
                    user_filter,
                    attributes=['distinguishedName']
                )
                
                if conn.entries:
                    user_dn = conn.entries[0].distinguishedName.value
                    conn.modify(
                        user_dn,
                        {'manager': [(MODIFY_REPLACE, [manager_dn])]}
                    )
                    ldap_logger.info(f"Менеджер {manager_id} назначен для пользователя {sam_account_name}")
                else:
                    ldap_logger.warning(f"Пользователь {sam_account_name} не найден для назначения менеджера")
            else:
                ldap_logger.warning(f"Менеджер с pager {manager_id} не найден")
                
        except Exception as e:
            ldap_logger.warning(f"Ошибка назначения менеджера: {e}")
    
    async def block_user(self, unique_id: str) -> Dict[str, Any]:
        """Блокировка пользователя в AD через LDAP (точно как в PS_block.ps1)"""
        try:
            ldap_logger.info(f"Блокировка пользователя через LDAP: {unique_id}")
            
            conn = await self._get_connection()
            
            search_filter = f"(pager={unique_id})"
            conn.search(
                'DC=central,DC=st-ing,DC=com',
                search_filter,
                attributes=['sAMAccountName', 'memberOf', 'distinguishedName']
            )
            
            if not conn.entries:
                return {"success": False, "stderr": f"Пользователь с pager {unique_id} не найден"}
            
            user = conn.entries[0]
            sam_account_name = user.sAMAccountName.value
            
            if hasattr(user, 'memberOf') and user.memberOf:
                for group_dn in user.memberOf.values:
                    try:
                        conn.extend.microsoft.remove_members_from_groups(
                            sam_account_name,
                            group_dn
                        )
                        ldap_logger.info(f"Удален из группы: {group_dn}")
                    except Exception as e:
                        ldap_logger.warning(f"Ошибка удаления из группы {group_dn}: {e}")
            
            conn.modify(
                user.entry_dn,
                {'userAccountControl': [(MODIFY_REPLACE, ['2'])]}  # ACCOUNTDISABLE
            )
            
            conn.modify(
                user.entry_dn,
                {'pager': [(MODIFY_REPLACE, [unique_id])]}
            )
            
            target_ou = "OU=Уволенные сотрудники,DC=central,DC=st-ing,DC=com"
            try:
                conn.modify_dn(
                    user.distinguishedName.value,
                    f"CN={sam_account_name}",
                    new_superior=target_ou
                )
                ldap_logger.info(f"Перемещен в OU: {target_ou}")
            except Exception as e:
                ldap_logger.warning(f"Ошибка перемещения в OU: {e}")
            
            if conn.result['result'] == 0:
                ldap_logger.info(f"Пользователь {sam_account_name} заблокирован через LDAP")
                return {"success": True, "stdout": f"User {sam_account_name} blocked successfully"}
            else:
                error_msg = f"Ошибка блокировки: {conn.result}"
                ldap_logger.error(error_msg)
                return {"success": False, "stderr": error_msg}
                
        except Exception as e:
            ldap_logger.error(f"Исключение при блокировке через LDAP: {e}")
            return {"success": False, "stderr": str(e)}
    
    async def change_password(self, username: str, new_password: str) -> Dict[str, Any]:
        """Смена пароля пользователя через LDAP (точно как в PowerShell)"""
        try:
            ldap_logger.info(f"Смена пароля через LDAP для пользователя: {username}")
            
            conn = await self._get_connection()
            
            search_filter = f"(sAMAccountName={username})"
            conn.search(
                'DC=central,DC=st-ing,DC=com',
                search_filter,
                attributes=['distinguishedName']
            )
            
            if not conn.entries:
                return {"success": False, "stderr": f"Пользователь {username} не найден"}
            
            user_dn = conn.entries[0].distinguishedName.value
            
            conn.extend.microsoft.modify_password(user_dn, new_password)
            
            conn.modify(
                user_dn,
                {'pwdLastSet': [(MODIFY_REPLACE, ['-1'])]} 
            )
            
            if conn.result['result'] == 0:
                ldap_logger.info(f"Пароль для пользователя {username} изменен через LDAP")
                return {"success": True, "stdout": f"Password changed successfully for {username}"}
            else:
                error_msg = f"Ошибка смены пароля: {conn.result}"
                ldap_logger.error(error_msg)
                return {"success": False, "stderr": error_msg}
                
        except Exception as e:
            ldap_logger.error(f"Исключение при смене пароля через LDAP: {e}")
            return {"success": False, "stderr": str(e)}
    
    async def export_users_from_ad(self) -> Dict[str, Any]:
        """Экспорт всех пользователей из AD через LDAP (точно как в PowerShell)"""
        try:
            ldap_logger.info("Экспорт пользователей из AD через LDAP")
            
            conn = await self._get_connection()
            
            conn.search(
                'DC=central,DC=st-ing,DC=com',
                '(&(objectClass=user)(objectCategory=person)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))',
                attributes=['sAMAccountName', 'displayName', 'mail', 'department', 'company', 'pager', 'givenName', 'physicalDeliveryOfficeName', 'telephoneNumber', 'description', 'lastLogon', 'pwdLastSet', 'whenCreated', 'whenChanged', 'userAccountControl'],
                search_scope=SUBTREE
            )
            
            users = []
            for entry in conn.entries:
                display_name = entry.displayName.value if hasattr(entry, 'displayName') else ''
                if display_name and not any(system in display_name for system in ['Служебная учетная запись', 'Microsoft', 'E4E', 'SystemMailbox', 'HealthMailbox', 'wms', 'WMS']):
                users.append({
                        'displayName': display_name,
                    'mail': entry.mail.value if hasattr(entry, 'mail') else '',
                        'givenName': entry.givenName.value if hasattr(entry, 'givenName') else '',
                        'physicalDeliveryOfficeName': entry.physicalDeliveryOfficeName.value if hasattr(entry, 'physicalDeliveryOfficeName') else '',
                    'department': entry.department.value if hasattr(entry, 'department') else '',
                        'description': entry.description.value if hasattr(entry, 'description') else '',
                        'pager': entry.pager.value if hasattr(entry, 'pager') else '',
                        'sAMAccountName': entry.sAMAccountName.value if hasattr(entry, 'sAMAccountName') else '',
                    'company': entry.company.value if hasattr(entry, 'company') else '',
                        'telephoneNumber': entry.telephoneNumber.value if hasattr(entry, 'telephoneNumber') else '',
                        'lastLogon': entry.lastLogon.value if hasattr(entry, 'lastLogon') else '',
                        'pwdLastSet': entry.pwdLastSet.value if hasattr(entry, 'pwdLastSet') else '',
                        'whenCreated': entry.whenCreated.value if hasattr(entry, 'whenCreated') else '',
                        'whenChanged': entry.whenChanged.value if hasattr(entry, 'whenChanged') else '',
                        'userAccountControl': entry.userAccountControl.value if hasattr(entry, 'userAccountControl') else ''
                    })
            
            ldap_logger.info(f"Экспортировано {len(users)} пользователей через LDAP")
            return {
                "success": True,
                "users": users,
                "count": len(users),
                "stdout": f"Exported {len(users)} users successfully"
            }
            
        except Exception as e:
            ldap_logger.error(f"Исключение при экспорте через LDAP: {e}")
            return {"success": False, "stderr": str(e)}
    
    async def change_phone_number(self, pager: str, new_phone: str) -> Dict[str, Any]:
        """Смена номера телефона пользователя через LDAP (точно как в PowerShell)"""
        try:
            ldap_logger.info(f"Смена номера телефона через LDAP для пользователя: {pager}")
            
            conn = await self._get_connection()
            
            search_filter = f"(pager={pager})"
            conn.search(
                'DC=central,DC=st-ing,DC=com',
                search_filter,
                attributes=['sAMAccountName']
            )
            
            if not conn.entries:
                return {"success": False, "stderr": f"Пользователь с pager {pager} не найден"}
            
            user = conn.entries[0]
            sam_account_name = user.sAMAccountName.value
            
            conn.modify(
                user.entry_dn,
                {'telephoneNumber': [(MODIFY_REPLACE, [new_phone])]}
            )
            
            if conn.result['result'] == 0:
                ldap_logger.info(f"Номер телефона для пользователя {pager} изменен через LDAP")
                return {"success": True, "stdout": f"Phone number changed successfully for {pager}"}
            else:
                error_msg = f"Ошибка смены номера телефона: {conn.result}"
                ldap_logger.error(error_msg)
                return {"success": False, "stderr": error_msg}
                
        except Exception as e:
            ldap_logger.error(f"Исключение при смене номера телефона через LDAP: {e}")
            return {"success": False, "stderr": str(e)}
    
    async def assign_manager(self, employee_id: str, manager_id: str) -> Dict[str, Any]:
        """Назначение менеджера для пользователя через LDAP (точно как в PowerShell)"""
        try:
            ldap_logger.info(f"Назначение менеджера через LDAP: {manager_id} для {employee_id}")
            
            conn = await self._get_connection()
            

            manager_filter = f"(pager={manager_id})"
            conn.search(
                'DC=central,DC=st-ing,DC=com',
                manager_filter,
                attributes=['sAMAccountName', 'distinguishedName']
            )
            
            if not conn.entries:
                return {"success": False, "stderr": f"Менеджер с pager {manager_id} не найден"}
            
            manager = conn.entries[0]
            manager_dn = manager.distinguishedName.value
            
            employee_filter = f"(pager={employee_id})"
            conn.search(
                'DC=central,DC=st-ing,DC=com',
                employee_filter,
                attributes=['sAMAccountName']
            )
            
            if not conn.entries:
                return {"success": False, "stderr": f"Сотрудник с pager {employee_id} не найден"}
            
            employee = conn.entries[0]

            conn.modify(
                employee.entry_dn,
                {'manager': [(MODIFY_REPLACE, [manager_dn])]}
            )
            
            if conn.result['result'] == 0:
                ldap_logger.info(f"Менеджер {manager_id} назначен для сотрудника {employee_id} через LDAP")
                return {"success": True, "stdout": f"Manager assigned successfully"}
            else:
                error_msg = f"Ошибка назначения менеджера: {conn.result}"
                ldap_logger.error(error_msg)
                return {"success": False, "stderr": error_msg}
                
        except Exception as e:
            ldap_logger.error(f"Исключение при назначении менеджера через LDAP: {e}")
            return {"success": False, "stderr": str(e)}
    
    async def block_user_complete(self, unique_id: str) -> Dict[str, Any]:
        """Полная блокировка пользователя"""
        try:
            ldap_logger.info(f"Полная блокировка пользователя через LDAP: {unique_id}")
            
            conn = await self._get_connection()
            
            search_filter = f"(pager={unique_id})"
            conn.search(
                'DC=central,DC=st-ing,DC=com',
                search_filter,
                attributes=['sAMAccountName', 'memberOf', 'distinguishedName']
            )
            
            if not conn.entries:
                return {"success": False, "stderr": f"Пользователь с pager {unique_id} не найден"}
            
            user = conn.entries[0]
            sam_account_name = user.sAMAccountName.value

            if hasattr(user, 'memberOf') and user.memberOf:
                for group_dn in user.memberOf.values:
                    try:
                        conn.extend.microsoft.remove_members_from_groups(
                            sam_account_name,
                            group_dn
                        )
                        ldap_logger.info(f"Удален из группы: {group_dn}")
                    except Exception as e:
                        ldap_logger.warning(f"Ошибка удаления из группы {group_dn}: {e}")
            
            target_ou = "OU=Уволенные сотрудники,DC=central,DC=st-ing,DC=com"
            try:
                conn.modify_dn(
                    user.distinguishedName.value,
                    f"CN={sam_account_name}",
                    new_superior=target_ou
                )
                ldap_logger.info(f"Перемещен в OU: {target_ou}")
            except Exception as e:
                ldap_logger.warning(f"Ошибка перемещения в OU: {e}")
            
            conn.modify(
                user.entry_dn,
                {'userAccountControl': [(MODIFY_REPLACE, ['2'])]}  # ACCOUNTDISABLE
            )
            
            if conn.result['result'] == 0:
                ldap_logger.info(f"Пользователь {sam_account_name} полностью заблокирован через LDAP")
                return {"success": True, "stdout": f"User {sam_account_name} completely blocked"}
            else:
                error_msg = f"Ошибка полной блокировки: {conn.result}"
                ldap_logger.error(error_msg)
                return {"success": False, "stderr": error_msg}
                
        except Exception as e:
            ldap_logger.error(f"Исключение при полной блокировке через LDAP: {e}")
            return {"success": False, "stderr": str(e)}
    
    async def create_new_object(self, object_name: str) -> Dict[str, Any]:
        """Создание нового объекта в AD (точно как в CreateNewObject.ps1)"""
        try:
            ldap_logger.info(f"Создание нового объекта в AD: {object_name}")
            
            ou_result = await self._create_ad_ou_for_object(object_name)
            if not ou_result["success"]:
                return ou_result
            
            group_result = await self._create_ad_groups_for_object(object_name, ou_result["ou_path"])
            if not group_result["success"]:
                return group_result
            
            folders = [
                "01 Производство Документация", 
                "02 Производство", 
                "03 Проектирование", 
                "04 Сметная документация", 
                "05 Общая", 
                "06 ПТО", 
                "07 Документация", 
                "08 Договора", 
                "09 Протоколы совещаний", 
                "10 Безопасность", 
                "11 Субподрядчики", 
                "12 Вендор-лист", 
                "13 Транспортные расходы", 
                "14 MTO", 
                "15 Заявки"
            ]
            
            base_path = f"\\\\datastorage\\Storage\\06_СТИ\\Строительные объекты\\{object_name}"
            
            if not await self._path_exists(base_path):
                await self._create_directory(base_path)
                ldap_logger.info(f"Основная папка создана: {base_path}")
            else:
                ldap_logger.info(f"Основная папка уже существует: {base_path}")
            
            for folder in folders:
                folder_path = f"{base_path}\\{folder}"
                if not await self._path_exists(folder_path):
                    await self._create_directory(folder_path)
                    ldap_logger.info(f"Папка '{folder}' создана")
                else:
                    ldap_logger.info(f"Папка '{folder}' уже существует")
            
            return {
                "success": True,
                "message": f"Объект {object_name} создан успешно",
                "details": {
                    "ou_created": ou_result["success"],
                    "groups_created": group_result["groups_count"],
                    "folders_created": len(folders) + 1  # +1 для основной папки
                }
            }
            
        except Exception as e:
            ldap_logger.error(f"Исключение при создании объекта: {e}")
            return {"success": False, "stderr": str(e)}
    
    async def _create_ad_ou_for_object(self, object_name: str) -> Dict[str, Any]:
        """Создание OU для объекта (точно как в PowerShell)"""
        try:
            conn = await self._get_connection()
            
            ou_name = f"права {object_name}"
            ou_path = f"OU={ou_name},OU=права доступа к папкам строительных объектов,OU=Группы прав доступа к папкам,DC=central,DC=st-ing,DC=com"
            
            conn.search(
                'DC=central,DC=st-ing,DC=com',
                f'(name="{ou_name}")',
                attributes=['distinguishedName']
            )
            
            if not conn.entries:
                attributes = {
                    'objectClass': ['top', 'organizationalUnit'],
                    'name': ou_name
                }
                
                success = conn.add(ou_path, attributes=attributes)
                
                if success:
                    ldap_logger.info(f"OU '{ou_name}' создана в AD")
                    return {"success": True, "ou_path": ou_path, "message": f"OU {ou_name} created successfully"}
                else:
                    error_msg = f"Ошибка создания OU: {conn.result}"
                    ldap_logger.error(error_msg)
                    return {"success": False, "stderr": error_msg}
            else:
                ldap_logger.info(f"OU '{ou_name}' уже существует")
                return {"success": True, "ou_path": ou_path, "message": f"OU {ou_name} already exists"}
                
        except Exception as e:
            ldap_logger.error(f"Исключение при создании OU: {e}")
            return {"success": False, "stderr": str(e)}
    
    async def _create_ad_groups_for_object(self, object_name: str, ou_path: str) -> Dict[str, Any]:
        """Создание групп AD для объекта (точно как в PowerShell)"""
        try:
            conn = await self._get_connection()
            
            groups_created = 0
            
            basic_groups = [
                f"STORAGE-{object_name}-write",
                f"STORAGE-{object_name}-read"
            ]
            
            for group_name in basic_groups:
                success = await self._create_single_ad_group(group_name, ou_path)
                if success:
                    groups_created += 1
            
            folders = [
                "01 Производство Документация", 
                "02 Производство", 
                "03 Проектирование", 
                "04 Сметная документация", 
                "05 Общая", 
                "06 ПТО", 
                "07 Документация", 
                "08 Договора", 
                "09 Протоколы совещаний", 
                "10 Безопасность", 
                "11 Субподрядчики", 
                "12 Вендор-лист", 
                "13 Транспортные расходы", 
                "14 MTO", 
                "15 Заявки"
            ]
            
            for folder in folders:
                folder_name = folder.replace(' ', '-') 
                read_group = f"STORAGE-{object_name}-{folder_name}-read"
                write_group = f"STORAGE-{object_name}-{folder_name}-write"
                
                success_read = await self._create_single_ad_group(read_group, ou_path)
                if success_read:
                    groups_created += 1
                
                success_write = await self._create_single_ad_group(write_group, ou_path)
                if success_write:
                    groups_created += 1
            
            ldap_logger.info(f"Создано {groups_created} групп для объекта {object_name}")
            return {"success": True, "groups_count": groups_created, "message": f"Created {groups_created} groups"}
            
        except Exception as e:
            ldap_logger.error(f"Исключение при создании групп: {e}")
            return {"success": False, "stderr": str(e)}
    
    async def _create_single_ad_group(self, group_name: str, ou_path: str) -> bool:
        """Создание одной группы AD"""
        try:
            conn = await self._get_connection()
            
            conn.search(
                'DC=central,DC=st-ing,DC=com',
                f'(name="{group_name}")',
                attributes=['distinguishedName']
            )
            
            if not conn.entries:
                group_dn = f"CN={group_name},{ou_path}"
                
                attributes = {
                    'objectClass': ['top', 'group'],
                    'name': group_name,
                    'sAMAccountName': group_name,
                    'groupType': '2147483650', 
                    'groupCategory': '1'  
                }
                
                success = conn.add(group_dn, attributes=attributes)
                
                if success:
                    ldap_logger.info(f"Группа '{group_name}' создана")
                    return True
                else:
                    ldap_logger.warning(f"Ошибка создания группы '{group_name}': {conn.result}")
                    return False
            else:
                ldap_logger.info(f"Группа '{group_name}' уже существует")
                return True
                
        except Exception as e:
            ldap_logger.warning(f"Ошибка при создании группы '{group_name}': {e}")
            return False
    
    async def _create_file_folders(self, object_name: str, folders: list):
        """Создание файловых папок через WinRM (точно как в CreateNewObject.ps1)"""
        try:
            from app.infrastructure.external.winrm_service import WinRMService
            
            winrm_service = WinRMService()
            return await winrm_service.create_file_folders(object_name, folders)
            
        except Exception as e:
            ldap_logger.warning(f"Ошибка при создании файловых папок: {e}")
            return {"success": False, "stderr": str(e)}
    
    async def _path_exists(self, path: str) -> bool:
        """Проверка существования пути (аналог Test-Path в PowerShell)"""
        try:
            from app.infrastructure.external.winrm_service import WinRMService
            
            winrm_service = WinRMService()
            ps_script = f"""
            if (Test-Path "{path}") {{
                Write-Host "EXISTS"
            }} else {{
                Write-Host "NOT_EXISTS"
            }}
            """
            
            result = await winrm_service.execute_powershell(ps_script)
            return "EXISTS" in result.get("stdout", "")
            
        except Exception as e:
            ldap_logger.warning(f"Ошибка проверки пути {path}: {e}")
            return False
    
    async def _create_directory(self, path: str):
        """Создание директории (аналог New-Item в PowerShell)"""
        try:
            from app.infrastructure.external.winrm_service import WinRMService
            
            winrm_service = WinRMService()
            ps_script = f"""
            New-Item -ItemType Directory -Path "{path}" -Force
            Write-Host "Directory created: {path}"
            """
            
            result = await winrm_service.execute_powershell(ps_script)
            if not result["success"]:
                ldap_logger.warning(f"Ошибка создания директории {path}: {result.get('stderr', '')}")
                
        except Exception as e:
            ldap_logger.warning(f"Ошибка создания директории {path}: {e}")
    
    async def _execute_powershell(self, script: str) -> Dict[str, Any]:
        """Выполнение PowerShell скрипта через WinRM"""
        try:
            from app.infrastructure.external.winrm_service import WinRMService
            
            winrm_service = WinRMService()
            return await winrm_service.execute_powershell(script)
            
        except Exception as e:
            ldap_logger.error(f"Ошибка выполнения PowerShell: {e}")
            return {"success": False, "stderr": str(e)}
    
    async def update_test_attributes(self, pager: str, test_type: str) -> Dict[str, Any]:
        """Обновление тестовых атрибутов пользователя через LDAP (точно как в testSuccessful.ps1)"""
        try:
            ldap_logger.info(f"Обновление тестовых атрибутов через LDAP: {pager}, тип: {test_type}")
            
            conn = await self._get_connection()
            
            search_filter = f"(pager={pager})"
            conn.search(
                'DC=central,DC=st-ing,DC=com',
                search_filter,
                attributes=['sAMAccountName', 'extensionAttribute1', 'extensionAttribute2']
            )
            
            if not conn.entries:
                return {"success": False, "stderr": f"Пользователь с pager {pager} не найден"}
            
            user = conn.entries[0]
            sam_account_name = user.sAMAccountName.value
            
            attribute_to_update = None
            if any(keyword in test_type.lower() for keyword in ['anykey', 'facekit']):
                attribute_to_update = 'extensionAttribute1'
            elif 'sysadmin' in test_type.lower():
                attribute_to_update = 'extensionAttribute2'
            else:
                return {"success": False, "stderr": f"Неизвестный тип теста: {test_type}"}
            
            conn.modify(
                user.entry_dn,
                {attribute_to_update: [(MODIFY_REPLACE, ['true'])]}  # Устанавливаем true как в PowerShell
            )
            
            if conn.result['result'] == 0:
                ldap_logger.info(f"Тестовый атрибут {attribute_to_update} обновлен для пользователя {sam_account_name}")
                return {
                    "success": True, 
                    "stdout": f"Test attribute {attribute_to_update} updated successfully for {sam_account_name}",
                    "attribute": attribute_to_update,
                    "value": test_type
                }
            else:
                error_msg = f"Ошибка обновления атрибута: {conn.result}"
                ldap_logger.error(error_msg)
                return {"success": False, "stderr": error_msg}
                
        except Exception as e:
            ldap_logger.error(f"Исключение при обновлении тестовых атрибутов через LDAP: {e}")
            return {"success": False, "stderr": str(e)}
