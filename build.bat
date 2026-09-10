@echo off
chcp 65001 >nul
title Сборка Schedule.exe
color 0A

REM === Логирование ===
set "SCRIPT_DIR=%~dp0"
set "LOG=%SCRIPT_DIR%build_log.txt"
echo ============================================ > "%LOG%"
echo СТАРТ: %date% %time% >> "%LOG%"
echo ============================================ >> "%LOG%"

echo ============================================
echo    АВТОСБОРКА Schedule.exe
echo ============================================
echo.

cd /d "%SCRIPT_DIR%"
echo [LOG] Папка: %SCRIPT_DIR% >> "%LOG%"

REM === Шаг 1: Python ===
echo [1/6] Проверка Python...
echo [1/6] Проверка Python >> "%LOG%"

where python >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python уже установлен
    echo [OK] Python найден >> "%LOG%"
    python --version >> "%LOG%" 2>&1
    set "PYTHON_CMD=python"
    goto :pip_step
)

echo [INFO] Python не найден через "where"
echo [INFO] Python не найден >> "%LOG%"

REM Проверяем через py launcher
where py >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Найден py launcher
    echo [OK] py launcher найден >> "%LOG%"
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
echo [INFO] Установка Python >> "%LOG%"
start /wait "" "%SCRIPT_DIR%python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
echo [INFO] Установка завершена >> "%LOG%"

del /f /q "%SCRIPT_DIR%python_installer.exe" >nul 2>&1
echo [INFO] Установщик удалён >> "%LOG%"

set "PATH=%LOCALAPPDATA%\Programs\Python\Python313;%LOCALAPPDATA%\Programs\Python\Python313\Scripts;%PATH%"
set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"

if not exist "%PYTHON_CMD%" (
    echo [ОШИБКА] Python не установился
    echo [ОШИБКА] Python не найден после установки >> "%LOG%"
    pause
    exit /b 1
)
echo [OK] Python установлен
echo [OK] Python установлен >> "%LOG%"

:pip_step
echo.
echo [2/6] Обновление pip...
echo [2/6] Обновление pip >> "%LOG%"
"%PYTHON_CMD%" -m pip install --upgrade pip --quiet --no-warn-script-location >> "%LOG%" 2>&1
echo [OK]
echo [OK] pip обновлён >> "%LOG%"
echo.

echo [3/6] Установка библиотек...
echo [3/6] Установка PyQt5, psutil, pyinstaller >> "%LOG%"
"%PYTHON_CMD%" -m pip install PyQt5 psutil pyinstaller --quiet --no-warn-script-location >> "%LOG%" 2>&1

if errorlevel 1 (
    echo [ОШИБКА] Не удалось установить библиотеки
    echo [ОШИБКА] Установка библиотек не удалась >> "%LOG%"
    pause
    exit /b 1
)
echo [OK]
echo [OK] Библиотеки установлены >> "%LOG%"
echo.

echo [4/6] Поиск overlay.py...
echo [4/6] Поиск overlay.py >> "%LOG%"
if not exist "%SCRIPT_DIR%overlay.py" (
    echo [ОШИБКА] Файл overlay.py не найден!
    echo [ОШИБКА] overlay.py не найден >> "%LOG%"
    pause
    exit /b 1
)
echo [OK] overlay.py найден
echo [OK] overlay.py найден >> "%LOG%"
echo.

echo [5/6] Сборка .exe (1-3 минуты)...
echo [5/6] Сборка .exe >> "%LOG%"
"%PYTHON_CMD%" -m PyInstaller --onefile --windowed --name "Schedule" --clean overlay.py >> "%LOG%" 2>&1

if errorlevel 1 (
    echo [ОШИБКА] Сборка не удалась
    echo [ОШИБКА] Сборка не удалась >> "%LOG%"
    pause
    exit /b 1
)
echo [OK] Сборка завершена
echo [OK] Сборка завершена >> "%LOG%"
echo.

echo [6/6] Очистка...
echo [6/6] Очистка >> "%LOG%"
if exist "%SCRIPT_DIR%build" rmdir /s /q "%SCRIPT_DIR%build" >nul 2>&1
if exist "%SCRIPT_DIR%Schedule.spec" del /f /q "%SCRIPT_DIR%Schedule.spec" >nul 2>&1
if exist "%SCRIPT_DIR%__pycache__" rmdir /s /q "%SCRIPT_DIR%__pycache__" >nul 2>&1
echo [OK] Мусор удалён
echo [OK] Мусор удалён >> "%LOG%"
echo.

echo ============================================
echo    ГОТОВО!
echo ============================================
echo Файл: dist\Schedule.exe
echo.
echo ГОТОВО >> "%LOG%"
echo КОНЕЦ: %date% %time% >> "%LOG%"

if exist "%SCRIPT_DIR%dist" (
    explorer "%SCRIPT_DIR%dist"
)

pause
