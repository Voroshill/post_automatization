# Устанавливаем кодировку вывода в UTF-8


param(
    $objectName
)

$new_obj_name = $objectName

function Write-Log {
    param(
        [string]$message
    )
    Write-Host $message
}

# Функция для создания групп в AD
function Create-ADGroup {
    param (
        [string]$groupName,
        [string]$path
    )
    try {
        if (-not (Get-ADGroup -Filter { Name -eq $groupName })) {
            New-ADGroup -Name $groupName -Path $path -GroupCategory Security -GroupScope Global
            Write-Log "Группа '$groupName' создана."
        } else {
            Write-Log "Группа '$groupName' уже существует."
        }
    } catch {
        Write-Log "Ошибка при создании группы '$groupName': $_"
    }
}

# Создание основной папки
try {
    $basePath = "\\datastorage\Storage\06_СТИ\Строительные объекты\$new_obj_name"
    
    # Проверяем, существует ли главная папка
    if (-not (Test-Path $basePath)) {
        New-Item -ItemType Directory -Path $basePath -Force
        Write-Log "Основная папка создана: $basePath"
    } else {
        Write-Log "Основная папка уже существует: $basePath"
    }
} catch {
    Write-Log "Ошибка при создании основной папки: $_"
}

# Создание организационной единицы и групп
try {
    $ouPath = "OU=права $new_obj_name,OU=права доступа к папкам строительных объектов,OU=Группы прав доступа к папкам,DC=central,DC=st-ing,DC=com"
    
    # Проверяем существование OU
    if (-not (Get-ADOrganizationalUnit -Filter { Name -eq "права $new_obj_name" })) {
        New-ADOrganizationalUnit -Name "права $new_obj_name" -Path "OU=права доступа к папкам строительных объектов,OU=Группы прав доступа к папкам,DC=central,DC=st-ing,DC=com"
        Write-Log "Организационная единица 'права $new_obj_name' создана."
    } else {
        Write-Log "Организационная единица 'права $new_obj_name' уже существует."
    }

    # Создание основных групп read и write
    Create-ADGroup "STORAGE-$new_obj_name-write" $ouPath
    Create-ADGroup "STORAGE-$new_obj_name-read" $ouPath

    # Список групп для вложенных папок
    $folders = @(
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
    )

    # Создание групп для каждой вложенной папки
    foreach ($folder in $folders) {
        $folderName = $folder.Replace(' ', '-') # Заменяем пробелы на дефисы
        Create-ADGroup "STORAGE-$new_obj_name-$folderName-read" $ouPath
        Create-ADGroup "STORAGE-$new_obj_name-$folderName-write" $ouPath
    }
} catch {
    Write-Log "Ошибка при создании групп или организационной единицы: $_"
}

# Создание вложенных папок
try {
    $folders = @(
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
    )

    # Создание каждой папки внутри главной
    foreach ($folder in $folders) {
        $folderPath = Join-Path -Path $basePath -ChildPath $folder
        if (-not (Test-Path $folderPath)) {
            New-Item -ItemType Directory -Path $folderPath -Force
            Write-Log "Папка '$folder' создана."
        } else {
            Write-Log "Папка '$folder' уже существует."
        }
    }
} catch {
    Write-Log "Ошибка при создании вложенных папок: $_"
}


# SIG # Begin signature block
# MIIJ3gYJKoZIhvcNAQcCoIIJzzCCCcsCAQExCzAJBgUrDgMCGgUAMGkGCisGAQQB
# gjcCAQSgWzBZMDQGCisGAQQBgjcCAR4wJgIDAQAABBAfzDtgWUsITrck0sYpfvNR
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQUwqzPw8xPmvA1X7mq/UZWhbqd
# mYugggcxMIIHLTCCBhWgAwIBAgITLwAAAAytuJFAeUaCCwAAAAAADDANBgkqhkiG
# 9w0BAQsFADBfMRMwEQYKCZImiZPyLGQBGRYDY29tMRYwFAYKCZImiZPyLGQBGRYG
# c3QtaW5nMRcwFQYKCZImiZPyLGQBGRYHY2VudHJhbDEXMBUGA1UEAxMOY2VudHJh
# bC1QREMtQ0EwHhcNMjMxMjEyMDc0MDMxWhcNMjQxMjExMDc0MDMxWjCCATkxEzAR
# BgoJkiaJk/IsZAEZFgNjb20xFjAUBgoJkiaJk/IsZAEZFgZzdC1pbmcxFzAVBgoJ
# kiaJk/IsZAEZFgdjZW50cmFsMTEwLwYDVQQLDCjQodGC0YDQvtC50KLQtdGF0L3Q
# vtCY0L3QttC10L3QtdGA0LjQvdCzMTYwNAYDVQQLDC3QlNC10L/QsNGA0YLQsNC8
# 0LXQvdGCINC+0LHQtdGB0L/QtdGH0LXQvdC40Y8xRTBDBgNVBAsMPNCe0YLQtNC1
# 0Lsg0LjQvdGE0L7RgNC80LDRhtC40L7QvdC90YvRhSDRgtC10YXQvdC+0LvQvtCz
# 0LjQuTE/MD0GA1UEAww20JDQvdC00YDQtdC5INCS0LvQsNC00LjQvNC40YDQvtCy
# 0LjRhyDQmtCw0LTRh9C10L3QutC+MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIB
# CgKCAQEAr4MgeV6osA6sSo8W9kVjz3bzypZYXnAUlgLit9ae6U0oQ+z9QDHJjzAJ
# 0Z+lWGX+cYtNdqV9tMroXsOLHCg0SUAYOwgRY+fSLLL6MIp/UWpS20DkNCE0096q
# SfFhvJky/HZl1+vXukNA5/Qr98HV45cy4dx7H5Hig9di5fx/3O3Oem+LqkIK2Kq6
# 5HSfTiybZDX2y9D9c738/ujSqxGNtYpWpTfHRdmK7LMcN6vY3cMWwlo4aoiSXr3Q
# n5wMP2Cj5Ko7HvGgchDhfdfKdBiV1Ymq+ZFETPqSmv+WTxMg35rvSX88MCuNem4S
# MnlNffqZspBfHi42Nmcyj9U/3FmfkQIDAQABo4IDBDCCAwAwJQYJKwYBBAGCNxQC
# BBgeFgBDAG8AZABlAFMAaQBnAG4AaQBuAGcwEwYDVR0lBAwwCgYIKwYBBQUHAwMw
# DgYDVR0PAQH/BAQDAgeAMB0GA1UdDgQWBBRES4DLaxtNsRGqn/acUz6zYiiO2TAf
# BgNVHSMEGDAWgBS1IN9kKE0hFBe7vkN0JiZYgd8zwjCCARIGA1UdHwSCAQkwggEF
# MIIBAaCB/qCB+4aBu2xkYXA6Ly8vQ049Y2VudHJhbC1QREMtQ0EsQ049UERDLENO
# PUNEUCxDTj1QdWJsaWMlMjBLZXklMjBTZXJ2aWNlcyxDTj1TZXJ2aWNlcyxDTj1D
# b25maWd1cmF0aW9uLERDPWNlbnRyYWwsREM9c3QtaW5nLERDPWNvbT9jZXJ0aWZp
# Y2F0ZVJldm9jYXRpb25MaXN0P2Jhc2U/b2JqZWN0Q2xhc3M9Y1JMRGlzdHJpYnV0
# aW9uUG9pbnSGO2h0dHA6Ly9QREMuY2VudHJhbC5zdC1pbmcuY29tL0NlcnRFbnJv
# bGwvY2VudHJhbC1QREMtQ0EuY3JsMIHKBggrBgEFBQcBAQSBvTCBujCBtwYIKwYB
# BQUHMAKGgapsZGFwOi8vL0NOPWNlbnRyYWwtUERDLUNBLENOPUFJQSxDTj1QdWJs
# aWMlMjBLZXklMjBTZXJ2aWNlcyxDTj1TZXJ2aWNlcyxDTj1Db25maWd1cmF0aW9u
# LERDPWNlbnRyYWwsREM9c3QtaW5nLERDPWNvbT9jQUNlcnRpZmljYXRlP2Jhc2U/
# b2JqZWN0Q2xhc3M9Y2VydGlmaWNhdGlvbkF1dGhvcml0eTA+BgNVHREENzA1oDMG
# CisGAQQBgjcUAgOgJQwjYW5kcmVpLmthZGNoZW5rb0BjZW50cmFsLnN0LWluZy5j
# b20wTwYJKwYBBAGCNxkCBEIwQKA+BgorBgEEAYI3GQIBoDAELlMtMS01LTIxLTQx
# NzA1Njg3MzYtMjMwMzU1MzEyOC0xMjc4OTUwMTI4LTE0NDYwDQYJKoZIhvcNAQEL
# BQADggEBAHRjtnczX1BnxfaeDgCIWz9tC++/Zwou/kJjEdO9+/281KFrrYOVLiEb
# NyoJpzcxScjiQzrxDmtzALOQYGtfFahmAw2YP5+Fztvu6aDWWvBPasUPQwGsu2nj
# ZFjrZyVbmD17X2eWTggJ+7kOnJJF5V/ex0uPoHP0LD4DriLSHxwJ/OfXVrTy4ass
# UJYJwEKgRFEJ3dJEdBKFKD91HJblFkImsAPxBKIPnrqGLFWzfWqUwy1DtKIpg6da
# YFMfzZWTxxc2hz55RBcvIzGC+xHAWsUnnVnk1jYENGBBqIU5GVW21cnzLPznpbpe
# d/NTGELXFCY20HNiwr9BpGBoTcLYA0ExggIXMIICEwIBATB2MF8xEzARBgoJkiaJ
# k/IsZAEZFgNjb20xFjAUBgoJkiaJk/IsZAEZFgZzdC1pbmcxFzAVBgoJkiaJk/Is
# ZAEZFgdjZW50cmFsMRcwFQYDVQQDEw5jZW50cmFsLVBEQy1DQQITLwAAAAytuJFA
# eUaCCwAAAAAADDAJBgUrDgMCGgUAoHgwGAYKKwYBBAGCNwIBDDEKMAigAoAAoQKA
# ADAZBgkqhkiG9w0BCQMxDAYKKwYBBAGCNwIBBDAcBgorBgEEAYI3AgELMQ4wDAYK
# KwYBBAGCNwIBFTAjBgkqhkiG9w0BCQQxFgQUPdBtJhNTUK698G4OhqqpoGA4+DAw
# DQYJKoZIhvcNAQEBBQAEggEANC0djQOXETcT6dorPjZJBsNI1REeCKuqo4VHQPJZ
# 1Lr62ZgUl5mLrFmwM6Sar021Xb3SCDy8lIUO3rLnq1zDpTij1gLltC7i8cPlgyca
# /6uGJExmicUId9B88TOGOcf6cfp0COt6VHErTvsUlelxoSpoSuRCZoaD/xllfJXp
# pthATf1/tK8BeCO0O+tkxzex96MCZ5vYxKfQew5CQYF85/98ZsCXzGobTu+wj7sU
# 2T+urxIXMSABqI8KJmfiwcmC1/21a1IP+xU0WcOTYgiISwvDWL1mBqZCKgfRnVSH
# +hhR0kKhurFwOg4oHME+h2yJDu1aYoLgMGF5Gx1+55HNfA==
# SIG # End signature block