@echo off
setlocal EnableDelayedExpansion

:: Check for admin rights
>nul 2>&1 openfiles
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Set Python command
where python >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
        set "PYTHON_CMD=%LocalAppData%\Programs\Python\Python312\python.exe"
    ) else (
        powershell -Command "Invoke-WebRequest https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe -OutFile python_installer.exe"
        start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
        del python_installer.exe
        set "PYTHON_CMD=python"
    )
) else (
    set "PYTHON_CMD=python"
)

:: Install required modules
"%PYTHON_CMD%" -m pip install --upgrade pip
"%PYTHON_CMD%" -m pip install pywin32 pywinauto psutil

:: Run the Python script (already in admin context)
"%PYTHON_CMD%" "%~dp0wrobot_auto_trial.py"
