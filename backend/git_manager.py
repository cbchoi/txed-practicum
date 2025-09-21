"""
Git 관리자 모듈
학생 저장소들의 git pull 작업을 비동기적으로 관리합니다.
"""

import asyncio
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any

class GitManager:
    """Git 작업을 관리하는 클래스"""

    def __init__(self, max_concurrent: int = 5, timeout: int = 30):
        """
        GitManager 초기화

        Args:
            max_concurrent (int): 동시 실행할 최대 git 작업 수
            timeout (int): git 작업 타임아웃 (초)
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    async def pull_repository(self, student_id: str, repo_path: Path) -> Dict[str, Any]:
        """
        개별 저장소에서 git pull 수행

        Args:
            student_id (str): 학생 ID
            repo_path (Path): 저장소 경로

        Returns:
            Dict[str, Any]: 결과 정보 {'success': bool, 'message': str, 'error': str}
        """
        async with self.semaphore:
            result = {
                'success': False,
                'message': '',
                'error': ''
            }

            try:
                # .git 디렉터리 확인
                if not (repo_path / '.git').exists():
                    result['error'] = 'Not a git repository'
                    self.logger.warning(f"{student_id}: {result['error']}")
                    return result

                # git pull 실행
                process = await asyncio.create_subprocess_exec(
                    'git', 'pull',
                    cwd=repo_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=self.timeout
                    )

                    stdout_text = stdout.decode('utf-8').strip()
                    stderr_text = stderr.decode('utf-8').strip()

                    if process.returncode == 0:
                        result['success'] = True
                        result['message'] = stdout_text if stdout_text else 'Pull completed'
                        self.logger.info(f"{student_id}: Git pull successful")
                    else:
                        result['error'] = stderr_text if stderr_text else 'Git pull failed'
                        self.logger.warning(f"{student_id}: {result['error']}")

                except asyncio.TimeoutError:
                    # 프로세스 종료
                    try:
                        process.terminate()
                        await asyncio.wait_for(process.wait(), timeout=5)
                    except asyncio.TimeoutError:
                        process.kill()

                    result['error'] = f'Git pull timeout ({self.timeout}s)'
                    self.logger.warning(f"{student_id}: {result['error']}")

            except Exception as e:
                result['error'] = f'Unexpected error: {str(e)}'
                self.logger.error(f"{student_id}: {result['error']}")

            return result

    async def update_all_repositories(self) -> Dict[str, Dict[str, Any]]:
        """
        모든 학생 저장소에서 git pull 수행

        Returns:
            Dict[str, Dict[str, Any]]: 학생별 결과 정보
        """
        students_dir = Path('students')

        if not students_dir.exists():
            self.logger.error("Students directory not found")
            return {}

        # 학생 디렉터리 수집
        tasks = []
        student_paths = []

        for student_dir in students_dir.iterdir():
            if student_dir.is_dir():
                repo_path = student_dir / 'repo'
                if repo_path.exists():
                    student_paths.append((student_dir.name, repo_path))

        if not student_paths:
            self.logger.warning("No student repositories found")
            return {}

        self.logger.info(f"Starting git pull for {len(student_paths)} repositories")

        # 비동기 작업 생성
        for student_id, repo_path in student_paths:
            task = self.pull_repository(student_id, repo_path)
            tasks.append((student_id, task))

        # 모든 작업 실행
        results = {}
        completed_tasks = await asyncio.gather(
            *[task for _, task in tasks],
            return_exceptions=True
        )

        # 결과 정리
        for i, (student_id, _) in enumerate(tasks):
            if isinstance(completed_tasks[i], Exception):
                results[student_id] = {
                    'success': False,
                    'message': '',
                    'error': f'Task failed: {str(completed_tasks[i])}'
                }
            else:
                results[student_id] = completed_tasks[i]

        # 요약 로그
        success_count = sum(1 for r in results.values() if r['success'])
        fail_count = len(results) - success_count

        self.logger.info(f"Git pull completed: {success_count} success, {fail_count} failed")

        return results

    async def check_repository_status(self, student_id: str) -> Dict[str, Any]:
        """
        저장소 상태 확인

        Args:
            student_id (str): 학생 ID

        Returns:
            Dict[str, Any]: 상태 정보
        """
        repo_path = Path(f'students/{student_id}/repo')

        status = {
            'exists': False,
            'is_git_repo': False,
            'last_commit': None,
            'has_changes': False
        }

        try:
            if repo_path.exists():
                status['exists'] = True

                if (repo_path / '.git').exists():
                    status['is_git_repo'] = True

                    # 마지막 커밋 정보
                    try:
                        process = await asyncio.create_subprocess_exec(
                            'git', 'log', '-1', '--format=%H %s %ad',
                            cwd=repo_path,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        stdout, _ = await process.communicate()

                        if process.returncode == 0:
                            status['last_commit'] = stdout.decode('utf-8').strip()
                    except Exception:
                        pass

                    # 변경사항 확인
                    try:
                        process = await asyncio.create_subprocess_exec(
                            'git', 'status', '--porcelain',
                            cwd=repo_path,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        stdout, _ = await process.communicate()

                        if process.returncode == 0:
                            status['has_changes'] = bool(stdout.decode('utf-8').strip())
                    except Exception:
                        pass

        except Exception as e:
            self.logger.error(f"Error checking repository status for {student_id}: {e}")

        return status