import asyncio
import subprocess
from pathlib import Path
import logging
import yaml
from typing import Dict, Any


class GitManager:
    def __init__(self, max_concurrent=5):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            with open('backend/config.backend.yaml', 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {'git': {'timeout': 30, 'clone_timeout': 30}}

    async def pull_repository(self, repo_path: Path) -> Dict[str, Any]:
        async with self.semaphore:
            try:
                self.logger.info(f"Pulling repository: {repo_path}")

                process = await asyncio.create_subprocess_exec(
                    'git', 'pull',
                    cwd=repo_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config['git']['timeout']
                )

                if process.returncode == 0:
                    message = stdout.decode().strip()
                    self.logger.info(f"Successfully pulled {repo_path}: {message}")
                    return {'success': True, 'message': message}
                else:
                    error = stderr.decode().strip()
                    self.logger.warning(f"Git pull failed for {repo_path}: {error}")
                    return {'success': False, 'error': error}

            except asyncio.TimeoutError:
                self.logger.error(f"Timeout pulling {repo_path}")
                return {'success': False, 'error': 'Timeout'}
            except Exception as e:
                self.logger.error(f"Error pulling {repo_path}: {e}")
                return {'success': False, 'error': str(e)}

    async def update_all_repositories(self) -> Dict[str, Dict[str, Any]]:
        students_dir = Path('students')
        if not students_dir.exists():
            self.logger.warning("Students directory does not exist")
            return {}

        tasks = []
        for student_dir in students_dir.iterdir():
            if student_dir.is_dir():
                repo_path = student_dir / 'repo'
                if repo_path.exists() and (repo_path / '.git').exists():
                    task = self.pull_repository(repo_path)
                    tasks.append((student_dir.name, task))
                else:
                    self.logger.warning(f"No git repository found for {student_dir.name}")

        if not tasks:
            self.logger.info("No repositories to update")
            return {}

        results = {}
        for student_id, task in tasks:
            try:
                result = await task
                results[student_id] = result
            except Exception as e:
                self.logger.error(f"Failed to update {student_id}: {e}")
                results[student_id] = {'success': False, 'error': str(e)}

        success_count = sum(1 for r in results.values() if r['success'])
        self.logger.info(f"Updated {success_count}/{len(results)} repositories successfully")

        return results

    async def clone_repository(self, repo_url: str, target_path: Path) -> Dict[str, Any]:
        async with self.semaphore:
            try:
                self.logger.info(f"Cloning {repo_url} to {target_path}")

                process = await asyncio.create_subprocess_exec(
                    'git', 'clone', repo_url, str(target_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config['git'].get('timeout', 30)
                )

                if process.returncode == 0:
                    self.logger.info(f"Successfully cloned {repo_url}")
                    return {'success': True, 'message': 'Cloned successfully'}
                else:
                    error = stderr.decode().strip()
                    self.logger.error(f"Failed to clone {repo_url}: {error}")
                    return {'success': False, 'error': error}

            except asyncio.TimeoutError:
                self.logger.error(f"Timeout cloning {repo_url}")
                return {'success': False, 'error': 'Clone timeout'}
            except Exception as e:
                self.logger.error(f"Error cloning {repo_url}: {e}")
                return {'success': False, 'error': str(e)}