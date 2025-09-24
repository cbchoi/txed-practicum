#!/usr/bin/env python3
import csv
import os
import sys
import logging
import shutil
import asyncio
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.append(str(Path(__file__).parent.parent))
from backend.git_manager import GitManager


def setup_logging():
    """Setup logging for bootstrap process"""
    # Create logs directory relative to parent directory
    logs_dir = Path('../logs')
    logs_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('../logs/bootstrap.log'),
            logging.StreamHandler()
        ]
    )


def read_process_list(csv_path: str = '../class_info/process_list.csv'):
    """Read student process list from CSV file"""
    students = []

    if not Path(csv_path).exists():
        logging.error(f"Process list file not found: {csv_path}")
        logging.info("Please run: python bootstrap/generate_process_list.py first")
        return students

    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                student_id = row.get('id', '').strip()
                repository_url = row.get('repository_url', '').strip()

                if student_id and repository_url:
                    students.append({
                        'id': student_id,
                        'repository_url': repository_url
                    })
                    logging.info(f"Added student: {student_id} -> {repository_url}")
                else:
                    logging.warning(f"Skipping incomplete row: {row}")

    except Exception as e:
        logging.error(f"Failed to read process list: {e}")

    logging.info(f"Loaded {len(students)} students from process list")
    return students


def create_grading_template():
    """Create a basic grading template if grading directory doesn't exist"""
    grading_dir = Path('../grading')
    grading_dir.mkdir(exist_ok=True)

    # Create week01 subdirectory as example
    week01_dir = grading_dir / 'week01'
    week01_dir.mkdir(exist_ok=True)

    # Create a basic grade.py template
    grade_template = week01_dir / 'grade.py'
    if not grade_template.exists():
        template_content = '''#!/usr/bin/env python3
"""
Basic grading template for week01
This script should create pass/fail files for each problem
"""
import os
from pathlib import Path

def main():
    """Main grading logic"""
    try:
        # Add your grading logic here
        # For example, check if specific files exist, run tests, etc.

        repo_dir = Path('.')  # Current directory contains cloned repo
        if not repo_dir.exists():
            create_fail_result("Repository not found")
            return

        # Example: Check if specific files exist for each problem
        problems = [
            {'id': '01', 'files': ['problem1.py']},
            {'id': '02', 'files': ['problem2.py']},
            {'id': '03', 'files': ['problem3.py']},
        ]

        for problem in problems:
            problem_id = problem['id']
            required_files = problem['files']

            all_files_exist = True
            for file in required_files:
                if not (repo_dir / file).exists():
                    all_files_exist = False
                    break

            if all_files_exist:
                create_pass_result(problem_id, f"Problem {problem_id} completed")
            else:
                create_fail_result(problem_id, f"Problem {problem_id} missing files")

    except Exception as e:
        for i in range(1, 4):  # Assuming 3 problems
            create_fail_result(f"{i:02d}", f"Grading error: {e}")

def create_pass_result(problem_id, message=""):
    """Create a pass result file for specific problem"""
    with open(f'pass{problem_id}', 'w') as f:
        f.write(message)
    print(f"PASS {problem_id}: {message}")

def create_fail_result(problem_id, message=""):
    """Create a fail result file for specific problem"""
    with open(f'fail{problem_id}', 'w') as f:
        f.write(message)
    print(f"FAIL {problem_id}: {message}")

if __name__ == '__main__':
    main()
'''
        grade_template.write_text(template_content)
        logging.info("Created basic grading template for week01")


async def setup_student(student: dict, git_manager: GitManager):
    """Setup a single student's directory and repository"""
    student_id = student['id']
    student_dir = Path(f"../students/{student_id}")

    # Check if directory already exists
    if student_dir.exists():
        logging.info(f"Directory already exists for {student_id}")
        return True

    try:
        # Create student directory
        student_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created directory for {student_id}")

        # Clone repository directly to student directory (not in subdirectory)
        clone_result = await git_manager.clone_repository(
            student['repository_url'],
            student_dir
        )

        if not clone_result['success']:
            logging.error(f"Failed to clone repository for {student_id}: {clone_result.get('error', 'Unknown error')}")
            return False

        # Copy grading scripts to cloned repository
        source_grading = Path('../grading')
        if source_grading.exists():
            try:
                for week_dir in source_grading.iterdir():
                    if week_dir.is_dir():
                        target_dir = student_dir / week_dir.name
                        if not target_dir.exists():
                            shutil.copytree(week_dir, target_dir)
                            logging.info(f"Copied grading scripts {week_dir.name} for {student_id}")
            except Exception as e:
                logging.warning(f"Failed to copy grading scripts for {student_id}: {e}")
        else:
            logging.warning("No grading directory found to copy")

        logging.info(f"Successfully set up {student_id}")
        return True

    except Exception as e:
        logging.error(f"Failed to setup {student_id}: {e}")
        # Cleanup on failure
        if student_dir.exists():
            try:
                shutil.rmtree(student_dir)
            except:
                pass
        return False


async def main():
    """Main bootstrap process"""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting bootstrap process...")

    # Create grading template if needed
    create_grading_template()

    # Read student process list
    students = read_process_list()
    if not students:
        logger.error("No students found in process list. Exiting.")
        logger.info("Please run: python bootstrap/generate_process_list.py first")
        sys.exit(1)

    # Create students directory
    students_dir = Path('../students')
    students_dir.mkdir(exist_ok=True)

    # Initialize git manager
    git_manager = GitManager(max_concurrent=3)  # Limit concurrent clones

    # Setup students
    successful_setups = 0
    failed_setups = 0

    logger.info(f"Setting up {len(students)} students...")

    for student in students:
        try:
            success = await setup_student(student, git_manager)
            if success:
                successful_setups += 1
            else:
                failed_setups += 1
        except Exception as e:
            logger.error(f"Error setting up {student['id']}: {e}")
            failed_setups += 1

    logger.info(f"Bootstrap completed: {successful_setups} successful, {failed_setups} failed")

    if failed_setups > 0:
        logger.warning(f"{failed_setups} students failed to setup. Check logs for details.")
        sys.exit(1)

    logger.info("Bootstrap process completed successfully!")


if __name__ == '__main__':
    asyncio.run(main())