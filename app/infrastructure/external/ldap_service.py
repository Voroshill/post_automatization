import asyncio
import os
import subprocess
from typing import Dict, Any, Optional, List
from ldap3 import Server, Connection, ALL, NTLM, SIMPLE, SUBTREE, MODIFY_REPLACE
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
        
        self.server = Server(self.ad_server, get_info=ALL, connect_timeout=settings.ldap_timeout, use_ssl=False, port=389)
        self.connection = None
    
    async def _get_connection(self) -> Connection:
        """Получение подключения к AD"""
        if not self.connection or not self.connection.bound:
            # Логируем параметры подключения
            ldap_logger.info(f"Создание LDAP подключения:")
            ldap_logger.info(f"  Сервер: {self.ad_server}")
            ldap_logger.info(f"  Домен: {self.ad_domain}")
            ldap_logger.info(f"  Пользователь: {self.admin_username}")
            # фактический формат логина и тип аутентификации уточняются ниже (SIMPLE, UPN)
            ldap_logger.info(f"  Формат пользователя: UPN")
            ldap_logger.info(f"  Аутентификация: SIMPLE")
            ldap_logger.info(f"  Timeout: {settings.ldap_timeout}")
            ldap_logger.info(f"  SSL: False")
            
            try:
                auth_user = (
                    self.admin_username
                    if "@" in self.admin_username
                    else f"{self.admin_username}@{self.ad_domain}"
                )
                self.connection = Connection(
                    self.server,
                    user=auth_user,
                    password=self.admin_password,
                    authentication=SIMPLE,
                    auto_bind=True
                )
                
                ldap_logger.info(f"LDAP подключение создано успешно")
                ldap_logger.info(f"  Статус привязки: {self.connection.bound}")
                ldap_logger.info(f"  Результат подключения: {self.connection.result}")
                
                if not self.connection.bound:
                    ldap_logger.error(f"LDAP подключение не привязано!")
                    ldap_logger.error(f"  Код ошибки: {self.connection.result.get('result', 'N/A')}")
                    ldap_logger.error(f"  Описание: {self.connection.result.get('description', 'N/A')}")
                    ldap_logger.error(f"  Сообщение: {self.connection.result.get('message', 'N/A')}")
                    raise Exception(f"Не удалось подключиться к AD: {self.connection.result}")
                else:
                    ldap_logger.info(f"LDAP подключение успешно привязано!")
                    
            except Exception as e:
                ldap_logger.error(f"Исключение при создании LDAP подключения: {str(e)}")
                ldap_logger.error(f"  Тип исключения: {type(e).__name__}")
                raise
        
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
            # Используем только название отдела (как в PowerShell)
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
            elif 'пто' in department.lower():
                return "OU=Отдел ПТО,OU=Технический департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            elif 'метный' in department.lower():
                return "OU=Сметный отдел,OU=Технический департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            elif 'планово' in department.lower():
                return "OU=Планово экономический отдел,OU=Финансовый департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            elif 'ухгалтери' in department.lower():
                return "OU=Бухгалтерия,OU=Финансовый департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            elif 'азначе' in department.lower():
                return "OU=Казначейство,OU=Финансовый департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            elif 'ридически' in department.lower():
                return "OU=Юридический отдел,OU=Юридический департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            elif 'дминистративны' in department.lower():
                return "OU=Административный отдел,OU=Департамент обеспечения,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        
        # Проверяем строительные объекты - используем полное название объекта
        construction_objects = ['емеров', 'амчатк', 'гнитогор', 'инько', 'ер К32', 'авидо', 'ктафар', 'ухарев', 'алент', 'рофлот', 'ON']
        for obj in construction_objects:
            if obj in obj_name.lower():
                # Точно как в PowerShell: создаем индивидуальную OU для каждого строительного объекта
                individual_ou = f"OU={obj_name},OU=Строительные объекты,OU=Отдел управления проектами,OU=Технический департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
                
                # Проверяем, не превышает ли DN лимит в 256 символов
                if len(individual_ou) > 256:
                    ldap_logger.warning(f"Индивидуальная OU слишком длинная ({len(individual_ou)} символов), используем общую OU")
                    return "OU=Строительные объекты,OU=Отдел управления проектами,OU=Технический департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
                
                return individual_ou
        
        # Если не найдена подходящая OU, возвращаем ошибку (точно как в PowerShell)
        raise ValueError(f"Не найдена подходящая организационная единица для объекта '{obj_name}' и отдела '{department}'")
    
    async def list_available_ous(self) -> List[str]:
        """Получение списка всех доступных организационных единиц в AD"""
        try:
            conn = await self._get_connection()
            
            # Поиск всех OU в домене
            conn.search(
                'DC=central,DC=st-ing,DC=com',
                '(objectClass=organizationalUnit)',
                attributes=['distinguishedName']
            )
            
            ous = []
            for entry in conn.entries:
                ous.append(entry.distinguishedName.value)
            
            ldap_logger.info(f"Найдено {len(ous)} организационных единиц:")
            for ou in sorted(ous):
                ldap_logger.info(f"  - {ou}")
            
            return ous
            
        except Exception as e:
            ldap_logger.error(f"Ошибка получения списка OU: {e}")
            return []
    
    async def create_user_in_ad(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание пользователя в Active Directory через LDAP (точно как в PowerShell)"""
        try:
            ldap_logger.info(f"=== НАЧАЛО СОЗДАНИЯ ПОЛЬЗОВАТЕЛЯ В AD ===")
            ldap_logger.info(f"ID пользователя: {user_data.get('unique_id', 'Unknown')}")
            ldap_logger.info(f"Имя: {user_data.get('firstname', '')}")
            ldap_logger.info(f"Фамилия: {user_data.get('secondname', '')}")
            ldap_logger.info(f"Компания: {user_data.get('company', '')}")
            ldap_logger.info(f"Департамент: {user_data.get('department', '')}")
            ldap_logger.info(f"Отдел: {user_data.get('otdel', '')}")
            ldap_logger.info(f"Локация: {user_data.get('current_location_id', '')}")
            
            ldap_logger.info(f"Получение LDAP подключения...")
            conn = await self._get_connection()
            ldap_logger.info(f"LDAP подключение получено успешно")
            
            # Подготовка данных пользователя
            ldap_logger.info(f"Подготовка данных пользователя...")
            firstname_translit = self.translit(user_data.get('firstname', ''))
            secondname_translit = self.translit(user_data.get('secondname', ''))
            sam_account_name = f"{firstname_translit}.{secondname_translit}"
            
            ldap_logger.info(f"  Транслитерация: {user_data.get('firstname', '')} -> {firstname_translit}")
            ldap_logger.info(f"  Транслитерация: {user_data.get('secondname', '')} -> {secondname_translit}")
            ldap_logger.info(f"  SAM Account Name: {sam_account_name}")
            
            user_principal_name = self.get_user_principal_name(sam_account_name, user_data.get('company', ''))
            ldap_logger.info(f"  User Principal Name: {user_principal_name}")
            
            # Определяем тип пользователя: если is_engineer == 1, то технический
            if user_data.get('is_engineer') == 1:
                ou = 'OU=Технические логины,DC=central,DC=st-ing,DC=com'
                ldap_logger.info(f"  Тип пользователя: Технический (is_engineer=1)")
            else:
                # Определяем OU по логике из PowerShell скрипта
                ou = self.find_ou(
                    user_data.get('current_location_id', ''), 
                    user_data.get('department', '')
                )
                ldap_logger.info(f"  Тип пользователя: Обычный (is_engineer={user_data.get('is_engineer', 'None')})")
                ldap_logger.info(f"  OU найдена по логике: {ou}")
            
            ldap_logger.info(f"  Организационная единица: {ou}")
            
            # Строим отображаемое имя без лишних пробелов
            name_parts = [
                (user_data.get('firstname', '') or '').strip(),
                (user_data.get('secondname', '') or '').strip(),
                (user_data.get('thirdname', '') or '').strip(),
            ]
            display_name = ' '.join([p for p in name_parts if p])
            
            # Сначала проверяем длину OU и сокращаем CN соответственно
            ou_length = len(ou)
            max_dn_length = 200  # Более консервативный лимит для AD
            max_cn_length = max_dn_length - ou_length - 4  # 4 символа для "CN=,"
            
            ldap_logger.info(f"  Длина OU: {ou_length} символов")
            ldap_logger.info(f"  Максимальная длина CN: {max_cn_length} символов")
            
            # Сокращаем CN с учетом длины OU
            cn_name = display_name
            if len(cn_name) > max_cn_length:
                ldap_logger.warning(f"  CN слишком длинный ({len(cn_name)} символов), сокращаем")
                
                # Сначала пробуем только имя и фамилию
                firstname = (user_data.get('firstname', '') or '').strip()
                secondname = (user_data.get('secondname', '') or '').strip()
                cn_name = ' '.join([p for p in [firstname, secondname] if p])
                
                if len(cn_name) > max_cn_length:
                    # Если и это слишком длинное, сокращаем каждую часть
                    firstname_len = min(len(firstname), max_cn_length // 2)
                    secondname_len = min(len(secondname), max_cn_length - firstname_len - (1 if firstname_len and secondname else 0))
                    
                    cn_join = ' ' if firstname_len and secondname_len else ''
                    cn_name = f"{firstname[:firstname_len]}{cn_join}{secondname[:secondname_len]}".strip()
                    
                    # Если все еще слишком длинное, используем только имя
                    if len(cn_name) > max_cn_length:
                        cn_name = firstname[:max_cn_length]
                        
                    ldap_logger.warning(f"  CN сокращен до: '{cn_name}' ({len(cn_name)} символов)")
            
            # Экранируем значение RDN согласно RFC 4514 (для DN используем экранированное, для атрибутов — исходное значение)
            def _escape_rdn_value(val: str) -> str:
                v = (val or '')
                # Сначала экранируем обратную косую черту
                v = v.replace('\\', '\\\\')
                # Затем остальные спецсимволы RDN
                for ch in [',', '+', '"', '<', '>', ';', '=']:
                    v = v.replace(ch, f"\\{ch}")
                # Экранируем ведущий пробел или #
                if v.startswith(' '):
                    v = '\\ ' + v[1:]
                if v.startswith('#'):
                    v = '\\#' + v[1:]
                # Экранируем замыкающий пробел
                if v.endswith(' '):
                    v = v[:-1] + '\\ '
                return v

            escaped_cn_for_dn = _escape_rdn_value(cn_name)
            user_dn = f"CN={escaped_cn_for_dn},{ou}"
            ldap_logger.info(f"  Distinguished Name: {user_dn}")
            
            # Финальная проверка длины DN
            if len(user_dn) > max_dn_length:
                ldap_logger.error(f"  ❌ DN все еще слишком длинный ({len(user_dn)} символов)")
                # Используем только SAM Account Name как CN
                cn_name = sam_account_name
                user_dn = f"CN={cn_name},{ou}"
                ldap_logger.warning(f"  Используем SAM Account Name как CN: {user_dn}")
                
                # Если и это не помогает, используем короткий CN
                if len(user_dn) > max_dn_length:
                    cn_name = f"User{user_data.get('unique_id', '')}"
                    user_dn = f"CN={cn_name},{ou}"
                    ldap_logger.warning(f"  Используем короткий CN: {user_dn}")
            
            ldap_logger.info(f"  Итоговый DN ({len(user_dn)} символов): {user_dn}")
            if cn_name != display_name:
                ldap_logger.info(f"  CN сокращен с '{display_name}' до '{cn_name}'")
            
            # Финальная валидация DN перед созданием
            if len(user_dn) > max_dn_length:
                error_msg = f"DN слишком длинный ({len(user_dn)} символов), максимально допустимо {max_dn_length}"
                ldap_logger.error(f"❌ {error_msg}")
                return {"success": False, "stderr": error_msg}
            
            # Дополнительная диагностика DN
            ldap_logger.info(f"  Диагностика DN:")
            ldap_logger.info(f"    Длина OU: {ou_length}")
            ldap_logger.info(f"    Длина CN: {len(cn_name)}")
            ldap_logger.info(f"    Общая длина DN: {len(user_dn)}")
            ldap_logger.info(f"    Лимит DN: {max_dn_length}")
            ldap_logger.info(f"    Запас: {max_dn_length - len(user_dn)} символов")
            
            attributes = {
                'objectClass': ['top', 'person', 'organizationalPerson', 'user'],
                'cn': cn_name,
                'sAMAccountName': sam_account_name,
                'userPrincipalName': user_principal_name,
                'givenName': user_data.get('firstname', ''),
                'sn': user_data.get('secondname', ''),
                'displayName': cn_name,
                'mail': user_principal_name,
                'pager': user_data.get('unique_id', ''),
                'company': user_data.get('company', ''),
                'department': user_data.get('department', ''),
                'title': user_data.get('appointment', ''),
                'description': user_data.get('appointment', ''),
                'streetAddress': user_data.get('current_location_id', ''),
                'physicalDeliveryOfficeName': user_data.get('current_location_id', ''),
                'telephoneNumber': user_data.get('work_phone', ''),
                # Создаём ОТКЛЮЧЕННОГО пользователя, затем установим пароль по LDAPS и включим
                'userAccountControl': 514  # NORMAL_ACCOUNT + ACCOUNTDISABLE
            }
            
            # Валидация атрибутов перед использованием
            validated_attributes = {}
            for attr_name, attr_value in attributes.items():
                if attr_value is None or attr_value == '':
                    ldap_logger.warning(f"    Пропускаем пустой атрибут: {attr_name}")
                    continue
                
                # Специальная обработка для критических атрибутов
                if attr_name == 'userAccountControl':
                    validated_attributes[attr_name] = int(attr_value)
                    continue
                
                # Очистка от недопустимых символов
                if isinstance(attr_value, str):
                    # Удаляем только управляющие символы (0-31, 127) и недопустимые для LDAP символы
                    # Разрешаем кириллицу и другие Unicode символы
                    cleaned_value = ''.join(char for char in attr_value if ord(char) >= 32 and ord(char) != 127)
                    
                    # Специальная обработка для критических атрибутов
                    if attr_name in ['sAMAccountName', 'userPrincipalName']:
                        # Для SAM Account Name и UPN оставляем только латиницу, цифры, точки, дефисы и @
                        import re
                        cleaned_value = re.sub(r'[^a-zA-Z0-9.\-@]', '', cleaned_value)
                    elif attr_name in ['givenName', 'sn', 'displayName']:
                        # Для имен разрешаем кириллицу, латиницу, цифры, пробелы, точки и дефисы
                        import re
                        cleaned_value = re.sub(r'[^\u0400-\u04FF\u0500-\u052Fa-zA-Z0-9.\-\s]', '', cleaned_value)
                    
                    if cleaned_value != attr_value:
                        ldap_logger.warning(f"    Очищен атрибут {attr_name}: '{attr_value}' -> '{cleaned_value}'")
                    
                    # Проверяем, что значение не пустое после очистки
                    if cleaned_value.strip():
                        validated_attributes[attr_name] = cleaned_value.strip()
                    else:
                        ldap_logger.warning(f"    Атрибут {attr_name} стал пустым после очистки, пропускаем")
                else:
                    validated_attributes[attr_name] = attr_value

            # Проверяем обязательные атрибуты
            required_attrs = ['sAMAccountName', 'userPrincipalName', 'givenName', 'sn', 'displayName']
            missing_attrs = []
            for attr in required_attrs:
                if attr not in validated_attributes or not validated_attributes[attr]:
                    missing_attrs.append(attr)
            
            if missing_attrs:
                error_msg = f"Отсутствуют обязательные атрибуты: {', '.join(missing_attrs)}"
                ldap_logger.error(f"❌ {error_msg}")
                return {"success": False, "stderr": error_msg}
            
            ldap_logger.info(f"Все обязательные атрибуты присутствуют: {', '.join(required_attrs)}")
            
            # Проверка существования по sAMAccountName
            conn.search('DC=central,DC=st-ing,DC=com', f'(sAMAccountName={sam_account_name})', attributes=['distinguishedName'])
            exists_dn = conn.entries[0].distinguishedName.value if conn.entries else None

            # Создание или обновление пользователя в AD
            if exists_dn:
                ldap_logger.info(f"Пользователь уже существует: {sam_account_name} -> {exists_dn}")
                user_dn = exists_dn

                # Обновляем атрибуты существующего пользователя (без изменения RDN/CN)
                ldap_logger.info(f"Обновление атрибутов существующего пользователя...")

                # Подготавливаем атрибуты для обновления (исключаем неизменяемые атрибуты и CN как RDN)
                immutable_attrs = ['objectClass', 'userAccountControl', 'sAMAccountName', 'userPrincipalName', 'cn']

                # Используем правильный формат для LDAP modify
                changes = {}
                for attr_name, attr_value in validated_attributes.items():
                    if (attr_name not in immutable_attrs and 
                        attr_value and 
                        str(attr_value).strip() and
                        attr_name not in ['mail']):  # Исключаем mail, так как он может конфликтовать с UPN
                        changes[attr_name] = [(MODIFY_REPLACE, [str(attr_value).strip()])]

                ldap_logger.info(f"  Атрибуты для обновления: {len(changes)} атрибутов")
                for attr_name, change_list in changes.items():
                    ldap_logger.info(f"    {attr_name}: {change_list[0][1][0]}")

                # Выполняем обновление атрибутов с правильным форматом
                if changes:
                    success = conn.modify(user_dn, changes)
                else:
                    ldap_logger.info("  Нет атрибутов для обновления - пользователь уже актуален")
                    success = True
                ldap_logger.info(f"  Результат обновления: {success}")
                ldap_logger.info(f"  Код результата: {conn.result.get('result', 'N/A')}")
                ldap_logger.info(f"  Описание: {conn.result.get('description', 'N/A')}")
                
                if not success:
                    ldap_logger.error(f"Ошибка обновления пользователя: {conn.result}")
            else:
                ldap_logger.info(f"Создание пользователя в AD...")
                ldap_logger.info(f"  DN: {user_dn}")
                ldap_logger.info(f"  Атрибуты: {len(validated_attributes)} атрибутов")
                
                # Детальное логирование каждого атрибута
                for attr_name, attr_value in validated_attributes.items():
                    ldap_logger.info(f"    {attr_name}: {attr_value} (тип: {type(attr_value).__name__})")
                
                # Дополнительная проверка проблемных атрибутов
                for attr_name, attr_value in validated_attributes.items():
                    if isinstance(attr_value, str):
                        # Проверяем на пустые значения в критических атрибутах
                        if attr_name in ['sAMAccountName', 'userPrincipalName', 'givenName', 'sn'] and not attr_value.strip():
                            ldap_logger.error(f"    ПУСТОЕ ЗНАЧЕНИЕ в критическом атрибуте {attr_name}")
                        
                        # Проверяем на недопустимые символы
                        for i, char in enumerate(attr_value):
                            if ord(char) < 32 or ord(char) == 127:
                                ldap_logger.error(f"    НЕДОПУСТИМЫЙ СИМВОЛ в {attr_name}[{i}]: '{char}' (код: {ord(char)})")
                        # Проверяем длину
                        if len(attr_value) > 255:
                            ldap_logger.error(f"    СЛИШКОМ ДЛИННЫЙ {attr_name}: {len(attr_value)} символов")
                
                success = conn.add(user_dn, attributes=validated_attributes)
            
            # Логирование результата
            if exists_dn:
                ldap_logger.info(f"  Результат обновления: {success}")
            else:
                ldap_logger.info(f"  Результат создания: {success}")
            ldap_logger.info(f"  Код результата: {conn.result.get('result', 'N/A')}")
            ldap_logger.info(f"  Описание: {conn.result.get('description', 'N/A')}")
            
            if success:
                if exists_dn:
                    ldap_logger.info(f"✅ Пользователь {sam_account_name} успешно обновлен в AD через LDAP")
                else:
                    ldap_logger.info(f"✅ Пользователь {sam_account_name} успешно создан в AD через LDAP")
                # Установка пароля по LDAPS и включение пользователя, чтобы совпадать с поведением PowerShell
                ldap_logger.info(f"Установка пароля для пользователя по LDAPS...")
                try:
                    secure_server = Server(self.ad_server, get_info=ALL, connect_timeout=settings.ldap_timeout, use_ssl=True, port=636)
                    secure_conn = Connection(
                        secure_server,
                        user=(self.admin_username if "@" in self.admin_username else f"{self.admin_username}@{self.ad_domain}"),
                        password=self.admin_password,
                        authentication=SIMPLE,
                        auto_bind=True
                    )
                    secure_conn.extend.microsoft.modify_password(user_dn, settings.default_user_password)
                    ldap_logger.info(f"✅ Пароль установлен успешно (LDAPS)")
                    
                    # Включаем учетную запись (NORMAL_ACCOUNT = 512)
                    conn.modify(
                        user_dn,
                        {'userAccountControl': [(MODIFY_REPLACE, ['512'])]}
                    )
                    ldap_logger.info(f"✅ Пользователь включен (userAccountControl=512)")
                    
                    # Требовать смену пароля при первом входе
                    conn.modify(
                        user_dn,
                        {'pwdLastSet': [(MODIFY_REPLACE, ['0'])]}
                    )
                    ldap_logger.info(f"✅ Установлено требование смены пароля при первом входе")
                    
                except Exception as e:
                    ldap_logger.error(f"❌ Ошибка установки пароля: {str(e)}")
                
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
                # Получаем детальную информацию об ошибке от LDAP
                result_code = conn.result.get('result', 'N/A')
                description = conn.result.get('description', 'N/A')
                message = conn.result.get('message', 'N/A')
                
                # Преобразуем код ошибки в понятное сообщение
                error_messages = {
                    1: "Операция не выполнена",
                    2: "Протокольная ошибка",
                    3: "Таймаут",
                    4: "Размер превышен",
                    5: "Сравнение ложно",
                    6: "Сравнение истинно",
                    7: "Аутентификация не поддерживается",
                    8: "Сильные аутентификации требуются",
                    9: "Частичные результаты",
                    10: "Ссылки",
                    11: "Административное ограничение",
                    12: "Недоступно критическое расширение",
                    13: "Конфиденциальность требуется",
                    14: "SASL bind в процессе",
                    16: "Нет такого атрибута",
                    17: "Неопределенный тип атрибута",
                    18: "Неподходящий сопоставление",
                    19: "Ограничение нарушения",
                    20: "Атрибут или значение существует",
                    21: "Недопустимый синтаксис атрибута",
                    32: "Организационная единица не существует в Active Directory",
                    33: "Проблема псевдонима",
                    34: "Недопустимый DN синтаксис",
                    35: "Является листовым",
                    36: "Псевдоним проблема",
                    48: "Недостаточно прав",
                    49: "Недоступно",
                    50: "Занято",
                    51: "Неразрешимо",
                    52: "Нарушение ограничения времени",
                    53: "Нарушение ограничения размера",
                    64: "Тип объекта нарушает",
                    65: "Не разрешено на нелистовом",
                    66: "Не разрешено на RDN",
                    67: "Запись уже существует",
                    68: "Нет такого объекта класса",
                    69: "Проблема псевдонима",
                    70: "Проблема ссылки",
                    80: "Другая ошибка сервера"
                }
                
                human_error = error_messages.get(result_code, f"Неизвестная ошибка (код {result_code})")
                
                # Специальная обработка для ошибки "нет такого объекта" (код 32)
                if result_code == 32:
                    error_msg = f"Организационная единица не существует в Active Directory: {ou}"
                    error_msg += f"\nПроверьте, что OU '{ou}' создана в Active Directory."
                    if 'Строительные объекты' in ou:
                        error_msg += f"\nДля строительных объектов может потребоваться создание индивидуальной OU."
                else:
                    error_msg = f"LDAP ошибка: {human_error}"
                    if description != 'N/A':
                        error_msg += f" - {description}"
                    if message != 'N/A':
                        error_msg += f" ({message})"
                
                ldap_logger.error(f"❌ {error_msg}")
                ldap_logger.error(f"  Код ошибки: {result_code}")
                ldap_logger.error(f"  Описание: {description}")
                ldap_logger.error(f"  Сообщение: {message}")
                ldap_logger.error(f"  DN: {user_dn}")
                
                return {"success": False, "stderr": error_msg, "ldap_code": result_code, "ldap_description": description}
                
        except Exception as e:
            ldap_logger.error(f"❌ Исключение при создании пользователя через LDAP: {e}")
            ldap_logger.error(f"  Тип исключения: {type(e).__name__}")
            ldap_logger.error(f"  Детали: {str(e)}")
            return {"success": False, "stderr": str(e)}
    
    async def _add_user_to_groups(self, sam_account_name: str, user_data: Dict[str, Any]):
        """Добавление пользователя в группы AD (точно как в PowerShell)"""
        try:
            conn = await self._get_connection()
            
            # Ищем DN пользователя по sAMAccountName, так как методы расширения ждут DN
            user_dn: Optional[str] = None
            conn.search('DC=central,DC=st-ing,DC=com', f'(sAMAccountName={sam_account_name})', attributes=['distinguishedName'])
            if conn.entries:
                user_dn = conn.entries[0].distinguishedName.value
            else:
                ldap_logger.warning(f"Пользователь {sam_account_name} не найден для добавления в группы")
                return

            company = user_data.get('company', '')
            # Добавляем в организационные группы, используя DN групп
            if any(keyword in company.upper() for keyword in ['СТРОЙ', 'ТЕХНО', 'ИНЖЕНЕРИНГ', 'STI', 'ТРОЙ']):
                conn.search('DC=central,DC=st-ing,DC=com', '(cn=СтройТехноИнженеринг)', attributes=['distinguishedName'])
                if conn.entries:
                    org_grp_dn = conn.entries[0].distinguishedName.value
                    conn.extend.microsoft.add_members_to_groups(user_dn, org_grp_dn)
            elif any(keyword in company.upper() for keyword in ['DTTERMO', 'ДТ']):
                conn.search('DC=central,DC=st-ing,DC=com', '(cn=DttermoSign)', attributes=['distinguishedName'])
                if conn.entries:
                    org_grp_dn = conn.entries[0].distinguishedName.value
                    conn.extend.microsoft.add_members_to_groups(user_dn, org_grp_dn)
            
            department = user_data.get('department', '')
            if department:
                # Ищем DN группы по имени/CN, чтобы избежать ошибки "attribute type not present"
                grp_dn = None
                for filt in [f'(name={department})', f'(cn={department})']:
                    conn.search('DC=central,DC=st-ing,DC=com', filt, attributes=['distinguishedName'])
                    if conn.entries:
                        grp_dn = conn.entries[0].distinguishedName.value
                        break
                if grp_dn:
                    conn.extend.microsoft.add_members_to_groups(user_dn, grp_dn)
                else:
                    ldap_logger.warning(f"Группа отдела не найдена: {department}")
                
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
            current_dn = user.entry_dn
            
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
            
            # Отключаем учетную запись по текущему DN (идемпотентно)
            try:
                conn.modify(
                    current_dn,
                    {'userAccountControl': [(MODIFY_REPLACE, ['2'])]}  # ACCOUNTDISABLE
                )
                if conn.result['result'] == 0:
                    ldap_logger.info("Учетная запись отключена (ACCOUNTDISABLE)")
                else:
                    ldap_logger.warning(f"Не удалось отключить учетную запись: {conn.result}")
            except Exception as e:
                ldap_logger.warning(f"Ошибка отключения учетной записи: {e}")

            # Перемещаем в OU "Уволенные сотрудники" с сохранением RDN
            target_ou = "OU=Уволенные сотрудники,DC=central,DC=st-ing,DC=com"
            try:
                rdn = current_dn.split(",", 1)[0]  # например, CN=ФИО
                conn.modify_dn(
                    current_dn,
                    rdn,
                    new_superior=target_ou
                )
                if conn.result['result'] == 0:
                    current_dn = f"{rdn},{target_ou}"
                    ldap_logger.info(f"Перемещен в OU: {target_ou}")
                else:
                    ldap_logger.warning(f"Не удалось переместить объект: {conn.result}")
            except Exception as e:
                ldap_logger.warning(f"Ошибка перемещения в OU: {e}")
            
            # Финальная проверка
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

    async def search_users(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Поиск пользователей в AD. Возвращает список сокращённых карточек.

        Поля: cn, sAMAccountName, userPrincipalName, mail, pager, distinguishedName
        """
        conn = await self._get_connection()
        safe_query = (query or "").strip()
        if safe_query:
            filter_expr = (
                f"(|(cn=*{safe_query}*)(sAMAccountName=*{safe_query}*)"
                f"(userPrincipalName=*{safe_query}*)(mail=*{safe_query}*)(pager=*{safe_query}*))"
            )
        else:
            filter_expr = "(objectClass=user)"

        conn.search(
            'DC=central,DC=st-ing,DC=com',
            filter_expr,
            SUBTREE,
            attributes=[
                'cn', 'sAMAccountName', 'userPrincipalName', 'mail', 'pager', 'distinguishedName'
            ],
            size_limit=limit
        )

        results: List[Dict[str, Any]] = []
        for entry in conn.entries:
            results.append({
                'cn': entry.cn.value if hasattr(entry, 'cn') else '',
                'sAMAccountName': entry.sAMAccountName.value if hasattr(entry, 'sAMAccountName') else '',
                'userPrincipalName': entry.userPrincipalName.value if hasattr(entry, 'userPrincipalName') else '',
                'mail': entry.mail.value if hasattr(entry, 'mail') else '',
                'pager': entry.pager.value if hasattr(entry, 'pager') else '',
                'distinguishedName': entry.distinguishedName.value if hasattr(entry, 'distinguishedName') else ''
            })

        return results
