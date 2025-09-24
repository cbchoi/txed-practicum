# 학생 실습 모니터링 시스템

실시간으로 학생들의 GitHub 저장소를 모니터링하고 자동으로 채점하는 시스템입니다.

## 주요 기능

- 🔄 **실시간 Git 저장소 모니터링**: 학생들의 GitHub 저장소를 주기적으로 확인
- 🤖 **자동 채점**: 코드 변경사항이 감지되면 자동으로 채점 수행
- 📊 **실시간 대시보드**: 웹 브라우저에서 실시간으로 학생 상태 모니터링
- 🌐 **웹소켓 연결**: 실시간 업데이트를 위한 양방향 통신
- 📱 **반응형 UI**: 다양한 디바이스에서 최적화된 사용자 경험

## 시스템 요구사항

- Python 3.8 이상
- Git
- 인터넷 연결 (GitHub 저장소 접근용)

## 설치 및 실행

### 1. 빠른 시작

#### Windows:
```batch
# 시스템 실행
run.bat

# 시스템 종료
stop.bat
```

#### Linux/macOS:
```bash
# 시스템 실행
./run.sh

# 시스템 종료
./stop.sh
```

### 2. 수동 설치

```bash
# 가상 환경 생성
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 또는
venv\Scripts\activate.bat  # Windows

# 의존성 설치
pip install -r requirements.txt

# 부트스트랩 실행 (학생 저장소 초기화)
python bootstrap.py

# 백엔드 스케줄러 시작
python -m backend.scheduler &

# 프론트엔드 서버 시작
uvicorn frontend.main:app --host 0.0.0.0 --port 8000
```

## 사용 방법

### 1. roster.csv 파일 준비

학생 목록을 `roster.csv` 파일에 작성합니다:

```csv
id,git_id
S20237132,student_github_id1
S20237133,student_github_id2
```

### 2. 채점 스크립트 설정

`grading/grade.py` 파일에 채점 로직을 구현합니다:

```python
def main():
    # 채점 로직 구현
    # 성공시: result.pass 파일 생성
    # 실패시: result.fail 파일 생성
    pass
```

### 3. 시스템 실행

- `run.bat` (Windows) 또는 `./run.sh` (Linux/macOS) 실행
- 브라우저에서 `http://localhost:8000` 접속
- 실시간 대시보드에서 학생 상태 모니터링

## 프로젝트 구조

```
txed-practicum/
├── backend/                 # 백엔드 모듈들
│   ├── git_manager.py      # Git 저장소 관리
│   ├── grader.py           # 채점 시스템
│   └── scheduler.py        # 스케줄러
├── frontend/               # 프론트엔드
│   ├── main.py            # FastAPI 애플리케이션
│   └── templates/         # HTML 템플릿
├── grading/               # 채점 스크립트
├── students/              # 학생 데이터 (자동 생성)
├── logs/                  # 로그 파일 (자동 생성)
├── config.yaml           # 시스템 설정
├── requirements.txt      # Python 의존성
├── bootstrap.py          # 초기화 스크립트
├── roster.csv           # 학생 명단
└── run.bat/run.sh       # 실행 스크립트
```

## 설정

`config.yaml` 파일에서 시스템 설정을 변경할 수 있습니다:

```yaml
scheduler:
  pull_interval: 30        # Git pull 간격 (초)
  max_concurrent_pulls: 5  # 동시 pull 최대 개수

git:
  clone_timeout: 30        # Clone 타임아웃 (초)
  pull_timeout: 30         # Pull 타임아웃 (초)

grading:
  max_memory_mb: 512       # 채점시 최대 메모리 (MB)
  max_cpu_seconds: 30      # 채점시 최대 CPU 시간 (초)
```

## API 엔드포인트

- `GET /`: 메인 대시보드
- `GET /api/status`: 전체 학생 상태 조회
- `GET /api/stats`: 통계 정보 조회
- `GET /api/students/{student_id}`: 특정 학생 상태 조회
- `GET /health`: 시스템 상태 확인
- `WebSocket /ws`: 실시간 업데이트

## 로그 확인

시스템 로그는 `logs/` 디렉터리에 저장됩니다:

```bash
# 스케줄러 로그
tail -f logs/scheduler.log

# 부트스트랩 로그
tail -f logs/bootstrap.log
```

## 문제 해결

### 1. 저장소 Clone 실패
- GitHub 저장소가 공개 저장소인지 확인
- 저장소 URL이 올바른지 확인
- 네트워크 연결 상태 확인

### 2. 채점이 작동하지 않음
- `grading/grade.py` 파일이 올바르게 구현되었는지 확인
- 채점 스크립트가 `result.pass` 또는 `result.fail` 파일을 생성하는지 확인

### 3. 웹소켓 연결 실패
- 방화벽에서 8000 포트가 허용되어 있는지 확인
- 프록시 설정이 웹소켓을 차단하지 않는지 확인

## 보안 고려사항

- 신뢰할 수 없는 코드 실행을 위한 샌드박싱
- 리소스 제한 (CPU, 메모리, 시간)
- 로그에 민감한 정보 기록 방지

## 라이선스

이 프로젝트는 교육 목적으로 제작되었습니다.