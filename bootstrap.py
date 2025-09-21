#!/usr/bin/env python3
"""
학생 실습 모니터링 시스템 부트스트랩 스크립트
process_list.csv를 기반으로 학생 디렉터리를 생성하고 초기 설정을 수행합니다.
"""

import csv
import os
import sys
import subprocess
import shutil
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bootstrap.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def read_process_list(csv_path):
    """
    process_list.csv 파일을 읽어서 학생 정보를 반환

    Args:
        csv_path (str): process_list.csv 파일 경로

    Returns:
        list: 학생 정보 리스트 [{'id': 'S20211001', 'repository_url': 'https://...'}, ...]
    """
    students = []

    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if 'id' in row and 'repository_url' in row:
                    students.append({
                        'id': row['id'].strip(),
                        'repository_url': row['repository_url'].strip()
                    })
                else:
                    logger.warning(f"Invalid row format in process_list.csv: {row}")
    except FileNotFoundError:
        logger.error(f"Process list file '{csv_path}' not found")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading process list file: {e}")
        sys.exit(1)

    return students

def setup_student(student):
    """
    개별 학생 디렉터리 설정

    Args:
        student (dict): 학생 정보 {'id': 'S20211001', 'repository_url': 'https://...'}

    Returns:
        dict: 설정 결과 {'student_id': str, 'success': bool, 'message': str}
    """
    student_id = student['id']
    repository_url = student['repository_url']

    student_dir = Path(f"students/{student_id}")
    repo_dir = student_dir / "repo"
    grading_dir = student_dir / "grading"

    result = {
        'student_id': student_id,
        'success': False,
        'message': ''
    }

    try:
        # 디렉터리가 이미 존재하면 건너뛰기
        if student_dir.exists():
            logger.info(f"Directory already exists for {student_id}, skipping")
            result['success'] = True
            result['message'] = 'Directory already exists'
            return result

        # 학생 디렉터리 생성
        student_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory for {student_id}")

        # Git 클론 (personal access token 사용 안 함)
        logger.info(f"Cloning repository for {student_id}: {repository_url}")
        clone_result = subprocess.run([
            'git', 'clone', repository_url, str(repo_dir)
        ],
        capture_output=True,
        text=True,
        timeout=60  # 60초 타임아웃
        )

        if clone_result.returncode != 0:
            error_msg = f"Failed to clone repository: {clone_result.stderr}"
            logger.error(f"{student_id}: {error_msg}")
            result['message'] = error_msg
            return result

        logger.info(f"Successfully cloned repository for {student_id}")

        # grading 폴더 복사
        if Path("grading").exists():
            shutil.copytree("grading", grading_dir)
            logger.info(f"Copied grading folder for {student_id}")
        else:
            logger.warning("grading/ folder not found, skipping copy")

        result['success'] = True
        result['message'] = 'Setup completed successfully'

    except subprocess.TimeoutExpired:
        error_msg = f"Timeout while cloning repository (60 seconds)"
        logger.error(f"{student_id}: {error_msg}")
        result['message'] = error_msg

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"{student_id}: {error_msg}")
        result['message'] = error_msg

    return result

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("학생 실습 모니터링 시스템 부트스트랩")
    print("=" * 60)

    # 로그 디렉터리 확인/생성
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # process_list.csv 파일 확인
    process_list_path = "process_list.csv"
    if not Path(process_list_path).exists():
        logger.error(f"Process list file '{process_list_path}' not found")
        logger.error("Please run generate_process_list.py first")
        sys.exit(1)

    # grading 폴더 확인
    if not Path("grading").exists():
        logger.error("grading/ folder not found")
        logger.error("Please create grading/ folder with driver_template.py")
        sys.exit(1)

    # students 디렉터리 생성
    students_dir = Path("students")
    students_dir.mkdir(exist_ok=True)

    # process_list.csv 읽기
    logger.info("Reading process list...")
    students = read_process_list(process_list_path)

    if not students:
        logger.warning("No students found in process list")
        return

    logger.info(f"Found {len(students)} students to process")

    # 병렬 처리로 학생 설정 수행
    success_count = 0
    fail_count = 0

    print(f"\nProcessing {len(students)} students...")

    with ThreadPoolExecutor(max_workers=3) as executor:
        # 모든 학생에 대해 작업 제출
        future_to_student = {
            executor.submit(setup_student, student): student
            for student in students
        }

        # 결과 수집
        for future in as_completed(future_to_student):
            result = future.result()

            if result['success']:
                success_count += 1
                print(f"✓ {result['student_id']}: {result['message']}")
            else:
                fail_count += 1
                print(f"✗ {result['student_id']}: {result['message']}")

    # 결과 요약
    print("\n" + "=" * 60)
    print("부트스트랩 완료")
    print("=" * 60)
    print(f"총 학생 수: {len(students)}")
    print(f"성공: {success_count}")
    print(f"실패: {fail_count}")

    if fail_count > 0:
        print(f"\n실패한 학생들은 logs/bootstrap.log를 확인하세요.")

    # 생성된 디렉터리 구조 표시
    print(f"\n생성된 디렉터리 구조:")
    try:
        for student_dir in sorted(students_dir.iterdir()):
            if student_dir.is_dir():
                print(f"  students/{student_dir.name}/")
                repo_dir = student_dir / "repo"
                grading_dir = student_dir / "grading"

                if repo_dir.exists():
                    print(f"    ├── repo/ (Git repository)")
                if grading_dir.exists():
                    print(f"    └── grading/ (Grading scripts)")
    except Exception as e:
        logger.error(f"Error displaying directory structure: {e}")

if __name__ == "__main__":
    main()