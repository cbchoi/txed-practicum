#!/usr/bin/env python3
"""
일반 채점 스크립트 템플릿
Python 코드를 채점하는 기본 템플릿입니다.
각 주차별로 복사하여 사용할 수 있습니다.
"""

import subprocess
import sys
import os
import importlib.util
from pathlib import Path


def main():
    """메인 채점 함수"""
    if len(sys.argv) != 2:
        print("Usage: python3 grade.py <problem_directory>")
        sys.exit(1)

    problem_dir = Path(sys.argv[1]).resolve()
    grading_dir = Path(__file__).parent.resolve()

    print(f"Starting Python grading...")
    print(f"Problem directory: {problem_dir}")
    print(f"Grading directory: {grading_dir}")

    # 결과 파일 초기화
    results_pass = grading_dir / "results.pass"
    results_fail = grading_dir / "results.fail"

    # 기존 결과 파일 삭제
    if results_pass.exists():
        results_pass.unlink()
    if results_fail.exists():
        results_fail.unlink()

    try:
        # 1. Python 파일 확인
        python_files = list(problem_dir.glob("*.py"))
        if not python_files:
            error_msg = "No Python files found in problem directory"
            print(error_msg)
            results_fail.write_text(f"FAIL: {error_msg}")
            return False

        print(f"Found Python files: {[f.name for f in python_files]}")

        # 2. main.py 파일 확인
        main_py = problem_dir / "main.py"
        if not main_py.exists():
            error_msg = "main.py file not found"
            print(error_msg)
            results_fail.write_text(f"FAIL: {error_msg}")
            return False

        # 3. Python 코드 실행 테스트
        print("Running Python code...")
        result = subprocess.run(
            ["python3", "main.py"],
            cwd=problem_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        print(f"Code output: {result.stdout}")
        if result.stderr:
            print(f"Code errors: {result.stderr}")

        # 4. 기본 성공 조건: 정상 실행 (exit code 0)
        if result.returncode == 0:
            success_msg = f"Python code executed successfully. Output: {result.stdout[:200]}"
            print(success_msg)
            results_pass.write_text(f"PASS: {success_msg}")
            return True
        else:
            error_msg = f"Python code execution failed. Error: {result.stderr[:200]}"
            print(error_msg)
            results_fail.write_text(f"FAIL: {error_msg}")
            return False

    except subprocess.TimeoutExpired:
        error_msg = "Code execution timeout (30 seconds exceeded)"
        print(error_msg)
        results_fail.write_text(f"FAIL: {error_msg}")
        return False
    except Exception as e:
        error_msg = f"Grading error: {str(e)}"
        print(error_msg)
        results_fail.write_text(f"FAIL: {error_msg}")
        return False


def test_specific_functionality():
    """
    특정 기능 테스트를 위한 함수
    각 주차별로 필요한 테스트 로직을 여기에 구현합니다.
    """
    # 예시: 특정 함수 존재 여부 확인
    # 예시: 특정 출력 형식 확인
    # 예시: 특정 알고리즘 구현 확인
    pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)