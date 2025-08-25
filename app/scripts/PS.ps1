param(
    $givenName,
    $displayName,
    $sn,
    $company,
    $department,
    $description,
    $managerUid,
    $physicalDeliveryOfficeName,
    $streetAddress = $physicalDeliveryOfficeName,
    $pager,
    $city = $physicalDeliveryOfficeName,
    $telephoneNumber
)
$PWord = ConvertTo-SecureString -String "" -AsPlainText -Force
$PSCredential = New-Object System.Management.Automation.PSCredential('central\', $Pword)
$Session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri http://mailzone..com/PowerShell/ -Authentication Kerberos -Credential ($PSCredential)

function Create
{
    function Translit
    {
        param([string]$inString)
        $Translit = @{

            [char]'а' = "a"
            [char]'А' = "a"
            [char]'б' = "b"
            [char]'Б' = "b"
            [char]'в' = "v"
            [char]'В' = "v"
            [char]'г' = "g"
            [char]'Г' = "g"
            [char]'д' = "d"
            [char]'Д' = "d"
            [char]'е' = "e"
            [char]'Е' = "e"
            [char]'ё' = "e"
            [char]'Ё' = "e"
            [char]'ж' = "zh"
            [char]'Ж' = "zh"
            [char]'з' = "z"
            [char]'З' = "z"
            [char]'и' = "i"
            [char]'И' = "i"
            [char]'й' = "i"
            [char]'Й' = "i"
            [char]'к' = "k"
            [char]'К' = "k"
            [char]'л' = "l"
            [char]'Л' = "l"
            [char]'м' = "m"
            [char]'М' = "m"
            [char]'н' = "n"
            [char]'Н' = "n"
            [char]'о' = "o"
            [char]'О' = "o"
            [char]'п' = "p"
            [char]'П' = "p"
            [char]'р' = "r"
            [char]'Р' = "r"
            [char]'с' = "s"
            [char]'С' = "s"
            [char]'т' = "t"
            [char]'Т' = "t"
            [char]'у' = "u"
            [char]'У' = "u"
            [char]'ф' = "f"
            [char]'Ф' = "f"
            [char]'х' = "h"
            [char]'Х' = "h"
            [char]'ц' = "ts"
            [char]'Ц' = "ts"
            [char]'ч' = "ch"
            [char]'Ч' = "ch"
            [char]'ш' = "sh"
            [char]'Ш' = "sh"
            [char]'щ' = "sch"
            [char]'Щ' = "sch"
            [char]'ъ' = ""
            [char]'Ъ' = ""
            [char]'ы' = "y"
            [char]'Ы' = "y"
            [char]'ь' = ""
            [char]'Ь' = ""
            [char]'э' = "e"
            [char]'Э' = "e"
            [char]'ю' = "yu"
            [char]'Ю' = "yu"
            [char]'я' = "ya"
            [char]'Я' = "ya"
            [char]' ' = "-" #пробел

        }
        $outString = "";
        $chars = $inString.ToCharArray();
        foreach ($char in $chars)
        {
            $outString += $Translit[$char]
        }
        return $outString;
    }
    $sAMAccountName1 = translit($givenName)
    $sAMAccountName2 = translit($sn)
    $sAMAccountName = $sAMAccountName1 + '.' + $sAMAccountName2

    if ($company -like '*STI*' -or $company -like '*трой*')
    {
        $UserPrincipalName = $sAMAccountName + '@st-ing.com'
    }
    elseif ($company -like '*DTtermo*' -or $company -like '*ДТ*')
    {
        $UserPrincipalName = $sAMAccountName + '@dttermo.ru'
    }
    else
    {
        $UserPrincipalName = $sAMAccountName + '@st-ing.com'
    }

    function find_ou
    {

        param (
            $obj_name,
            $department
        )
        if ($obj_name -like '*прудный*')
        {
            $OU = "OU=Доп. офис Трёхпрудный,OU=Отдел управления проектами,OU=Технический департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        }
        if ($obj_name -like '*Лобня*')
        {
            if ($department -like '*Отдел логистики и складского учета*')
            {
                $OU = "OU=Отдел логистики и складского учета,OU=Коммерческий департамент,OU=DtTermo,DC=central,DC=st-ing,DC=com"
            }
        }
        if ($obj_name -like '*Медовый*')
        {
            if ($department -like "*информац*")
            {
                $OU = "OU=Отдел информационных технологий,OU=Департамент обеспечения,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            }
            if ($department -like '*кадро*')
            {
                $OU = "OU=Отдел кадров,OU=Департамент обеспечения,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            }
            if ($department -like '*персона*')
            {
                $OU = "OU=Отдел персонала,OU=Департамент обеспечения,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            }
            if ($department -like '*управленческ*')
            {
                $OU = "OU=Отдел управленческого учета,OU=Департамент обеспечения,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            }
            if ($department -like '*проектир*')
            {
                $OU = "OU=Отдел проектирования,OU=Департамент развития,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            }
            if ($department -like '*ендерны*')
            {
                $OU = "OU=Тендерный отдел,OU=Департамент развития,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            }
            if ($department -like '*закупок*')
            {
                $OU = "OU=Отдел закупок,OU=Коммерческий департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            }
            if ($department -like '*логистик*')
            {
                $OU = "OU=Отдел логистики и складского учета,OU=Коммерческий департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            }
            if ($department -like '*снабже*')
            {
                $OU = "OU=Отдел снабжения,OU=Коммерческий департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            }
            if ($department -like '*труд*')
            {
                $OU = "OU=Отдел охраны труда,OU=Технический департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            }
            if ($department -like '*ПТО*')
            {
                $OU = "OU=Отдел ПТО,OU=Технический департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            }
            if ($department -like '*метный*')
            {
                $OU = "OU=Сметный отдел,OU=Технический департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            }
            if ($department -like '*ланово*')
            {
                $OU = "OU=Планово экономический отдел,OU=Финансовый департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            }
            if ($department -like '*ухгалтери*')
            {
                $OU = "OU=Бухгалтерия,OU=Финансовый департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            }
            if ($department -like '*азначе*')
            {
                $OU = "OU=Казначейство,OU=Финансовый департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            }
            if ($department -like '*ридически*')
            {
                $OU = "OU=Юридический отдел,OU=Юридический департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            }
            if ($department -like "*дминистративны*")
            {
                $OU = "OU=Административный отдел,OU=Департамент обеспечения,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
            }
        }
        if ($obj_name -like '*емеров*' -or $obj_name -like '*амчатк*' -or $obj_name -like '*гнитогор*' -or $obj_name -like '*инько*' -or $obj_name -like '*ер К32*' -or $obj_name -like '*авидо*' -or $obj_name -like '*ктафар*' -or $obj_name -like '*ухарев*' -or $obj_name -like '*алент*' -or $obj_name -like '*рофлот*' -or $obj_name -like '*ON*')
        {
            $OU = "OU=" + $obj_name + ",OU=Строительные объекты,OU=Отдел управления проектами,OU=Технический департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        }
        return $OU

    }

    function add_sec_dep_group
    {

        param (
            $department
        )

        if ($department -like '*кадро*')
        {
            $group_otdel = "CN=Отдел кадров,OU=Отдел кадров,OU=Департамент обеспечения,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        }
        if ($department -like '*персона*')
        {
            $group_otdel = "CN=Отдел персонала,OU=Отдел персонала,OU=Департамент обеспечения,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        }
        if ($department -like '*управленческ*')
        {
            $group_otdel = "CN=Отдел управленческого учета,OU=Отдел управленческого учета,OU=Департамент обеспечения,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        }
        if ($department -like '*проектир*')
        {
            $group_otdel = "CN=Отдел проектирования,OU=Отдел проектирования,OU=Департамент развития,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        }
        if ($department -like '*ендерны*')
        {
            $group_otdel = "CN=Тендерный отдел,OU=Тендерный отдел,OU=Департамент развития,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        }
        if ($department -like '*закупок*')
        {
            $group_otdel = "CN=Отдел закупок,OU=Отдел закупок,OU=Коммерческий департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        }
        if ($department -like '*логистик*')
        {
            $group_otdel = "CN=Отдел логистики и складского учета,OU=Отдел логистики и складского учета,OU=Коммерческий департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        }
        if ($department -like '*снабже*')
        {
            $group_otdel = "CN=Отдел снабжения,OU=Отдел снабжения,OU=Коммерческий департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        }
        if ($department -like '*труд*')
        {
            $group_otdel = "CN=Отдел охраны труда,OU=Отдел охраны труда,OU=Технический департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        }
        if ($department -like '*ПТО*')
        {
            $group_otdel = "CN=Отдел ПТО,OU=Отдел ПТО,OU=Технический департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        }
        if ($department -like '*метный*')
        {
            $group_otdel = "CN=Сметный отдел,OU=Сметный отдел,OU=Технический департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        }
        if ($department -like '*ланово*')
        {
            $group_otdel = "CN=Планово экономический отдел,OU=Планово экономический отдел,OU=Финансовый департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        }
        if ($department -like '*ухгалтери*')
        {
            $group_otdel = "CN=Бухгалтерия,OU=Бухгалтерия,OU=Финансовый департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        }
        if ($department -like '*азначе*')
        {
            $group_otdel = "CN=Казначейство,OU=Казначейство,OU=Финансовый департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        }
        if ($department -like '*ридически*')
        {
            $group_otdel = "CN=Юридический отдел,OU=Юридический отдел,OU=Юридический департамент,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        }
        if ($department -like "*дминистративны*")
        {
            $group_otdel = "CN=Административный отдел,OU=Административный отдел,OU=Департамент обеспечения,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        }
        if ($department -like "*информац*")
        {
            $group_otdel = "CN=Отдел информационных технологий,OU=Отдел информационных технологий,OU=Департамент обеспечения,OU=СтройТехноИнженеринг,DC=central,DC=st-ing,DC=com"
        }


        return $group_otdel


    }
    if ($technical -eq 'technical')
    {
        $OU = 'OU=Технические логины,DC=central,DC=st-ing,DC=com'
    }
    else
    {
        $OU = find_ou -obj_name $city -department $department
    }
    $password = ConvertTo-SecureString -String '' -AsPlainText -Force

    try
    {
        $OU = find_ou -obj_name $city -department $department
        $userParams = @{
            DisplayName = $displayName
            Name = $displayName
            GivenName = $givenName
            Surname = $sn
            SamAccountName = $sAMAccountName
            UserPrincipalName = $UserPrincipalName
            Path = $OU
            AccountPassword = $password
            ChangePasswordAtLogon = $true
            Enabled = $true
        }
        New-ADUser @userParams
    }
    catch
    {
        Write-Error "Ошибка при создании пользователя: $( $_.Exception.Message )"
    }

    Import-PSSession $Session -DisableNameChecking
    try
    {
        Enable-Mailbox -Identity $sAMAccountName -Database "STI_Mailbox"
    }
    catch
    {
        Write-Host 'Mailbox already exists'
    }

    #$managerFilter = "pager -eq '$managerUid'"
    #$managerObject = Get-ADUser -Filter $managerFilter -Properties *
    #$managerDn = $managerObject.DistinguishedName
	
	# Поиск и назначение менеджера
if ($managerUid -ne "") {
    try {
        # Если `pager` нельзя использовать в `-Filter`, выполняем фильтрацию через `Where-Object`
        $managerObject = Get-ADUser -Filter * -Properties pager | Where-Object { $_.pager -eq $managerUid }
        
        # Проверка наличия найденного объекта менеджера
        if ($managerObject) {
            $managerDn = $managerObject.DistinguishedName
            Set-ADUser -Identity $sAMAccountName -Replace @{ manager = $managerDn }
            Write-Host "Менеджер для пользователя $sAMAccountName успешно обновлен."
        } else {
            Write-Host "Менеджер с UID $managerUid не найден."
        }
    } catch {
        Write-Host "Произошла ошибка при обновлении менеджера: $($_.Exception.Message)"
    }
} else {
    Write-Host "UID менеджера не указан, пропускаем установку менеджера."
}


    try {
        Set-ADUser -Identity $sAMAccountName -Replace @{ pager = "$pager" }
        Set-ADUser -Identity $sAMAccountName -city $city -Company $company -Department $department -title $description -Description $description -Manager $managerDn -StreetAddress $streetAddress -Office $physicalDeliveryOfficeName
    }
    catch {
        Write-Error "An error occurred while updating all atrib: $( $_.Exception.Message )"
    }

    try {
        Set-ADUser -Identity $sAMAccountName -Replace @{manager=$managerDn}
        Write-Host "manager for user $sAMAccountName updated to the manager successfully."
    } catch {
        Write-Host "An error occurred while updating the manager: $($_.Exception.Message)"
    }

    try {
        Set-ADUser -Identity $sAMAccountName -Replace @{telephoneNumber=$telephoneNumber}
        Write-Host "Phone number for user $sAMAccountName updated to $newTelephoneNumber successfully."
    } catch {
        Write-Host "An error occurred while updating the phone number: $($_.Exception.Message)"
    }

    $usr = get-aduser -Identity $sAMAccountName
    #Группа Организации
    if ($company -like "*СТРОЙ*" -or $company -like "*ТЕХНО*" -or $company -like "*ИНЖЕНЕРИНГ*")
    {
        Add-ADGroupMember -Identity СтройТехноИнженеринг -members $usr.SamAccountName
    }
    if ($company -like "*STI*" -or $company -like "*трой*")
    {
        Add-ADGroupMember -Identity СтройТехноИнженеринг -members $usr.SamAccountName
    }
    if ($company -like "*Dttermo*" -or $company -like "*ДТ*")
    {
        Add-ADGroupMember -Identity DttermoSign -members $usr.SamAccountName
    }
    #Группа объекта
    $group_otdel = find_ou -obj_name $city -department $department

    Add-ADGroupMember -Identity $department -members $SamAccountName



    #группа отдела
    Write-Host $sn
    if ($company -like '*STI*' -or $company -like '*трой*')
    {
        $mailadr = $sAMAccountName + '@st-ing.com'
    }
    elseif ($company -like '*DTtermo*' -or $company -like '*ДТ*')
    {
        $mailadr = $sAMAccountName + '@dttermo.ru'
    }
    else
    {
        $mailadr = $sAMAccountName + '@st-ing.com'
    }

    $HUBServer = "mailzone.central.st-ing.com"
    $PWord = ConvertTo-SecureString -String "ПАРОЛЬ АДМИНА" -AsPlainText -Force
    $User = "central\ЛОГИН АДМИНА"
    $Credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $User, $PWord
    $HUBTask = new-object net.mail.smtpclient($HUBServer)
    $HUBTask.port = "465"
    $HUBTask.Credentials = $Credential
    $EMail = new-object net.mail.mailmessage
    $EMail.Subject = "Подтверждение приема " + $UsrIdentity
    $EMail.From = "noreply@st-ing.com"
    if ($technical -eq 'technical')
    {
        $Email.to.add("sta@st-ing.com")
        $Email.to.add("den@st-ing.com")
		$EMail.To.add("ian@st-ing.com")
    }
    else
    {
        $EMail.To.add("h@st-ing.com")
        $EMail.To.add("il@st-ing.com")
        $EMail.To.add("ok@st-ing.com")
        $EMail.To.add("st@st-ing.com")
        $EMail.To.add("den@st-ing.com")
		$EMail.To.add("ian@st-ing.com")
		$EMail.To.add("pav@st-ing.com")
		$EMail.To.add("evg@st-ing.com")
		$EMail.To.add("alek@st-ing.com")
		$EMail.To.add("dmitn@st-ing.com")
    }
    $tempmsg = $sAMAccountName + ' - учетная запись
' + $mailadr + ' - почта
' + ' - пароль для первого входа в учетную запись'
    $EMail.Body = $tempmsg
    $HUBTask.send($EMail)
    Start-Sleep -s 5
    $filenameAndPath = "C:\www\email_files\Инструкция по управлению почтой СТИ.docx"
    $attachment = New-Object System.Net.Mail.Attachment($filenameAndPath)
    $filenameAndPath2 = "C:\www\email_files\Welcomebook STI.pdf"
    $attachment2 = New-Object System.Net.Mail.Attachment($filenameAndPath2)
    $filenameAndPath3 = "C:\www\email_files\Инструкция по ServiceDesk.docx"
    $attachment3 = New-Object System.Net.Mail.Attachment($filenameAndPath3)
    $welcomsg = [string](get-content ("C:\www\email_files\Welcome.html") -encoding 'utf8')
    $welcomail = new-object net.mail.mailmessage
    $welcomail.Subject = " Добро пожаловать в компанию! " + $displayName + ' !'
    $welcomail.BodyEncoding = ([System.text.Encoding]::UTF8)
    $welcomail.From = "noreply@st-ing.com"
    if ($technical -eq 'technical')
    {
        $Email.to.add("sta@st-ing.com")
    }
    else
    {
        $welcomail.To.add("sta@st-ing.com")
        $welcomail.To.add("den@st-ing.com")
		$welcomail.To.add("ian@st-ing.com")
		$welcomail.To.add("alek@st-ing.com")
		$welcomail.To.add("pave@st-ing.com")
		$welcomail.To.add("evge@st-ing.com")
		$welcomail.To.add("dmi@st-ing.com")
    }
    $welcomail.To.add($mailadr)
    $welcomail.Attachments.Add($attachment)
    $welcomail.Attachments.Add($attachment2)
    $welcomail.Attachments.Add($attachment3)
    $welcomail.isBodyHTML = $true
    $welcomail.BodyTransferEncoding = 0
    $welcomail.Body = $welcomsg
    $HUBTask.send($welcomail)
    $enc = [system.Text.Encoding]::UTF8
}



Create #($givenName,$displayName,$sn,$company,$department,$description,$physicalDeliveryOfficeName,$streetAddress,$pager,$city)

Remove-PSSession $Session