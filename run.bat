@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 학생 실습 모니터링 시스템 실행 스크립트 (Windows)

echo ========================================
echo 학생 실습 모니터링 시스템
echo ========================================

REM Python 버전 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았습니다.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✓ Python 확인됨: !PYTHON_VERSION!

REM 가상 환경 설정 (선택적)
if exist "venv\Scripts\activate.bat" (
    echo 🔧 가상 환경을 활성화합니다...
    call venv\Scripts\activate.bat
    echo 📚 의존성을 설치합니다...
    pip install -q -r requirements.txt
) else (
    echo ⚠️  가상환경이 없습니다. 시스템 Python을 사용합니다...
    echo 📚 필요한 패키지 확인 중...
)

REM 로그 디렉터리 생성
if not exist "logs" mkdir logs

REM process_list.csv 확인 및 생성
if not exist "process_list.csv" (
    if not exist "roster.csv" (
        echo ❌ roster.csv 파일이 없습니다.
        echo    roster.csv 파일을 생성한 후 다시 실행하세요.
        pause
        exit /b 1
    )

    echo 📋 process_list.csv를 생성합니다...
    set /p TEMPLATE=GitHub 저장소 템플릿을 입력하세요 (예: https://github.com/HBNU-COME2201/software-design-practicum-{git_id}):

    if "!TEMPLATE!"=="" (
        echo ❌ 템플릿이 입력되지 않았습니다.
        pause
        exit /b 1
    )

    python generate_process_list.py --roster roster.csv --template "!TEMPLATE!" --output process_list.csv
)

REM 부트스트랩 실행 여부 확인
if not exist "students" (
    echo 🏗️  학생 디렉터리를 초기화합니다...
    python bootstrap.py
) else (
    dir /b students 2>nul | findstr . >nul
    if errorlevel 1 (
        echo 🏗️  학생 디렉터리를 초기화합니다...
        python bootstrap.py
    ) else (
        echo ✓ 학생 디렉터리가 이미 존재합니다.
    )
)

REM 이전 PID 파일 정리
if exist "scheduler.pid" del scheduler.pid
if exist "frontend.pid" del frontend.pid

REM 백엔드 스케줄러 시작
echo ⚙️  백엔드 스케줄러를 시작합니다...
start /b python -m backend.scheduler > logs\scheduler.log 2>&1

REM 스케줄러 PID 저장 (Windows에서는 프로세스 이름으로 관리)
echo scheduler > scheduler.pid
echo    스케줄러 시작됨

REM 스케줄러가 정상 시작될 때까지 잠시 대기
timeout /t 3 /nobreak >nul

REM 설정에서 포트 읽기
set PORT=8000
if exist "config.backend.yaml" (
    for /f "tokens=*" %%i in ('python -c "import yaml; print(yaml.safe_load(open('config.backend.yaml'))['server']['port'])" 2^>nul') do set PORT=%%i
)

REM 프론트엔드 서버 시작
echo 🌐 프론트엔드 서버를 시작합니다...
start /b python frontend\main.py > logs\frontend.log 2>&1

REM 프론트엔드 PID 저장
echo frontend > frontend.pid
echo    프론트엔드 시작됨 (Port: !PORT!)

REM 프론트엔드가 정상 시작될 때까지 잠시 대기
timeout /t 3 /nobreak >nul

echo.
echo 🎉 시스템이 성공적으로 시작되었습니다!
echo.
echo 📊 대시보드: http://localhost:!PORT!
echo 📋 API 상태: http://localhost:!PORT!/api/status
echo 💚 헬스체크: http://localhost:!PORT!/health
echo.
echo 📁 로그 파일:
echo    - 스케줄러: logs\scheduler.log
echo    - 프론트엔드: logs\frontend.log
echo    - 부트스트랩: logs\bootstrap.log
echo.
echo 🛑 종료하려면 stop.bat을 실행하거나 Ctrl+C를 누르세요
echo.

REM 사용자 입력 대기 (선택사항)
echo 종료하려면 아무 키나 누르세요...
pause >nul

REM 종료 시 정리
call stop.bat