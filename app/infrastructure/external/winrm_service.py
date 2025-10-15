import asyncio
import winrm
from typing import Dict, Any, Optional
from app.core.config.settings import settings
from app.core.logging.logger import winrm_logger


class WinRMService:
    def __init__(self):
        # Приоритет: явный WINRM_SERVER -> EXCHANGE_SERVER -> AD_SERVER
        self.server = settings.winrm_server or settings.exchange_server or settings.ad_server
        self.port = settings.winrm_port
        self.username = settings.admin_username
        self.password = settings.admin_password
        self.domain = getattr(settings, 'ad_domain', '')
        self.read_timeout_sec = getattr(settings, 'winrm_timeout', 30)
        self.operation_timeout_sec = 10
        
        winrm_logger.info(f"WinRMService инициализирован. Сервер: {self.server}:{self.port}")
    
    async def execute_powershell(self, script: str) -> Dict[str, Any]:
        """Выполнение PowerShell скрипта через WinRM"""
        try:
            winrm_logger.info(f"Выполнение PowerShell через WinRM")
            
            scheme = 'https' if str(self.port) == '5986' else 'http'
            session = winrm.Session(
                f"{scheme}://{self.server}:{self.port}/wsman",
                auth=(f"{self.domain}\\{self.username}", self.password),
                transport='ntlm',
                server_cert_validation='ignore',
                read_timeout_sec=self.read_timeout_sec,
                operation_timeout_sec=self.operation_timeout_sec
            )

            result = session.run_ps(script)
            
            if result.status_code == 0:
                winrm_logger.info("PowerShell скрипт выполнен успешно")
                return {
                    "success": True,
                    "stdout": result.std_out.decode('utf-8', errors='ignore'),
                    "stderr": result.std_err.decode('utf-8', errors='ignore'),
                    "status_code": result.status_code
                }
            else:
                winrm_logger.error(f"Ошибка выполнения PowerShell: {result.std_err}")
                return {
                    "success": False,
                    "stdout": result.std_out.decode('utf-8', errors='ignore'),
                    "stderr": result.std_err.decode('utf-8', errors='ignore'),
                    "status_code": result.status_code
                }
                
        except Exception as e:
            winrm_logger.error(f"Исключение при выполнении PowerShell через WinRM: {e}")
            return {"success": False, "stderr": str(e)}
    
    async def create_file_folders(self, object_name: str, folders: list) -> Dict[str, Any]:
        """Создание файловых папок через WinRM (точно как в CreateNewObject.ps1)"""
        try:
            base_path = f"\\\\datastorage\\Storage\\06_СТИ\\Строительные объекты\\{object_name}"
            
            check_script = f"""
            if (Test-Path "{base_path}") {{
                Write-Host "EXISTS"
            }} else {{
                Write-Host "NOT_EXISTS"
            }}
            """
            
            result = await self.execute_powershell(check_script)
            if not result["success"]:
                return result
            
            if "NOT_EXISTS" in result["stdout"]:
                create_base_script = f'New-Item -ItemType Directory -Path "{base_path}" -Force'
                result = await self.execute_powershell(create_base_script)
                if result["success"]:
                    winrm_logger.info(f"Основная папка создана: {base_path}")
                else:
                    return result
            else:
                winrm_logger.info(f"Основная папка уже существует: {base_path}")
            
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
                folder_path = f"{base_path}\\{folder}"
                check_folder_script = f"""
                if (Test-Path "{folder_path}") {{
                    Write-Host "EXISTS"
                }} else {{
                    Write-Host "NOT_EXISTS"
                }}
                """
                
                result = await self.execute_powershell(check_folder_script)
                if result["success"] and "NOT_EXISTS" in result["stdout"]:
                    create_folder_script = f'New-Item -ItemType Directory -Path "{folder_path}" -Force'
                    result = await self.execute_powershell(create_folder_script)
                    if result["success"]:
                        winrm_logger.info(f"Папка '{folder}' создана")
                    else:
                        winrm_logger.warning(f"Ошибка создания папки '{folder}': {result['stderr']}")
                elif result["success"]:
                    winrm_logger.info(f"Папка '{folder}' уже существует")
                else:
                    winrm_logger.warning(f"Ошибка проверки папки '{folder}': {result['stderr']}")
            
            return {"success": True, "message": "Файловые папки созданы успешно"}
            
        except Exception as e:
            winrm_logger.error(f"Исключение при создании файловых папок: {e}")
            return {"success": False, "stderr": str(e)}
    
    async def create_exchange_mailbox(self, sam_account_name: str, user_principal_name: str) -> Dict[str, Any]:
        """Создание почтового ящика Exchange через WinRM"""
        try:
            script = f"""
            # Подключение к Exchange
            $Session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri "http://{settings.exchange_server}/PowerShell/" -Authentication Kerberos
            
            # Создание почтового ящика
            Enable-Mailbox -Identity "{sam_account_name}" -Database "{settings.exchange_database}"
            
            # Отключение сессии
            Remove-PSSession $Session
            """
            
            return await self.execute_powershell(script)
            
        except Exception as e:
            winrm_logger.error(f"Исключение при создании почтового ящика: {e}")
            return {"success": False, "stderr": str(e)}
    
    async def send_smtp_email(self, to_email: str, subject: str, body: str, attachment_path: str = None) -> Dict[str, Any]:
        """Отправка email через SMTP на Windows сервере"""
        try:
            script = f"""
            $From = "{settings.smtp_username}"
            $To = "{to_email}"
            $Subject = "{subject}"
            $Body = @"
{body}
"@
            $SMTPServer = "{settings.smtp_server}"
            $SMTPPort = {settings.smtp_port}
            $Username = "{settings.smtp_username}"
            $Password = "{settings.smtp_password}"
            
            $SecurePassword = ConvertTo-SecureString -String $Password -AsPlainText -Force
            $Credential = New-Object System.Management.Automation.PSCredential($Username, $SecurePassword)
            
            $MailMessage = New-Object System.Net.Mail.MailMessage($From, $To, $Subject, $Body)
            $MailMessage.IsBodyHtml = $false
            
            if ("{attachment_path}" -ne "") {{
                $Attachment = New-Object System.Net.Mail.Attachment("{attachment_path}")
                $MailMessage.Attachments.Add($Attachment)
            }}
            
            $SmtpClient = New-Object System.Net.Mail.SmtpClient($SMTPServer, $SMTPPort)
            $SmtpClient.EnableSsl = $true
            $SmtpClient.Credentials = $Credential
            
            $SmtpClient.Send($MailMessage)
            
            Write-Host "Email отправлен успешно"
            """
            
            return await self.execute_powershell(script)
            
        except Exception as e:
            winrm_logger.error(f"Исключение при отправке email: {e}")
            return {"success": False, "stderr": str(e)}
