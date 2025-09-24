#!/bin/bash

echo "🔧 학생 실습 모니터링 시스템 시작 중..."

# Python 버전 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3이 설치되지 않았습니다."
    echo "Python 3.8 이상을 설치해주세요."
    exit 1
fi

echo "✅ Python 버전: $(python3 --version)"

# 가상 환경 확인 및 활성화
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    echo "🔧 가상 환경을 활성화합니다..."
    source venv/bin/activate
else
    echo "📦 가상 환경을 생성합니다..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ 가상 환경 생성에 실패했습니다."
        exit 1
    fi
    source venv/bin/activate
fi

# 의존성 설치
echo "📦 의존성을 설치합니다..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ 의존성 설치에 실패했습니다."
    exit 1
fi

# 로그 디렉터리 생성
mkdir -p logs

# 부트스트랩 실행 확인
if [ ! -d "students" ]; then
    echo "🚀 부트스트랩을 실행합니다..."
    python bootstrap.py
    if [ $? -ne 0 ]; then
        echo "❌ 부트스트랩 실행에 실패했습니다."
        exit 1
    fi
fi

echo ""
echo "✅ 시스템을 시작합니다..."
echo ""

# PID 파일 정리
rm -f scheduler.pid frontend.pid

# 백엔드 스케줄러 시작
echo "📊 백엔드 스케줄러를 시작합니다..."
python -m backend.scheduler &
SCHEDULER_PID=$!
echo $SCHEDULER_PID > scheduler.pid

# 잠시 대기
sleep 3

# 프론트엔드 서버 시작
echo "🌐 웹 서버를 시작합니다..."
echo ""
echo "📱 대시보드: http://localhost:8000"
echo "🔧 종료하려면 Ctrl+C를 누르세요"
echo ""

uvicorn frontend.main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!
echo $SERVER_PID > frontend.pid

# 종료 시그널 처리
cleanup() {
    echo ""
    echo "🛑 시스템을 종료합니다..."

    if [ -f "scheduler.pid" ]; then
        SCHEDULER_PID=$(cat scheduler.pid)
        kill $SCHEDULER_PID 2>/dev/null
        rm -f scheduler.pid
    fi

    if [ -f "frontend.pid" ]; then
        SERVER_PID=$(cat frontend.pid)
        kill $SERVER_PID 2>/dev/null
        rm -f frontend.pid
    fi

    echo "👋 시스템이 종료되었습니다."
    exit 0
}

# 시그널 핸들러 등록
trap cleanup SIGINT SIGTERM

# 백그라운드 프로세스 대기
wait