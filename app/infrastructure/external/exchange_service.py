import asyncio
import os
from typing import Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
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
    
    async def send_confirmation_email(self, user_data: Dict[str, Any], sam_account_name: str) -> Dict[str, Any]:
        """Отправка подтверждения приема (точно как в PS.ps1)"""
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
            

            for recipient in recipients:
                result = await self.winrm_service.send_smtp_email(
                    to_email=recipient,
                    subject=subject,
                    body=body
                )
                if not result["success"]:
                    exchange_logger.warning(f"Ошибка отправки email на {recipient}: {result['stderr']}")
            
            exchange_logger.info(f"Подтверждение приема отправлено для {sam_account_name}")
            return {
                "success": True,
                "stdout": f"Confirmation email sent successfully for {sam_account_name}",
                "recipients_count": len(recipients)
            }
            
        except Exception as e:
            exchange_logger.error(f"Исключение при отправке подтверждения: {e}")
            return {"success": False, "stderr": str(e)}
    
    async def send_welcome_email(self, user_data: Dict[str, Any], sam_account_name: str) -> Dict[str, Any]:
        """Отправка приветственного письма с вложениями (точно как в PS.ps1)"""
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
                cc_recipients = "sta@st-ing.com"
            else:
                cc_recipients = "sta@st-ing.com,den@st-ing.com,ian@st-ing.com,alek@st-ing.com,pave@st-ing.com,evge@st-ing.com,dmi@st-ing.com"
            
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
            

            attachments = [
                "C:/www/email_files/Инструкция по управлению почтой СТИ.docx",
                "C:/www/email_files/Welcomebook STI.pdf", 
                "C:/www/email_files/Инструкция по ServiceDesk.docx"
            ]
            

            script = f"""
            $From = "{self.smtp_username}"
            $To = "{mail_address}"
            $Subject = "{subject}"
            $Body = @"
{html_body}
"@
            $SMTPServer = "{self.smtp_server}"
            $SMTPPort = {self.smtp_port}
            $Username = "{self.smtp_username}"
            $Password = "{self.smtp_password}"
            
            $SecurePassword = ConvertTo-SecureString -String $Password -AsPlainText -Force
            $Credential = New-Object System.Management.Automation.PSCredential($Username, $SecurePassword)
            
            $MailMessage = New-Object System.Net.Mail.MailMessage($From, $To, $Subject, $Body)
            $MailMessage.IsBodyHtml = $true
            $MailMessage.CC.Add("{cc_recipients}")
            
            # Добавление вложений
            $attachments = @(
                "C:/www/email_files/Инструкция по управлению почтой СТИ.docx",
                "C:/www/email_files/Welcomebook STI.pdf", 
                "C:/www/email_files/Инструкция по ServiceDesk.docx"
            )
            
            foreach ($attachment in $attachments) {{
                if (Test-Path $attachment) {{
                    $Attachment = New-Object System.Net.Mail.Attachment($attachment)
                    $MailMessage.Attachments.Add($Attachment)
                    Write-Host "Attachment added: $attachment"
                }} else {{
                    Write-Host "Attachment not found: $attachment"
                }}
            }}
            
            $SmtpClient = New-Object System.Net.Mail.SmtpClient($SMTPServer, $SMTPPort)
            $SmtpClient.EnableSsl = $true
            $SmtpClient.Credentials = $Credential
            
            $SmtpClient.Send($MailMessage)
            
            Write-Host "Welcome email sent successfully"
            """
            
            result = await self.winrm_service.execute_powershell(script)
            
            if result["success"]:
                exchange_logger.info(f"Приветственное письмо отправлено для {sam_account_name}")
                return {
                    "success": True,
                    "stdout": f"Welcome email sent successfully for {sam_account_name}",
                    "attachments_count": len(attachments)
                }
            else:
                exchange_logger.error(f"Ошибка отправки приветственного письма: {result['stderr']}")
                return result
            
        except Exception as e:
            exchange_logger.error(f"Исключение при отправке приветственного письма: {e}")
            return {"success": False, "stderr": str(e)}
