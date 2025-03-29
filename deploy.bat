@echo off
echo Iniciando deploy com PowerShell...
powershell.exe -NoExit -ExecutionPolicy Bypass -File "%~dp0deploy_git.ps1"
pause


