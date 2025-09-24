#!/bin/bash

echo "🛑 학생 실습 모니터링 시스템 종료 중..."

# PID 파일에서 프로세스 종료
if [ -f "scheduler.pid" ]; then
    SCHEDULER_PID=$(cat scheduler.pid)
    echo "📊 스케줄러 종료 중... (PID: $SCHEDULER_PID)"
    kill $SCHEDULER_PID 2>/dev/null
    rm -f scheduler.pid
fi

if [ -f "frontend.pid" ]; then
    SERVER_PID=$(cat frontend.pid)
    echo "🌐 웹 서버 종료 중... (PID: $SERVER_PID)"
    kill $SERVER_PID 2>/dev/null
    rm -f frontend.pid
fi

# 남아있는 프로세스 찾아서 종료
echo "🔍 남아있는 프로세스를 찾는 중..."

# uvicorn 프로세스 종료
pkill -f "uvicorn.*frontend.main" 2>/dev/null

# scheduler 프로세스 종료
pkill -f "backend.scheduler" 2>/dev/null

# 잠시 대기 후 강제 종료
sleep 2

pkill -9 -f "uvicorn.*frontend.main" 2>/dev/null
pkill -9 -f "backend.scheduler" 2>/dev/null

echo "✅ 모든 프로세스가 종료되었습니다."