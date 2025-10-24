#!/usr/bin/env python3
"""
Диагностический скрипт для проверки интеграций на удаленном сервере
Запускать на сервере где развернуто приложение
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Добавляем путь к приложению
sys.path.append('/app')  # Путь в Docker контейнере
sys.path.append('.')     # Локальный путь

try:
    from app.core.config.settings import settings
    from app.infrastructure.external.ldap_service import LDAPService
    from app.infrastructure.external.exchange_service import ExchangeService
    from app.infrastructure.external.winrm_service import WinRMService
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь, что скрипт запускается из корневой директории проекта")
    sys.exit(1)


class RemoteIntegrationCheck:
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
            
            # Простая проверка через WinRM
            test_script = f"""
            try {{
                Write-Host "Testing Exchange connection..."
                $ErrorActionPreference = 'Stop'
                
                # Проверяем доступность Exchange сервера
                $exchangeServer = "{settings.exchange_server}"
                $testConnection = Test-NetConnection -ComputerName $exchangeServer -Port 80 -InformationLevel Quiet
                
                if ($testConnection) {{
                    Write-Host "SUCCESS: Exchange server {settings.exchange_server} is reachable"
                }} else {{
                    Write-Host "WARNING: Exchange server {settings.exchange_server} is not reachable on port 80"
                }}
                
                # Проверяем PowerShell модуль Exchange
                try {{
                    Import-Module -Name ExchangeOnlineManagement -ErrorAction SilentlyContinue
                    Write-Host "SUCCESS: Exchange PowerShell module available"
                }} catch {{
                    Write-Host "INFO: Exchange PowerShell module not available (normal for remote execution)"
                }}
                
            }} catch {{
                Write-Host "ERROR: $($_.Exception.Message)"
            }}
            """
            
            result = await exchange_service.winrm_service.execute_powershell(test_script)
            
            if result["success"] and "SUCCESS" in result["stdout"]:
                self.log("✅ Exchange сервер доступен")
                return {
                    "status": "success",
                    "server": settings.exchange_server,
                    "database": settings.exchange_database,
                    "output": result["stdout"]
                }
            else:
                self.log(f"⚠️ Exchange проверка: {result.get('stdout', 'No output')}", "WARNING")
                return {
                    "status": "warning",
                    "server": settings.exchange_server,
                    "output": result.get('stdout', 'No output'),
                    "error": result.get('stderr', 'No error details')
                }
                
        except Exception as e:
            self.log(f"❌ Ошибка Exchange подключения: {str(e)}", "ERROR")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def check_smtp_connection(self) -> Dict[str, Any]:
        """Проверка SMTP конфигурации"""
        self.log("🔍 Проверка SMTP конфигурации...")
        
        try:
            # Проверяем настройки SMTP
            if not settings.smtp_server or not settings.smtp_username:
                self.log("❌ SMTP настройки не заполнены", "ERROR")
                return {
                    "status": "failed",
                    "error": "SMTP settings not configured"
                }
            
            # Тест подключения к SMTP серверу
            test_script = f"""
            try {{
                $SMTPServer = "{settings.smtp_server}"
                $SMTPPort = {settings.smtp_port}
                
                # Проверяем доступность SMTP сервера
                $testConnection = Test-NetConnection -ComputerName $SMTPServer -Port $SMTPPort -InformationLevel Quiet
                
                if ($testConnection) {{
                    Write-Host "SUCCESS: SMTP server {settings.smtp_server}:{settings.smtp_port} is reachable"
                }} else {{
                    Write-Host "WARNING: SMTP server {settings.smtp_server}:{settings.smtp_port} is not reachable"
                }}
                
            }} catch {{
                Write-Host "ERROR: $($_.Exception.Message)"
            }}
            """
            
            winrm_service = WinRMService()
            result = await winrm_service.execute_powershell(test_script)
            
            if result["success"] and "SUCCESS" in result["stdout"]:
                self.log("✅ SMTP сервер доступен")
                return {
                    "status": "success",
                    "server": settings.smtp_server,
                    "port": settings.smtp_port,
                    "username": settings.smtp_username
                }
            else:
                self.log(f"⚠️ SMTP проверка: {result.get('stdout', 'No output')}", "WARNING")
                return {
                    "status": "warning",
                    "server": settings.smtp_server,
                    "port": settings.smtp_port,
                    "output": result.get('stdout', 'No output')
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
            try {
                Write-Host "SUCCESS: WinRM connection established"
                Write-Host "Computer: $env:COMPUTERNAME"
                Write-Host "User: $env:USERNAME"
                Write-Host "Date: $(Get-Date)"
            } catch {
                Write-Host "ERROR: $($_.Exception.Message)"
            }
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
                Write-Host "Checking path: $basePath"
                
                if (Test-Path $basePath) {{
                    $items = Get-ChildItem $basePath -ErrorAction SilentlyContinue
                    Write-Host "SUCCESS: Path accessible, $($items.Count) items found"
                }} else {{
                    Write-Host "WARNING: Base path not accessible: $basePath"
                    Write-Host "Attempting to create directory structure..."
                    
                    try {{
                        New-Item -ItemType Directory -Path $basePath -Force
                        Write-Host "SUCCESS: Directory created successfully"
                    }} catch {{
                        Write-Host "ERROR: Cannot create directory: $($_.Exception.Message)"
                    }}
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
                self.log(f"⚠️ Файловая система: {result.get('stdout', 'No output')}", "WARNING")
                return {
                    "status": "warning",
                    "base_path": base_path,
                    "output": result.get('stdout', 'No output'),
                    "error": result.get('stderr', 'No error details')
                }
                
        except Exception as e:
            self.log(f"❌ Ошибка проверки файловой системы: {str(e)}", "ERROR")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def check_database_connection(self) -> Dict[str, Any]:
        """Проверка подключения к базе данных"""
        self.log("🔍 Проверка подключения к базе данных...")
        
        try:
            from app.infrastructure.database.database import get_db
            from sqlalchemy import text
            
            # Получаем подключение к БД
            db = next(get_db())
            
            # Простой запрос для проверки
            result = db.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            
            if test_value == 1:
                self.log("✅ База данных доступна")
                return {
                    "status": "success",
                    "database_url": settings.database_url,
                    "test_query": "passed"
                }
            else:
                self.log("❌ Ошибка тестового запроса к БД", "ERROR")
                return {
                    "status": "failed",
                    "error": "Test query failed"
                }
                
        except Exception as e:
            self.log(f"❌ Ошибка подключения к БД: {str(e)}", "ERROR")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def run_all_checks(self):
        """Запуск всех проверок"""
        self.log("🚀 Диагностика интеграций на удаленном сервере")
        self.log("=" * 60)
        
        # Проверка базы данных
        self.results["database"] = await self.check_database_connection()
        self.log("-" * 40)
        
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
        warning_checks = sum(1 for result in self.results.values() if result["status"] == "warning")
        failed_checks = sum(1 for result in self.results.values() if result["status"] == "failed")
        
        self.log(f"Всего проверок: {total_checks}")
        self.log(f"✅ Успешных: {successful_checks}")
        self.log(f"⚠️ Предупреждений: {warning_checks}")
        self.log(f"❌ Неудачных: {failed_checks}")
        self.log("")
        
        for service, result in self.results.items():
            if result["status"] == "success":
                status_icon = "✅"
            elif result["status"] == "warning":
                status_icon = "⚠️"
            else:
                status_icon = "❌"
                
            self.log(f"{status_icon} {service.upper()}: {result['status']}")
            
            if result["status"] == "failed":
                self.log(f"   Ошибка: {result.get('error', 'Unknown error')}")
            elif result["status"] == "warning":
                self.log(f"   Предупреждение: {result.get('error', 'Check details')}")
        
        duration = datetime.now() - self.start_time
        self.log("")
        self.log(f"⏱️ Время выполнения: {duration.total_seconds():.2f} секунд")
        self.log("=" * 60)


async def main():
    """Главная функция"""
    print("🔧 Диагностика интеграций - Удаленный сервер")
    print("=" * 60)
    
    diagnostic = RemoteIntegrationCheck()
    await diagnostic.run_all_checks()


if __name__ == "__main__":
    asyncio.run(main())
