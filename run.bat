@echo off
echo 🔧 학생 실습 모니터링 시스템 시작 중...

REM Python 버전 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python이 설치되지 않았습니다.
    echo Python 3.8 이상을 설치해주세요.
    pause
    exit /b 1
)

REM 가상 환경 확인 및 생성
if exist "venv\Scripts\activate.bat" (
    echo 🔧 가상 환경을 활성화합니다...
    call venv\Scripts\activate.bat
) else (
    echo 📦 가상 환경을 생성합니다...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ❌ 가상 환경 생성에 실패했습니다.
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
)

REM 의존성 설치
echo 📦 의존성을 설치합니다...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ 의존성 설치에 실패했습니다.
    pause
    exit /b 1
)

REM 로그 디렉터리 생성
if not exist "logs" mkdir logs

REM 부트스트랩 실행 확인
if not exist "students" (
    echo 🚀 부트스트랩을 실행합니다...
    python bootstrap.py
    if %errorlevel% neq 0 (
        echo ❌ 부트스트랩 실행에 실패했습니다.
        pause
        exit /b 1
    )
)

echo.
echo ✅ 시스템을 시작합니다...
echo.

REM PID 파일 정리
if exist "scheduler.pid" del scheduler.pid
if exist "frontend.pid" del frontend.pid

REM 백엔드 스케줄러 시작
echo 📊 백엔드 스케줄러를 시작합니다...
start "Scheduler" /min python -m backend.scheduler

REM 잠시 대기
timeout /t 3 /nobreak >nul

REM 프론트엔드 서버 시작
echo 🌐 웹 서버를 시작합니다...
echo.
echo 📱 대시보드: http://localhost:8000
echo 🔧 종료하려면 Ctrl+C를 누르세요
echo.

uvicorn frontend.main:app --host 0.0.0.0 --port 8000

echo.
echo 👋 시스템이 종료되었습니다.
pause