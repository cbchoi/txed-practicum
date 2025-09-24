import asyncio
import time
import logging
import yaml
import signal
import sys
from pathlib import Path
from typing import Dict, Any

from .git_manager import GitManager
from .grader import Grader


class GradingScheduler:
    def __init__(self):
        self.config = self._load_config()
        self.git_manager = GitManager(max_concurrent=self.config['grading']['max_concurrent'])
        self.grader = Grader()
        self.student_states = {}
        self.running = False
        self.logger = logging.getLogger(__name__)

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _load_config(self) -> Dict[str, Any]:
        try:
            with open('backend/config.backend.yaml', 'r') as file:
                config = yaml.safe_load(file)
                return config
        except Exception as e:
            print(f"Failed to load config: {e}")
            return {
                'scheduler': {
                    'pull_interval': 60,
                    'grade_interval': 60
                },
                'grading': {
                    'max_concurrent': 5
                }
            }

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    async def start_monitoring(self):
        """Start the main monitoring loop"""
        self.running = True
        self.logger.info("Starting grading scheduler...")

        # Initial load of student states
        self.student_states = self.grader.get_all_student_statuses()
        self.logger.info(f"Loaded initial states for {len(self.student_states)} students")

        while self.running:
            try:
                loop_start = time.time()

                # Update repositories
                self.logger.info("Starting repository update cycle")
                git_results = await self.git_manager.update_all_repositories()

                # Process students whose repositories were updated successfully
                updated_students = []
                for student_id, result in git_results.items():
                    if result['success']:
                        # Only grade if there were actual changes
                        if 'Already up to date' not in result.get('message', ''):
                            updated_students.append(student_id)

                if updated_students:
                    self.logger.info(f"Grading {len(updated_students)} students with updates")
                    await self._grade_students(updated_students)
                else:
                    self.logger.info("No students need grading this cycle")

                # Update all student states
                self.student_states = self.grader.get_all_student_statuses()

                # Calculate sleep time
                loop_duration = time.time() - loop_start
                sleep_time = max(0, self.config['scheduler']['pull_interval'] - loop_duration)

                self.logger.info(f"Cycle completed in {loop_duration:.2f}s, sleeping for {sleep_time:.2f}s")

                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(10)  # Sleep on error to prevent rapid failures

        self.logger.info("Scheduler stopped")

    async def _grade_students(self, student_ids, week: str = 'week01'):
        """Grade a list of students for a specific week"""
        for student_id in student_ids:
            try:
                self.logger.info(f"Grading student: {student_id}/{week}")
                problem_results = self.grader.grade_student(student_id, week)

                # Determine overall status from individual problems
                if all(result == True for result in problem_results.values()):
                    overall_status = 'pass'
                elif any(result == False for result in problem_results.values()):
                    overall_status = 'fail'
                else:
                    overall_status = 'unknown'

                self.student_states[student_id] = {
                    'status': overall_status,
                    'problems': problem_results,
                    'last_update': time.time()
                }

                self.logger.info(f"Student {student_id}: {overall_status} (problems: {problem_results})")

            except Exception as e:
                self.logger.error(f"Error grading {student_id}: {e}")
                num_problems = self.config['grading']['num_of_problems']
                self.student_states[student_id] = {
                    'status': 'fail',
                    'problems': {f"{i:02d}": False for i in range(1, num_problems + 1)},
                    'last_update': time.time()
                }

    def get_current_states(self) -> Dict[str, Any]:
        """Get current student states"""
        return self.student_states.copy()

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        if not self.student_states:
            return {'total': 0, 'pass': 0, 'fail': 0, 'unknown': 0}

        stats = {'total': len(self.student_states), 'pass': 0, 'fail': 0, 'unknown': 0}
        for state in self.student_states.values():
            status = state.get('status', 'unknown')
            stats[status] = stats.get(status, 0) + 1

        return stats


def setup_logging():
    """Setup logging configuration"""
    try:
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
            log_level = config.get('logging', {}).get('level', 'INFO')
            log_format = config.get('logging', {}).get('format',
                                  '%(asctime)s - %(levelname)s - %(message)s')
    except:
        log_level = 'INFO'
        log_format = '%(asctime)s - %(levelname)s - %(message)s'

    # Create logs directory if it doesn't exist
    Path('logs').mkdir(exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.FileHandler('logs/scheduler.log'),
            logging.StreamHandler()
        ]
    )


async def main():
    """Main entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        scheduler = GradingScheduler()
        await scheduler.start_monitoring()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Scheduler crashed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())