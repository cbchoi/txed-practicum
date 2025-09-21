# 학생 실습 모니터링 시스템 사용 가이드

## 목차

1. [시스템 개요](#시스템-개요)
2. [설치 및 초기 설정](#설치-및-초기-설정)
3. [주차별 실습 관리](#주차별-실습-관리)
4. [웹 대시보드 사용법](#웹-대시보드-사용법)
5. [채점 스크립트 작성](#채점-스크립트-작성)
6. [문제 해결](#문제-해결)
7. [고급 설정](#고급-설정)

## 시스템 개요

이 시스템은 학생들의 GitHub 저장소를 실시간으로 모니터링하고 자동으로 채점하여 결과를 웹 대시보드에 표시합니다. **주차별 실습 관리** 기능을 통해 각 주차별로 별도의 채점 스크립트와 결과를 관리할 수 있습니다.

### 주요 기능
- ✅ **실시간 Git 모니터링**: 학생 저장소의 변경사항을 주기적으로 감지
- ✅ **자동 채점 시스템**: 미리 정의된 스크립트로 자동 평가
- ✅ **주차별 실습 관리**: 각 주차별 채점 스크립트 및 결과 관리
- ✅ **실시간 웹 대시보드**: Material Design 기반 직관적 UI
- ✅ **웹소켓 실시간 업데이트**: 페이지 새로고침 없이 상태 반영

## 설치 및 초기 설정

### 1. 시스템 요구사항

```bash
# OS: Linux (Ubuntu 20.04+ 권장)
# Python: 3.8 이상
# 메모리: 2GB 이상
# 디스크: 10GB 이상
# 네트워크: GitHub 접근 가능
```

### 2. 프로젝트 설정

```bash
# 1. 프로젝트 디렉터리로 이동
cd student-monitor

# 2. Python 의존성 설치
pip install -r requirements.txt

# 3. 로그 디렉터리 생성
mkdir -p logs
```

### 3. 학생 명단 설정

**roster.csv 파일 생성:**
```csv
id,git_id
S20211001,cbchoi
S20211002,testuser1
S20211003,testuser2
```

- `id`: 학생 ID (시스템 내부 식별자)
- `git_id`: GitHub 사용자명

### 4. 저장소 목록 생성

```bash
# 처리 목록 생성
python generate_process_list.py \
  --roster roster.csv \
  --template "https://github.com/HBNU-COME2201/software-design-practicum-{git_id}" \
  --output process_list.csv
```

**생성된 process_list.csv 예시:**
```csv
id,repository_url
S20211001,https://github.com/HBNU-COME2201/software-design-practicum-cbchoi
S20211002,https://github.com/HBNU-COME2201/software-design-practicum-testuser1
S20211003,https://github.com/HBNU-COME2201/software-design-practicum-testuser2
```

### 5. 시스템 초기화

```bash
# 부트스트랩 실행 (학생 디렉터리 생성 및 저장소 클론)
python bootstrap.py
```

이 과정에서 다음이 수행됩니다:
- 각 학생별 `students/{학생ID}/` 디렉터리 생성
- GitHub 저장소를 `students/{학생ID}/repo/`에 클론
- `grading/` 폴더를 `students/{학생ID}/grading/`로 복사

### 6. 시스템 실행

```bash
# 전체 시스템 실행
./run.sh
```

**실행 후 접속 정보:**
- 📊 **대시보드**: http://localhost:8000
- 📋 **API 상태**: http://localhost:8000/api/status
- 💚 **헬스체크**: http://localhost:8000/health

## 주차별 실습 관리

### 1. 주차 설정 구성

**config.backend.yaml에서 주차 설정:**
```yaml
weeks:
  current_week: 1                # 현재 활성 주차
  available_weeks: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
  grading_script_pattern: "week{week}_grader.py"
```

### 2. 주차별 채점 스크립트 작성

**기본 구조:**
```
grading/
├── driver_template.py      # 기본 채점 스크립트 (이전 버전 호환)
├── week1_grader.py        # 1주차 채점 스크립트
├── week2_grader.py        # 2주차 채점 스크립트
├── week3_grader.py        # 3주차 채점 스크립트
└── ...
```

**주차별 스크립트 우선순위:**
1. `week{N}_grader.py` (해당 주차 전용 스크립트)
2. `driver_template.py` (기본 스크립트)

### 3. 주차 변경 방법

#### 웹 대시보드에서 변경:
1. 대시보드 상단의 "실습 주차" 선택기 이용
2. 원하는 주차 선택
3. 자동으로 해당 주차 결과로 전환

#### API를 통한 변경:
```bash
# 2주차로 변경
curl -X POST http://localhost:8000/api/week/2

# 현재 주차 정보 확인
curl http://localhost:8000/api/weeks
```

### 4. 주차별 결과 파일 관리

**결과 파일 명명 규칙:**
- **통과**: `week{N}_pass` (예: `week1_pass`, `week2_pass`)
- **실패**: `week{N}_fail` (예: `week1_fail`, `week2_fail`)
- **기본** (이전 버전 호환): `pass`, `fail`

**결과 판정 우선순위:**
1. 주차별 결과 파일 (`week{N}_pass/fail`)
2. 기본 결과 파일 (`pass/fail`)

## 웹 대시보드 사용법

### 1. 대시보드 구성 요소

#### 헤더 영역:
- **제목**: "학생 실습 모니터링"
- **주차 선택기**: 드롭다운으로 주차 변경
- **통계 정보**: 전체/통과/실패 학생 수

#### 상태 바:
- **연결 상태**: 실시간 연결 상태 표시
- **마지막 업데이트**: 최근 업데이트 시간

#### 학생 카드 영역:
- **학생 ID**: 각 학생의 식별자
- **상태 배지**: 통과(초록)/실패(빨강)/알수없음(주황)
- **마지막 업데이트**: 해당 학생의 최근 채점 시간

### 2. 상태 해석

| 상태 | 색상 | 의미 | 아이콘 |
|------|------|------|--------|
| **통과** | 초록색 | 해당 주차 실습 완료 | ✓ |
| **실패** | 빨간색 | 해당 주차 실습 미완료 또는 오류 | ✗ |
| **알 수 없음** | 주황색 | 채점 결과 없음 또는 처리 중 | ? |

### 3. 실시간 기능

- **웹소켓 연결**: 실시간 상태 업데이트
- **자동 페이지 전환**: 학생이 많을 경우 15초마다 페이지 전환
- **실시간 통계**: 통과/실패 학생 수 실시간 갱신

### 4. 반응형 디자인

- **데스크톱**: 그리드 레이아웃으로 다중 카드 표시
- **태블릿**: 2열 그리드
- **모바일**: 단일 컬럼 레이아웃

## 채점 스크립트 작성

### 1. 주차별 채점 스크립트 템플릿

```python
#!/usr/bin/env python3
"""
Week N Grading Script
목적: N주차 실습 자동 채점
"""

import sys
import subprocess
import json
from pathlib import Path

def main():
    """주차별 채점 메인 함수"""
    try:
        print(f"Starting Week {WEEK_NUMBER} grading...")

        # 1. 학생 저장소 경로 확인
        repo_dir = Path('../repo')
        if not repo_dir.exists():
            create_fail_file("Student repository not found")
            return

        # 2. 필수 파일 확인
        required_files = ['main.py', 'requirements.txt']
        missing_files = []

        for file in required_files:
            if not (repo_dir / file).exists():
                missing_files.append(file)

        if missing_files:
            create_fail_file(f"Missing required files: {', '.join(missing_files)}")
            return

        # 3. 의존성 설치 (필요한 경우)
        install_dependencies(repo_dir)

        # 4. 실습 과제 테스트 실행
        test_results = run_tests(repo_dir)

        # 5. 결과 판정 및 파일 생성
        if test_results['success']:
            create_pass_file(test_results['message'])
            print(f"✅ Week {WEEK_NUMBER} grading PASSED")
        else:
            create_fail_file(test_results['message'])
            print(f"❌ Week {WEEK_NUMBER} grading FAILED")

    except Exception as e:
        error_msg = f"Grading error: {str(e)}"
        create_fail_file(error_msg)
        print(f"💥 Week {WEEK_NUMBER} grading ERROR: {error_msg}")

def install_dependencies(repo_dir):
    """필요한 의존성 설치"""
    requirements_file = repo_dir / 'requirements.txt'
    if requirements_file.exists():
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
            ], check=True, capture_output=True, timeout=60)
            print("📦 Dependencies installed successfully")
        except subprocess.TimeoutExpired:
            print("⚠️ Dependency installation timeout (skipped)")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Dependency installation failed: {e}")

def run_tests(repo_dir):
    """실습 과제 테스트 실행"""
    try:
        # 예시: Python 스크립트 실행
        result = subprocess.run([
            sys.executable, str(repo_dir / 'main.py')
        ], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            # 출력 내용 검증
            output = result.stdout.strip()
            if validate_output(output):
                return {
                    'success': True,
                    'message': f'All tests passed. Output: {output[:100]}...'
                }
            else:
                return {
                    'success': False,
                    'message': f'Output validation failed. Got: {output[:100]}...'
                }
        else:
            return {
                'success': False,
                'message': f'Script execution failed: {result.stderr[:200]}...'
            }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'message': 'Script execution timeout (30s)'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Test execution error: {str(e)}'
        }

def validate_output(output):
    """출력 내용 검증 (주차별 요구사항에 따라 수정)"""
    # 예시: 특정 키워드나 패턴 확인
    required_keywords = ['success', 'completed', 'result']

    return any(keyword in output.lower() for keyword in required_keywords)

def create_pass_file(message):
    """통과 결과 파일 생성"""
    result_file = Path(f'week{WEEK_NUMBER}_pass')
    result_file.write_text(f"PASSED: {message}\nTimestamp: {get_timestamp()}")

def create_fail_file(message):
    """실패 결과 파일 생성"""
    result_file = Path(f'week{WEEK_NUMBER}_fail')
    result_file.write_text(f"FAILED: {message}\nTimestamp: {get_timestamp()}")

def get_timestamp():
    """현재 시간 문자열 반환"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 주차 번호 설정 (각 스크립트별로 수정)
WEEK_NUMBER = 1  # week1_grader.py의 경우

if __name__ == "__main__":
    main()
```

### 2. 주차별 요구사항 예시

#### Week 1: 기본 Python 프로그래밍
```python
def validate_output(output):
    """1주차: Hello World 출력 확인"""
    return "Hello, World!" in output

required_files = ['hello.py']
```

#### Week 2: 데이터 구조 실습
```python
def validate_output(output):
    """2주차: 리스트/딕셔너리 조작 결과 확인"""
    try:
        result = json.loads(output)
        return isinstance(result, dict) and 'data' in result
    except:
        return False

required_files = ['data_structures.py', 'test_data.json']
```

#### Week 3: 객체지향 프로그래밍
```python
def run_tests(repo_dir):
    """3주차: 클래스 구현 테스트"""
    # 특정 클래스의 존재 여부 확인
    test_script = repo_dir / 'test_classes.py'
    if test_script.exists():
        result = subprocess.run([sys.executable, str(test_script)], ...)
        return check_class_implementation(result)
```

### 3. 고급 채점 기법

#### 코드 품질 검사:
```python
def check_code_quality(repo_dir):
    """코드 품질 검사 (PEP8, 복잡도 등)"""
    try:
        # flake8으로 코드 스타일 검사
        result = subprocess.run([
            'flake8', str(repo_dir), '--max-line-length=120'
        ], capture_output=True, text=True)

        return result.returncode == 0
    except:
        return True  # 도구가 없으면 패스
```

#### 단위 테스트 실행:
```python
def run_unit_tests(repo_dir):
    """학생이 작성한 단위 테스트 실행"""
    test_files = list(repo_dir.glob('test_*.py'))

    for test_file in test_files:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', str(test_file), '-v'
        ], capture_output=True, text=True)

        if result.returncode != 0:
            return False

    return True
```

## 문제 해결

### 1. 일반적인 문제들

#### 시스템 실행 실패
```bash
# 원인: Python 가상환경 생성 실패
# 해결: python3-venv 패키지 설치
sudo apt install python3-venv

# 원인: 권한 문제
# 해결: 실행 권한 부여
chmod +x run.sh bootstrap.py generate_process_list.py
```

#### Git 클론 실패
```bash
# 원인: 프라이빗 저장소
# 해결: 공개 저장소로 변경하거나 config에서 인증 설정

# 원인: 저장소가 존재하지 않음
# 해결: process_list.csv의 URL 확인
```

#### 채점 실패
```bash
# 원인: 채점 스크립트 실행 권한 없음
# 해결:
chmod +x students/*/grading/*.py

# 원인: 의존성 설치 실패
# 해결: requirements.txt 확인 및 수동 설치
```

### 2. 로그 분석

#### 로그 파일 위치:
- **스케줄러**: `logs/scheduler.log`
- **프론트엔드**: `logs/frontend.log`
- **부트스트랩**: `logs/bootstrap.log`

#### 로그 분석 명령어:
```bash
# 최근 에러 확인
tail -n 50 logs/scheduler.log | grep ERROR

# 특정 학생 채점 로그 확인
grep "S20211001" logs/scheduler.log

# 실시간 로그 모니터링
tail -f logs/scheduler.log
```

### 3. 성능 최적화

#### 메모리 사용량 모니터링:
```bash
# 시스템 리소스 확인
ps aux | grep python
htop

# 메모리 사용량 알림 설정
watch -n 5 'ps -o pid,user,%mem,command ax | sort -b -k3 -r'
```

#### 채점 성능 조정:
```yaml
# config.backend.yaml
grading:
  max_concurrent: 3      # 동시 채점 수 감소
  timeout: 60           # 타임아웃 증가

scheduler:
  pull_interval: 120    # Git pull 간격 증가
```

## 고급 설정

### 1. 사용자 정의 설정

#### 주차별 다른 설정:
```yaml
# config.backend.yaml
week_specific:
  week1:
    timeout: 30
    required_files: ['hello.py']
  week2:
    timeout: 60
    required_files: ['main.py', 'data.json']
```

#### 알림 설정:
```yaml
notifications:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    recipients: ["teacher@university.edu"]
  slack:
    enabled: false
    webhook_url: "https://hooks.slack.com/..."
```

### 2. 데이터베이스 연동

#### SQLite 설정:
```python
# database.py
import sqlite3
from pathlib import Path

def init_database():
    db_path = Path('data/monitoring.db')
    db_path.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS grades (
            student_id TEXT,
            week INTEGER,
            status TEXT,
            timestamp DATETIME,
            message TEXT
        )
    ''')
    conn.commit()
    return conn
```

### 3. 확장 모듈

#### 커스텀 채점기 플러그인:
```python
# plugins/custom_grader.py
class CustomGrader:
    def __init__(self, config):
        self.config = config

    def grade(self, student_id, week, repo_path):
        # 커스텀 채점 로직
        pass
```

### 4. 배포 설정

#### Docker 컨테이너:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["./run.sh"]
```

#### Nginx 리버스 프록시:
```nginx
server {
    listen 80;
    server_name monitoring.university.edu;

    location / {
        proxy_pass http://localhost:8000;
        proxy_websocket true;
    }
}
```

## 사용자 가이드 요약

### 📋 체크리스트: 시스템 운영

#### 매 학기 시작:
- [ ] roster.csv 업데이트
- [ ] process_list.csv 재생성
- [ ] 부트스트랩 실행
- [ ] 주차별 채점 스크립트 준비

#### 매주 시작:
- [ ] 새로운 주차로 변경
- [ ] 해당 주차 채점 스크립트 확인
- [ ] 시스템 상태 모니터링

#### 일일 운영:
- [ ] 대시보드 상태 확인
- [ ] 로그 파일 점검
- [ ] 문제 학생 식별 및 대응

이 가이드를 통해 주차별 실습 관리 기능을 포함한 전체 시스템을 효과적으로 운영할 수 있습니다.