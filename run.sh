#!/bin/bash

# 학생 실습 모니터링 시스템 실행 스크립트

set -e  # 오류 발생 시 스크립트 종료

echo "========================================"
echo "학생 실습 모니터링 시스템"
echo "========================================"

# Python 버전 확인 (크로스 플랫폼)
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    if command -v python &> /dev/null; then
        PYTHON_CMD="python"
        echo "✓ Python 확인됨: $(python --version)"
    else
        echo "❌ Python이 설치되지 않았습니다."
        exit 1
    fi
else
    echo "✓ Python 3 확인됨: $(python3 --version)"
fi

# 가상 환경 설정 (선택적, 크로스 플랫폼)
if [ -d "venv" ]; then
    if [ -f "venv/bin/activate" ]; then
        # Unix/Linux/macOS
        echo "🔧 가상 환경을 활성화합니다..."
        source venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        # Windows (Git Bash)
        echo "🔧 가상 환경을 활성화합니다..."
        source venv/Scripts/activate
    fi
    # 의존성 설치
    echo "📚 의존성을 설치합니다..."
    pip install -q -r requirements.txt
else
    echo "⚠️  가상환경이 없습니다. 시스템 Python을 사용합니다..."
    # 시스템 Python으로 의존성 확인
    echo "📚 필요한 패키지 확인 중..."
fi

# 로그 디렉터리 생성
mkdir -p logs

# process_list.csv 확인 및 생성
if [ ! -f "process_list.csv" ]; then
    if [ ! -f "roster.csv" ]; then
        echo "❌ roster.csv 파일이 없습니다."
        echo "   roster.csv 파일을 생성한 후 다시 실행하세요."
        exit 1
    fi

    echo "📋 process_list.csv를 생성합니다..."
    read -p "GitHub 저장소 템플릿을 입력하세요 (예: https://github.com/HBNU-COME2201/software-design-practicum-{git_id}): " TEMPLATE

    if [ -z "$TEMPLATE" ]; then
        echo "❌ 템플릿이 입력되지 않았습니다."
        exit 1
    fi

    $PYTHON_CMD generate_process_list.py --roster roster.csv --template "$TEMPLATE" --output process_list.csv
fi

# 부트스트랩 실행 여부 확인
if [ ! -d "students" ] || [ -z "$(ls -A students 2>/dev/null)" ]; then
    echo "🏗️  학생 디렉터리를 초기화합니다..."
    $PYTHON_CMD bootstrap.py
else
    echo "✓ 학생 디렉터리가 이미 존재합니다."
fi

# PID 파일 정리 함수
cleanup() {
    echo ""
    echo "🛑 시스템을 종료합니다..."

    if [ -f "scheduler.pid" ]; then
        SCHEDULER_PID=$(cat scheduler.pid)
        if kill -0 $SCHEDULER_PID 2>/dev/null; then
            kill $SCHEDULER_PID
            echo "   스케줄러 프로세스 종료됨 (PID: $SCHEDULER_PID)"
        fi
        rm -f scheduler.pid
    fi

    if [ -f "frontend.pid" ]; then
        FRONTEND_PID=$(cat frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            echo "   프론트엔드 프로세스 종료됨 (PID: $FRONTEND_PID)"
        fi
        rm -f frontend.pid
    fi

    echo "✓ 시스템이 정상적으로 종료되었습니다."
    exit 0
}

# 신호 처리 설정
trap cleanup SIGINT SIGTERM

# 백엔드 스케줄러 시작
echo "⚙️  백엔드 스케줄러를 시작합니다..."
$PYTHON_CMD -m backend.scheduler > logs/scheduler.log 2>&1 &
SCHEDULER_PID=$!
echo $SCHEDULER_PID > scheduler.pid
echo "   스케줄러 시작됨 (PID: $SCHEDULER_PID)"

# 스케줄러가 정상 시작될 때까지 잠시 대기
sleep 3

# 스케줄러 프로세스 확인
if ! kill -0 $SCHEDULER_PID 2>/dev/null; then
    echo "❌ 스케줄러 시작에 실패했습니다. 로그를 확인하세요:"
    tail -n 20 logs/scheduler.log
    exit 1
fi

# 프론트엔드 서버 시작
echo "🌐 프론트엔드 서버를 시작합니다..."

# 설정에서 포트 읽기
PORT=8000
if [ -f "config.backend.yaml" ]; then
    PORT=$($PYTHON_CMD -c "import yaml; print(yaml.safe_load(open('config.backend.yaml'))['server']['port'])" 2>/dev/null || echo "8000")
fi

$PYTHON_CMD frontend/main.py > logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > frontend.pid
echo "   프론트엔드 시작됨 (PID: $FRONTEND_PID, Port: $PORT)"

# 프론트엔드가 정상 시작될 때까지 잠시 대기
sleep 3

# 프론트엔드 프로세스 확인
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "❌ 프론트엔드 시작에 실패했습니다. 로그를 확인하세요:"
    tail -n 20 logs/frontend.log
    cleanup
    exit 1
fi

echo ""
echo "🎉 시스템이 성공적으로 시작되었습니다!"
echo ""
echo "📊 대시보드: http://localhost:$PORT"
echo "📋 API 상태: http://localhost:$PORT/api/status"
echo "💚 헬스체크: http://localhost:$PORT/health"
echo ""
echo "📁 로그 파일:"
echo "   - 스케줄러: logs/scheduler.log"
echo "   - 프론트엔드: logs/frontend.log"
echo "   - 부트스트랩: logs/bootstrap.log"
echo ""
echo "🛑 종료하려면 Ctrl+C를 누르세요"
echo ""

# 프로세스 모니터링
while true; do
    # 스케줄러 프로세스 확인
    if ! kill -0 $SCHEDULER_PID 2>/dev/null; then
        echo "❌ 스케줄러 프로세스가 종료되었습니다."
        cleanup
        exit 1
    fi

    # 프론트엔드 프로세스 확인
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "❌ 프론트엔드 프로세스가 종료되었습니다."
        cleanup
        exit 1
    fi

    sleep 5
done