# 학생 실습 모니터링 시스템 기술 명세서

## 1. 시스템 개요

### 1.1 목적
학생 GitHub 저장소를 실시간으로 모니터링하고 자동으로 코드를 채점하여 웹 대시보드에 결과를 표시하는 시스템

### 1.2 주요 기능
- **실시간 Git 저장소 모니터링**: 학생들의 GitHub 저장소를 주기적으로 pull하여 변경사항 감지
- **자동 채점 시스템**: 미리 정의된 채점 스크립트를 통한 자동 평가
- **주차별 실습 관리**: 각 주차별로 별도의 채점 스크립트 및 결과 관리
- **실시간 웹 대시보드**: Material Design 기반의 직관적인 UI로 실시간 상태 표시
- **웹소켓 기반 실시간 업데이트**: 페이지 새로고침 없이 실시간 상태 변경 반영

### 1.3 시스템 아키텍처
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Student Repos │
│  (FastAPI)      │◄──►│   Scheduler     │◄──►│   (GitHub)      │
│                 │    │                 │    │                 │
│ - Dashboard     │    │ - Git Manager   │    │ - Student Code  │
│ - WebSocket     │    │ - Grader        │    │ - Results       │
│ - Week Selector │    │ - Week Support  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 2. 주차별 실습 시스템

### 2.1 주차 관리
- **현재 주차 설정**: 시스템 전체에서 참조하는 현재 실습 주차
- **사용 가능한 주차**: 설정에서 정의된 실습 주차 목록 (1-15주차)
- **주차별 채점 스크립트**: `week{N}_grader.py` 형태의 주차별 채점 스크립트

### 2.2 채점 스크립트 우선순위
1. **주차별 스크립트**: `week{N}_grader.py` (예: `week1_grader.py`)
2. **기본 스크립트**: `driver_template.py` (이전 버전 호환성)

### 2.3 결과 파일 관리
- **주차별 결과**: `week{N}_pass`, `week{N}_fail` (예: `week1_pass`)
- **기본 결과**: `pass`, `fail` (이전 버전 호환성)

## 3. 시스템 구성 요소

### 3.1 디렉터리 구조
```
student-monitor/
├── config.backend.yaml          # 시스템 설정 파일
├── roster.csv                   # 학생 명단 (id,git_id)
├── process_list.csv             # 처리 대상 저장소 목록 (id,repository_url)
├── requirements.txt             # Python 의존성
├── run.sh                       # 시스템 실행 스크립트
├── bootstrap.py                 # 초기 설정 스크립트
├── generate_process_list.py     # 처리 목록 생성 유틸리티
├── backend/                     # 백엔드 모듈
│   ├── git_manager.py          # Git 작업 관리
│   ├── grader.py               # 채점 로직 (주차별 지원)
│   └── scheduler.py            # 작업 스케줄링 (주차별 지원)
├── frontend/                    # 프론트엔드
│   ├── main.py                 # FastAPI 애플리케이션 (주차별 API)
│   └── templates/
│       └── dashboard.html      # 대시보드 템플릿 (주차 선택기 포함)
├── grading/                     # 채점 스크립트 템플릿
│   ├── driver_template.py      # 기본 채점 스크립트
│   ├── week1_grader.py         # 1주차 채점 스크립트 (선택)
│   ├── week2_grader.py         # 2주차 채점 스크립트 (선택)
│   └── ...
├── students/                    # 학생별 디렉터리
│   ├── S20211001/
│   │   ├── repo/               # 클론된 저장소
│   │   └── grading/            # 복사된 채점 스크립트
│   │       ├── driver_template.py
│   │       ├── week1_grader.py
│   │       ├── week1_pass      # 1주차 통과 결과
│   │       ├── week2_fail      # 2주차 실패 결과
│   │       └── ...
│   └── ...
└── logs/                        # 로그 파일
    ├── scheduler.log
    ├── frontend.log
    └── bootstrap.log
```

### 3.2 설정 파일 (config.backend.yaml)
```yaml
# 주차별 실습 설정
weeks:
  current_week: 1                # 현재 주차 (기본값)
  available_weeks: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
  grading_script_pattern: "week{week}_grader.py"

# Git 관련 설정
git:
  auth_method: none              # 공개 저장소만 지원
  timeout: 30
  max_retries: 3

# 채점 관련 설정
grading:
  timeout: 30                    # 채점 타임아웃 (초)
  max_concurrent: 5              # 동시 채점 수
  max_memory_mb: 512             # 최대 메모리 사용량
  max_cpu_time: 30               # 최대 CPU 시간

# 스케줄러 설정
scheduler:
  pull_interval: 60              # Git pull 주기 (초)
  grade_interval: 60             # 채점 주기 (초)

# 서버 설정
server:
  host: 0.0.0.0
  port: 8000
  reload: false
```

## 4. API 명세

### 4.1 프론트엔드 API

#### 메인 대시보드
```
GET /
Query Parameters:
  - week (int, optional): 조회할 주차 (없으면 현재 주차 사용)

Response: HTML (대시보드 페이지)
```

#### 학생 상태 조회
```
GET /api/status
Response: {
  "student_id": {
    "status": "pass|fail|unknown",
    "last_update": timestamp,
    "git_status": "success|failed",
    "last_git_pull": timestamp,
    "week": int
  }
}
```

#### 주차 관리
```
POST /api/week/{week}
Response: {
  "success": true,
  "current_week": int,
  "message": "Week changed to {week}"
}

GET /api/weeks
Response: {
  "current_week": int,
  "available_weeks": [1, 2, 3, ...]
}
```

#### 헬스체크
```
GET /health
Response: {
  "status": "healthy",
  "timestamp": timestamp,
  "students_count": int,
  "scheduler_running": boolean
}
```

#### 웹소켓
```
WS /ws
- 실시간 학생 상태 업데이트
- ping/pong 메시지 지원
```

### 4.2 백엔드 API (내부)

#### 채점 관리 (Grader)
```python
def grade_student(student_id: str, week: int = 1) -> GradeResult
def get_student_status(student_id: str, week: int = 1) -> dict
def cleanup_old_results(student_id: str, week: int = None)
```

#### 스케줄러 관리
```python
def set_current_week(week: int)
def get_current_week() -> int
def get_available_weeks() -> list
def get_current_states() -> Dict[str, Any]
```

## 5. 주차별 채점 시스템

### 5.1 채점 프로세스
1. **스크립트 선택**: 주차별 스크립트 우선, 없으면 기본 스크립트 사용
2. **실행 환경**: 제한된 리소스 (30초 타임아웃, 512MB 메모리)
3. **결과 판정**:
   - `week{N}_pass` 파일 존재 → 통과
   - `week{N}_fail` 파일 존재 → 실패
   - 둘 다 없음 → 알 수 없음

### 5.2 채점 스크립트 작성 가이드
```python
#!/usr/bin/env python3
"""
Week N Grader Script
"""

import sys
import subprocess
from pathlib import Path

def main():
    """주차별 채점 로직"""
    try:
        # 1. 학생 코드 디렉터리 확인
        repo_dir = Path('../repo')
        if not repo_dir.exists():
            create_fail_file("Repository not found")
            return

        # 2. 필요한 파일 확인
        required_files = ['main.py', 'requirements.txt']
        for file in required_files:
            if not (repo_dir / file).exists():
                create_fail_file(f"Required file missing: {file}")
                return

        # 3. 테스트 실행
        result = subprocess.run([
            sys.executable, str(repo_dir / 'main.py')
        ], capture_output=True, text=True, timeout=20)

        # 4. 결과 판정
        if result.returncode == 0 and "success" in result.stdout:
            create_pass_file("All tests passed")
        else:
            create_fail_file(f"Tests failed: {result.stderr}")

    except Exception as e:
        create_fail_file(f"Grading error: {e}")

def create_pass_file(message: str):
    """통과 결과 파일 생성"""
    Path('week1_pass').write_text(message)

def create_fail_file(message: str):
    """실패 결과 파일 생성"""
    Path('week1_fail').write_text(message)

if __name__ == "__main__":
    main()
```

## 6. 웹 대시보드

### 6.1 주요 기능
- **주차 선택기**: 헤더에 위치한 드롭다운으로 주차 변경
- **실시간 통계**: 전체/통과/실패 학생 수 표시
- **학생 카드**: 각 학생의 상태를 카드 형태로 표시
- **자동 페이지 전환**: 학생이 많을 경우 15초마다 페이지 전환
- **실시간 업데이트**: 웹소켓을 통한 실시간 상태 반영

### 6.2 상태 표시
- **통과 (pass)**: 초록색 배경, 체크 아이콘
- **실패 (fail)**: 빨간색 배경, 에러 아이콘
- **알 수 없음 (unknown)**: 주황색 배경, 물음표 아이콘

### 6.3 반응형 디자인
- **데스크톱**: 그리드 레이아웃으로 다중 카드 표시
- **태블릿/모바일**: 단일 컬럼 레이아웃으로 적응

## 7. 보안 및 성능

### 7.1 보안 고려사항
- **샌드박스 실행**: 학생 코드는 제한된 권한으로 실행
- **리소스 제한**: CPU, 메모리, 파일 시스템 접근 제한
- **타임아웃 적용**: 모든 외부 작업에 타임아웃 설정
- **공개 저장소만**: Git personal access token 사용 안 함

### 7.2 성능 요구사항
- **확장성**: 100명 이상의 학생 지원
- **응답성**: 전체 업데이트 사이클 2분 미만
- **실시간성**: 웹소켓 지연 100ms 미만
- **리소스 효율성**: 메모리 사용량 500MB 미만

## 8. 배포 및 운영

### 8.1 시스템 요구사항
- **OS**: Linux (Ubuntu 20.04+ 권장)
- **Python**: 3.8 이상
- **메모리**: 2GB 이상
- **디스크**: 10GB 이상 (학생 저장소 크기에 따라 조정)

### 8.2 실행 방법
```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 처리 목록 생성
python generate_process_list.py \
  --roster roster.csv \
  --template "https://github.com/HBNU-COME2201/software-design-practicum-{git_id}" \
  --output process_list.csv

# 3. 부트스트랩 실행
python bootstrap.py

# 4. 시스템 실행
./run.sh
```

### 8.3 모니터링
- **로그 파일**: `logs/` 디렉터리에 컴포넌트별 로그 저장
- **헬스체크**: `/health` 엔드포인트로 시스템 상태 확인
- **메트릭**: 실시간 통계를 통한 성능 모니터링

## 9. 확장 계획

### 9.1 향후 기능
- **상세 채점 리포트**: 채점 결과의 상세 정보 제공
- **히스토리 관리**: 주차별 진행 상황 히스토리
- **알림 시스템**: 이메일/슬랙 통합
- **고급 필터링**: 학생 그룹별, 상태별 필터

### 9.2 기술적 개선
- **데이터베이스 도입**: SQLite/PostgreSQL 도입으로 데이터 영속성 강화
- **캐싱 시스템**: Redis를 통한 성능 최적화
- **컨테이너화**: Docker를 통한 배포 표준화
- **CI/CD 파이프라인**: 자동 테스트 및 배포 체계

이 명세서는 학생 실습 모니터링 시스템의 주차별 실습 관리 기능을 포함한 전체 시스템의 기술적 세부사항을 다룹니다.