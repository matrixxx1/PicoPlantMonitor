param([Parameter(Mandatory = $true)][string]$Backend)

$exe = Join-Path $PSScriptRoot 'tailnet-proxy.exe'
if (-not (Test-Path -LiteralPath $exe)) {
    throw "Build the proxy first: $exe"
}
$dataDir = Join-Path $env:LOCALAPPDATA 'PicoPlantMonitor\tailnet-state'
New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
$logPath = Join-Path $dataDir 'proxy.log'
$arguments = '-backend "{0}" -state-dir "{1}" -log-file "{2}"' -f $Backend, $dataDir, $logPath
$action = New-ScheduledTaskAction -Execute $exe -Argument $arguments
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $identity
$principal = New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Seconds 0) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName 'PicoPlantMonitorTailnetProxy' -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
Start-ScheduledTask -TaskName 'PicoPlantMonitorTailnetProxy'
Write-Output 'PicoPlantMonitor tailnet proxy scheduled at Windows logon and started.'
