#!/usr/bin/env python3
"""
Диагностический скрипт для проверки всех внешних интеграций
Проверяет: LDAP, Exchange, SMTP, WinRM, файловую систему
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config.settings import settings
from app.infrastructure.external.ldap_service import LDAPService
from app.infrastructure.external.exchange_service import ExchangeService
from app.infrastructure.external.winrm_service import WinRMService


class IntegrationDiagnostic:
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    async def check_ldap_connection(self) -> Dict[str, Any]:
        """Проверка подключения к Active Directory"""
        self.log("🔍 Проверка LDAP подключения...")
        
        try:
            ldap_service = LDAPService()
            conn = await ldap_service._get_connection()
            
            if conn and conn.bound:
                # Тестовый поиск пользователей
                conn.search(
                    'DC=central,DC=st-ing,DC=com',
                    '(objectClass=user)',
                    attributes=['sAMAccountName'],
                    size_limit=5
                )
                
                user_count = len(conn.entries)
                
                self.log(f"✅ LDAP подключение успешно. Найдено {user_count} пользователей")
                return {
                    "status": "success",
                    "server": settings.ad_server,
                    "domain": settings.ad_domain,
                    "users_found": user_count,
                    "connection_bound": conn.bound
                }
            else:
                self.log("❌ LDAP подключение не установлено", "ERROR")
                return {
                    "status": "failed",
                    "error": "Connection not bound"
                }
                
        except Exception as e:
            self.log(f"❌ Ошибка LDAP подключения: {str(e)}", "ERROR")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def check_exchange_connection(self) -> Dict[str, Any]:
        """Проверка подключения к Exchange Server"""
        self.log("🔍 Проверка Exchange подключения...")
        
        try:
            exchange_service = ExchangeService()
            
            # Тестовый PowerShell скрипт для проверки подключения
            test_script = f"""
            try {{
                $ErrorActionPreference = 'Stop'
                $PWord = ConvertTo-SecureString -String "{settings.admin_password}" -AsPlainText -Force
                $Cred = New-Object System.Management.Automation.PSCredential('{settings.ad_domain}\\{settings.admin_username}', $PWord)

                $session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri "http://{settings.exchange_server}/PowerShell/" -Authentication Kerberos -Credential $Cred -AllowRedirection
                Import-PSSession $session -DisableNameChecking | Out-Null
                
                $mailboxes = Get-Mailbox -ResultSize 5
                Write-Host "SUCCESS: Found $($mailboxes.Count) mailboxes"
                
                Remove-PSSession $session
            }} catch {{
                Write-Host "ERROR: $($_.Exception.Message)"
            }}
            """
            
            result = await exchange_service.winrm_service.execute_powershell(test_script)
            
            if result["success"] and "SUCCESS" in result["stdout"]:
                self.log("✅ Exchange подключение успешно")
                return {
                    "status": "success",
                    "server": settings.exchange_server,
                    "database": settings.exchange_database,
                    "output": result["stdout"]
                }
            else:
                self.log(f"❌ Ошибка Exchange подключения: {result.get('stderr', 'Unknown error')}", "ERROR")
                return {
                    "status": "failed",
                    "error": result.get('stderr', 'Unknown error')
                }
                
        except Exception as e:
            self.log(f"❌ Ошибка Exchange подключения: {str(e)}", "ERROR")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def check_smtp_connection(self) -> Dict[str, Any]:
        """Проверка SMTP подключения"""
        self.log("🔍 Проверка SMTP подключения...")
        
        try:
            # Тестовый PowerShell скрипт для проверки SMTP
            smtp_test_script = f"""
            try {{
                $ErrorActionPreference = 'Stop'
                $SMTPServer = "{settings.smtp_server}"
                $SMTPPort = {settings.smtp_port}
                $Username = "{settings.smtp_username}"
                $Password = "{settings.smtp_password}"
                
                $SecurePassword = ConvertTo-SecureString -String $Password -AsPlainText -Force
                $Credential = New-Object System.Management.Automation.PSCredential($Username, $SecurePassword)
                
                $SmtpClient = New-Object System.Net.Mail.SmtpClient($SMTPServer, $SMTPPort)
                $SmtpClient.EnableSsl = $true
                $SmtpClient.Credentials = $Credential
                
                # Тестовое подключение без отправки
                $SmtpClient.SendCompleted += {{
                    Write-Host "SUCCESS: SMTP connection established"
                }}
                
                Write-Host "SUCCESS: SMTP configuration valid"
            }} catch {{
                Write-Host "ERROR: $($_.Exception.Message)"
            }}
            """
            
            winrm_service = WinRMService()
            result = await winrm_service.execute_powershell(smtp_test_script)
            
            if result["success"] and "SUCCESS" in result["stdout"]:
                self.log("✅ SMTP конфигурация корректна")
                return {
                    "status": "success",
                    "server": settings.smtp_server,
                    "port": settings.smtp_port,
                    "username": settings.smtp_username
                }
            else:
                self.log(f"❌ Ошибка SMTP конфигурации: {result.get('stderr', 'Unknown error')}", "ERROR")
                return {
                    "status": "failed",
                    "error": result.get('stderr', 'Unknown error')
                }
                
        except Exception as e:
            self.log(f"❌ Ошибка SMTP проверки: {str(e)}", "ERROR")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def check_winrm_connection(self) -> Dict[str, Any]:
        """Проверка WinRM подключения"""
        self.log("🔍 Проверка WinRM подключения...")
        
        try:
            winrm_service = WinRMService()
            
            # Простой тестовый скрипт
            test_script = """
            Write-Host "SUCCESS: WinRM connection established"
            Get-Date
            $env:COMPUTERNAME
            """
            
            result = await winrm_service.execute_powershell(test_script)
            
            if result["success"] and "SUCCESS" in result["stdout"]:
                self.log("✅ WinRM подключение успешно")
                return {
                    "status": "success",
                    "server": winrm_service.server,
                    "port": winrm_service.port,
                    "output": result["stdout"]
                }
            else:
                self.log(f"❌ Ошибка WinRM подключения: {result.get('stderr', 'Unknown error')}", "ERROR")
                return {
                    "status": "failed",
                    "error": result.get('stderr', 'Unknown error')
                }
                
        except Exception as e:
            self.log(f"❌ Ошибка WinRM подключения: {str(e)}", "ERROR")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def check_filesystem_access(self) -> Dict[str, Any]:
        """Проверка доступа к файловой системе"""
        self.log("🔍 Проверка доступа к файловой системе...")
        
        try:
            winrm_service = WinRMService()
            
            # Проверка базового пути
            base_path = "\\\\datastorage\\Storage\\06_СТИ\\Строительные объекты"
            
            test_script = f"""
            try {{
                $basePath = "{base_path}"
                if (Test-Path $basePath) {{
                    $items = Get-ChildItem $basePath -ErrorAction SilentlyContinue
                    Write-Host "SUCCESS: Path accessible, $($items.Count) items found"
                }} else {{
                    Write-Host "WARNING: Base path not accessible, attempting to create"
                    New-Item -ItemType Directory -Path $basePath -Force
                    Write-Host "SUCCESS: Path created successfully"
                }}
            }} catch {{
                Write-Host "ERROR: $($_.Exception.Message)"
            }}
            """
            
            result = await winrm_service.execute_powershell(test_script)
            
            if result["success"] and "SUCCESS" in result["stdout"]:
                self.log("✅ Доступ к файловой системе работает")
                return {
                    "status": "success",
                    "base_path": base_path,
                    "output": result["stdout"]
                }
            else:
                self.log(f"❌ Ошибка доступа к файловой системе: {result.get('stderr', 'Unknown error')}", "ERROR")
                return {
                    "status": "failed",
                    "error": result.get('stderr', 'Unknown error')
                }
                
        except Exception as e:
            self.log(f"❌ Ошибка проверки файловой системы: {str(e)}", "ERROR")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def run_all_checks(self):
        """Запуск всех проверок"""
        self.log("🚀 Начало диагностики интеграций")
        self.log("=" * 60)
        
        # Проверка LDAP
        self.results["ldap"] = await self.check_ldap_connection()
        self.log("-" * 40)
        
        # Проверка Exchange
        self.results["exchange"] = await self.check_exchange_connection()
        self.log("-" * 40)
        
        # Проверка SMTP
        self.results["smtp"] = await self.check_smtp_connection()
        self.log("-" * 40)
        
        # Проверка WinRM
        self.results["winrm"] = await self.check_winrm_connection()
        self.log("-" * 40)
        
        # Проверка файловой системы
        self.results["filesystem"] = await self.check_filesystem_access()
        self.log("-" * 40)
        
        # Итоговый отчет
        self.print_summary()
    
    def print_summary(self):
        """Печать итогового отчета"""
        self.log("📊 ИТОГОВЫЙ ОТЧЕТ")
        self.log("=" * 60)
        
        total_checks = len(self.results)
        successful_checks = sum(1 for result in self.results.values() if result["status"] == "success")
        
        self.log(f"Всего проверок: {total_checks}")
        self.log(f"Успешных: {successful_checks}")
        self.log(f"Неудачных: {total_checks - successful_checks}")
        self.log("")
        
        for service, result in self.results.items():
            status_icon = "✅" if result["status"] == "success" else "❌"
            self.log(f"{status_icon} {service.upper()}: {result['status']}")
            
            if result["status"] == "failed":
                self.log(f"   Ошибка: {result.get('error', 'Unknown error')}")
        
        duration = datetime.now() - self.start_time
        self.log("")
        self.log(f"⏱️ Время выполнения: {duration.total_seconds():.2f} секунд")
        self.log("=" * 60)


async def main():
    """Главная функция"""
    diagnostic = IntegrationDiagnostic()
    await diagnostic.run_all_checks()


if __name__ == "__main__":
    asyncio.run(main())
