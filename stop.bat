@echo off
echo 🛑 학생 실습 모니터링 시스템 종료 중...

REM Python 프로세스 종료
echo 🔍 실행 중인 프로세스를 찾는 중...

REM uvicorn 프로세스 종료
for /f "tokens=2" %%i in ('tasklist ^| findstr "python" ^| findstr "uvicorn"') do (
    echo 🌐 웹 서버 종료 중... (PID: %%i)
    taskkill /PID %%i /F >nul 2>&1
)

REM scheduler 프로세스 종료
for /f "tokens=2" %%i in ('tasklist ^| findstr "python" ^| findstr "scheduler"') do (
    echo 📊 스케줄러 종료 중... (PID: %%i)
    taskkill /PID %%i /F >nul 2>&1
)

REM 일반적인 python 프로세스 중 관련된 것들 종료
wmic process where "name='python.exe' and commandline like '%%backend.scheduler%%'" delete >nul 2>&1
wmic process where "name='python.exe' and commandline like '%%frontend.main%%'" delete >nul 2>&1

REM PID 파일 정리
if exist "scheduler.pid" del scheduler.pid
if exist "frontend.pid" del frontend.pid

echo ✅ 모든 프로세스가 종료되었습니다.
pause