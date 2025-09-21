# CLAUDE.md

이 파일은 Claude Code가 학생 실습 모니터링 시스템을 개발할 때 참고할 지침서입니다.

## 프로젝트 개요

학생 GitHub 저장소를 실시간으로 모니터링하고 자동으로 코드를 채점하여 웹 대시보드에 결과를 표시하는 시스템입니다.

## 개발 환경

- **언어**: Python 3.8+
- **프레임워크**: FastAPI
- **의존성 관리**: pip, requirements.txt
- **버전 관리**: Git
- **배포**: uvicorn

## 프로젝트 구조

다음 구조로 프로젝트를 생성하세요:

```
student-monitor/
├── roster.csv              # 학생 ID 및 Git ID 정보 (id,git_id 형태)
├── process_list.csv        # 유틸리티로 생성된 처리 목록 (id, repository_url)
├── grading/                # 채점용 스크립트 폴더
│   └── driver_template.py  # 채점 스크립트 템플릿
├── bootstrap.py            # 초기 설정 스크립트
├── generate_process_list.py # roster.csv와 템플릿에서 process_list.csv 생성
├── backend/
│   ├── __init__.py
│   ├── git_manager.py     # Git 작업 관리
│   ├── grader.py          # 채점 로직
│   └── scheduler.py       # 작업 스케줄링
├── frontend/
│   ├── main.py            # FastAPI 애플리케이션
│   └── templates/
│       └── dashboard.html  # Material Design 대시보드
├── students/               # 학생 개별 폴더들 (부트스트랩으로 생성)
│   ├── S20211001/         # 학생별 폴더
│   │   ├── repo/          # 클론된 저장소
│   │   └── grading/       # 복사된 채점 폴더
│   └── ...
├── logs/                   # 로그 파일들
├── config.backend.yaml     # 백엔드 구성 파일 (pull_interval 등)
└── requirements.txt        # Python 의존성
```

## 핵심 구현 요구사항

### 1. 유틸리티 프로그램 (generate_process_list.py)

**기능**:
- roster.csv (id,git_id 형태) 읽기
- GitHub 저장소 템플릿에서 {git_id} 부분을 실제 git_id로 치환
- process_list.csv (id,repository_url 형태) 생성

**예시**:
- 입력: `S20211001,cbchoi`
- 템플릿: `https://github.com/HBNU-COME2201/software-design-practicum-{git_id}`
- 출력: `S20211001,https://github.com/HBNU-COME2201/software-design-practicum-cbchoi`

### 2. 부트스트랩 스크립트 (bootstrap.py)

**기능**:
- process_list.csv 읽기
- 각 학생별로 `students/{id}/` 폴더 생성
- GitHub 저장소를 `students/{id}/repo/`에 클론 (Git personal access token 사용 안 함)
- `grading/` 폴더 전체를 `students/{id}/grading/`로 복사

### 3. Git 관리자 (backend/git_manager.py)

**기능**:
- 모든 학생 저장소에서 비동기적으로 git pull 수행
- 타임아웃 30초, 동시 작업 수 제한 (기본값: 5)
- 실패한 pull에 대한 재시도 로직

### 4. 채점 관리자 (backend/grader.py)

**기능**:
- 각 학생의 `grading/` 폴더에서 채점 스크립트 실행
- 실행 결과에 따라 `pass` 또는 `fail` 파일 생성
- 30초 타임아웃, 리소스 제한 적용
- 결과 판정:
  - `pass` 파일 존재 → 통과
  - `fail` 파일 존재 → 실패
  - 둘 다 없음 → 알 수 없음

### 5. 스케줄러 (backend/scheduler.py)

**기능**:
- `config.backend.yaml`에서 설정된 간격으로 git pull 실행
- 성공적인 pull 후 채점 트리거
- 모든 학생 정보를 수집하여 frontend에 제공
- 웹소켓을 통한 실시간 업데이트 브로드캐스트

### 6. 프론트엔드 (frontend/main.py, templates/dashboard.html)

**기능**:
- FastAPI 기반 웹 애플리케이션
- Material Design 컴포넌트 사용
- 한 화면에 10명의 학생 표시
- 학생이 많으면 주기적으로 페이지 전환
- 색상 구분:
  - 초록색 배경: 실습 통과 학생
  - 기본 배경: 실습 미통과 학생
- 웹소켓을 통한 실시간 업데이트

## 구성 파일

### config.backend.yaml
```yaml
git:
  auth_method: none      # Git personal access token 사용 안 함
  timeout: 30

grading:
  timeout: 30
  max_concurrent: 5

scheduler:
  pull_interval: 60     # Git pull 주기 (초)
  grade_interval: 60

server:
  host: 0.0.0.0
  port: 8000
  reload: false
```

### requirements.txt
```
fastapi>=0.68.0
uvicorn[standard]>=0.15.0
pyyaml>=5.4.1
aiofiles>=0.7.0
jinja2>=3.0.0
python-multipart>=0.0.5
websockets>=10.0
psutil>=5.8.0
```

## 개발 순서

1. **기본 구조 생성**: 프로젝트 폴더 및 기본 파일들 생성
2. **유틸리티 프로그램**: generate_process_list.py 구현
3. **부트스트랩**: bootstrap.py 구현 및 테스트
4. **백엔드 컴포넌트**: git_manager.py, grader.py 구현
5. **스케줄러**: scheduler.py 구현
6. **프론트엔드**: FastAPI 앱과 대시보드 구현
7. **통합 테스트**: 전체 시스템 테스트

## 보안 고려사항

- 학생 코드는 제한된 권한으로 실행 (subprocess + 리소스 제한)
- Git personal access token 사용 안 함 (공개 저장소만)
- 파일 시스템 접근 제한
- 네트워크 격리 적용

## 성능 요구사항

- 100명 이상의 학생 지원
- 전체 업데이트 사이클 2분 미만
- 대시보드 로딩 시간 1초 미만
- 웹소켓 지연 100ms 미만
- 메모리 사용량 500MB 미만

## 테스트 지침

- 단위 테스트: 각 컴포넌트별 개별 테스트
- 통합 테스트: 전체 워크플로우 테스트
- 성능 테스트: 다수 학생 동시 처리 테스트
- 오류 테스트: 네트워크 장애, 저장소 문제 등

## 로깅

- Python logging 모듈 사용
- 별도 로그 파일: git.log, grading.log
- 모든 로그에 타임스탬프와 학생 ID 포함
- 일일 로그 순환, 7일간 보관

## 실행 방법

```bash
# 1. 프로젝트 설정
cd student-monitor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. process_list.csv 생성
python generate_process_list.py --roster roster.csv --template "https://github.com/HBNU-COME2201/software-design-practicum-{git_id}" --output process_list.csv

# 3. 부트스트랩 실행
python bootstrap.py

# 4. 백엔드 스케줄러 시작 (백그라운드)
python -m backend.scheduler &

# 5. 프론트엔드 서버 시작
uvicorn frontend.main:app --host 0.0.0.0 --port 8000
```

## 중요 참고사항

- **절대 Git personal access token을 사용하지 마세요** - 공개 저장소만 처리
- **모든 외부 작업에 타임아웃을 적용하세요** - git, 채점 등
- **학생 코드는 반드시 샌드박스에서 실행하세요**
- **결과 파일은 `pass`/`fail` 파일명을 사용하세요**
- **Material Design을 사용하여 직관적인 UI를 구성하세요**
- **한 화면에 10명씩 표시하고 필요시 자동 페이지 전환하세요**

이 지침을 따라 단계별로 구현하면 안정적이고 확장 가능한 학생 실습 모니터링 시스템을 구축할 수 있습니다.