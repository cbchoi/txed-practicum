#!/usr/bin/env python3
"""
generate_process_list.py - 유틸리티 프로그램

class_info/roster.csv에서 학생 정보를 읽어서 GitHub 저장소 템플릿에 git_id를 치환하여
class_info/process_list.csv 파일을 생성합니다.

사용법:
python generate_process_list.py --roster class_info/roster.csv --template "https://github.com/HBNU-COME2201/software-design-practicum-{git_id}" --output class_info/process_list.csv
"""

import argparse
import csv
import logging
from pathlib import Path


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def read_roster(roster_path: str):
    """roster.csv 파일 읽기"""
    students = []

    if not Path(roster_path).exists():
        logging.error(f"Roster 파일을 찾을 수 없습니다: {roster_path}")
        return students

    try:
        with open(roster_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                student_id = row.get('id', '').strip()
                git_id = row.get('git_id', '').strip()

                if student_id and git_id:
                    students.append({
                        'id': student_id,
                        'git_id': git_id
                    })
                    logging.info(f"학생 정보 읽음: {student_id} -> {git_id}")
                else:
                    logging.warning(f"불완전한 행 건너뜀: {row}")

    except Exception as e:
        logging.error(f"Roster 파일 읽기 실패: {e}")

    logging.info(f"총 {len(students)}명의 학생 정보를 읽었습니다.")
    return students


def generate_process_list(students, template, output_path):
    """process_list.csv 생성"""
    try:
        # 출력 디렉터리 생성
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            # 헤더 작성
            writer.writerow(['id', 'repository_url'])

            for student in students:
                # 템플릿에서 {git_id} 부분을 실제 git_id로 치환
                repository_url = template.format(git_id=student['git_id'])

                writer.writerow([student['id'], repository_url])
                logging.info(f"처리 목록 추가: {student['id']} -> {repository_url}")

        logging.info(f"Process list가 생성되었습니다: {output_path}")
        return True

    except Exception as e:
        logging.error(f"Process list 생성 실패: {e}")
        return False


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='roster.csv에서 process_list.csv 생성'
    )

    parser.add_argument(
        '--roster',
        default='class_info/roster.csv',
        help='입력 roster.csv 파일 경로 (기본값: class_info/roster.csv)'
    )

    parser.add_argument(
        '--template',
        default='https://github.com/HBNU-COME2201/software-design-practicum-{git_id}',
        help='GitHub 저장소 URL 템플릿 (기본값: https://github.com/HBNU-COME2201/software-design-practicum-{git_id})'
    )

    parser.add_argument(
        '--output',
        default='class_info/process_list.csv',
        help='출력 process_list.csv 파일 경로 (기본값: class_info/process_list.csv)'
    )

    args = parser.parse_args()

    setup_logging()

    logging.info("Process list 생성을 시작합니다...")
    logging.info(f"입력 파일: {args.roster}")
    logging.info(f"템플릿: {args.template}")
    logging.info(f"출력 파일: {args.output}")

    # roster.csv 읽기
    students = read_roster(args.roster)
    if not students:
        logging.error("학생 정보가 없습니다. 종료합니다.")
        return 1

    # process_list.csv 생성
    if generate_process_list(students, args.template, args.output):
        logging.info("Process list 생성이 완료되었습니다!")
        return 0
    else:
        logging.error("Process list 생성에 실패했습니다.")
        return 1


if __name__ == '__main__':
    exit(main())