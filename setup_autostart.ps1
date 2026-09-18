$ErrorActionPreference = 'Stop'

$workDir = 'C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\Trendcarpet_Interiors'
$scriptPath = Join-Path $workDir 'start_hub_with_tunnel.py'
$pythonw = 'C:\Users\AndronikLindgren\miniconda3\pythonw.exe'

Write-Host '[1/2] Registrerar schemalagd aktivitet i Windows Task Scheduler...'
$action = New-ScheduledTaskAction -Execute $pythonw -Argument $scriptPath -WorkingDirectory $workDir
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Days 365) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName 'Trendcarpet_QA_Hub' -Action $action -Trigger $trigger -Settings $settings -Description 'Trendcarpet Photo QA Hub Backend' -Force
Write-Host '  [OK] Schemalagd aktivitet skapad: Trendcarpet_QA_Hub (kor vid inloggning)'

Write-Host '[2/2] Uppdaterar autostart i Startup-mappen...'
$startupFolder = [System.Environment]::GetFolderPath('Startup')
$vbsPath = Join-Path $startupFolder 'Start_Foto_QA_Hub.vbs'
$v1 = 'Set WshShell = CreateObject("WScript.Shell")' + [Environment]::NewLine
$v2 = 'WshShell.CurrentDirectory = "' + $workDir + '"' + [Environment]::NewLine
$v3 = 'WshShell.Run """' + $pythonw + '"" start_hub_with_tunnel.py", 0, False' + [Environment]::NewLine
[System.IO.File]::WriteAllText(
    $vbsPath,
    ($v1 + $v2 + $v3),
    [System.Text.Encoding]::ASCII
)
Write-Host ('  [OK] Uppdaterade: ' + $vbsPath)

Write-Host ''
Write-Host '=== Autostart ar nu 100% konfigurerat for Windows-uppstart ==='
