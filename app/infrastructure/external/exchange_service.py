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
            exchange_logger.info(f"Создание почтового ящика Exchange для {sam_account_name}")
            

            if '@st-ing.com' in user_principal_name:
                mail_domain = 'st-ing.com'
            elif '@dttermo.ru' in user_principal_name:
                mail_domain = 'dttermo.ru'
            else:
                mail_domain = 'st-ing.com'
            
            script = f"""
            # Подключение к Exchange с учетными данными
            $PWord = ConvertTo-SecureString -String "{settings.admin_password}" -AsPlainText -Force
            $PSCredential = New-Object System.Management.Automation.PSCredential('{settings.ad_domain}\\{settings.admin_username}', $PWord)
            $Session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri "http://{self.exchange_server}/PowerShell/" -Authentication Kerberos -Credential $PSCredential
            
            Import-PSSession $Session -DisableNameChecking
            
            try {{
                # Создание почтового ящика
                Enable-Mailbox -Identity "{sam_account_name}" -Database "{self.exchange_database}"
                Write-Host "Mailbox created successfully for {sam_account_name}"
            }}
            catch {{
                Write-Host "Mailbox already exists or error occurred: $($_.Exception.Message)"
            }}
            
            Remove-PSSession $Session
            """
            
            return await self.winrm_service.execute_powershell(script)
            
        except Exception as e:
            exchange_logger.error(f"Исключение при создании почтового ящика: {e}")
            return {"success": False, "stderr": str(e)}
    
    async def send_confirmation_email(self, user_data: Dict[str, Any], sam_account_name: str) -> Dict[str, Any]:
        """Отправка подтверждения приема (точно как в PS.ps1)"""
        try:
            exchange_logger.info(f"Отправка подтверждения приема: {sam_account_name}")
            
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
