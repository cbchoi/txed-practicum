@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 학생 실습 모니터링 시스템 종료 스크립트 (Windows)

echo ========================================
echo 학생 실습 모니터링 시스템 종료
echo ========================================

REM PID 파일에서 프로세스 종료
call :terminate_process "frontend.pid" "프론트엔드"
call :terminate_process "scheduler.pid" "스케줄러"

REM 프로세스명 기반 종료 (PID 파일이 없는 경우 대비)
call :terminate_by_name "backend.scheduler" "백엔드 스케줄러"
call :terminate_by_name "frontend.main" "프론트엔드 서버"

REM 포트 기반 종료 (8000번 포트 사용 프로세스)
echo 🔍 포트 8000을 사용하는 프로세스를 확인합니다...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000"') do (
    set pid=%%a
    if not "!pid!"=="" (
        echo 🛑 포트 8000을 사용하는 프로세스를 종료합니다: !pid!
        taskkill /f /pid !pid! >nul 2>&1
    )
)

REM 임시 파일 정리
echo 🧹 임시 파일을 정리합니다...
if exist "*.pid" del *.pid >nul 2>&1

REM 최종 확인
echo.
echo 🔍 종료 후 상태 확인:

REM 관련 프로세스가 남아있는지 확인
set remaining=0
for /f %%a in ('tasklist /fi "imagename eq python.exe" /fo csv ^| findstr "backend.scheduler\|frontend.main" 2^>nul') do set remaining=1

if !remaining!==1 (
    echo ⚠️  아직 실행 중인 관련 프로세스가 있습니다.
    tasklist /fi "imagename eq python.exe" | findstr "backend.scheduler\|frontend.main"
) else (
    echo ✅ 모든 관련 프로세스가 종료되었습니다.
)

REM 포트 사용 확인
netstat -aon | findstr ":8000" >nul 2>&1
if errorlevel 1 (
    echo ✅ 포트 8000이 해제되었습니다.
) else (
    echo ⚠️  포트 8000이 아직 사용 중입니다:
    netstat -aon | findstr ":8000"
)

echo.
echo ✅ 학생 실습 모니터링 시스템이 종료되었습니다.
echo.
echo 📁 로그 파일은 logs\ 디렉터리에서 확인할 수 있습니다:
echo    - logs\scheduler.log
echo    - logs\frontend.log
echo.
echo 🔄 시스템을 다시 시작하려면: run.bat

goto :eof

REM 함수: PID 파일 기반 프로세스 종료
:terminate_process
set pid_file=%~1
set process_name=%~2

if exist %pid_file% (
    set /p process_type=<%pid_file%

    echo 🛑 %process_name% 프로세스를 종료합니다...

    REM Python 프로세스 중에서 해당하는 것들을 찾아서 종료
    for /f "tokens=2" %%a in ('tasklist /fi "imagename eq python.exe" /fo csv ^| findstr "!process_type!" 2^>nul') do (
        set pid=%%a
        echo    프로세스 종료: !pid!
        taskkill /f /pid !pid! >nul 2>&1
    )

    REM PID 파일 삭제
    del %pid_file% >nul 2>&1
    echo    ✓ %process_name% 프로세스가 종료되었습니다.
) else (
    echo 📄 %process_name% PID 파일이 없습니다.
)
goto :eof

REM 함수: 프로세스명 기반 종료
:terminate_by_name
set pattern=%~1
set description=%~2

echo 🔍 %description% 프로세스를 확인합니다...
for /f "tokens=2" %%a in ('tasklist /fi "imagename eq python.exe" /fo csv ^| findstr "%pattern%" 2^>nul') do (
    set pid=%%a
    echo    🛑 프로세스 종료: !pid!
    taskkill /f /pid !pid! >nul 2>&1
)
goto :eof