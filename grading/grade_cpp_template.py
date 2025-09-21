#!/usr/bin/env python3
"""
C++ 채점 스크립트 템플릿
C++ 코드를 컴파일하고 실행하여 채점하는 템플릿입니다.
"""

import subprocess
import sys
import os
from pathlib import Path


def main():
    """메인 채점 함수"""
    if len(sys.argv) != 2:
        print("Usage: python3 grade.py <problem_directory>")
        sys.exit(1)

    problem_dir = Path(sys.argv[1]).resolve()
    grading_dir = Path(__file__).parent.resolve()

    print(f"Starting C++ grading...")
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
        # 1. C++ 파일 확인
        cpp_files = list(problem_dir.glob("*.cpp")) + list(problem_dir.glob("*.cc"))
        if not cpp_files:
            error_msg = "No C++ files found in problem directory"
            print(error_msg)
            results_fail.write_text(f"FAIL: {error_msg}")
            return False

        print(f"Found C++ files: {[f.name for f in cpp_files]}")

        # 2. C++ 코드 컴파일
        print("Compiling C++ code...")
        compile_result = subprocess.run(
            ["g++", "-o", "main", "*.cpp"],
            cwd=problem_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        if compile_result.returncode != 0:
            error_msg = f"C++ compilation failed: {compile_result.stderr}"
            print(error_msg)
            results_fail.write_text(f"FAIL: {error_msg}")
            return False

        # 3. 컴파일된 실행 파일 실행
        print("Running C++ executable...")
        executable = problem_dir / "main"
        if not executable.exists():
            error_msg = "Compiled executable not found"
            print(error_msg)
            results_fail.write_text(f"FAIL: {error_msg}")
            return False

        result = subprocess.run(
            ["./main"],
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
            success_msg = f"C++ code executed successfully. Output: {result.stdout[:200]}"
            print(success_msg)
            results_pass.write_text(f"PASS: {success_msg}")
            return True
        else:
            error_msg = f"C++ code execution failed. Error: {result.stderr[:200]}"
            print(error_msg)
            results_fail.write_text(f"FAIL: {error_msg}")
            return False

    except subprocess.TimeoutExpired:
        error_msg = "Compilation or execution timeout (30 seconds exceeded)"
        print(error_msg)
        results_fail.write_text(f"FAIL: {error_msg}")
        return False
    except Exception as e:
        error_msg = f"Grading error: {str(e)}"
        print(error_msg)
        results_fail.write_text(f"FAIL: {error_msg}")
        return False
    finally:
        # 컴파일된 파일 정리
        executable = problem_dir / "main"
        if executable.exists():
            try:
                executable.unlink()
            except:
                pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)