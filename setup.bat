@echo off
TITLE DIY Racing Controller - Quick Setup
COLOR 0B

echo ========================================================
echo   DIY Racing Controller - Global Setup
echo ========================================================
echo.

:: Get the current folder path where the .exe and bat reside
set "CURRENT_DIR=%~dp0"
:: Remove trailing backslash
set "CURRENT_DIR=%CURRENT_DIR:~0,-1%"

echo [1/3] Registering application to Windows PATH...
echo This allows you to run the app from any command prompt!

:: Add directory to User PATH environment variable permanently without duplicates
powershell -Command "$userPath = [Environment]::GetEnvironmentVariable('Path', 'User'); if ($userPath -notlike '*%CURRENT_DIR%*') { [Environment]::SetEnvironmentVariable('Path', $userPath + ';%CURRENT_DIR%', 'User'); Write-Host 'Added successfully!' } else { Write-Host 'Already in PATH.' }"

echo.
echo [2/3] Creating a Desktop Shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\DIY Racing Controller.lnk'); $Shortcut.TargetPath = '%CURRENT_DIR%\DIY Racing Controller.exe'; $Shortcut.IconLocation = '%CURRENT_DIR%\DIY Racing Controller.exe,0'; $Shortcut.Save()"

echo.
echo ========================================================
echo   SETUP COMPLETE!
echo ========================================================
echo - A shortcut has been placed on your Desktop.
echo - You can now type 'DIY Racing Controller.exe' into any 
echo   Command Prompt or PowerShell window from anywhere!
echo ========================================================
pause