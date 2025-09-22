"""
채점 관리자 모듈
학생 코드를 안전하게 실행하고 채점 결과를 관리합니다.
주차별 problem/week{N} 폴더의 학생 코드를 grading/week{N} 스크립트로 채점합니다.
"""

import subprocess
import os
import signal
import logging
import time
import yaml
import platform
from pathlib import Path
from typing import Literal, Optional, Dict, Any

# Windows/Unix 호환성을 위한 resource 모듈 처리
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    # Windows에서는 resource 모듈이 없음
    HAS_RESOURCE = False

# 결과 타입 정의
GradeResult = Literal['pass', 'fail', 'unknown']

class Grader:
    """채점 작업을 관리하는 클래스"""

    def __init__(self, timeout: int = 30, max_memory_mb: int = 512, config_path: str = "config.backend.yaml"):
        """
        Grader 초기화

        Args:
            timeout (int): 채점 타임아웃 (초)
            max_memory_mb (int): 최대 메모리 사용량 (MB)
            config_path (str): 설정 파일 경로
        """
        self.timeout = timeout
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """설정 파일 로드"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            self.logger.warning(f"Failed to load config: {e}, using defaults")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """기본 설정 반환"""
        return {
            'directories': {
                'problem_folder': 'problem',
                'grading_folder': 'grading',
                'week_pattern': 'week{week}'
            },
            'results': {
                'pass_file': 'results.pass',
                'fail_file': 'results.fail'
            },
            'languages': {
                'java': {
                    'compile_command': 'javac *.java',
                    'run_command': 'java Main',
                    'source_extensions': ['.java']
                },
                'python': {
                    'compile_command': None,
                    'run_command': 'python3 main.py',
                    'source_extensions': ['.py']
                }
            }
        }

    def limit_resources(self):
        """
        자식 프로세스의 리소스 제한 설정
        subprocess의 preexec_fn으로 사용됩니다.
        Windows에서는 resource 모듈이 없으므로 제한 기능을 건너뜁니다.
        """
        if not HAS_RESOURCE:
            # Windows에서는 리소스 제한 불가
            return

        try:
            # CPU 시간 제한 (초)
            resource.setrlimit(resource.RLIMIT_CPU, (self.timeout, self.timeout))

            # 메모리 제한 (바이트)
            resource.setrlimit(resource.RLIMIT_AS, (self.max_memory_bytes, self.max_memory_bytes))

            # 파일 생성 제한
            resource.setrlimit(resource.RLIMIT_FSIZE, (50 * 1024 * 1024, 50 * 1024 * 1024))  # 50MB

            # 프로세스 수 제한
            resource.setrlimit(resource.RLIMIT_NPROC, (10, 10))

        except Exception as e:
            # 리소스 제한 설정 실패는 로그만 남기고 계속 진행
            pass

    def grade_student(self, student_id: str, week: int = 1) -> GradeResult:
        """
        학생 코드 채점 실행 (새로운 구조: problem/week{N} -> grading/week{N})

        Args:
            student_id (str): 학생 ID
            week (int): 실습 주차 (기본값: 1)

        Returns:
            GradeResult: 채점 결과 ('pass', 'fail', 'unknown')
        """
        student_dir = Path(f'students/{student_id}')
        repo_dir = student_dir / 'repo'

        # 설정에서 디렉터리 패턴 가져오기
        week_pattern = self.config.get('directories', {}).get('week_pattern', 'week{week}')
        problem_folder = self.config.get('directories', {}).get('problem_folder', 'problem')
        grading_folder = self.config.get('directories', {}).get('grading_folder', 'grading')

        week_folder = week_pattern.format(week=week)

        # 학생 문제 폴더와 채점 폴더 경로
        student_problem_dir = repo_dir / problem_folder / week_folder
        student_grading_dir = student_dir / grading_folder / week_folder

        if not repo_dir.exists():
            self.logger.warning(f"Repository not cloned for {student_id}, skipping grading")
            return 'unknown'

        if not student_problem_dir.exists():
            self.logger.warning(f"Problem folder not found for {student_id} week {week}: {student_problem_dir}")
            return 'unknown'

        if not student_grading_dir.exists():
            self.logger.error(f"Grading folder not found for {student_id} week {week}: {student_grading_dir}")
            return 'unknown'

        try:
            # 기존 결과 파일 정리
            self._cleanup_result_files(student_grading_dir)

            self.logger.info(f"Starting grading for {student_id} week {week}")

            # 채점 실행
            start_time = time.time()
            result = self._execute_grading(student_id, week, student_problem_dir, student_grading_dir)
            execution_time = time.time() - start_time

            self.logger.info(f"Grading completed for {student_id} week {week} in {execution_time:.2f}s: {result}")
            return result

        except Exception as e:
            self.logger.error(f"Grading error for {student_id} week {week}: {e}")
            self._create_fail_result(student_grading_dir, f"Grading error: {e}")
            return 'fail'

    def _execute_grading(self, student_id: str, week: int, problem_dir: Path, grading_dir: Path) -> GradeResult:
        """채점 실행 로직"""
        try:
            # 1. 언어 감지
            language = self._detect_language(problem_dir)
            if not language:
                self._create_fail_result(grading_dir, "No supported language detected")
                return 'fail'

            self.logger.info(f"Detected language: {language} for {student_id} week {week}")

            # 2. 언어별 설정 가져오기
            lang_config = self.config.get('languages', {}).get(language, {})

            # 3. 코드 컴파일 (필요한 경우)
            if lang_config.get('compile_command'):
                if not self._compile_code(problem_dir, lang_config['compile_command']):
                    self._create_fail_result(grading_dir, "Compilation failed")
                    return 'fail'

            # 4. 코드 실행 및 테스트
            success, message = self._run_tests(problem_dir, grading_dir, lang_config.get('run_command'))

            # 5. 결과 파일 생성
            if success:
                self._create_pass_result(grading_dir, message)
                return 'pass'
            else:
                self._create_fail_result(grading_dir, message)
                return 'fail'

        except Exception as e:
            self._create_fail_result(grading_dir, f"Execution error: {e}")
            return 'fail'

    def _detect_language(self, problem_dir: Path) -> Optional[str]:
        """문제 디렉터리에서 언어 감지 (재귀적 검색)"""
        for language, config in self.config.get('languages', {}).items():
            extensions = config.get('source_extensions', [])
            for ext in extensions:
                # 직접 디렉터리와 하위 디렉터리 모두 검색
                direct_files = list(problem_dir.glob(f'*{ext}'))
                recursive_files = list(problem_dir.glob(f'**/*{ext}'))
                if direct_files or recursive_files:
                    return language
        return None

    def _compile_code(self, problem_dir: Path, compile_command: str) -> bool:
        """코드 컴파일"""
        try:
            # Windows 호환성: preexec_fn은 Unix에서만 사용 가능
            kwargs = {
                'shell': True,
                'cwd': problem_dir,
                'capture_output': True,
                'text': True,
                'timeout': self.timeout
            }

            if platform.system() != 'Windows' and HAS_RESOURCE:
                kwargs['preexec_fn'] = self.limit_resources

            result = subprocess.run(compile_command, **kwargs)

            if result.returncode == 0:
                self.logger.debug(f"Compilation successful: {compile_command}")
                return True
            else:
                self.logger.warning(f"Compilation failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.warning(f"Compilation timeout: {compile_command}")
            return False
        except Exception as e:
            self.logger.error(f"Compilation error: {e}")
            return False

    def _run_tests(self, problem_dir: Path, grading_dir: Path, run_command: str) -> tuple[bool, str]:
        """테스트 실행"""
        try:
            # 채점 스크립트 실행 (grading 디렉터리에서)
            grading_script = grading_dir / 'grade.py'

            if grading_script.exists():
                # 채점 스크립트가 있는 경우 실행
                # Windows/Unix 호환 Python 명령어
                python_cmd = 'python' if platform.system() == 'Windows' else 'python3'

                kwargs = {
                    'cwd': grading_dir,
                    'capture_output': True,
                    'text': True,
                    'timeout': self.timeout
                }

                if platform.system() != 'Windows' and HAS_RESOURCE:
                    kwargs['preexec_fn'] = self.limit_resources

                result = subprocess.run([
                    python_cmd, 'grade.py', str(problem_dir)
                ], **kwargs)
            elif run_command:
                # 기본 실행 명령어 사용 - Windows 호환 python 명령어로 변경
                if 'python3' in run_command and platform.system() == 'Windows':
                    run_command = run_command.replace('python3', 'python')

                kwargs = {
                    'shell': True,
                    'cwd': problem_dir,
                    'capture_output': True,
                    'text': True,
                    'timeout': self.timeout
                }

                if platform.system() != 'Windows' and HAS_RESOURCE:
                    kwargs['preexec_fn'] = self.limit_resources

                result = subprocess.run(run_command, **kwargs)
            else:
                return False, "No grading script or run command found"

            if result.returncode == 0:
                return True, f"Tests passed. Output: {result.stdout[:200]}..."
            else:
                return False, f"Tests failed. Error: {result.stderr[:200]}..."

        except subprocess.TimeoutExpired:
            return False, f"Test execution timeout ({self.timeout}s)"
        except Exception as e:
            return False, f"Test execution error: {e}"

    def _cleanup_result_files(self, grading_dir: Path):
        """기존 결과 파일 정리"""
        pass_file = self.config.get('results', {}).get('pass_file', 'results.pass')
        fail_file = self.config.get('results', {}).get('fail_file', 'results.fail')

        for filename in [pass_file, fail_file]:
            result_file = grading_dir / filename
            if result_file.exists():
                result_file.unlink()

    def _create_pass_result(self, grading_dir: Path, message: str):
        """통과 결과 파일 생성"""
        pass_file = self.config.get('results', {}).get('pass_file', 'results.pass')
        result_file = grading_dir / pass_file

        detailed_message = f"""✅ 실습 과제 통과

{message}

📝 피드백:
- 모든 요구사항이 정상적으로 구현되었습니다.
- 코드가 성공적으로 컴파일되고 실행되었습니다.
- 테스트 케이스를 모두 통과했습니다.

🎉 수고하셨습니다!

Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}"""

        result_file.write_text(detailed_message, encoding='utf-8')

    def _create_fail_result(self, grading_dir: Path, message: str):
        """실패 결과 파일 생성"""
        fail_file = self.config.get('results', {}).get('fail_file', 'results.fail')
        result_file = grading_dir / fail_file

        # 실패 유형별 구체적인 피드백 제공
        if "No supported language detected" in message:
            detailed_message = f"""❌ 실습 과제 실패

문제: 지원되는 프로그래밍 언어를 찾을 수 없습니다.

📝 해결 방법:
1. 올바른 위치에 소스 코드 파일이 있는지 확인하세요.
   - Java: .java 파일이 problem/week01/ 폴더에 있어야 합니다.
   - Python: .py 파일이 problem/week01/ 폴더에 있어야 합니다.
   - C++: .cpp, .cc, .cxx 파일이 problem/week01/ 폴더에 있어야 합니다.

2. 파일 확장자가 올바른지 확인하세요.

3. 파일명에 특수문자나 공백이 없는지 확인하세요.

💡 힌트: GitHub 저장소의 problem/week01/ 폴더에 과제 파일을 업로드하세요.

Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}"""

        elif "Compilation failed" in message:
            detailed_message = f"""❌ 실습 과제 실패

문제: 코드 컴파일에 실패했습니다.

📝 해결 방법:
1. 문법 오류를 확인하고 수정하세요.
   - 세미콜론(;) 누락
   - 괄호 (), 중괄호 {{}}, 대괄호 [] 짝이 맞지 않음
   - 변수명 오타
   - import/include 문 오류

2. 컴파일러 오류 메시지를 자세히 읽고 해당 라인을 수정하세요.

3. IDE나 온라인 컴파일러에서 먼저 테스트해보세요.

💡 힌트: 로컬 환경에서 컴파일이 성공하는지 확인 후 커밋하세요.

Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}"""

        elif "Execution error" in message or "Runtime error" in message:
            detailed_message = f"""❌ 실습 과제 실패

문제: 코드 실행 중 오류가 발생했습니다.

📝 해결 방법:
1. 런타임 에러를 확인하세요:
   - NullPointerException (Java)
   - IndexError, KeyError (Python)
   - Segmentation fault (C/C++)

2. 입력값 검증을 추가하세요.

3. 배열/리스트 인덱스 범위를 확인하세요.

4. 예외 처리를 추가하세요.

💡 힌트: 다양한 테스트 케이스로 프로그램을 실행해보세요.

Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}"""

        else:
            detailed_message = f"""❌ 실습 과제 실패

문제: {message}

📝 일반적인 해결 방법:
1. 과제 요구사항을 다시 확인하세요.
2. 코드를 다시 검토하고 테스트하세요.
3. 로컬 환경에서 정상 동작하는지 확인하세요.
4. GitHub에 올바른 폴더 구조로 업로드했는지 확인하세요.

📁 올바른 폴더 구조:
repository/
└── problem/
    └── week01/
        └── [your_source_files]

💡 도움이 필요하면 담당 교수나 조교에게 문의하세요.

Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}"""

        result_file.write_text(detailed_message, encoding='utf-8')

    def _determine_result(self, grading_dir: Path, student_id: str, week: int = 1) -> GradeResult:
        """
        채점 결과 파일을 확인하여 최종 결과 결정 (새로운 구조)

        Args:
            grading_dir (Path): 채점 디렉터리 경로 (students/{student_id}/grading/week{N}/)
            student_id (str): 학생 ID
            week (int): 실습 주차

        Returns:
            GradeResult: 채점 결과
        """
        # 설정에서 결과 파일명 가져오기
        pass_filename = self.config.get('results', {}).get('pass_file', 'results.pass')
        fail_filename = self.config.get('results', {}).get('fail_file', 'results.fail')

        pass_file = grading_dir / pass_filename
        fail_file = grading_dir / fail_filename

        # results.pass 파일이 존재하면 통과
        if pass_file.exists():
            if fail_file.exists():
                # 두 파일이 모두 존재하는 경우 경고 로그
                self.logger.warning(f"Both {pass_filename} and {fail_filename} files exist for {student_id} week {week}, treating as pass")
                fail_file.unlink()  # fail 파일 제거
            return 'pass'

        # results.fail 파일이 존재하면 실패
        if fail_file.exists():
            return 'fail'

        # 이전 버전 호환성을 위한 기본 파일 확인 (grading 최상위 디렉터리)
        parent_grading_dir = grading_dir.parent
        old_pass_file = parent_grading_dir / f'week{week}_pass'
        old_fail_file = parent_grading_dir / f'week{week}_fail'

        if old_pass_file.exists():
            self.logger.debug(f"Using legacy pass file for {student_id} week {week}")
            return 'pass'
        if old_fail_file.exists():
            self.logger.debug(f"Using legacy fail file for {student_id} week {week}")
            return 'fail'

        # 기본 legacy 파일 확인
        legacy_pass = parent_grading_dir / 'pass'
        legacy_fail = parent_grading_dir / 'fail'

        if legacy_pass.exists():
            self.logger.debug(f"Using legacy default pass file for {student_id}")
            return 'pass'
        if legacy_fail.exists():
            self.logger.debug(f"Using legacy default fail file for {student_id}")
            return 'fail'

        # 모든 파일이 없으면 알 수 없음
        self.logger.warning(f"No result files found for {student_id} week {week} in {grading_dir}")
        return 'unknown'

    def get_student_status(self, student_id: str, week: int = 1) -> dict:
        """
        학생의 현재 채점 상태 조회

        Args:
            student_id (str): 학생 ID
            week (int): 실습 주차

        Returns:
            dict: 상태 정보
        """
        student_dir = Path(f'students/{student_id}')
        grading_dir = student_dir / 'grading'

        # 새로운 구조: week01, week02 등
        week_pattern = self.config.get('directories', {}).get('week_pattern', 'week{week:02d}')
        week_folder = week_pattern.format(week=week)
        week_grading_dir = grading_dir / week_folder

        status = {
            'student_id': student_id,
            'week': week,
            'grading_dir_exists': grading_dir.exists(),
            'week_grading_dir_exists': week_grading_dir.exists(),
            'week_script_exists': False,
            'driver_script_exists': False,
            'result': 'unknown',
            'last_modified': None
        }

        if grading_dir.exists():
            week_script = grading_dir / f'week{week}_grader.py'
            driver_script = grading_dir / 'driver_template.py'

            status['week_script_exists'] = week_script.exists()
            status['driver_script_exists'] = driver_script.exists()

            # 새로운 구조의 결과 파일 확인 (week01, week02 등)
            if week_grading_dir.exists():
                status['result'] = self._determine_result(week_grading_dir, student_id, week)
            else:
                # 기존 구조 확인 (legacy)
                status['result'] = self._determine_result(grading_dir, student_id, week)

            # 마지막 수정 시간 확인
            try:
                # 새로운 구조 결과 파일 (week01/results.pass, week01/results.fail)
                pass_filename = self.config.get('results', {}).get('pass_file', 'results.pass')
                fail_filename = self.config.get('results', {}).get('fail_file', 'results.fail')

                if week_grading_dir.exists():
                    new_pass_file = week_grading_dir / pass_filename
                    new_fail_file = week_grading_dir / fail_filename

                    if new_pass_file.exists():
                        status['last_modified'] = new_pass_file.stat().st_mtime
                    elif new_fail_file.exists():
                        status['last_modified'] = new_fail_file.stat().st_mtime

                # Legacy 파일들 확인
                if status['last_modified'] is None:
                    pass_file = grading_dir / f'week{week}_pass'
                    fail_file = grading_dir / f'week{week}_fail'
                    old_pass_file = grading_dir / 'pass'
                    old_fail_file = grading_dir / 'fail'

                    # 주차별 파일 우선
                    if pass_file.exists():
                        status['last_modified'] = pass_file.stat().st_mtime
                    elif fail_file.exists():
                        status['last_modified'] = fail_file.stat().st_mtime
                    # 기본 파일 확인
                    elif old_pass_file.exists():
                        status['last_modified'] = old_pass_file.stat().st_mtime
                    elif old_fail_file.exists():
                        status['last_modified'] = old_fail_file.stat().st_mtime

            except Exception as e:
                self.logger.debug(f"Error getting last modified time for {student_id} week {week}: {e}")

        return status

    def cleanup_old_results(self, student_id: str, week: int = None):
        """
        이전 채점 결과 파일들을 정리

        Args:
            student_id (str): 학생 ID
            week (int, optional): 특정 주차 결과만 정리. None이면 모든 결과 정리
        """
        grading_dir = Path(f'students/{student_id}/grading')

        if not grading_dir.exists():
            return

        try:
            if week is not None:
                # 특정 주차 결과 파일만 제거
                for result_file in grading_dir.glob(f'week{week}_pass'):
                    result_file.unlink()
                for result_file in grading_dir.glob(f'week{week}_fail'):
                    result_file.unlink()
                self.logger.debug(f"Cleaned up week {week} results for {student_id}")
            else:
                # 모든 결과 파일 제거 (기본 파일 + 주차별 파일)
                for result_file in grading_dir.glob('pass'):
                    result_file.unlink()
                for result_file in grading_dir.glob('fail'):
                    result_file.unlink()
                for result_file in grading_dir.glob('week*_pass'):
                    result_file.unlink()
                for result_file in grading_dir.glob('week*_fail'):
                    result_file.unlink()
                self.logger.debug(f"Cleaned up all results for {student_id}")

        except Exception as e:
            self.logger.error(f"Error cleaning up results for {student_id}: {e}")