#!/usr/bin/env python3
"""
Комплексная диагностика внешних подключений приложения:
 - DNS и TCP до AD/Exchange/SMTP/WinRM
 - LDAP bind и базовые запросы
 - WinRM базовая команда (Get-Date)
 - Exchange PowerShell сессия (легкий вызов)
 - SMTP подключение/опциональная аутентификация
 - База данных (SQLite) доступность файла
 - API и 1C статус-эндпоинты

Запуск внутри контейнера:
  docker exec -it user-management-app python /app/connectivity_diagnostic.py
"""

import asyncio
import os
import sys
import socket
import time
import errno
import traceback
from typing import Dict, Any, Tuple

# Добавляем путь к приложению, если скрипт выполняется внутри контейнера
APP_PATH = "/app"
if os.path.isdir(APP_PATH) and APP_PATH not in sys.path:
    sys.path.append(APP_PATH)

from app.core.config.settings import Settings  # type: ignore


def print_section(title: str):
    print()
    print(title)
    print("=" * max(50, len(title)))


def tcp_check(host: str, port: int, timeout: float = 5.0) -> Tuple[bool, str]:
    try:
        start = time.time()
        with socket.create_connection((host, port), timeout=timeout) as s:
            try:
                s.settimeout(1.0)
                # Небольшой баннер/привет (например, WinRM/HTTP может ответить)
                try:
                    s.send(b"GET /wsman HTTP/1.1\r\nHost: %b\r\n\r\n" % host.encode())
                except Exception:
                    pass
            except Exception:
                pass
            elapsed = round((time.time() - start) * 1000, 2)
            return True, f"TCP OK ({elapsed} ms)"
    except OSError as e:
        code = e.errno
        hint = ""
        if code in (errno.ECONNREFUSED,):
            hint = "(refused: порт закрыт/файрвол)"
        elif code in (errno.ETIMEDOUT,):
            hint = "(timeout: блокировка по сети/файрвол/маршрутизация)"
        elif code in (errno.EHOSTUNREACH, errno.ENETUNREACH):
            hint = "(unreachable: маршрут отсутствует/ACL)"
        return False, f"TCP ERR [{code}] {e} {hint}"
    except Exception as e:
        return False, f"TCP ERR: {type(e).__name__}: {e}"


async def test_dns_and_tcp(settings: Settings):
    print_section("🌐 DNS/TCP ПРОВЕРКИ")
    items = [
        ("AD", settings.ad_server, [settings.ldap_port, settings.ldap_ssl_port]),
        ("WinRM", settings.winrm_server or settings.ad_server, [settings.winrm_port]),
        ("Exchange", settings.exchange_server, [80, 443]),
    ]
    if settings.smtp_server:
        items.append(("SMTP", settings.smtp_server, [int(settings.smtp_port)]))

    for name, host, ports in items:
        try:
            ip = socket.gethostbyname(host)
            print(f"{name}: {host} -> {ip}")
        except Exception as e:
            print(f"{name}: DNS ERR for {host}: {e}")
            print("  Подсказка: проверь extra_hosts/docker DNS или .env хостнейм")
            continue

        for p in ports:
            ok, msg = tcp_check(host, int(p))
            print(f"  - Port {p}: {msg}")
            if not ok:
                print("    Подсказка: проверь firewall на целевом узле, маршрут до подсети Docker, правила для порта")


async def test_ldap(settings: Settings):
    print_section("🔐 LDAP ТЕСТЫ")
    try:
        from ldap3 import Server, Connection, SIMPLE, SUBTREE, ALL  # type: ignore
    except Exception as e:
        print(f"ldap3 не установлен: {e}")
        return

    server = Server(settings.ad_server, get_info=ALL, connect_timeout=settings.ldap_timeout, use_ssl=False, port=settings.ldap_port)
    user_upn = f"{settings.admin_username}@{settings.ad_domain}"
    try:
        conn = Connection(server, user=user_upn, password=settings.admin_password, authentication=SIMPLE, auto_bind=True)
        print("Bind SIMPLE UPN: OK")
        try:
            conn.search(settings.ldap_base_dn, "(objectClass=user)", SUBTREE, attributes=["cn"], size_limit=3)
            print(f"Поиск пользователей: OK (найдено {len(conn.entries)} записей)")
        except Exception as e:
            print(f"Поиск пользователей: ERR: {e}")
            if hasattr(conn, 'result'):
                print(f"  LDAP result: {conn.result}")
        finally:
            try:
                if hasattr(conn, 'result'):
                    print(f"Bind result: {conn.result}")
            except Exception:
                pass
            conn.unbind()
    except Exception as e:
        print(f"Bind SIMPLE UPN: ERR: {e}")
        print("  Подсказка: проверь ADMIN_USERNAME/ADMIN_PASSWORD/AD_DOMAIN, SSL/порт и доступ из контейнера")


async def test_winrm(settings: Settings):
    print_section("💻 WINRM ТЕСТ")
    try:
        from app.infrastructure.external.winrm_service import WinRMService  # type: ignore
    except Exception as e:
        print(f"Импорт WinRMService ERR: {e}")
        return

    try:
        svc = WinRMService()
        res = await svc.execute_powershell("Get-Date")
        if res.get("success"):
            print("WinRM PowerShell: OK")
            if res.get("stdout"):
                print("  STDOUT:")
                print("  " + res["stdout"].strip().replace("\n", "\n  "))
        else:
            print("WinRM PowerShell: ERR")
            print(f"  status_code: {res.get('status_code')}")
            if res.get("stderr"):
                print("  STDERR:")
                print("  " + res["stderr"].strip().replace("\n", "\n  "))
            if res.get("stdout"):
                print("  STDOUT:")
                print("  " + res["stdout"].strip().replace("\n", "\n  "))
            print("  Подсказка: включи WinRM, открой порт, разреши подсеть Docker в Windows Firewall")
    except Exception as e:
        print(f"WinRM исключение: {e}")
        print("  Трассировка:")
        print("  " + traceback.format_exc().replace("\n", "\n  "))


async def test_exchange(settings: Settings):
    print_section("✉️ EXCHANGE POWERSHELL ТЕСТ")
    try:
        from app.infrastructure.external.winrm_service import WinRMService  # type: ignore
    except Exception as e:
        print(f"Импорт WinRMService ERR: {e}")
        return

    # Лёгкая проверка подключения к Exchange PowerShell: открыть сессию и вызвать простой cmdlet
    ps = f"""
    $ErrorActionPreference = 'Stop'
    $PWord = ConvertTo-SecureString -String "{settings.admin_password}" -AsPlainText -Force
    $Cred = New-Object System.Management.Automation.PSCredential('{settings.ad_domain}\\{settings.admin_username}', $PWord)

    try {{
        $sess = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri "http://{settings.exchange_server}/PowerShell/" -Authentication Kerberos -Credential $Cred -AllowRedirection
    }} catch {{ $sess = $null }}
    if ($null -eq $sess) {{
        try {{
            $sess = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri "https://{settings.exchange_server}/PowerShell/" -Authentication Basic -Credential $Cred -AllowRedirection
        }} catch {{ $sess = $null }}
    }}

    if ($null -eq $sess) {{
        Write-Host "EXCHANGE: CONNECT ERR"
        exit 1
    }}

    Import-PSSession $sess -DisableNameChecking | Out-Null
    try {{ Get-OrganizationConfig | Select-Object Name | Out-String | Write-Host }} catch {{ Write-Host "EXCHANGE: QUERY ERR" }}
    Remove-PSSession $sess
    """

    try:
        svc = WinRMService()
        res = await svc.execute_powershell(ps)
        if res.get("success"):
            print("Exchange PowerShell: OK")
            if res.get("stdout"):
                out = res["stdout"].strip()
                if out:
                    print("  STDOUT (tail):")
                    tail = "\n".join(out.splitlines()[-10:])
                    print("  " + tail.replace("\n", "\n  "))
        else:
            print("Exchange PowerShell: ERR")
            if res.get("stderr"):
                print("  STDERR:")
                print("  " + res["stderr"].strip().replace("\n", "\n  "))
            if res.get("stdout"):
                print("  STDOUT:")
                print("  " + res["stdout"].strip().replace("\n", "\n  "))
            print("  Подсказка: проверь Kerberos/Basic на Exchange PowerShell и права учётки")
    except Exception as e:
        print(f"Exchange исключение: {e}")
        print("  Трассировка:")
        print("  " + traceback.format_exc().replace("\n", "\n  "))


async def test_smtp(settings: Settings):
    print_section("📮 SMTP ТЕСТ")
    if not settings.smtp_server:
        print("SMTP не настроен")
        return
    import ssl
    import smtplib

    host = settings.smtp_server
    port = int(settings.smtp_port)
    try:
        if port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host=host, port=port, context=context, timeout=settings.smtp_timeout) as s:
                code, banner = s.docmd('EHLO', 'diagnostic')
                print(f"SMTP SSL connect: OK (EHLO {code})")
                if banner:
                    print("  BANNER:")
                    print("  " + banner.decode(errors='ignore').replace("\n", "\n  "))
        else:
            with smtplib.SMTP(host=host, port=port, timeout=settings.smtp_timeout) as s:
                code, banner = s.docmd('EHLO', 'diagnostic')
                if port == 587:
                    s.starttls(context=ssl.create_default_context())
                    print("SMTP STARTTLS: OK")
                    code2, banner2 = s.docmd('EHLO', 'diagnostic')
                    print(f"SMTP connect: OK (EHLO {code2})")
                    if banner2:
                        print("  BANNER:")
                        print("  " + banner2.decode(errors='ignore').replace("\n", "\n  "))
                else:
                    print(f"SMTP connect: OK (EHLO {code})")
                    if banner:
                        print("  BANNER:")
                        print("  " + banner.decode(errors='ignore').replace("\n", "\n  "))
    except Exception as e:
        print(f"SMTP ERR: {e}")
        print("  Подсказка: проверь порт (25/465/587), STARTTLS/SSL и firewall")


async def test_database(settings: Settings):
    print_section("🗄️ БАЗА ДАННЫХ")
    url = settings.database_url
    if url.startswith("sqlite:///"):
        path = url.replace("sqlite:///", "")
        if path.startswith("./"):
            path = path[2:]
        exists = os.path.exists(path)
        try:
            if exists:
                with open(path, "rb") as f:
                    f.read(1)
                print(f"SQLite файл доступен: {path}")
            else:
                print(f"SQLite файл отсутствует: {path}")
        except Exception as e:
            print(f"SQLite ERR: {e}")
    else:
        print(f"DB URL: {url}")


async def test_api_and_onec(settings: Settings):
    print_section("🧭 API / 1C ЭНДПОИНТЫ")
    import urllib.request
    import urllib.error

    candidates = [
        "http://172.17.177.57:8000/docs",
        "http://172.17.177.57:8000/redoc", 
        "http://172.17.177.57:8080/",
        "http://172.17.177.56/",
    ]

    for url in candidates:
        start = time.time()
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                elapsed = round((time.time() - start) * 1000, 2)
                body = resp.read(256)
                print(f"GET {url}: {resp.status} ({elapsed} ms)")
                if body:
                    try:
                        snippet = body.decode('utf-8', errors='ignore').strip().replace('\n', ' ')
                        print(f"  BODY: {snippet[:200]}")
                    except Exception:
                        pass
        except urllib.error.HTTPError as e:
            elapsed = round((time.time() - start) * 1000, 2)
            print(f"GET {url}: HTTP {e.code} ({elapsed} ms)")
            try:
                err_body = e.read(256)
                if err_body:
                    snippet = err_body.decode('utf-8', errors='ignore').strip().replace('\n', ' ')
                    print(f"  BODY: {snippet[:200]}")
            except Exception:
                pass
        except Exception as e:
            elapsed = round((time.time() - start) * 1000, 2)
            print(f"GET {url}: ERR {type(e).__name__}: {e} ({elapsed} ms)")
            print("  Подсказка: проверь проброс порта 8080 и запуск приложения")


async def main():
    s = Settings()

    print_section("⚙️ ТЕКУЩИЕ НАСТРОЙКИ")
    print(f"AD: {s.ad_server} / {s.ad_domain}")
    print(f"LDAP ports: {s.ldap_port},{s.ldap_ssl_port}; timeout: {s.ldap_timeout}s")
    print(f"WinRM: {s.winrm_server or s.ad_server}:{s.winrm_port}")
    print(f"Exchange: {s.exchange_server}")
    print(f"SMTP: {s.smtp_server}:{s.smtp_port}" if s.smtp_server else "SMTP: not configured")
    print(f"DB: {s.database_url}")

    await test_dns_and_tcp(s)
    await test_ldap(s)
    await test_winrm(s)
    await test_exchange(s)
    await test_smtp(s)
    await test_database(s)
    await test_api_and_onec(s)


if __name__ == "__main__":
    asyncio.run(main())


