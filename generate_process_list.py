#!/usr/bin/env python3
"""
학생 roster.csv와 GitHub 저장소 템플릿을 이용하여 process_list.csv를 생성하는 유틸리티
"""

import csv
import argparse
import sys
from pathlib import Path

def read_roster(roster_path):
    """
    roster.csv 파일을 읽어서 학생 정보를 반환 (git_id가 있는 학생만)

    Args:
        roster_path (str): roster.csv 파일 경로

    Returns:
        list: 학생 정보 리스트 [{'id': 'S20211001', 'git_id': 'cbchoi'}, ...]
    """
    students = []
    skipped_students = []

    try:
        with open(roster_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if 'id' in row and 'git_id' in row:
                    student_id = row['id'].strip()
                    git_id = row['git_id'].strip()

                    # git_id가 비어있거나 없으면 스킵
                    if not git_id or git_id == '':
                        skipped_students.append(student_id)
                        print(f"Skipping {student_id}: No git_id provided")
                        continue

                    # git_id에 물음표가 있으면 스킵 (확정되지 않은 계정)
                    if '?' in git_id:
                        skipped_students.append(student_id)
                        print(f"Skipping {student_id}: Unconfirmed git_id '{git_id}'")
                        continue

                    students.append({
                        'id': student_id,
                        'git_id': git_id
                    })
                else:
                    print(f"Warning: Invalid row format in roster.csv: {row}")
    except FileNotFoundError:
        print(f"Error: Roster file '{roster_path}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading roster file: {e}")
        sys.exit(1)

    if skipped_students:
        print(f"Skipped {len(skipped_students)} students without git_id: {', '.join(skipped_students)}")

    return students

def generate_repository_urls(students, template):
    """
    학생 정보와 템플릿을 이용하여 저장소 URL을 생성

    Args:
        students (list): 학생 정보 리스트
        template (str): GitHub 저장소 URL 템플릿

    Returns:
        list: 처리 목록 [{'id': 'S20211001', 'repository_url': 'https://...'}, ...]
    """
    process_list = []

    for student in students:
        try:
            repository_url = template.format(git_id=student['git_id'])
            process_list.append({
                'id': student['id'],
                'repository_url': repository_url
            })
        except KeyError as e:
            print(f"Error: Template variable {e} not found in template")
            sys.exit(1)

    return process_list

def write_process_list(process_list, output_path):
    """
    process_list.csv 파일을 생성

    Args:
        process_list (list): 처리 목록
        output_path (str): 출력 파일 경로
    """
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            # 헤더 작성
            writer.writerow(['id', 'repository_url'])

            # 데이터 작성
            for item in process_list:
                writer.writerow([item['id'], item['repository_url']])

        print(f"Process list generated successfully: {output_path}")
        print(f"Total students: {len(process_list)}")

    except Exception as e:
        print(f"Error writing process list file: {e}")
        sys.exit(1)

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description='Generate process_list.csv from roster.csv and repository template'
    )

    parser.add_argument(
        '--roster',
        required=True,
        help='Path to roster.csv file (id,git_id format)'
    )

    parser.add_argument(
        '--template',
        required=True,
        help='GitHub repository URL template with {git_id} placeholder'
    )

    parser.add_argument(
        '--output',
        default='process_list.csv',
        help='Output file path (default: process_list.csv)'
    )

    args = parser.parse_args()

    # 입력 파일 존재 확인
    if not Path(args.roster).exists():
        print(f"Error: Roster file '{args.roster}' does not exist")
        sys.exit(1)

    # 템플릿 유효성 확인
    if '{git_id}' not in args.template:
        print("Error: Template must contain {git_id} placeholder")
        sys.exit(1)

    print(f"Reading roster from: {args.roster}")
    print(f"Repository template: {args.template}")
    print(f"Output file: {args.output}")
    print("-" * 50)

    # 1. roster.csv 읽기
    students = read_roster(args.roster)

    if not students:
        print("Warning: No students found in roster file")
        sys.exit(0)

    # 2. 저장소 URL 생성
    process_list = generate_repository_urls(students, args.template)

    # 3. process_list.csv 생성
    write_process_list(process_list, args.output)

    # 결과 미리보기
    print("\nGenerated entries:")
    for item in process_list[:5]:  # 처음 5개만 표시
        print(f"  {item['id']} -> {item['repository_url']}")

    if len(process_list) > 5:
        print(f"  ... and {len(process_list) - 5} more entries")

if __name__ == "__main__":
    main()