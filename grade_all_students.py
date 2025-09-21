#!/usr/bin/env python3
"""
모든 학생을 위한 간단한 채점 스크립트
"""
import os
import subprocess
import time
from pathlib import Path

def check_student_code(student_id):
    """학생 코드 존재 여부 확인"""
    student_dir = Path(f'students/{student_id}')
    repo_dir = student_dir / 'repo'
    grading_dir = student_dir / 'grading'

    # Week01 문제 폴더 확인
    problem_dir = repo_dir / 'problem' / 'week01'
    grading_week_dir = grading_dir / 'week01'

    result = {
        'student_id': student_id,
        'repo_exists': repo_dir.exists(),
        'problem_week01_exists': problem_dir.exists(),
        'grading_week01_exists': grading_week_dir.exists(),
        'java_files_count': 0,
        'result': 'unknown'
    }

    if problem_dir.exists():
        # 직접 디렉터리와 하위 디렉터리에서 Java 파일 찾기
        java_files = list(problem_dir.glob('*.java')) + list(problem_dir.glob('**/*.java'))
        result['java_files_count'] = len(java_files)

        # 간단한 평가: Java 파일이 5개 이상 있으면 pass
        if len(java_files) >= 5:
            result['result'] = 'pass'
            # pass 파일 생성
            if grading_week_dir.exists():
                pass_file = grading_week_dir / 'results.pass'
                with open(pass_file, 'w') as f:
                    f.write(f"PASS: Found {len(java_files)} Java files\n")
                    f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        else:
            result['result'] = 'fail'
            # fail 파일 생성
            if grading_week_dir.exists():
                fail_file = grading_week_dir / 'results.fail'
                with open(fail_file, 'w') as f:
                    f.write(f"FAIL: Only found {len(java_files)} Java files (need 5+)\n")
                    f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    return result

def main():
    print("Starting grading for all students...")

    students_dir = Path('students')
    if not students_dir.exists():
        print("Students directory not found!")
        return

    results = []

    for student_folder in sorted(students_dir.iterdir()):
        if student_folder.is_dir():
            student_id = student_folder.name
            print(f"Grading {student_id}...")

            result = check_student_code(student_id)
            results.append(result)

            status = result['result']
            java_count = result['java_files_count']
            print(f"  {student_id}: {status} ({java_count} Java files)")

    # 결과 요약
    print("\n=== GRADING SUMMARY ===")
    pass_count = sum(1 for r in results if r['result'] == 'pass')
    fail_count = sum(1 for r in results if r['result'] == 'fail')
    unknown_count = sum(1 for r in results if r['result'] == 'unknown')

    print(f"Total students: {len(results)}")
    print(f"PASS: {pass_count}")
    print(f"FAIL: {fail_count}")
    print(f"UNKNOWN: {unknown_count}")

    print("\n=== DETAILED RESULTS ===")
    for result in results:
        print(f"{result['student_id']}: {result['result']} "
              f"(repo: {result['repo_exists']}, "
              f"problem: {result['problem_week01_exists']}, "
              f"java files: {result['java_files_count']})")

if __name__ == "__main__":
    main()