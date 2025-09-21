"""
학생 실습 모니터링 시스템 프론트엔드
FastAPI 기반 웹 애플리케이션
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# 백엔드 모듈 import
import sys
sys.path.append(str(Path(__file__).parent.parent))

from backend.scheduler import get_scheduler

# FastAPI 앱 생성
app = FastAPI(
    title="학생 실습 모니터링 시스템",
    description="학생 GitHub 저장소를 실시간 모니터링하고 채점 결과를 표시",
    version="1.0.0"
)

# 템플릿 설정
templates = Jinja2Templates(directory="frontend/templates")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 초기화"""
    logger.info("Starting frontend application...")

    # 로그 디렉터리 생성
    Path("logs").mkdir(exist_ok=True)

    # 스케줄러 초기화 (백그라운드에서 실행하지 않음 - 별도 프로세스에서 실행)
    scheduler = get_scheduler()
    await scheduler.initialize_student_states()

    logger.info("Frontend application started")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 정리"""
    logger.info("Shutting down frontend application...")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, week: int = None):
    """
    메인 대시보드 페이지

    Args:
        request (Request): HTTP 요청 객체
        week (int, optional): 조회할 주차. None이면 현재 주차 사용

    Returns:
        HTMLResponse: 대시보드 HTML 페이지
    """
    try:
        # 현재 학생 상태 가져오기
        scheduler = get_scheduler()

        # 주차 변경 요청이 있는 경우
        if week is not None:
            try:
                scheduler.set_current_week(week)
            except ValueError as e:
                logger.warning(f"Invalid week requested: {e}")

        student_states = scheduler.get_current_states()
        current_week = scheduler.get_current_week()
        available_weeks = scheduler.get_available_weeks()

        # 템플릿에 전달할 데이터 준비
        template_data = {
            "request": request,
            "students": student_states,
            "total_students": len(student_states),
            "passed_students": sum(1 for state in student_states.values() if state['status'] == 'pass'),
            "failed_students": sum(1 for state in student_states.values() if state['status'] == 'fail'),
            "current_week": current_week,
            "available_weeks": available_weeks,
            "last_update": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        return templates.TemplateResponse("dashboard.html", template_data)

    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        return HTMLResponse(
            content=f"<h1>Error</h1><p>Failed to load dashboard: {str(e)}</p>",
            status_code=500
        )

@app.get("/api/status")
async def get_status() -> Dict[str, Any]:
    """
    모든 학생의 현재 상태 API

    Returns:
        Dict[str, Any]: 학생별 상태 정보
    """
    try:
        scheduler = get_scheduler()
        return scheduler.get_current_states()

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return {"error": str(e)}

@app.get("/api/student/{student_id}")
async def get_student_status(student_id: str) -> Dict[str, Any]:
    """
    특정 학생의 상태 조회

    Args:
        student_id (str): 학생 ID

    Returns:
        Dict[str, Any]: 학생 상태 정보
    """
    try:
        scheduler = get_scheduler()
        student_states = scheduler.get_current_states()

        if student_id in student_states:
            return {
                "student_id": student_id,
                **student_states[student_id]
            }
        else:
            return {
                "error": f"Student {student_id} not found",
                "student_id": student_id
            }

    except Exception as e:
        logger.error(f"Error getting student status: {e}")
        return {"error": str(e)}

@app.post("/api/week/{week}")
async def set_week(week: int) -> Dict[str, Any]:
    """
    현재 주차 설정

    Args:
        week (int): 설정할 주차

    Returns:
        Dict[str, Any]: 설정 결과
    """
    try:
        scheduler = get_scheduler()
        scheduler.set_current_week(week)

        return {
            "success": True,
            "current_week": week,
            "message": f"Week changed to {week}"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error setting week: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/weeks")
async def get_weeks() -> Dict[str, Any]:
    """
    사용 가능한 주차 목록 및 현재 주차 조회

    Returns:
        Dict[str, Any]: 주차 정보
    """
    try:
        scheduler = get_scheduler()

        return {
            "current_week": scheduler.get_current_week(),
            "available_weeks": scheduler.get_available_weeks()
        }

    except Exception as e:
        logger.error(f"Error getting weeks: {e}")
        return {"error": str(e)}

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    헬스 체크 엔드포인트

    Returns:
        Dict[str, Any]: 시스템 상태 정보
    """
    try:
        scheduler = get_scheduler()
        student_states = scheduler.get_current_states()

        return {
            "status": "healthy",
            "timestamp": time.time(),
            "students_count": len(student_states),
            "scheduler_running": scheduler.running if hasattr(scheduler, 'running') else False
        }

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "error": str(e)
        }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    실시간 업데이트를 위한 웹소켓 엔드포인트

    Args:
        websocket (WebSocket): 웹소켓 연결
    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    scheduler = get_scheduler()
    scheduler.add_websocket_connection(websocket)

    try:
        # 초기 데이터 전송
        initial_data = scheduler.get_current_states()
        await websocket.send_text(json.dumps(initial_data))

        # 연결 유지 (클라이언트로부터 ping 메시지 대기)
        while True:
            try:
                message = await websocket.receive_text()

                # ping 메시지에 대한 pong 응답
                if message == "ping":
                    await websocket.send_text("pong")

            except WebSocketDisconnect:
                break

    except Exception as e:
        logger.error(f"WebSocket error: {e}")

    finally:
        scheduler.remove_websocket_connection(websocket)
        logger.info("WebSocket connection closed")

@app.get("/api/stats")
async def get_statistics() -> Dict[str, Any]:
    """
    시스템 통계 정보

    Returns:
        Dict[str, Any]: 통계 데이터
    """
    try:
        scheduler = get_scheduler()
        student_states = scheduler.get_current_states()

        stats = {
            "total_students": len(student_states),
            "passed_students": 0,
            "failed_students": 0,
            "unknown_students": 0,
            "last_update": None,
            "active_connections": len(scheduler.websocket_connections)
        }

        latest_update = 0

        for state in student_states.values():
            try:
                status = state.get('status', 'unknown')

                if status == 'pass':
                    stats["passed_students"] += 1
                elif status == 'fail':
                    stats["failed_students"] += 1
                else:
                    stats["unknown_students"] += 1

                # 가장 최근 업데이트 시간 찾기
                last_update = state.get('last_update')
                if last_update is not None and isinstance(last_update, (int, float)) and last_update > latest_update:
                    latest_update = last_update
            except Exception as e:
                # 개별 상태 처리 중 오류가 발생해도 계속 진행
                logger.debug(f"Error processing state: {e}")
                continue

        if latest_update > 0:
            stats["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(latest_update))

        return stats

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return {"error": str(e)}

# 에러 핸들러
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """404 에러 핸들러"""
    return HTMLResponse(
        content="<h1>404 Not Found</h1><p>The requested page was not found.</p>",
        status_code=404
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """500 에러 핸들러"""
    logger.error(f"Internal server error: {exc}")
    return HTMLResponse(
        content="<h1>500 Internal Server Error</h1><p>An internal error occurred.</p>",
        status_code=500
    )

if __name__ == "__main__":
    import uvicorn

    # 설정 로드
    try:
        import yaml
        with open("config.backend.yaml", "r") as f:
            config = yaml.safe_load(f)

        server_config = config.get("server", {})
        host = server_config.get("host", "0.0.0.0")
        port = server_config.get("port", 8000)
        reload = server_config.get("reload", False)

    except Exception:
        # 기본값 사용
        host = "0.0.0.0"
        port = 8000
        reload = False

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(
        "frontend.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )