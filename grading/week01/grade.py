#!/usr/bin/env python3
"""
Week 1 자동 채점 스크립트
Java 채점 시스템을 실행하여 학생 코드를 채점합니다.
"""

import subprocess
import sys
import os
import tempfile
import shutil
from pathlib import Path


def main():
    """메인 채점 함수"""
    if len(sys.argv) != 2:
        print("Usage: python3 grade.py <problem_directory>")
        sys.exit(1)

    problem_dir = Path(sys.argv[1]).resolve()
    grading_dir = Path(__file__).parent.resolve()

    print(f"Starting Week 1 grading...")
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
        # 1. Java 채점 시스템 컴파일
        print("Compiling grading system...")
        compile_result = subprocess.run(
            ["javac", "*.java"],
            cwd=grading_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        if compile_result.returncode != 0:
            error_msg = f"Failed to compile grading system: {compile_result.stderr}"
            print(error_msg)
            results_fail.write_text(f"FAIL: {error_msg}")
            return False

        # 2. 학생 코드 Java 파일 확인
        java_files = list(problem_dir.glob("*.java"))
        if not java_files:
            error_msg = "No Java files found in problem directory"
            print(error_msg)
            results_fail.write_text(f"FAIL: {error_msg}")
            return False

        print(f"Found Java files: {[f.name for f in java_files]}")

        # 3. 학생 코드 컴파일
        print("Compiling student code...")
        student_compile_result = subprocess.run(
            ["javac", "*.java"],
            cwd=problem_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        if student_compile_result.returncode != 0:
            error_msg = f"Student code compilation failed: {student_compile_result.stderr}"
            print(error_msg)
            results_fail.write_text(f"FAIL: {error_msg}")
            return False

        # 4. Week1AutoGrader 실행
        print("Running Week1AutoGrader...")
        grader_result = subprocess.run(
            ["java", "Week1AutoGrader", str(problem_dir)],
            cwd=grading_dir,
            capture_output=True,
            text=True,
            timeout=60
        )

        print(f"Grader output: {grader_result.stdout}")
        if grader_result.stderr:
            print(f"Grader errors: {grader_result.stderr}")

        # 5. 결과 판정 (exit code 기반)
        if grader_result.returncode == 0:
            success_msg = f"Week 1 grading passed. Output: {grader_result.stdout[:200]}"
            print(success_msg)
            results_pass.write_text(f"PASS: {success_msg}")
            return True
        else:
            error_msg = f"Week 1 grading failed. Error: {grader_result.stderr[:200]}"
            print(error_msg)
            results_fail.write_text(f"FAIL: {error_msg}")
            return False

    except subprocess.TimeoutExpired:
        error_msg = "Grading timeout (60 seconds exceeded)"
        print(error_msg)
        results_fail.write_text(f"FAIL: {error_msg}")
        return False
    except Exception as e:
        error_msg = f"Grading error: {str(e)}"
        print(error_msg)
        results_fail.write_text(f"FAIL: {error_msg}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)