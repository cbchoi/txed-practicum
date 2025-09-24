from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
import asyncio
import time
import logging
import sys
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.append(str(Path(__file__).parent.parent))

from backend.grader import Grader

app = FastAPI(title="학생 실습 모니터링 시스템")
templates = Jinja2Templates(directory="frontend/templates")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)

        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()
grader = Grader()

# Global variable to store scheduler instance (will be set when scheduler starts)
scheduler_instance = None

def set_scheduler_instance(scheduler):
    """Called by scheduler to register itself"""
    global scheduler_instance
    scheduler_instance = scheduler


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/api/status")
async def get_status():
    """Get current status of all students"""
    try:
        if scheduler_instance:
            return scheduler_instance.get_current_states()
        else:
            # Fallback to grader if scheduler is not available
            return grader.get_all_student_statuses()
    except Exception as e:
        logging.error(f"Error getting status: {e}")
        return {}


@app.get("/api/stats")
async def get_stats():
    """Get statistics about student status"""
    try:
        if scheduler_instance:
            return scheduler_instance.get_stats()
        else:
            statuses = grader.get_all_student_statuses()
            stats = {'total': len(statuses), 'pass': 0, 'fail': 0, 'unknown': 0}
            for status in statuses.values():
                status_type = status.get('status', 'unknown')
                stats[status_type] = stats.get(status_type, 0) + 1
            return stats
    except Exception as e:
        logging.error(f"Error getting stats: {e}")
        return {'total': 0, 'pass': 0, 'fail': 0, 'unknown': 0}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "scheduler_running": scheduler_instance is not None
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)

    try:
        # Send initial data
        initial_data = await get_status()
        await manager.send_personal_message(
            json.dumps({"type": "status_update", "data": initial_data}),
            websocket
        )

        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for message from client (mainly for keepalive)
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                # Echo back a pong if client sends ping
                if message == "ping":
                    await manager.send_personal_message("pong", websocket)
            except asyncio.TimeoutError:
                # Send periodic updates every 30 seconds if no messages
                current_status = await get_status()
                await manager.send_personal_message(
                    json.dumps({"type": "status_update", "data": current_status}),
                    websocket
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def broadcast_updates():
    """Background task to broadcast updates to all connected clients"""
    while True:
        try:
            if manager.active_connections:
                current_status = await get_status()
                stats = await get_stats()

                message = json.dumps({
                    "type": "status_update",
                    "data": current_status,
                    "stats": stats,
                    "timestamp": time.time()
                })

                await manager.broadcast(message)
        except Exception as e:
            logging.error(f"Error broadcasting updates: {e}")

        # Wait 5 seconds before next broadcast
        await asyncio.sleep(5)


# Background task for broadcasting updates
@app.on_event("startup")
async def startup_event():
    """Start background tasks when the app starts"""
    # Start the background task for broadcasting updates
    asyncio.create_task(broadcast_updates())


# Simple API endpoints for external monitoring
@app.get("/api/students/{student_id}")
async def get_student_status(student_id: str):
    """Get status of a specific student"""
    try:
        if scheduler_instance:
            all_states = scheduler_instance.get_current_states()
            if student_id in all_states:
                return all_states[student_id]
        else:
            status = grader.get_student_status(student_id)
            if status:
                return status

        return {"error": "Student not found"}, 404
    except Exception as e:
        logging.error(f"Error getting student {student_id} status: {e}")
        return {"error": "Internal server error"}, 500


if __name__ == "__main__":
    import uvicorn

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )