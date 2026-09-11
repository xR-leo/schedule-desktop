@echo off
chcp 65001 >nul
title Сборка Schedule.exe
color 0A

set "SCRIPT_DIR=%~dp0"
set "LOG=%SCRIPT_DIR%build_log.txt"
echo ============================================ > "%LOG%"
echo СТАРТ: %date% %time% >> "%LOG%"
echo ============================================ >> "%LOG%"

echo ============================================
echo    СБОРКА Schedule.exe
echo ============================================
echo.

cd /d "%SCRIPT_DIR%"

REM === 1. Python ===
echo [1/6] Проверка Python...
echo [1/6] Python >> "%LOG%"
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python найден
    python --version >> "%LOG%" 2>&1
    set "PYTHON_CMD=python"
    goto :pip_step
)
where py >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Найден py launcher
    set "PYTHON_CMD=py"
    goto :pip_step
)

echo [INFO] Python не найден. Скачиваю...
echo [INFO] Скачиваю Python >> "%LOG%"
powershell -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.1/python-3.13.1-amd64.exe' -OutFile '%SCRIPT_DIR%python_installer.exe'" >> "%LOG%" 2>&1

if not exist "%SCRIPT_DIR%python_installer.exe" (
    echo [ОШИБКА] Не удалось скачать Python
    echo [ОШИБКА] Скачивание не удалось >> "%LOG%"
    pause
    exit /b 1
)

echo [INFO] Устанавливаю Python...
echo [INFO] Установка >> "%LOG%"
start /wait "" "%SCRIPT_DIR%python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
del /f /q "%SCRIPT_DIR%python_installer.exe" >nul 2>&1

set "PATH=%LOCALAPPDATA%\Programs\Python\Python313;%LOCALAPPDATA%\Programs\Python\Python313\Scripts;%PATH%"
set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"

if not exist "%PYTHON_CMD%" (
    echo [ОШИБКА] Python не установился
    pause
    exit /b 1
)
echo [OK] Python установлен

:pip_step
echo.
echo [2/6] Обновление pip...
"%PYTHON_CMD%" -m pip install --upgrade pip --quiet --no-warn-script-location >> "%LOG%" 2>&1
echo [OK]
echo.

echo [3/6] Установка библиотек...
"%PYTHON_CMD%" -m pip install PyQt5 psutil pyinstaller --quiet --no-warn-script-location >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Не удалось установить библиотеки
    pause
    exit /b 1
)
echo [OK]
echo.

echo [4/6] Поиск overlay_empty.py...
if not exist "%SCRIPT_DIR%overlay_empty.py" (
    echo [ОШИБКА] Файл overlay_empty.py не найден!
    pause
    exit /b 1
)
echo [OK] overlay_empty.py найден
echo.

echo [5/6] Сборка .exe (1-3 минуты)...
"%PYTHON_CMD%" -m PyInstaller --onefile --windowed --name "Schedule" --clean overlay_empty.py >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Сборка не удалась
    pause
    exit /b 1
)
echo [OK] Сборка завершена
echo.

echo [6/6] Очистка...
if exist "%SCRIPT_DIR%build" rmdir /s /q "%SCRIPT_DIR%build" >nul 2>&1
if exist "%SCRIPT_DIR%Schedule.spec" del /f /q "%SCRIPT_DIR%Schedule.spec" >nul 2>&1
if exist "%SCRIPT_DIR%__pycache__" rmdir /s /q "%SCRIPT_DIR%__pycache__" >nul 2>&1
echo [OK] Мусор удалён
echo.

echo ============================================
echo    ГОТОВО!
echo ============================================
echo Файл: dist\Schedule.exe
echo.

if exist "%SCRIPT_DIR%dist" (
    explorer "%SCRIPT_DIR%dist"
)
pause
