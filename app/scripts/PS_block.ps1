param(
	$uid
)

function block {
	param($uid)
	write-host "Trying to find $uid in AD"
	$fug = Get-ADUser -Filter "pager -eq '$uid'" -Properties memberOf

	if ($fug -ne $null) {
		write-host $fug

		$fug.memberOf | ForEach-Object {
			Remove-ADGroupMember -Identity $_ -Members $fug.DistinguishedName -Confirm:$false
		}

		$OU = 'OU=Уволенные сотрудники,DC=central,DC=st-ing,DC=com'
		Write-host "User found: " $fug.SamAccountName
		Disable-ADAccount -Identity $fug.DistinguishedName
		Set-ADUser -Identity $fug.SamAccountName -Replace @{pager=$uid}
		Move-ADObject -Identity $fug.DistinguishedName -TargetPath $OU
	}
	else {
		Write-Host "No user found with the specified UID."
	}
}

block -uid $uid
