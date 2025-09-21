# 학생 실습 모니터링 시스템

학생 GitHub 저장소를 실시간으로 모니터링하고 자동으로 코드를 채점하여 웹 대시보드에 결과를 표시하는 시스템입니다.

## 🚀 주요 기능

- **주차별 실습 관리**: 주차별로 구분된 실습 관리 및 채점
- **실시간 모니터링**: 학생 GitHub 저장소의 변경사항을 주기적으로 확인
- **다중 언어 지원**: Java, Python, C++ 등 다양한 프로그래밍 언어 지원
- **자동 컴파일 및 실행**: 언어별 자동 컴파일 및 실행 지원
- **실시간 대시보드**: Material Design 기반의 직관적인 웹 인터페이스
- **주차 선택 기능**: 웹 대시보드에서 주차를 쉽게 변경
- **페이지네이션**: 많은 학생을 효율적으로 표시 (10명씩 자동 전환)
- **웹소켓 통신**: 실시간 상태 업데이트

## 📋 시스템 요구사항

- Python 3.8 이상
- Git
- 네트워크 연결 (GitHub 접근용)
- 최소 1GB 사용 가능한 디스크 공간

## 🏗️ 프로젝트 구조

```
txed-practicum/
├── roster.csv              # 학생 정보 (id,git_id 형태)
├── process_list.csv        # 생성된 처리 목록
├── grading/                # 주차별 채점 스크립트 폴더
│   ├── week01/            # 1주차 채점 스크립트
│   │   ├── grade.py       # Python 실행 스크립트
│   │   └── *.java         # Java 채점 시스템
│   ├── week02/            # 2주차 채점 스크립트
│   └── grade_template.py   # 새 주차용 템플릿
├── backend/                # 백엔드 모듈
├── frontend/               # 프론트엔드 웹앱
├── students/               # 학생별 폴더 (자동 생성)
│   └── S20211001/         # 학생별 폴더
│       ├── repo/          # 클론된 학생 저장소
│       │   └── problem/   # 학생 제출 코드
│       │       └── week1/ # 주차별 학생 코드
│       └── grading/       # 복사된 채점 폴더
│           └── week1/     # 주차별 채점 스크립트
├── logs/                   # 로그 파일들
├── config.backend.yaml     # 시스템 설정
└── requirements.txt        # Python 의존성
```

## 🔧 설치 및 실행

### 1. 저장소 클론
```bash
git clone <repository-url>
cd txed-practicum
```

### 2. 학생 정보 준비
`roster.csv` 파일을 생성하고 다음 형식으로 학생 정보를 입력:

```csv
id,git_id
S20211001,cbchoi
S20211002,student1
S20211003,student2
```

### 3. 시스템 실행
```bash
./run.sh
```

실행 시 GitHub 저장소 템플릿을 입력하라는 메시지가 나타납니다:
```
예: https://github.com/HBNU-COME2201/software-design-practicum-{git_id}
```

### 4. 대시보드 접속
브라우저에서 `http://localhost:8000`에 접속하여 대시보드를 확인합니다.

## 👨‍🎓 학생 저장소 구조

학생들은 다음과 같은 구조로 저장소를 구성해야 합니다:

```
student-repository/
└── problem/
    ├── week1/              # 1주차 실습
    │   ├── Main.java       # Java의 경우
    │   └── main.py         # Python의 경우
    ├── week2/              # 2주차 실습
    └── week3/              # 3주차 실습
```

### 지원 언어별 파일 구조

**Java:**
```
problem/week1/
├── Main.java      # 메인 클래스 (필수)
└── *.java         # 기타 Java 파일들
```

**Python:**
```
problem/week1/
├── main.py        # 메인 실행 파일 (필수)
└── *.py           # 기타 Python 파일들
```

**C++:**
```
problem/week1/
├── main.cpp       # 메인 실행 파일
└── *.cpp          # 기타 C++ 파일들
```

## ⚙️ 설정

### 백엔드 설정 (config.backend.yaml)
```yaml
# 주차별 실습 설정
weeks:
  current_week: 1                # 현재 주차
  available_weeks: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

# 디렉터리 구조 설정
directories:
  problem_folder: "problem"      # 학생 문제 폴더
  grading_folder: "grading"      # 채점 스크립트 폴더
  week_pattern: "week{week}"     # 주차 폴더 패턴

# 결과 파일 설정
results:
  pass_file: "results.pass"      # 통과 결과 파일명
  fail_file: "results.fail"      # 실패 결과 파일명

# 지원 언어별 실행 설정
languages:
  java:
    compile_command: "javac *.java"
    run_command: "java Main"
    source_extensions: [".java"]
  python:
    compile_command: null
    run_command: "python3 main.py"
    source_extensions: [".py"]
  cpp:
    compile_command: "g++ -o main *.cpp"
    run_command: "./main"
    source_extensions: [".cpp", ".cc"]

scheduler:
  pull_interval: 60      # Git pull 주기 (초)

grading:
  timeout: 30            # 채점 타임아웃 (초)
  max_concurrent: 5      # 동시 채점 수

server:
  port: 8000            # 웹서버 포트
```

### 주차별 채점 스크립트 생성
각 주차별로 `grading/week{N}/grade.py` 파일을 생성하여 채점 로직을 구현합니다:

```python
#!/usr/bin/env python3
"""
Week N 자동 채점 스크립트
"""
import subprocess
import sys
from pathlib import Path

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 grade.py <problem_directory>")
        sys.exit(1)

    problem_dir = Path(sys.argv[1]).resolve()
    grading_dir = Path(__file__).parent.resolve()

    # 결과 파일 초기화
    results_pass = grading_dir / "results.pass"
    results_fail = grading_dir / "results.fail"

    # 채점 로직 구현
    # Java: Java 채점 시스템 실행
    # Python: Python 코드 실행 및 테스트
    # C++: 컴파일 후 실행 및 테스트

    # 결과에 따라 results.pass 또는 results.fail 파일 생성

if __name__ == "__main__":
    main()
```

## 📊 대시보드 기능

### 주차 선택 기능
- 헤더에 주차 선택 드롭다운 제공
- 클릭으로 원하는 주차 선택 가능
- 주차 변경 시 모든 학생의 해당 주차 결과 표시

### 실시간 상태 표시
- 🟢 **초록색**: 실습 통과
- 🔴 **빨간색**: 실습 실패
- 🟡 **노란색**: 상태 알 수 없음

### 자동 페이지 전환
- 한 화면에 10명의 학생 표시
- 15초마다 자동으로 다음 페이지로 전환
- 모든 학생을 순환하여 표시

### 실시간 업데이트
- WebSocket을 통한 즉시 상태 업데이트
- 연결 상태 표시
- 자동 재연결 기능
- 주차 변경 시 실시간으로 결과 갱신

## 🔒 보안 기능

- **샌드박스 실행**: 학생 코드를 제한된 환경에서 실행
- **리소스 제한**: CPU 시간, 메모리 사용량 제한
- **타임아웃**: 무한 루프 방지
- **Git 토큰 불필요**: 공개 저장소만 지원

## 📝 로그 파일

시스템 운영 중 생성되는 주요 로그 파일:

- `logs/scheduler.log`: 스케줄러 및 채점 로그
- `logs/frontend.log`: 웹 서버 로그
- `logs/bootstrap.log`: 초기 설정 로그

## 🛠️ 수동 실행 (개발용)

각 컴포넌트를 별도로 실행할 수 있습니다:

```bash
# 1. 가상환경 설정
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. process_list.csv 생성
python3 generate_process_list.py --roster roster.csv --template "https://github.com/HBNU-COME2201/software-design-practicum-{git_id}"

# 3. 부트스트랩 실행
python3 bootstrap.py

# 4. 백엔드 스케줄러 시작
python3 -m backend.scheduler &

# 5. 프론트엔드 서버 시작
uvicorn frontend.main:app --host 0.0.0.0 --port 8000
```

## 🔧 문제 해결

### 자주 발생하는 문제

1. **Git 클론 실패**
   - 저장소 URL이 올바른지 확인
   - 공개 저장소인지 확인
   - 네트워크 연결 상태 확인

2. **채점 실패**
   - `grading/driver_template.py` 파일 존재 확인
   - 학생 저장소에 필요한 파일 존재 확인

3. **웹소켓 연결 실패**
   - 방화벽 설정 확인
   - 포트 8000이 사용 가능한지 확인

### 로그 확인
```bash
# 실시간 로그 모니터링
tail -f logs/scheduler.log
tail -f logs/frontend.log

# 오류 로그 검색
grep -i error logs/*.log
```

## 📈 성능 특성

- **지원 학생 수**: 100명 이상
- **업데이트 주기**: 설정 가능 (기본 60초)
- **메모리 사용량**: 약 100-200MB
- **동시 처리**: 최대 5개 저장소 동시 처리

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.

## 📞 지원

문제가 발생하거나 질문이 있으면 다음을 확인하세요:

1. 이 README의 문제 해결 섹션
2. 로그 파일 (`logs/` 디렉터리)
3. GitHub Issues 섹션