# register_tasks.ps1
$taskDir = "c:\Users\nagas\.gemini\antigravity\Hiro\crowd_agent"
$batPath = Join-Path $taskDir "run_crowd_agent.bat"

$tasks = @(
    @{ Name = "CrowdAgent_Morning"; Time = "10:00" },
    @{ Name = "CrowdAgent_Midday"; Time = "15:00" },
    @{ Name = "CrowdAgent_Evening"; Time = "17:00" }
)

Write-Host "Registering tasks..."

foreach ($task in $tasks) {
    $name = $task.Name
    $time = $task.Time
    
    # Delete existing
    schtasks /delete /tn $name /f 2>$null
    
    # Create new
    # Using schtasks directly
    $arg = "/create /tn `"$name`" /tr `"`"$batPath`"`" /sc daily /st $time /f"
    Start-Process schtasks -ArgumentList $arg -Wait
    
    Write-Host "Task $name ($time) registered."
}

Write-Host "Current status:"
schtasks /query /v /fo list /tn "CrowdAgent_*"
