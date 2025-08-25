function Get-ADUsers
{
    try
    {
        $users = Get-ADUser -Filter * -Properties DisplayName, Mail, GivenName, PhysicalDeliveryOfficeName, IpPhone, Department, Description, Pager, PostalCode,  postOfficeBox, SAMAccountName, DistinguishedName, Company, TelephoneNumber, ThumbnailPhoto, LastLogon, PwdLastSet, WhenCreated, WhenChanged, userAccountControl |
                Where-Object { $_.DisplayName -ne $null -and $_.DisplayName -notmatch 'Администратор|Microsoft|E4E|SystemMailbox|HealthMailbox|Почтовый ящик поиска методом обнаружения|wms|WMS|Пользователь' -and ($_.userAccountControl -band 2) -eq 0 } |
                Select-Object @{
                    Name = "displayName"; Expression = { $_.DisplayName }
                },
                @{
                    Name = "mail"; Expression = { $_.Mail }
                },
                @{
                    Name = "givenName"; Expression = { $_.GivenName }
                },
                @{
                    Name = "physicalDeliveryOfficeName"; Expression = { $_.PhysicalDeliveryOfficeName }
                },
                @{
                    Name = "ipPhone"; Expression = { $_.IpPhone }
                },
                @{
                    Name = "department"; Expression = { $_.Department }
                },
                @{
                    Name = "description"; Expression = { $_.Description }
                },
                @{
                    Name = "pager"; Expression = { $_.Pager }
                },
                @{
                    Name = "postalCode"; Expression = { $_.PostalCode }
                },
				@{
                    Name = "postOfficeBox"; Expression = { $_.postOfficeBox }
                },
                @{
                    Name = "sAMAccountName"; Expression = { $_.SAMAccountName }
                },
                @{
                    Name = "distinguishedName"; Expression = { $_.DistinguishedName }
                },
                @{
                    Name = "company"; Expression = { $_.Company }
                },
                @{
                    Name = "telephoneNumber"; Expression = { $_.TelephoneNumber }
                },
                @{
                    Name = "thumbnailPhoto"; Expression = { if ($_.ThumbnailPhoto)
                    {
                        "data:image/jpeg;base64," + [System.Convert]::ToBase64String($_.ThumbnailPhoto)
                    }
                    else
                    {
                        $null
                    } }
                },
                @{
                    Name = "lastLogon"; Expression = { if ($_.LastLogon)
                    {
                        [datetime]::FromFileTime($_.LastLogon).ToString("yyyy-MM-dd")
                    }
                    else
                    {
                        $null
                    } }
                },
                @{
                    Name = "pwdLastSet";
                    Expression = { if ($_.PwdLastSet)
                    {
                        [datetime]::FromFileTime($_.PwdLastSet).ToString("yyyy-MM-dd")
                    }
                    else
                    {
                        $null
                    } }
                },
                @{
                    Name = "whenCreated"; Expression = { $_.WhenCreated.ToString("yyyy-MM-dd") }
                },
                @{
                    Name = "whenChanged"; Expression = { $_.WhenChanged.ToString("yyyy-MM-dd") }
                },
                @{
                    Name = "userAccountControl"; Expression = { $_.userAccountControl }
                }
        $usersJson = $users | ConvertTo-Json -Depth 3
        $outputFilePath = "C:/userJSON/users.json"
        $usersJson | Out-File -FilePath $outputFilePath -Encoding utf8
        Write-Host "Data exported to $outputFilePath"

    }
    catch
    {
        Write-Error "Произошла ошибка: $_"
    }
}

Get-ADUsers




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