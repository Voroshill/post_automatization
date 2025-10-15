## DevOps: сеть и доступы для Order

Краткая шпаргалка что нужно открыть/настроить, чтобы контейнер(ы) приложения стабильно ходили во внешние системы (AD/LDAP, WinRM/Exchange, SMTP, API/1C).

### 1) Docker-сеть (стабильный CIDR)
- В `docker-compose.yml` уже создана именованная сеть с фиксированным CIDR:
  - Сеть: `user-management_net`
  - CIDR: `172.30.0.0/24`
- Команда на применение/пересоздание:
  - `docker compose down && docker compose up -d`
 - Если целевые сервера видят не подсеть контейнера, а IP хоста (SNAT), дополнительно разрешите вход с IP хоста.

### 2) DNS/hosts
- На хосте/в контейнере должны корректно резолвиться:
  - `pdc.central.st-ing.com` → IP контроллера домена (пример: `172.17.177.29`)
  - `mailzone.central.st-ing.com` → IP Exchange (пример: `172.17.177.25`)
- В `docker-compose.yml` заданы:
  - `dns: [10.0.0.10, 10.0.0.11]`
  - `extra_hosts` для DC/Exchange (оставить актуальные IP)
 - При необходимости разрешите на целевых серверах доступ от `host.docker.internal` (маршрутизируется на IP хоста).

### 3) Файрвол/ACL: разрешить подсеть Docker
Открыть доступ ИЗ подсети `172.30.0.0/24` на нужные сервисы:
- На контроллере домена/LDAP:
  - TCP 389 (LDAP), 636 (LDAPS по необходимости)
- На Exchange (узел `mailzone`):
  - TCP 5985 (WinRM HTTP)
  - TCP 5986 (WinRM HTTPS — по желанию)
  - TCP 25/465/587 (SMTP — в зависимости от используемого порта)
  - TCP 80/443 (для PowerShell over HTTP/HTTPS и/или тестов)
 - Если политика запрещает доступ целиком подсети, точечно разрешите IP контейнера (узнать: `docker inspect user-management-app ...`) и/или IP хоста.

Примеры правил Windows Firewall (на целевом сервере, PowerShell от Админа):
```
New-NetFirewallRule -DisplayName "Allow WinRM from Order Docker subnet" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 5985 -RemoteAddress 172.30.0.0/24
New-NetFirewallRule -DisplayName "Allow LDAP from Order Docker subnet"  -Direction Inbound -Action Allow -Protocol TCP -LocalPort 389  -RemoteAddress 172.30.0.0/24
New-NetFirewallRule -DisplayName "Allow SMTP from Order Docker subnet"  -Direction Inbound -Action Allow -Protocol TCP -LocalPort 587  -RemoteAddress 172.30.0.0/24
```
 Аналогично можно добавить правила на Linux (iptables/firewalld) при необходимости.

### 4) WinRM на Exchange/Windows-сервере
На `mailzone.central.st-ing.com` (или узле, через который выполняется PowerShell):
```
winrm quickconfig -q
winrm set winrm/config/service/auth @{Basic="true";Kerberos="true";NTLM="true"}
winrm set winrm/config/service @{AllowUnencrypted="true"}
```
При использовании HTTPS и Basic — настроить сертификат и открыть 5986 (опционально).
 Дополнительно:
 - Убедиться, что служба WinRM запущена (`Get-Service WinRM`).
 - Проверить `TrustedHosts` при использовании NTLM/Basic в небезопасных доменных сценариях (`winrm set winrm/config/client @{TrustedHosts="*"}` при тестировании).

### 5) Exchange PowerShell (Remote)
- Разрешить подключение Remote PowerShell к Exchange (Kerberos/Basic).
- Убедиться, что сервисная учётка имеет права для `Enable-Mailbox`.
 - При Kerberos: синхронизировано время (±5 минут), DNS/SPN корректны; иначе используйте NTLM/Basic по HTTPS.

### 6) Параметры приложения (.env)
Ключевые переменные (совпадают с `docker-compose.yml`):
```
AD_DOMAIN=central.st-ing.com
AD_SERVER=pdc.central.st-ing.com
LDAP_PORT=389
LDAP_SSL_PORT=636

WINRM_SERVER=mailzone.central.st-ing.com
WINRM_PORT=5985
EXCHANGE_SERVER=mailzone.central.st-ing.com

SMTP_SERVER=mailzone.central.st-ing.com
SMTP_PORT=587  # или 465/25

ADMIN_USERNAME=<svc-admin>
ADMIN_PASSWORD=<secret>
```
 Рекомендации по безопасности:
 - Сервисная учётка: не истекающий пароль / контролируемая ротация, ограниченные RBAC-права.
 - Для LDAPS (636): импортируйте корневой сертификат CA в контейнер, если требуется доверие к сертификату AD.
 - Для SMTP: либо разрешить релэй с подсети `172.30.0.0/24`, либо использовать аутентификацию SMTP.

### 7) Проверки/диагностика
- В контейнере:
  - `docker exec -it user-management-app python /app/connectivity_diagnostic.py`
- На Windows (вне контейнера):
  - `powershell -ExecutionPolicy Bypass -File .\scripts\connectivity_diagnostic.ps1 -EnvPath .\.env -ApiBase http://localhost:8080`

Обе диагностики печатают детальные причины (DNS, TCP errno, LDAP result, WinRM/Exchange STDERR/STDOUT, SMTP баннеры, API latency).
 При сетевых таймаутах проверьте трассировку с хоста и из контейнера (Test-NetConnection/PowerShell, `wget --spider` внутри контейнера).

### 8) Права учётной записи
- AD:
  - Разрешения на создание/изменение пользователей, назначение атрибутов/групп (по требованиям функций).
- Exchange:
  - RBAC роль/права, позволяющие `Enable-Mailbox` и управление почтовыми ящиками для нужных OU/пользователей.
- SMTP:
  - Если требуется аутентификация — валидный SMTP аккаунт и разрешение на отправку.
 - WinRM:
   - Разрешить удалённое выполнение для сервисной учётки (членство в нужных группах/политиках исполнения).

### 9) Частые причины проблем и быстрые фиксы
- DNS не резолвит имя → обновить `extra_hosts`/DNS, проверить доступность DNS-серверов.
- TCP timeout/refused → открыть порт на целевом сервере, проверить маршрут/ACL до `172.30.0.0/24`.
- WinRM `Test-WSMan` падает → включить WinRM, открыть порт, проверить Авторизацию (Kerberos/NTLM/Basic). 
- Exchange PS не коннектится → разрешить Kerberos/Basic, проверить права сервисной учётки.
- LDAP bind invalidCredentials → проверить `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `AD_DOMAIN`.
- SMTP STARTTLS/SSL ошибки → сверить порт и режим (25/465/587), сертификаты и политику сервера.
 - Kerberos/SPNEGO ошибки → проверить синхронизацию времени (NTP), часы домена и клиента, часовые пояса.
 - LDAPS ошибки сертификата → импортировать доверенные CA в контейнер/хост или использовать валидный серверный сертификат.


