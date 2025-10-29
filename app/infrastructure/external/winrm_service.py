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
        self.read_timeout_sec = getattr(settings, 'winrm_timeout', 60)  # Увеличено для SMTP операций
        self.operation_timeout_sec = 30  # Должен быть меньше read_timeout_sec
        
        winrm_logger.info(f"WinRMService инициализирован. Сервер: {self.server}:{self.port}")
    
    async def execute_powershell(self, script: str) -> Dict[str, Any]:
        """Выполнение PowerShell скрипта через WinRM"""
        try:
            winrm_logger.info(f"=== ВЫПОЛНЕНИЕ POWERSHELL ЧЕРЕЗ WINRM ===")
            winrm_logger.info(f"Сервер: {self.server}:{self.port}")
            winrm_logger.info(f"Пользователь: {self.domain}\\{self.username}")
            winrm_logger.info(f"Таймаут: {self.read_timeout_sec}с")
            
            scheme = 'https' if str(self.port) == '5986' else 'http'
            winrm_logger.info(f"Схема подключения: {scheme}")
            
            session = winrm.Session(
                f"{scheme}://{self.server}:{self.port}/wsman",
                auth=(f"{self.domain}\\{self.username}", self.password),
                transport='ntlm',
                server_cert_validation='ignore',
                read_timeout_sec=self.read_timeout_sec,
                operation_timeout_sec=self.operation_timeout_sec
            )

            winrm_logger.info(f"Отправка скрипта на выполнение...")
            # Важно: run_ps — блокирующий вызов; переносим в отдельный поток, чтобы не блокировать event loop
            # Добавляем asyncio таймаут чтобы прервать зависшие операции (например SMTP)
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(session.run_ps, script),
                    timeout=45.0  # Таймаут выше чем read_timeout_sec для возможности прерывания
                )
            except asyncio.TimeoutError:
                winrm_logger.error(f"❌ WinRM операция превысила таймаут 45 секунд - возможно зависание SMTP")
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "WinRM operation timeout: SMTP send may have hung",
                    "status_code": -1
                }
            
            stdout = result.std_out.decode('utf-8', errors='ignore')
            stderr = result.std_err.decode('utf-8', errors='ignore')
            
            winrm_logger.info(f"Код завершения: {result.status_code}")
            winrm_logger.info(f"STDOUT длина: {len(stdout)} символов")
            winrm_logger.info(f"STDERR длина: {len(stderr)} символов")
            
            if stdout.strip():
                winrm_logger.info(f"STDOUT: {stdout[:500]}{'...' if len(stdout) > 500 else ''}")
            if stderr.strip():
                winrm_logger.warning(f"STDERR: {stderr[:500]}{'...' if len(stderr) > 500 else ''}")
            
            if result.status_code == 0:
                winrm_logger.info("✅ PowerShell скрипт выполнен успешно")
                return {
                    "success": True,
                    "stdout": stdout,
                    "stderr": stderr,
                    "status_code": result.status_code
                }
            else:
                winrm_logger.error(f"❌ Ошибка выполнения PowerShell (код {result.status_code})")
                winrm_logger.error(f"STDERR: {stderr}")
                return {
                    "success": False,
                    "stdout": stdout,
                    "stderr": stderr,
                    "status_code": result.status_code
                }
                
        except Exception as e:
            winrm_logger.error(f"❌ Исключение при выполнении PowerShell через WinRM: {e}")
            winrm_logger.error(f"Тип исключения: {type(e).__name__}")
            import traceback
            winrm_logger.error(f"Трассировка: {traceback.format_exc()}")
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
            # Валидация SMTP параметров
            if not settings.smtp_server or not str(settings.smtp_server).strip():
                winrm_logger.error("SMTP server is not configured")
                return {"success": False, "stderr": "SMTP server is not configured"}
            if not settings.smtp_port:
                winrm_logger.error("SMTP port is not configured")
                return {"success": False, "stderr": "SMTP port is not configured"}
            if not settings.smtp_username or not str(settings.smtp_username).strip():
                winrm_logger.error("SMTP username is not configured")
                return {"success": False, "stderr": "SMTP username is not configured"}
            if not settings.smtp_password or not str(settings.smtp_password).strip():
                winrm_logger.error("SMTP password is not configured")
                return {"success": False, "stderr": "SMTP password is not configured"}

            # Диагностика (без пароля)
            winrm_logger.info(
                f"SMTP config: server={settings.smtp_server}, port={settings.smtp_port}, username={settings.smtp_username}, use_ssl={getattr(settings, 'smtp_use_ssl', True)}"
            )

            safe_attachment = attachment_path or ""
            # Формат SMTP логина и From
            raw_username = settings.smtp_username or ""
            username_val = raw_username
            
            # Для credentials в PowerShell нужен формат domain\user (как в оригинале PS.ps1)
            # Если username это email - конвертируем в domain\user
            if "@" in username_val:
                # Преобразуем UPN в domain\user: nikita.kopyti@central.st-ing.com -> central\nikita.kopyti
                local_part = username_val.split("@")[0]
                domain_part = username_val.split("@")[1]
                # Извлекаем short domain name из FQDN: central.st-ing.com -> central
                if "." in domain_part:
                    domain_name = domain_part.split(".")[0]
                else:
                    domain_name = domain_part
                username_val = f"{domain_name}\\{local_part}"
                winrm_logger.info(f"SMTP username converted from UPN to domain\\user: {raw_username} -> {username_val}")
            elif "\\" not in username_val and settings.ad_domain:
                # Если нет ни @ ни \, добавляем domain\
                short_domain = settings.ad_domain.split(".")[0]
                username_val = f"{short_domain}\\{username_val}"
                winrm_logger.info(f"SMTP username formatted as domain\\user: {username_val}")

            # Определяем адрес отправителя: приоритет smtp_from, иначе используем email из username (для авторизации)
            # Если username это email - используем его как From (сервер требует совпадения для auth)
            if settings.smtp_from and "@" in settings.smtp_from:
                from_addr = settings.smtp_from
            elif "@" in raw_username:
                from_addr = raw_username  # Используем authenticated email как From
            else:
                from_addr = "noreply@st-ing.com"
            winrm_logger.info(f"SMTP From address: {from_addr} (using authenticated email for auth compatibility)")
            
            script = f"""
            Write-Host "[SMTP] Step 1: Preparing credentials"
            $HUBServer = "{settings.smtp_server}"
            $PWord = ConvertTo-SecureString -String "{settings.smtp_password}" -AsPlainText -Force
            $User = "{username_val}"
            Write-Host "[SMTP] Step 2: Creating credential for user: $User"
            $Credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $User, $PWord
            Write-Host "[SMTP] Step 3: Prepared credentials and server info"
            Write-Host "[SMTP] Server: $HUBServer"
            Write-Host "[SMTP] Port: {settings.smtp_port}"
            Write-Host "[SMTP] User: $User"
            Write-Host "[SMTP] From: {from_addr}"
            Write-Host "[SMTP] To: {to_email}"
            Write-Host "[SMTP] About to start send job (will timeout in 20s if hangs)..."
            
            $tempmsg = @"
{body}
"@
            
            # ДИАГНОСТИКА: Проверка доступности SMTP сервера
            Write-Host "[SMTP] Testing connection to $HUBServer port {settings.smtp_port}..."
            try {{
                $testConnection = Test-NetConnection -ComputerName $HUBServer -Port {settings.smtp_port} -WarningAction SilentlyContinue -ErrorAction Stop
                Write-Host "[SMTP] Test-NetConnection result: TcpTestSucceeded=$($testConnection.TcpTestSucceeded), RemoteAddress=$($testConnection.RemoteAddress)"
            }} catch {{
                Write-Host "[SMTP] WARNING: Test-NetConnection failed: $($_.Exception.Message)"
            }}
            
            # Проверка DNS резолюции
            try {{
                $dnsResult = Resolve-DnsName -Name $HUBServer -ErrorAction Stop
                Write-Host "[SMTP] DNS resolution: $($dnsResult | Select-Object -First 1 | ForEach-Object {{ $_.IPAddress }})"
            }} catch {{
                Write-Host "[SMTP] WARNING: DNS resolution failed: $($_.Exception.Message)"
            }}
            
            # Используем Job для отправки с таймаутом - если зависнет, сможем прервать
            Write-Host "[SMTP] Starting send job..."
            $sendJob = Start-Job -ScriptBlock {{
                param($server, $port, $username, $password, $from, $to, $subject, $body, $useSsl)
                
                try {{
                    Write-Host "[SMTP Job] Step 1: Creating credential"
                    $PWord = ConvertTo-SecureString -String $password -AsPlainText -Force
                    $Credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $username, $PWord
                    
                    Write-Host "[SMTP Job] Step 2: Creating SMTP client - Server=$server, Port=$port"
                    $HUBTask = new-object net.mail.smtpclient($server)
                    $HUBTask.port = $port
                    # Порты 465 и 587 ОБЯЗАТЕЛЬНО требуют SSL
                    if ($port -eq 465 -or $port -eq 587 -or $useSsl) {{
                        $HUBTask.EnableSsl = $true
                        Write-Host "[SMTP Job] Step 3: SSL enabled (required for port $port)"
                    }} else {{
                        Write-Host "[SMTP Job] Step 3: SSL disabled (port $port)"
                    }}
                    Write-Host "[SMTP Job] Step 4: Setting credentials for user: $username"
                    $HUBTask.Credentials = $Credential
                    Write-Host "[SMTP Job] Step 5: Setting timeout to 15s"
                    $HUBTask.Timeout = 15000
                    Write-Host "[SMTP Job] Step 6: Final config - EnableSsl=$($HUBTask.EnableSsl), Port=$($HUBTask.Port), Timeout=$($HUBTask.Timeout)ms"
                    
                    Write-Host "[SMTP Job] Step 7: Creating mail message"
                    $EMail = new-object net.mail.mailmessage
                    $EMail.Subject = $subject
                    $EMail.From = $from
                    $EMail.To.add($to)
                    $EMail.Body = $body
                    Write-Host "[SMTP Job] Step 8: Message created - From=$from, To=$to, Authenticated as=$username"
                    Write-Host "[SMTP Job] Step 9: Calling Send() - ensure From matches authenticated user for auth..."
                    $HUBTask.send($EMail)
                    Write-Host "[SMTP Job] Step 10: Send completed successfully!"
                    return "SUCCESS"
                }} catch {{
                    Write-Host "[SMTP Job] ERROR at step: $($_.Exception.Message)"
                    Write-Host "[SMTP Job] Exception type: $($_.Exception.GetType().FullName)"
                    Write-Host "[SMTP Job] Stack trace: $($_.ScriptStackTrace)"
                    if ($_.Exception.InnerException) {{
                        Write-Host "[SMTP Job] Inner exception: $($_.Exception.InnerException.Message)"
                    }}
                    return "ERROR: $($_.Exception.Message)"
                }}
            }} -ArgumentList $HUBServer, "{settings.smtp_port}", $User, "{settings.smtp_password}", "{from_addr}", "{to_email}", "{subject}", $tempmsg, $({str(getattr(settings, 'smtp_use_ssl', True)).lower()})
            
            Write-Host "[SMTP] Job started, waiting for result..."
            
            Write-Host "[SMTP] Waiting for send job (max 20 seconds)..."
            $jobResult = Wait-Job -Job $sendJob -Timeout 20
            
            if ($jobResult) {{
                $output = Receive-Job -Job $sendJob
                Remove-Job -Job $sendJob
                Write-Host "[SMTP] Job output: $output"
                if ($output -like "*ERROR*") {{
                    throw $output
                }}
            }} else {{
                Stop-Job -Job $sendJob
                Remove-Job -Job $sendJob
                Write-Host "[SMTP] ERROR: Send job timed out after 20 seconds - SMTP server may be unreachable"
                throw "SMTP send timeout - server may be unreachable or hung"
            }}
            
            Write-Host "Email отправлен успешно"
            """
            
            return await self.execute_powershell(script)
            
        except Exception as e:
            winrm_logger.error(f"Исключение при отправке email: {e}")
            return {"success": False, "stderr": str(e)}
