#!/bin/bash

# 학생 실습 모니터링 시스템 종료 스크립트

set -e  # 오류 발생 시 스크립트 종료

echo "========================================"
echo "학생 실습 모니터링 시스템 종료"
echo "========================================"

# PID 파일에서 프로세스 종료
terminate_process() {
    local pid_file=$1
    local process_name=$2

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")

        if kill -0 "$pid" 2>/dev/null; then
            echo "🛑 $process_name 프로세스를 종료합니다... (PID: $pid)"
            kill "$pid"

            # 프로세스가 종료될 때까지 최대 10초 대기
            for i in {1..10}; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    echo "   ✓ $process_name 프로세스가 정상적으로 종료되었습니다."
                    break
                fi
                sleep 1
            done

            # 여전히 실행 중이면 강제 종료
            if kill -0 "$pid" 2>/dev/null; then
                echo "   ⚠️  $process_name 프로세스를 강제 종료합니다..."
                kill -9 "$pid" 2>/dev/null || true
            fi
        else
            echo "⚠️  $process_name 프로세스가 이미 종료되어 있습니다. (PID: $pid)"
        fi

        # PID 파일 삭제
        rm -f "$pid_file"
    else
        echo "📄 $process_name PID 파일이 없습니다."
    fi
}

# 실행 중인 모든 관련 프로세스 찾기 및 종료
terminate_by_name() {
    local pattern=$1
    local description=$2

    local pids=$(pgrep -f "$pattern" 2>/dev/null || true)

    if [ -n "$pids" ]; then
        echo "🔍 $description 프로세스를 찾았습니다: $pids"
        for pid in $pids; do
            if kill -0 "$pid" 2>/dev/null; then
                echo "   🛑 프로세스 종료: $pid"
                kill "$pid" 2>/dev/null || true
            fi
        done

        # 잠시 대기 후 강제 종료
        sleep 2
        for pid in $pids; do
            if kill -0 "$pid" 2>/dev/null; then
                echo "   ⚠️  프로세스 강제 종료: $pid"
                kill -9 "$pid" 2>/dev/null || true
            fi
        done
    fi
}

# 1. PID 파일 기반 종료
terminate_process "frontend.pid" "프론트엔드"
terminate_process "scheduler.pid" "스케줄러"

# 2. 프로세스명 기반 종료 (PID 파일이 없는 경우 대비)
terminate_by_name "backend.scheduler" "백엔드 스케줄러"
terminate_by_name "frontend.main" "프론트엔드 서버"
terminate_by_name "uvicorn.*frontend" "Uvicorn 프론트엔드"

# 3. 포트 기반 종료 (8000번 포트 사용 프로세스)
echo "🔍 포트 8000을 사용하는 프로세스를 확인합니다..."
port_pids=$(lsof -ti:8000 2>/dev/null || true)

if [ -n "$port_pids" ]; then
    echo "🛑 포트 8000을 사용하는 프로세스를 종료합니다: $port_pids"
    for pid in $port_pids; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done

    # 잠시 대기 후 강제 종료
    sleep 2
    for pid in $port_pids; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "   ⚠️  포트 프로세스 강제 종료: $pid"
            kill -9 "$pid" 2>/dev/null || true
        fi
    done
fi

# 4. 임시 파일 정리
echo "🧹 임시 파일을 정리합니다..."
rm -f *.pid 2>/dev/null || true

# 5. 최종 확인
echo ""
echo "🔍 종료 후 상태 확인:"

# 관련 프로세스가 남아있는지 확인
remaining_processes=$(pgrep -f "backend.scheduler|frontend.main|uvicorn.*frontend" 2>/dev/null || true)
if [ -n "$remaining_processes" ]; then
    echo "⚠️  아직 실행 중인 관련 프로세스가 있습니다:"
    ps -p $remaining_processes -o pid,ppid,cmd 2>/dev/null || true
else
    echo "✅ 모든 관련 프로세스가 종료되었습니다."
fi

# 포트 사용 확인
port_check=$(lsof -ti:8000 2>/dev/null || true)
if [ -n "$port_check" ]; then
    echo "⚠️  포트 8000이 아직 사용 중입니다:"
    lsof -i:8000 2>/dev/null || true
else
    echo "✅ 포트 8000이 해제되었습니다."
fi

echo ""
echo "✅ 학생 실습 모니터링 시스템이 종료되었습니다."
echo ""
echo "📁 로그 파일은 logs/ 디렉터리에서 확인할 수 있습니다:"
echo "   - logs/scheduler.log"
echo "   - logs/frontend.log"
echo ""
echo "🔄 시스템을 다시 시작하려면: ./run.sh"