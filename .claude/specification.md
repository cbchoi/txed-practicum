# 학생 실습 모니터링 시스템 명세서

## 시스템 개요
학생 GitHub 저장소를 실시간으로 모니터링하고 자동으로 코드를 채점하여 웹 대시보드에 결과를 표시하는 시스템입니다.

## 전체 시스템 아키텍처
- **초기화 단계**: roster.csv에서 학생 디렉터리 초기화
- **백엔드**: 주기적 git pull 및 자동 채점
- **프론트엔드**: FastAPI 기반 경량 대시보드 (실시간 업데이트)

---

## 백엔드 명세

### 1. 프로젝트 구조
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
│   ├── git_manager.py     # Git 작업
│   ├── grader.py          # 채점 로직
│   └── scheduler.py       # 작업 스케줄링
├── frontend/
│   ├── main.py            # FastAPI 애플리케이션
│   └── templates/
│       └── dashboard.html  # Material Design 대시보드
├── students/               # 학생 개별 폴더들
│   ├── S20211001/         # 학생별 폴더
│   │   ├── repo/          # 클론된 저장소
│   │   └── grading/       # 복사된 채점 폴더
│   └── ...
├── config.backend.yaml     # 백엔드 구성 파일 (pull_interval 등)
└── requirements.txt        # Python 의존성
```

### 2. 유틸리티 프로그램 (generate_process_list.py)

#### 2.1 기능 명세
1. **roster.csv 읽기**: `id,git_id` 형태의 CSV 파일
2. **템플릿 처리**: GitHub 저장소 템플릿에서 {git_id} 부분을 실제 git_id로 치환
   - 예: `https://github.com/HBNU-COME2201/software-design-practicum-{git_id}`
   - 결과: `https://github.com/HBNU-COME2201/software-design-practicum-cbchoi`
3. **process_list.csv 생성**: `id,repository_url` 형태로 출력
   - 예: `S20211001,https://github.com/HBNU-COME2201/software-design-practicum-cbchoi`

#### 2.2 사용법
```bash
python generate_process_list.py --roster roster.csv --template "https://github.com/HBNU-COME2201/software-design-practicum-{git_id}" --output process_list.csv
```

### 3. 부트스트랩 구현 (bootstrap.py)

#### 2.1 기능 명세
1. **process_list.csv 읽기**: `id`, `repository_url` 컬럼 포함
2. **각 학생별 처리**:
   - `students/{id}/` 디렉터리 생성 (없는 경우만)
   - GitHub 저장소를 `students/{id}/repo/`에 클론
   - `grading/` 폴더 전체를 `students/{id}/grading/`로 복사
   - Git personal access token은 사용하지 않음 (공개 저장소만)
3. **오류 처리**:
   - 이미 존재하는 디렉터리 건너뛰기
   - 클론 실패 작업 로깅
   - 오류 발생 시 다음 학생으로 계속 진행

#### 2.2 기술 요구사항
- subprocess를 사용한 git 작업
- 적절한 로깅 구현
- 프라이빗 저장소 인증 처리 (환경 변수로 토큰 관리)

### 3. Git 관리자 (backend/git_manager.py)

#### 3.1 GitManager 클래스 명세
- **기능**:
  - 모든 학생 저장소에서 git pull 수행
  - 각 저장소별 상태 반환 (성공/실패)
  - SSH 키 또는 토큰을 통한 git 인증 처리
  - 실패한 pull에 대한 재시도 로직
  - 세마포어 제한을 둔 asyncio를 사용한 동시 작업

#### 3.2 기술 명세
- **동시성**: asyncio 기반 비동기 처리
- **제한**: 동시 작업 수 제한 (기본값: 5)
- **타임아웃**: git 작업 타임아웃 (기본값: 30초)
- **재시도**: 네트워크 오류 시 최대 3회 재시도

### 4. 채점 관리자 (backend/grader.py)

#### 4.1 Grader 클래스 명세
- **기능**:
  - 각 학생 디렉터리의 `grading/` 폴더에서 채점 스크립트 실행
  - 실행 결과에 따라 `pass` 파일 또는 `fail` 파일 생성
  - 각 채점 작업에 30초 타임아웃 구현
  - 디버깅을 위한 stderr/stdout 캡처 및 로깅
  - 제한된 리소스로 격리된 환경에서 실행 (subprocess)
- **결과 판정**:
  - `pass` 파일이 존재하면 통과
  - `fail` 파일이 존재하면 실패
  - 두 파일 모두 없으면 알 수 없음 상태

#### 4.2 기술 명세
- **샌드박싱**: 제한된 권한으로 학생 코드 실행
- **리소스 제한**: CPU (1코어), 메모리 (512MB), 디스크 (100MB)
- **네트워크 격리**: 채점 중 네트워크 액세스 비활성화
- **타임아웃**: 각 채점 작업 30초 제한

### 5. 스케줄러 (backend/scheduler.py)

#### 5.1 GradingScheduler 클래스 명세
- **기능**:
  - `config.backend.yaml`에서 설정된 간격으로 git pull 실행
  - 성공적인 pull 후 채점 트리거
  - 각 학생의 마지막 알려진 상태 유지
  - FastAPI 통합을 위한 비동기 인터페이스 제공
  - 우아한 종료 구현
  - 모든 학생 정보를 수집하여 frontend에 제공

#### 5.2 기술 명세
- **스케줄링**: APScheduler 또는 asyncio 기반
- **상태 관리**: 메모리 내 상태 저장 (데이터베이스 불필요)
- **인터페이스**: 웹소켓을 통한 실시간 업데이트

### 6. 구성 관리 (config.backend.yaml)

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

---

## 프론트엔드 명세

### 1. FastAPI 애플리케이션 (frontend/main.py)

#### 1.1 엔드포인트 명세
- `GET /` - 대시보드 HTML 제공
- `GET /api/status` - 모든 학생의 현재 상태 반환
- `WebSocket /ws` - 실시간 상태 업데이트
- `GET /health` - 시스템 상태 확인

#### 1.2 기술 요구사항
- **최소 의존성**: FastAPI, uvicorn만 사용
- **실시간 업데이트**: 폴링 없는 웹소켓
- **상태 관리**: 메모리 내 상태 관리 (데이터베이스 불필요)
- **자동 재연결**: 웹소켓 연결 끊김 시 자동 재연결

### 2. 대시보드 UI (frontend/templates/dashboard.html)

#### 2.1 기능 명세
- **표시 내용**:
  - 학생 ID 및 합격/불합격 상태
  - 마지막 업데이트 타임스탬프
  - 색상 코딩: 녹색(합격), 빨간색(불합격), 회색(알 수 없음)
- **기능**:
  - 웹소켓을 통한 자동 새로고침
  - 모바일 기기 지원
  - 외부 CSS/JS 라이브러리 불필요

#### 2.2 시각적 요구사항
- **레이아웃**: 학생 카드의 그리드 레이아웃 (한 화면에 10명씩)
- **디자인**: Material Design 컴포넌트 사용
- **접근성**: 고대비 색상
- **인디케이터**: 로딩 상태 표시
- **색상 구분**:
  - 초록색 배경: 실습 통과 학생
  - 기본 배경: 실습 미통과 학생
- **페이지네이션**: 한 화면에 들어가지 않으면 주기적으로 페이지 전환

#### 2.3 기술 명세
- **반응형**: CSS Grid 또는 Flexbox 사용
- **성능**: 100명 이상의 학생 지원
- **로딩 시간**: 1초 미만
- **웹소켓 지연**: 100ms 미만

---

## 보안 및 성능 요구사항

### 1. 보안 조치
1. **샌드박싱**: 제한된 권한으로 학생 코드 실행
2. **리소스 제한**: CPU (1코어), 메모리 (512MB), 디스크 (100MB)
3. **네트워크 격리**: 채점 중 네트워크 액세스 비활성화
4. **입력 검증**: roster.csv의 모든 입력 삭제
5. **인증**: 기본 인증으로 대시보드 보호 (선택사항)

### 2. 성능 요구사항
- **지원 학생 수**: 100명 이상
- **업데이트 주기**: 모든 학생 2분 미만
- **대시보드 로딩**: 1초 미만
- **웹소켓 지연**: 100ms 미만
- **메모리 사용**: 500MB 미만

### 3. 오류 처리 및 로깅
- **Git 오류**: 네트워크 문제, 인증 실패, 병합 충돌
- **채점 오류**: 컴파일 오류, 런타임 오류, 타임아웃
- **시스템 오류**: 디스크 부족, 권한 거부, 프로세스 제한

#### 로깅 요구사항
- Python logging 모듈 사용
- git 작업 및 채점용 별도 로그 파일
- 일일 로그 순환, 7일간 보관
- 모든 로그에 타임스탬프 및 학생 ID 포함

---

## 테스트 명세

### 1. 단위 테스트
- 모의 데이터를 사용한 부트스트랩 프로세스
- 가짜 저장소를 사용한 Git 작업
- 샘플 학생 코드를 사용한 채점
- FastAPI TestClient를 사용한 API 엔드포인트
- 웹소켓 연결

### 2. 통합 테스트
- 전체 시스템 워크플로우
- 다중 학생 동시 처리
- 오류 시나리오 및 복구
- 성능 및 메모리 사용

### 3. 성공 기준
1. 50명 이상의 학생 저장소 동시 모니터링 가능
2. 2분 내에 모든 상태 업데이트
3. 웹소켓을 통한 대시보드 실시간 업데이트
4. 일반적인 실패 시나리오 우아하게 처리
5. 메모리 누수 없이 24시간 이상 연속 실행
6. 문제 디버깅을 위한 명확한 로그 제공