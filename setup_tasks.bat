@echo off
setlocal
set "TASK_DIR=c:\Users\nagas\.gemini\antigravity\Hiro\crowd_agent"
set "BAT_PATH=%TASK_DIR%\run_crowd_agent.bat"

echo [*] クラウドエージェントの定期タスクを登録しています...

:: 既存のタスクを削除 (上書きするため)
schtasks /delete /tn "CrowdAgent_Morning" /f >nul 2>&1
schtasks /delete /tn "CrowdAgent_Midday" /f >nul 2>&1
schtasks /delete /tn "CrowdAgent_Evening" /f >nul 2>&1

:: 朝のタスク (09:00)
schtasks /create /tn "CrowdAgent_Morning" /tr "\"%BAT_PATH%\"" /sc daily /st 09:00 /f
if %ERRORLEVEL% EQU 0 (echo [+] 朝のタスク(09:00)を登録しました。) else (echo [!] 朝のタスク登録に失敗しました。)

:: 昼のタスク (15:00)
schtasks /create /tn "CrowdAgent_Midday" /tr "\"%BAT_PATH%\"" /sc daily /st 15:00 /f
if %ERRORLEVEL% EQU 0 (echo [+] 昼のタスク(15:00)を登録しました。) else (echo [!] 昼のタスク登録に失敗しました。)

:: 夜のタスク (20:00)
schtasks /create /tn "CrowdAgent_Evening" /tr "\"%BAT_PATH%\"" /sc daily /st 20:00 /f
if %ERRORLEVEL% EQU 0 (echo [+] 夜のタスク(20:00)を登録しました。) else (echo [!] 夜의タスク登録に失敗しました。)

echo.
echo [*] 登録が完了しました。タスクの一覧を表示します。
schtasks /query /v /fo list /tn "CrowdAgent_*"

pause
