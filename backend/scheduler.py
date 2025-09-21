"""
스케줄러 모듈
Git pull과 채점 작업을 주기적으로 실행하고 결과를 관리합니다.
"""

import asyncio
import yaml
import time
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Set
from .git_manager import GitManager
from .grader import Grader, GradeResult

class GradingScheduler:
    """채점 스케줄링을 관리하는 클래스"""

    def __init__(self, config_path: str = "config.backend.yaml"):
        """
        GradingScheduler 초기화

        Args:
            config_path (str): 설정 파일 경로
        """
        # 로거 먼저 초기화
        self.logger = logging.getLogger(__name__)

        self.config = self.load_config(config_path)
        self.git_manager = GitManager(
            max_concurrent=self.config.get('grading', {}).get('max_concurrent', 5),
            timeout=self.config.get('git', {}).get('timeout', 30)
        )
        self.grader = Grader(
            timeout=self.config.get('grading', {}).get('timeout', 30)
        )

        # 상태 관리
        self.student_states: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.current_week = self.config.get('weeks', {}).get('current_week', 1)

        # 웹소켓 연결 관리 (frontend와 통신용)
        self.websocket_connections: Set[Any] = set()

        # 신호 처리 설정
        self._setup_signal_handlers()

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """
        설정 파일 로드

        Args:
            config_path (str): 설정 파일 경로

        Returns:
            Dict[str, Any]: 설정 정보
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                self.logger.info(f"Configuration loaded from {config_path}")
                return config
        except FileNotFoundError:
            self.logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """기본 설정 반환"""
        return {
            'git': {
                'auth_method': 'none',
                'timeout': 30
            },
            'grading': {
                'timeout': 30,
                'max_concurrent': 5
            },
            'scheduler': {
                'pull_interval': 60,
                'grade_interval': 60
            },
            'server': {
                'host': '0.0.0.0',
                'port': 8000,
                'reload': False
            }
        }

    def _setup_signal_handlers(self):
        """신호 처리 핸들러 설정"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def initialize_student_states(self):
        """학생 상태 초기화"""
        students_dir = Path('students')

        if not students_dir.exists():
            self.logger.warning("Students directory not found")
            return

        # 모든 학생 디렉터리 스캔
        for student_dir in students_dir.iterdir():
            if student_dir.is_dir():
                student_id = student_dir.name
                status = self.grader.get_student_status(student_id, self.current_week)

                self.student_states[student_id] = {
                    'status': status['result'],
                    'last_update': status.get('last_modified', time.time()),
                    'git_status': 'unknown',
                    'last_git_pull': None,
                    'week': self.current_week
                }

        self.logger.info(f"Initialized states for {len(self.student_states)} students")

    async def start_monitoring(self):
        """모니터링 시작"""
        self.running = True
        self.logger.info("Starting grading scheduler...")

        # 초기 학생 상태 로드
        await self.initialize_student_states()

        # 스케줄링 루프
        pull_interval = self.config.get('scheduler', {}).get('pull_interval', 60)

        while self.running:
            try:
                cycle_start = time.time()

                # Git pull 및 채점 실행
                await self._run_monitoring_cycle()

                # 업데이트 브로드캐스트
                await self.broadcast_updates()

                # 다음 사이클까지 대기
                cycle_duration = time.time() - cycle_start
                sleep_time = max(0, pull_interval - cycle_duration)

                if sleep_time > 0:
                    self.logger.debug(f"Cycle completed in {cycle_duration:.2f}s, sleeping for {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)
                else:
                    self.logger.warning(f"Cycle took {cycle_duration:.2f}s, longer than interval {pull_interval}s")

            except Exception as e:
                self.logger.error(f"Error in monitoring cycle: {e}")
                await asyncio.sleep(10)  # 오류 시 10초 대기

        self.logger.info("Grading scheduler stopped")

    async def _run_monitoring_cycle(self):
        """단일 모니터링 사이클 실행"""
        self.logger.info("Starting monitoring cycle...")

        # 1. Git pull 실행
        git_results = await self.git_manager.update_all_repositories()

        # 2. 성공한 저장소에 대해 채점 실행
        grading_tasks = []
        current_time = time.time()

        for student_id, git_result in git_results.items():
            # Git 상태 업데이트
            if student_id in self.student_states:
                self.student_states[student_id]['git_status'] = 'success' if git_result['success'] else 'failed'
                self.student_states[student_id]['last_git_pull'] = current_time

            # Git pull이 성공한 경우에만 채점 실행
            if git_result['success']:
                # Repository가 실제로 존재하는지 확인
                repo_dir = Path(f'students/{student_id}/repo')
                if repo_dir.exists():
                    task = self._grade_student_async(student_id, self.current_week)
                    grading_tasks.append(task)
                else:
                    self.logger.warning(f"Repository directory not found for {student_id}, skipping grading")

        # 모든 채점 작업 병렬 실행
        if grading_tasks:
            self.logger.info(f"Running grading for {len(grading_tasks)} students")
            await asyncio.gather(*grading_tasks, return_exceptions=True)

        # 통계 로깅
        total_students = len(self.student_states)
        passed_students = sum(1 for state in self.student_states.values() if state['status'] == 'pass')
        failed_students = sum(1 for state in self.student_states.values() if state['status'] == 'fail')
        unknown_students = total_students - passed_students - failed_students

        self.logger.info(f"Cycle completed: {passed_students} pass, {failed_students} fail, {unknown_students} unknown")

    async def _grade_student_async(self, student_id: str, week: int = 1):
        """비동기 래퍼로 학생 채점 실행"""
        try:
            # 동기 채점 함수를 별도 스레드에서 실행
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.grader.grade_student, student_id, week)

            # 상태 업데이트
            if student_id in self.student_states:
                self.student_states[student_id]['status'] = result
                self.student_states[student_id]['last_update'] = time.time()
                self.student_states[student_id]['week'] = week

        except Exception as e:
            self.logger.error(f"Error grading student {student_id} week {week}: {e}")

    def get_current_states(self) -> Dict[str, Any]:
        """현재 모든 학생 상태 반환"""
        return self.student_states.copy()

    def set_current_week(self, week: int):
        """현재 주차 설정 및 모든 학생 상태 재초기화"""
        available_weeks = self.config.get('weeks', {}).get('available_weeks', [1])
        if week not in available_weeks:
            raise ValueError(f"Week {week} is not in available weeks: {available_weeks}")

        self.current_week = week
        self.logger.info(f"Changed current week to {week}")

        # 모든 학생 상태를 새로운 주차로 재초기화
        for student_id in self.student_states:
            status = self.grader.get_student_status(student_id, week)
            self.student_states[student_id].update({
                'status': status['result'],
                'last_update': status.get('last_modified', time.time()),
                'week': week
            })

    def get_current_week(self) -> int:
        """현재 주차 반환"""
        return self.current_week

    def get_available_weeks(self) -> list:
        """사용 가능한 주차 목록 반환"""
        return self.config.get('weeks', {}).get('available_weeks', [1])

    def add_websocket_connection(self, websocket):
        """웹소켓 연결 추가"""
        self.websocket_connections.add(websocket)
        self.logger.debug("WebSocket connection added")

    def remove_websocket_connection(self, websocket):
        """웹소켓 연결 제거"""
        self.websocket_connections.discard(websocket)
        self.logger.debug("WebSocket connection removed")

    async def broadcast_updates(self):
        """모든 연결된 클라이언트에게 상태 업데이트 브로드캐스트"""
        if not self.websocket_connections:
            return

        message = self.student_states.copy()

        # 연결이 끊어진 웹소켓 제거를 위한 복사본 생성
        connections_to_remove = set()

        for websocket in self.websocket_connections:
            try:
                import json
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                self.logger.debug(f"Error sending to websocket: {e}")
                connections_to_remove.add(websocket)

        # 실패한 연결 제거
        for websocket in connections_to_remove:
            self.websocket_connections.discard(websocket)

    def stop(self):
        """스케줄러 중지"""
        self.running = False
        self.logger.info("Scheduler stop requested")

    async def shutdown(self):
        """정리 작업 수행"""
        self.stop()

        # 모든 웹소켓 연결 정리
        for websocket in self.websocket_connections.copy():
            try:
                await websocket.close()
            except Exception:
                pass

        self.websocket_connections.clear()
        self.logger.info("Scheduler shutdown completed")

# 스케줄러 인스턴스 (전역)
scheduler_instance: Optional[GradingScheduler] = None

def get_scheduler() -> GradingScheduler:
    """스케줄러 인스턴스 반환 (싱글톤)"""
    global scheduler_instance
    if scheduler_instance is None:
        scheduler_instance = GradingScheduler()
    return scheduler_instance

async def main():
    """메인 실행 함수 (독립 실행용)"""
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/scheduler.log'),
            logging.StreamHandler()
        ]
    )

    # 로그 디렉터리 생성
    Path('logs').mkdir(exist_ok=True)

    scheduler = get_scheduler()

    try:
        await scheduler.start_monitoring()
    except KeyboardInterrupt:
        logging.info("Received interrupt signal")
    finally:
        await scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())