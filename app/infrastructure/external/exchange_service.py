import asyncio
import os
from typing import Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
from email.utils import formataddr
from app.core.config.settings import settings
from app.core.logging.logger import exchange_logger
from app.infrastructure.external.winrm_service import WinRMService


class ExchangeService:
    def __init__(self, ldap_service=None):
        self.ldap_service = ldap_service
        self.winrm_service = WinRMService()
        self.exchange_server = settings.exchange_server
        self.exchange_database = settings.exchange_database
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        
        exchange_logger.info(f"ExchangeService инициализирован. Сервер: {self.exchange_server}")
    
    async def create_mailbox(self, sam_account_name: str, user_principal_name: str) -> Dict[str, Any]:
        """Создание почтового ящика Exchange через WinRM (точно как в PS.ps1)"""
        try:
            exchange_logger.info(f"=== СОЗДАНИЕ ПОЧТОВОГО ЯЩИКА EXCHANGE ===")
            exchange_logger.info(f"Пользователь: {sam_account_name}")
            exchange_logger.info(f"UPN: {user_principal_name}")
            exchange_logger.info(f"Exchange сервер: {self.exchange_server}")
            exchange_logger.info(f"База данных: {self.exchange_database}")

            # Если база не указана, не передаем параметр -Database (пусть решает Exchange)
            database_arg = f" -Database \"{self.exchange_database}\"" if (self.exchange_database and len(self.exchange_database.strip())>0) else ""
            exchange_logger.info(f"Параметр базы данных: '{database_arg}'")

            script = f"""
            $ErrorActionPreference = 'Stop'
            $PWord = ConvertTo-SecureString -String "{settings.admin_password}" -AsPlainText -Force
            $Cred = New-Object System.Management.Automation.PSCredential('{settings.ad_domain}\\{settings.admin_username}', $PWord)

            function Connect-Exchange {{
                param([string]$Uri, [string]$Auth)
                try {{
                    $sess = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri $Uri -Authentication $Auth -Credential $Cred -AllowRedirection
                    Import-PSSession $sess -DisableNameChecking | Out-Null
                    return $sess
                }} catch {{
                    return $null
                }}
            }}

            $session = $null
            # Пытаемся Kerberos по HTTP
            $session = Connect-Exchange -Uri "http://{self.exchange_server}/PowerShell/" -Auth "Kerberos"
            if ($null -eq $session) {{
                # Фоллбек на Basic по HTTPS (требует включенной Basic на виртуалке Exchange)
                $session = Connect-Exchange -Uri "https://{self.exchange_server}/PowerShell/" -Auth "Basic"
            }}

            if ($null -eq $session) {{
                Write-Host "Failed to connect to Exchange PowerShell"
                exit 1
            }}

            try {{
                $mb = Get-Mailbox -Identity "{sam_account_name}" -ErrorAction SilentlyContinue
                if ($null -eq $mb) {{
                    Write-Host "Creating mailbox for {sam_account_name}..."
                    $result = Enable-Mailbox -Identity "{sam_account_name}"{database_arg} -ErrorAction Stop
                    Write-Host "Mailbox created successfully for {sam_account_name}"
                    Write-Host "Result: $($result | ConvertTo-Json)"
                }} else {{
                    Write-Host "Mailbox already exists for {sam_account_name}"
                    Write-Host "Existing mailbox: $($mb | ConvertTo-Json)"
                }}
            }} catch {{
                Write-Host "Mailbox create/enable error: $($_.Exception.Message)"
                Write-Host "Error details: $($_.Exception)"
            }} finally {{
                if ($session) {{ Remove-PSSession $session }}
            }}
            """

            exchange_logger.info(f"Отправка PowerShell скрипта на Exchange сервер...")
            result = await self.winrm_service.execute_powershell(script)
            
            exchange_logger.info(f"Результат выполнения Exchange PowerShell:")
            exchange_logger.info(f"  Успех: {result.get('success', False)}")
            exchange_logger.info(f"  Код статуса: {result.get('status_code', 'N/A')}")
            
            if result.get('stdout'):
                exchange_logger.info(f"  STDOUT: {result['stdout'][:300]}{'...' if len(result['stdout']) > 300 else ''}")
            if result.get('stderr'):
                exchange_logger.warning(f"  STDERR: {result['stderr'][:300]}{'...' if len(result['stderr']) > 300 else ''}")
            
            if result.get('success'):
                exchange_logger.info(f"✅ Почтовый ящик Exchange создан успешно для {sam_account_name}")
                return result
            else:
                # Анализируем ошибку Exchange
                stderr = result.get('stderr', '')
                stdout = result.get('stdout', '')
                status_code = result.get('status_code', 0)
                
                # Определяем тип ошибки по содержимому
                if 'Failed to connect to Exchange PowerShell' in stderr:
                    error_msg = "Не удалось подключиться к Exchange PowerShell. Проверьте доступность сервера Exchange."
                elif 'Access is denied' in stderr or 'Unauthorized' in stderr:
                    error_msg = "Недостаточно прав для создания почтового ящика. Проверьте права пользователя."
                elif 'Mailbox already exists' in stdout:
                    error_msg = "Почтовый ящик уже существует для этого пользователя."
                elif 'The user account does not exist' in stderr:
                    error_msg = "Учетная запись пользователя не найдена в Active Directory."
                elif 'Database' in stderr and 'not found' in stderr:
                    error_msg = "База данных Exchange не найдена. Проверьте настройки базы данных."
                elif status_code != 0:
                    error_msg = f"Ошибка выполнения PowerShell (код {status_code}): {stderr[:200]}"
                else:
                    error_msg = f"Неизвестная ошибка Exchange: {stderr[:200]}"
                
                exchange_logger.error(f"❌ {error_msg}")
                
                return {
                    "success": False, 
                    "stderr": error_msg,
                    "exchange_status_code": status_code,
                    "exchange_raw_stderr": stderr,
                    "exchange_raw_stdout": stdout
                }
            
        except Exception as e:
            exchange_logger.error(f"❌ Исключение при создании почтового ящика: {e}")
            exchange_logger.error(f"Тип исключения: {type(e).__name__}")
            import traceback
            exchange_logger.error(f"Трассировка: {traceback.format_exc()}")
            return {"success": False, "stderr": str(e)}
    
    def _send_email_direct(self, to_email: str, subject: str, body: str, html: bool = False, cc: list = None) -> Dict[str, Any]:
        """Прямая отправка email через Python smtplib (без WinRM)"""
        try:
            if not self.smtp_server or not self.smtp_port:
                return {"success": False, "stderr": "SMTP server or port not configured"}
            if not self.smtp_username or not self.smtp_password:
                return {"success": False, "stderr": "SMTP credentials not configured"}
            
            exchange_logger.info(f"=== ОТПРАВКА EMAIL ЧЕРЕЗ SMTPLIB ===")
            exchange_logger.info(f"SMTP сервер: {self.smtp_server}:{self.smtp_port}")
            exchange_logger.info(f"Username: {self.smtp_username}")
            
            # From адрес всегда noreply@st-ing.com (как в оригинальном PS.ps1)
            from_addr = getattr(settings, 'smtp_from', None) or "noreply@st-ing.com"
            exchange_logger.info(f"From: {from_addr} -> To: {to_email}")
            
            # Создаем сообщение
            if html:
                msg = MIMEMultipart('alternative')
                html_part = MIMEText(body, 'html', 'utf-8')
                msg.attach(html_part)
            else:
                msg = MIMEText(body, 'plain', 'utf-8')
            
            msg['From'] = from_addr
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # Подключение к SMTP серверу
            use_ssl = getattr(settings, 'smtp_use_ssl', True)
            use_tls = (self.smtp_port == 587)
            
            exchange_logger.info(f"Подключение к SMTP: порт={self.smtp_port}, SSL={use_ssl}, TLS={use_tls}")

            # Автоматические попытки подключения: Exchange может требовать STARTTLS даже на порту 465
            # Пробуем разные варианты подключения
            connection_attempts = []
            if self.smtp_port == 465:
                # Для порта 465 пробуем: STARTTLS на 465, затем SSL на 465, затем STARTTLS на 587
                connection_attempts = [
                    (self.smtp_server, 465, "STARTTLS"),  # Сначала обычное подключение с STARTTLS
                    (self.smtp_server, 465, "SSL"),       # Затем прямой SSL
                    (self.smtp_server, 587, "STARTTLS"),  # Фоллбек на 587
                    (self.smtp_server, 25, "PLAIN")       # Последний вариант - порт 25
                ]
            elif self.smtp_port == 587:
                connection_attempts = [
                    (self.smtp_server, 587, "STARTTLS"),
                    (self.smtp_server, 465, "STARTTLS"),  # 465 тоже через STARTTLS
                    (self.smtp_server, 465, "SSL"),
                    (self.smtp_server, 25, "PLAIN")
                ]
            else:
                connection_attempts = [
                    (self.smtp_server, self.smtp_port, "AUTO"),
                    (self.smtp_server, 587, "STARTTLS"),
                    (self.smtp_server, 465, "STARTTLS"),
                    (self.smtp_server, 465, "SSL"),
                    (self.smtp_server, 25, "PLAIN")
                ]

            server = None
            last_connect_error = None
            try:
                for host, port, mode in connection_attempts:
                    try:
                        exchange_logger.info(f"Пробую подключиться: {host}:{port} режим={mode}")
                        if mode == "SSL":
                            server = smtplib.SMTP_SSL(host, port, timeout=30)
                            server.ehlo()
                        else:
                            server = smtplib.SMTP(host, port, timeout=30)
                            server.ehlo()
                            if mode in ("STARTTLS", "AUTO"):
                                exchange_logger.info("Включение STARTTLS")
                                server.starttls()
                                server.ehlo()
                        # Если дошли сюда без исключений — подключение успешно
                        exchange_logger.info(f"SMTP подключение установлено: {host}:{port} ({mode})")
                        break
                    except Exception as ce:
                        last_connect_error = ce
                        exchange_logger.warning(f"Не удалось подключиться {host}:{port} ({mode}): {ce}")
                        # Закрываем и пробуем следующий вариант
                        if server:
                            try:
                                server.quit()
                            except:
                                pass
                        server = None
                        continue
                if not server:
                    raise last_connect_error or Exception("SMTP connection attempts failed")
                
                # Авторизация
                # В оригинальном PS.ps1 используется формат domain\username для авторизации
                # Python smtplib может не поддерживать domain\username напрямую
                # Пробуем разные варианты формата username
                login_username = self.smtp_username
                auth_success = False
                
                # Список вариантов username для попытки авторизации
                username_variants = []
                
                # Если формат domain\user - пробуем разные варианты
                if "\\" in login_username:
                    domain_part, user_part = login_username.split("\\", 1)
                    # Варианты для Exchange SMTP:
                    # 1. Как есть (domain\user) - может не работать в Python smtplib
                    # 2. Email формат: user@domain.st-ing.com
                    # 3. Email формат: user@st-ing.com
                    username_variants = [
                        login_username,  # Пробуем как есть сначала
                        f"{user_part}@{domain_part}.st-ing.com",
                        f"{user_part}@st-ing.com",
                        f"{user_part}@{domain_part}.central.st-ing.com",
                        f"{domain_part}\\{user_part}"  # Еще раз пробуем с экранированием
                    ]
                    exchange_logger.info(f"Username содержит \\: {login_username}, варианты: {username_variants}")
                elif "@" in login_username:
                    # Если это уже email - пробуем как есть
                    username_variants = [login_username]
                    exchange_logger.info(f"Username в формате email: {login_username}")
                else:
                    # Если просто username без @ - пробуем добавить домен
                    username_variants = [
                        login_username,  # Пробуем как есть
                        f"{login_username}@st-ing.com",
                        f"{login_username}@central.st-ing.com"
                    ]
                    exchange_logger.info(f"Username без домена: {login_username}, варианты: {username_variants}")
                
                # Пробуем авторизоваться с каждым вариантом
                last_error = None
                for variant in username_variants:
                    try:
                        exchange_logger.info(f"Попытка авторизации: username={variant}")
                        server.login(variant, self.smtp_password)
                        exchange_logger.info(f"✅ Авторизация успешна с username={variant}")
                        auth_success = True
                        login_username = variant  # Сохраняем успешный вариант
                        break
                    except smtplib.SMTPAuthenticationError as e:
                        last_error = e
                        exchange_logger.warning(f"❌ Авторизация не удалась с username={variant}: {e}")
                        continue
                    except Exception as e:
                        last_error = e
                        exchange_logger.warning(f"❌ Ошибка при авторизации с username={variant}: {e}")
                        continue
                
                if not auth_success:
                    error_msg = f"Authentication failed with all username variants. Last error: {last_error}"
                    exchange_logger.error(error_msg)
                    raise smtplib.SMTPAuthenticationError(535, error_msg)
                
                # Отправка
                recipients = [to_email]
                if cc:
                    recipients.extend(cc)
                exchange_logger.info(f"Отправка сообщения получателям: {recipients}")
                server.sendmail(from_addr, recipients, msg.as_string())
                exchange_logger.info(f"Email успешно отправлен: {to_email}")
                
                return {"success": True, "stdout": f"Email sent successfully to {to_email}"}
                
            finally:
                if server:
                    try:
                        server.quit()
                    except:
                        pass
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP authentication failed: {e}"
            exchange_logger.error(error_msg)
            exchange_logger.error(f"Проверьте username ({self.smtp_username}) и password")
            return {"success": False, "stderr": error_msg}
        except smtplib.SMTPConnectError as e:
            error_msg = f"SMTP connection failed: {e}"
            exchange_logger.error(error_msg)
            exchange_logger.error(f"Проверьте доступность сервера {self.smtp_server}:{self.smtp_port}")
            return {"success": False, "stderr": error_msg}
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {e}"
            exchange_logger.error(error_msg)
            return {"success": False, "stderr": error_msg}
        except Exception as e:
            exchange_logger.error(f"Ошибка отправки email через smtplib: {e}")
            import traceback
            exchange_logger.error(f"Трассировка: {traceback.format_exc()}")
            return {"success": False, "stderr": str(e)}
    
    async def send_confirmation_email(self, user_data: Dict[str, Any], sam_account_name: str) -> Dict[str, Any]:
        """Отправка подтверждения приема через Python smtplib"""
        try:
            exchange_logger.info(f"=== ОТПРАВКА ПОДТВЕРЖДЕНИЯ ПРИЕМА ===")
            exchange_logger.info(f"Пользователь: {sam_account_name}")
            exchange_logger.info(f"Данные пользователя: {user_data.get('unique_id', 'N/A')}")
            
            company = user_data.get('company', '')
            if any(keyword in company.upper() for keyword in ['STI', 'СТРОЙ', 'ТЕХНО', 'ИНЖЕНЕРИНГ']):
                mail_address = f"{sam_account_name}@st-ing.com"
            elif any(keyword in company.upper() for keyword in ['DTTERMO', 'ДТ']):
                mail_address = f"{sam_account_name}@dttermo.ru"
            else:
                mail_address = f"{sam_account_name}@st-ing.com"
            
            recipients = []
            if user_data.get('technical') == 'technical':
                recipients = ["sta@st-ing.com", "den@st-ing.com", "ian@st-ing.com"]
            else:
                recipients = [
                    "h@st-ing.com", "il@st-ing.com", "ok@st-ing.com", 
                    "st@st-ing.com", "den@st-ing.com", "ian@st-ing.com",
                    "pav@st-ing.com", "evg@st-ing.com", "alek@st-ing.com", 
                    "dmitn@st-ing.com"
                ]
            
            subject = f"Подтверждение приема {user_data.get('unique_id', '')}"
            body = f"""{sam_account_name} - учетная запись
{mail_address} - почта
{settings.default_user_password} - пароль для первого входа в учетную запись"""
            
            # Отправляем через Python smtplib (без WinRM)
            success_count = 0
            for recipient in recipients:
                result = await asyncio.to_thread(
                    self._send_email_direct,
                    recipient,
                    subject,
                    body,
                    False
                )
                if result["success"]:
                    success_count += 1
                else:
                    exchange_logger.warning(f"Ошибка отправки email на {recipient}: {result['stderr']}")
            
            exchange_logger.info(f"Подтверждение приема отправлено для {sam_account_name} ({success_count}/{len(recipients)})")
            return {
                "success": success_count > 0,
                "stdout": f"Confirmation email sent successfully for {sam_account_name}",
                "recipients_count": len(recipients),
                "success_count": success_count
            }
            
        except Exception as e:
            exchange_logger.error(f"Исключение при отправке подтверждения: {e}")
            return {"success": False, "stderr": str(e)}
    
    async def send_welcome_email(self, user_data: Dict[str, Any], sam_account_name: str) -> Dict[str, Any]:
        """Отправка приветственного письма через Python smtplib"""
        try:
            exchange_logger.info(f"Отправка приветственного письма: {sam_account_name}")
            
            company = user_data.get('company', '')
            if any(keyword in company.upper() for keyword in ['STI', 'СТРОЙ', 'ТЕХНО', 'ИНЖЕНЕРИНГ']):
                mail_address = f"{sam_account_name}@st-ing.com"
            elif any(keyword in company.upper() for keyword in ['DTTERMO', 'ДТ']):
                mail_address = f"{sam_account_name}@dttermo.ru"
            else:
                mail_address = f"{sam_account_name}@st-ing.com"
            
            subject = f"Добро пожаловать в компанию! {user_data.get('firstname', '')} {user_data.get('secondname', '')} !"
            
            if user_data.get('technical') == 'technical':
                cc_recipients = ["sta@st-ing.com"]
            else:
                cc_recipients = ["sta@st-ing.com", "den@st-ing.com", "ian@st-ing.com", "alek@st-ing.com", "pave@st-ing.com", "evge@st-ing.com", "dmi@st-ing.com"]
            
            html_body = """
            <html>
            <head>
                <meta charset="utf-8">
                <title>Добро пожаловать в компанию!</title>
            </head>
            <body>
                <h1>Добро пожаловать в компанию СтройТехноИнженеринг!</h1>
                <p>Мы рады приветствовать вас в нашей команде.</p>
                <p>В приложении вы найдете полезные материалы для начала работы.</p>
                <br>
                <p>С уважением,<br>Команда СТИ</p>
            </body>
            </html>
            """
            
            # Отправляем через Python smtplib (без WinRM)
            # Примечание: вложения находятся на Windows сервере и недоступны напрямую
            # Если нужны вложения - можно добавить через WinRM только чтение файлов
            result = await asyncio.to_thread(
                self._send_email_direct,
                mail_address,
                subject,
                html_body,
                True,
                cc_recipients
            )
            
            if result["success"]:
                exchange_logger.info(f"Приветственное письмо отправлено для {sam_account_name}")
                return {
                    "success": True,
                    "stdout": f"Welcome email sent successfully for {sam_account_name}"
                }
            else:
                exchange_logger.error(f"Ошибка отправки приветственного письма: {result['stderr']}")
                return result
            
        except Exception as e:
            exchange_logger.error(f"Исключение при отправке приветственного письма: {e}")
            return {"success": False, "stderr": str(e)}
