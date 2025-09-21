#!/usr/bin/env python3
"""
채점 스크립트 템플릿
이 스크립트는 학생의 코드를 평가하고 결과에 따라 pass 또는 fail 파일을 생성합니다.
"""

import os
import sys
from pathlib import Path

def evaluate_student_code():
    """
    학생 코드를 평가하는 함수
    실제 구현에서는 이 부분을 수정하여 구체적인 채점 로직을 작성합니다.
    """
    try:
        # 학생 저장소 경로 (grading 폴더의 상위/repo)
        repo_path = Path.cwd().parent / "repo"

        # 간단한 예시: main.py 파일이 존재하는지 확인
        main_file = repo_path / "main.py"

        if main_file.exists():
            # 실제로는 여기서 학생 코드를 실행하고 테스트
            print("Student code found and evaluated successfully")
            return True
        else:
            print("main.py not found in student repository")
            return False

    except Exception as e:
        print(f"Error during evaluation: {e}")
        return False

def main():
    """메인 실행 함수"""
    grading_dir = Path.cwd()  # 현재 작업 디렉터리 (grading 폴더)

    # 기존 결과 파일 제거
    pass_file = grading_dir / "pass"
    fail_file = grading_dir / "fail"

    if pass_file.exists():
        pass_file.unlink()
    if fail_file.exists():
        fail_file.unlink()

    # 채점 실행
    success = evaluate_student_code()

    # 결과 파일 생성
    if success:
        pass_file.touch()
        print("RESULT: PASS")
    else:
        fail_file.touch()
        print("RESULT: FAIL")

if __name__ == "__main__":
    main()