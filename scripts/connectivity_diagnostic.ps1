#requires -Version 5.1
<#!
Скрипт диагностики внешних подключений (запуск на Windows вне контейнера)
Проверяет: DNS/TCP, LDAP, WinRM, Exchange PowerShell, SMTP, БД (SQLite), API/1C

Запуск из корня репозитория (или передай путь к .env):
  powershell -ExecutionPolicy Bypass -File .\scripts\connectivity_diagnostic.ps1 -EnvPath .\.env

Параметры (опционально):
  -EnvPath "C:\path\to\.env"
  -ApiBase "http://localhost:8080"
#>
param(
  [string]$EnvPath = ".\.env",
  [string]$ApiBase = "http://localhost:8080"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Section($Title) {
  "`n$Title"
  ('=' * [Math]::Max(50, $Title.Length))
}

function Load-Env($Path) {
  if (-not (Test-Path $Path)) { throw "ENV file not found: $Path" }
  $envDict = @{}
  Get-Content -LiteralPath $Path | ForEach-Object {
    $line = $_.Trim()
    if ([string]::IsNullOrWhiteSpace($line)) { return }
    if ($line.StartsWith('#')) { return }
    $idx = $line.IndexOf('=')
    if ($idx -lt 1) { return }
    $k = $line.Substring(0, $idx).Trim()
    $v = $line.Substring($idx+1).Trim()
    $envDict[$k] = $v
  }
  return $envDict
}

function Test-DnsTcp([string]$Name, [string]$Host, [int[]]$Ports) {
  if (-not $Host) { return }
  try {
    $dns = Resolve-DnsName -Name $Host -ErrorAction Stop | Select-Object -First 1
    Write-Output "$Name: $Host -> $($dns.IPAddress)"
  } catch {
    Write-Output "$Name: DNS ERR for $Host: $($_.Exception.Message)"
    Write-Output "  Hint: проверь доступность DNS/hosts, корректность имени"
    return
  }
  foreach ($p in $Ports) {
    try {
      $r = Test-NetConnection -ComputerName $Host -Port $p -WarningAction SilentlyContinue
      if ($r.TcpTestSucceeded) {
        Write-Output "  - Port $p: TCP OK (Latency ~ $($r.PingMilliseconds) ms)"
      } else {
        Write-Output "  - Port $p: TCP ERR (no connect)"
        Write-Output "    Hint: firewall/маршрутизация/ACL"
      }
    } catch {
      Write-Output "  - Port $p: TCP ERR: $($_.Exception.Message)"
    }
  }
}

function New-Cred($domain, $user, $password) {
  $u = if ($user -match '@') { $user } elseif ($domain) { "$domain\$user" } else { $user }
  $sec = ConvertTo-SecureString -String $password -AsPlainText -Force
  return New-Object System.Management.Automation.PSCredential($u, $sec)
}

function Test-Ldap($cfg) {
  Write-Section "🔐 LDAP ТЕСТЫ"
  $ad = $cfg.AD_SERVER; $domain = $cfg.AD_DOMAIN; $user = $cfg.ADMIN_USERNAME; $pass = $cfg.ADMIN_PASSWORD
  $base = $cfg.LDAP_BASE_DN; $port = [int]$cfg.LDAP_PORT
  try {
    $path = "LDAP://$ad:$port/$base"
    $de = New-Object System.DirectoryServices.DirectoryEntry($path, "$user@$domain", $pass)
    $null = $de.NativeObject  # bind
    Write-Output "Bind SIMPLE UPN: OK"
    $searcher = New-Object System.DirectoryServices.DirectorySearcher($de)
    $searcher.Filter = "(objectClass=user)"
    $searcher.PageSize = 1; $searcher.SizeLimit = 3
    $res = $searcher.FindAll()
    Write-Output "Поиск пользователей: OK (найдено $($res.Count))"
  } catch {
    Write-Output "LDAP ERR: $($_.Exception.Message)"
    Write-Output "  Hint: проверь ADMIN_USERNAME/ADMIN_PASSWORD/AD_DOMAIN/AD_SERVER и порты"
  }
}

function Test-WinRM($cfg) {
  Write-Section "💻 WINRM ТЕСТ"
  $host = $cfg.WINRM_SERVER; $port = [int]$cfg.WINRM_PORT
  try {
    $cred = New-Cred $cfg.AD_DOMAIN $cfg.ADMIN_USERNAME $cfg.ADMIN_PASSWORD
    $ws = Test-WSMan -ComputerName $host -Port $port -Authentication Default -Credential $cred -ErrorAction Stop
    Write-Output "Test-WSMan: OK (ProtocolVersion=$($ws.ProtocolVersion))"
  } catch {
    Write-Output "Test-WSMan ERR: $($_.Exception.Message)"
    Write-Output "  Hint: включи WinRM, открой $port, разреши подсеть Docker/хоста"
    return
  }
  try {
    $sess = New-PSSession -ConfigurationName Microsoft.PowerShell -ComputerName $host -Port $port -Authentication Default -Credential $cred
    $out = Invoke-Command -Session $sess -ScriptBlock { Get-Date }
    Write-Output "Invoke-Command(Get-Date): OK -> $out"
    Remove-PSSession $sess
  } catch {
    Write-Output "Invoke-Command ERR: $($_.Exception.Message)"
  }
}

function Test-Exchange($cfg) {
  Write-Section "✉️ EXCHANGE POWERSHELL ТЕСТ"
  $ex = $cfg.EXCHANGE_SERVER
  $cred = New-Cred $cfg.AD_DOMAIN $cfg.ADMIN_USERNAME $cfg.ADMIN_PASSWORD
  $sess = $null
  try {
    $sess = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri "http://$ex/PowerShell/" -Authentication Kerberos -Credential $cred -AllowRedirection
  } catch {}
  if (-not $sess) {
    try {
      $sess = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri "https://$ex/PowerShell/" -Authentication Basic -Credential $cred -AllowRedirection
    } catch {}
  }
  if (-not $sess) { Write-Output "Exchange PS CONNECT ERR"; Write-Output "  Hint: разреши Kerberos/Basic на виртуалке PowerShell"; return }
  try {
    Import-PSSession $sess -DisableNameChecking | Out-Null
    $org = Get-OrganizationConfig -ErrorAction SilentlyContinue | Select-Object -First 1 Name
    if ($org) { Write-Output "Exchange PowerShell: OK ($($org.Name))" } else { Write-Output "Exchange PowerShell: OK (no org name)" }
  } catch { Write-Output "Exchange PowerShell QUERY ERR: $($_.Exception.Message)" }
  finally { if ($sess) { Remove-PSSession $sess } }
}

function Test-SMTP($cfg) {
  Write-Section "📮 SMTP ТЕСТ"
  $host = $cfg.SMTP_SERVER; if (-not $host) { Write-Output "SMTP не настроен"; return }
  $port = [int]$cfg.SMTP_PORT
  try {
    $r = Test-NetConnection -ComputerName $host -Port $port -WarningAction SilentlyContinue
    if (-not $r.TcpTestSucceeded) { Write-Output "TCP ERR: нет подключения"; return }
    $client = New-Object System.Net.Sockets.TcpClient($host, $port)
    $stream = $client.GetStream()
    $reader = New-Object System.IO.StreamReader($stream)
    $writer = New-Object System.IO.StreamWriter($stream)
    $writer.NewLine = "`r`n"; $writer.AutoFlush = $true
    Start-Sleep -Milliseconds 200
    if ($reader.Peek() -ge 0) { $banner = $reader.ReadLine(); Write-Output "BANNER: $banner" }
    $writer.WriteLine("EHLO diagnostic")
    Start-Sleep -Milliseconds 200
    while ($reader.Peek() -ge 0) { Write-Output ("  " + $reader.ReadLine()) }
    $writer.WriteLine("QUIT")
    $reader.Dispose(); $writer.Dispose(); $client.Close()
    Write-Output "SMTP: OK"
  } catch { Write-Output "SMTP ERR: $($_.Exception.Message)" }
}

function Test-Database($cfg) {
  Write-Section "🗄️ БАЗА ДАННЫХ"
  $url = $cfg.DATABASE_URL
  if ($url -like 'sqlite:///*') {
    $path = $url.Replace('sqlite:///','')
    if ($path.StartsWith('./')) { $path = $path.Substring(2) }
    if (Test-Path $path) { try { Get-Content -LiteralPath $path -TotalCount 1 | Out-Null; Write-Output "SQLite доступен: $path" } catch { Write-Output "SQLite ERR: $($_.Exception.Message)" } } else { Write-Output "SQLite файл отсутствует: $path" }
  } else {
    Write-Output "DB URL: $url (для внешних СУБД добавь отдельные проверки)"
  }
}

function Test-ApiOneC($ApiBase) {
  Write-Section "🧭 API / 1C ЭНДПОИНТЫ"
  $urls = @(
    "$ApiBase/api/health",
    "$ApiBase/health",
    "$ApiBase/api/oneC/status",
    "$ApiBase/oneC/status",
    "$ApiBase/docs"
  )
  foreach ($u in $urls) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
      $resp = Invoke-WebRequest -Uri $u -Method GET -UseBasicParsing -TimeoutSec 5
      $sw.Stop()
      Write-Output ("GET {0}: {1} ({2} ms)" -f $u, $resp.StatusCode.value__, [math]::Round($sw.Elapsed.TotalMilliseconds,2))
    } catch {
      $sw.Stop()
      Write-Output ("GET {0}: ERR {1} ({2} ms)" -f $u, $_.Exception.Message, [math]::Round($sw.Elapsed.TotalMilliseconds,2))
    }
  }
}

try {
  Write-Section "⚙️ ЗАГРУЗКА НАСТРОЕК"
  $cfg = Load-Env -Path $EnvPath
  Write-Output ("AD: {0} / {1}" -f $cfg.AD_SERVER, $cfg.AD_DOMAIN)
  Write-Output ("LDAP ports: {0},{1}" -f $cfg.LDAP_PORT, $cfg.LDAP_SSL_PORT)
  Write-Output ("WinRM: {0}:{1}" -f $cfg.WINRM_SERVER, $cfg.WINRM_PORT)
  Write-Output ("Exchange: {0}" -f $cfg.EXCHANGE_SERVER)
  if ($cfg.SMTP_SERVER) { Write-Output ("SMTP: {0}:{1}" -f $cfg.SMTP_SERVER, $cfg.SMTP_PORT) } else { Write-Output "SMTP: not configured" }
  Write-Output ("DB: {0}" -f $cfg.DATABASE_URL)

  Write-Section "🌐 DNS/TCP ПРОВЕРКИ"
  Test-DnsTcp -Name 'AD' -Host $cfg.AD_SERVER -Ports @([int]$cfg.LDAP_PORT, [int]$cfg.LDAP_SSL_PORT)
  Test-DnsTcp -Name 'WinRM' -Host $cfg.WINRM_SERVER -Ports @([int]$cfg.WINRM_PORT)
  Test-DnsTcp -Name 'Exchange' -Host $cfg.EXCHANGE_SERVER -Ports @(80,443)
  if ($cfg.SMTP_SERVER) { Test-DnsTcp -Name 'SMTP' -Host $cfg.SMTP_SERVER -Ports @([int]$cfg.SMTP_PORT) }

  Test-Ldap -cfg $cfg
  Test-WinRM -cfg $cfg
  Test-Exchange -cfg $cfg
  Test-SMTP -cfg $cfg
  Test-Database -cfg $cfg
  Test-ApiOneC -ApiBase $ApiBase

  Write-Output "`nГотово. См. вывод выше для деталей/подсказок."
} catch {
  Write-Error $_
  exit 1
}
