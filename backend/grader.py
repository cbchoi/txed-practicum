import subprocess
import resource
import os
import time
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class Grader:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            with open('backend/config.backend.yaml', 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {
                'grading': {
                    'timeout': 30,
                    'max_concurrent': 5,
                    'num_of_problems': 3
                }
            }

    def limit_resources(self):
        """Resource limits for subprocess execution"""
        try:
            # CPU time limit
            cpu_limit = self.config['grading']['timeout']
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))

            # Memory limit (512MB in bytes)
            memory_limit = 512 * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
        except (AttributeError, OSError) as e:
            # Windows doesn't support resource limits
            self.logger.warning(f"Resource limits not available: {e}")

    def grade_student(self, student_id: str, week: str = 'week01') -> Dict[str, bool]:
        """Grade a single student's submission for a specific week"""
        student_dir = Path(f'students/{student_id}')

        if not student_dir.exists():
            self.logger.error(f"Student directory not found: {student_id}")
            return self._create_default_fail_results()

        # Look for grading script in student's week directory
        week_dir = student_dir / week
        grade_script = week_dir / 'grade.py'

        if not grade_script.exists():
            self.logger.warning(f"Grade script not found for {student_id}/{week}")
            # Try alternative locations
            for alt_location in [student_dir / 'grade.py', student_dir / 'driver.py']:
                if alt_location.exists():
                    grade_script = alt_location
                    break
            else:
                self.logger.error(f"No grading script found for {student_id}")
                return self._create_default_fail_results()

        try:
            # Clean up previous results in the week directory
            self._cleanup_results(week_dir)

            # Execute grading
            self.logger.info(f"Grading student: {student_id}/{week}")

            # Use different execution method based on OS
            if os.name == 'nt':  # Windows
                result = self._grade_windows(grade_script, week_dir)
            else:  # Unix-like
                result = self._grade_unix(grade_script, week_dir)

            # Check results for individual problems
            return self._check_problem_results(week_dir, student_id, week)

        except Exception as e:
            self.logger.error(f"Grading error for {student_id}/{week}: {e}")
            return self._create_default_fail_results()

    def _create_default_fail_results(self) -> Dict[str, bool]:
        """Create default fail results for all problems"""
        num_problems = self.config['grading']['num_of_problems']
        return {f"{i:02d}": False for i in range(1, num_problems + 1)}

    def _grade_windows(self, script_path: Path, working_dir: Path) -> subprocess.CompletedProcess:
        """Grade on Windows (no resource limits)"""
        return subprocess.run([
            'python', str(script_path)
        ],
        cwd=working_dir,
        timeout=self.config['grading']['timeout'],
        capture_output=True,
        text=True
        )

    def _grade_unix(self, script_path: Path, working_dir: Path) -> subprocess.CompletedProcess:
        """Grade on Unix-like systems (with resource limits)"""
        return subprocess.run([
            'python3', str(script_path)
        ],
        cwd=working_dir,
        timeout=self.config['grading']['timeout'],
        capture_output=True,
        text=True,
        preexec_fn=self.limit_resources
        )

    def _cleanup_results(self, working_dir: Path):
        """Remove previous result files"""
        for result_file in working_dir.glob('pass*'):
            try:
                result_file.unlink()
            except Exception as e:
                self.logger.warning(f"Failed to remove {result_file}: {e}")

        for result_file in working_dir.glob('fail*'):
            try:
                result_file.unlink()
            except Exception as e:
                self.logger.warning(f"Failed to remove {result_file}: {e}")

    def _check_problem_results(self, week_dir: Path, student_id: str, week: str) -> Dict[str, bool]:
        """Check grading results for individual problems"""
        results = {}
        num_problems = self.config['grading']['num_of_problems']

        for problem_num in range(1, num_problems + 1):
            problem_id = f"{problem_num:02d}"
            pass_file = week_dir / f'pass{problem_id}'
            fail_file = week_dir / f'fail{problem_id}'

            if pass_file.exists():
                results[problem_id] = True
                self.logger.info(f"Student {student_id}/{week} problem {problem_id}: PASS")
            elif fail_file.exists():
                results[problem_id] = False
                self.logger.info(f"Student {student_id}/{week} problem {problem_id}: FAIL")
            else:
                # No result file - treat as failure
                results[problem_id] = False
                self.logger.warning(f"No result file for {student_id}/{week} problem {problem_id}")

        return results

    def get_student_status(self, student_id: str, week: str = 'week01') -> Optional[Dict[str, Any]]:
        """Get current grading status for a student"""
        student_dir = Path(f'students/{student_id}')
        week_dir = student_dir / week

        if not week_dir.exists():
            return None

        # Get problem results
        num_problems = self.config['grading']['num_of_problems']
        problem_results = {}
        last_update_time = time.time()

        for problem_num in range(1, num_problems + 1):
            problem_id = f"{problem_num:02d}"
            pass_file = week_dir / f'pass{problem_id}'
            fail_file = week_dir / f'fail{problem_id}'

            if pass_file.exists():
                problem_results[problem_id] = True
                last_update_time = max(last_update_time, pass_file.stat().st_mtime)
            elif fail_file.exists():
                problem_results[problem_id] = False
                last_update_time = max(last_update_time, fail_file.stat().st_mtime)
            else:
                problem_results[problem_id] = None  # Unknown

        # Determine overall status
        if all(result == True for result in problem_results.values()):
            overall_status = 'pass'
        elif any(result == False for result in problem_results.values()):
            overall_status = 'fail'
        else:
            overall_status = 'unknown'

        return {
            'status': overall_status,
            'problems': problem_results,
            'last_update': last_update_time
        }

    def get_all_student_statuses(self, week: str = 'week01') -> Dict[str, Dict[str, Any]]:
        """Get grading status for all students"""
        students_dir = Path('students')
        if not students_dir.exists():
            return {}

        statuses = {}
        for student_dir in students_dir.iterdir():
            if student_dir.is_dir():
                status = self.get_student_status(student_dir.name, week)
                if status:
                    statuses[student_dir.name] = status

        return statuses