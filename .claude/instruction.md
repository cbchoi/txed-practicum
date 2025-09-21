# 학생 실습 모니터링 시스템 구현 지침

## 전체 개발 워크플로우

### 1. 초기 설정
```bash
# 프로젝트 구조 생성
mkdir -p student-monitor/{backend,frontend/templates,grading,students,logs}
cd student-monitor

# 가상 환경 설정
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# process_list.csv 생성 (roster.csv와 템플릿 제공)
python generate_process_list.py --roster roster.csv --template "https://github.com/HBNU-COME2201/software-design-practicum-{git_id}" --output process_list.csv
```

### 2. 부트스트랩 실행
```bash
# 학생 디렉터리 초기화
python bootstrap.py
```

### 3. 백엔드 스케줄러 시작
```bash
# 백그라운드에서 스케줄러 실행
python -m backend.scheduler &
```

### 4. 프론트엔드 서버 시작
```bash
# FastAPI 서버 시작
uvicorn frontend.main:app --host 0.0.0.0 --port 8000
```

### 5. 로그 모니터링
```bash
# 채점 로그 실시간 확인
tail -f logs/grading.log

# Git 로그 실시간 확인
tail -f logs/git.log
```

---

## 백엔드 구현 지침

### 1. 부트스트랩 스크립트 (bootstrap.py)

#### 구현 단계:
1. **CSV 파서 구현**
   ```python
   import csv
   import os
   import subprocess
   import logging
   from pathlib import Path

   def read_roster(csv_path):
       students = []
       with open(csv_path, 'r') as file:
           reader = csv.DictReader(file)
           for row in reader:
               students.append({
                   'id_num': row['id_num'],
                   'github_repo': row['github_repo']
               })
       return students
   ```

2. **디렉터리 생성 및 클론 로직**
   ```python
   def setup_student(student):
       student_dir = Path(f"students/{student['id_num']}")
       repo_dir = student_dir / "repo"

       # 디렉터리가 이미 존재하면 건너뛰기
       if student_dir.exists():
           logger.info(f"Directory already exists for {student['id_num']}")
           return

       # 디렉터리 생성
       student_dir.mkdir(parents=True, exist_ok=True)

       # Git 클론
       try:
           subprocess.run([
               'git', 'clone', student['github_repo'], str(repo_dir)
           ], check=True, timeout=30)

           # grading 폴더 복사
           shutil.copytree('grading', student_dir / 'grading')

       except subprocess.CalledProcessError as e:
           logger.error(f"Failed to clone {student['github_repo']}: {e}")
       except subprocess.TimeoutExpired:
           logger.error(f"Timeout cloning {student['github_repo']}")
   ```

3. **에러 처리 및 로깅**
   ```python
   import logging

   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler('logs/bootstrap.log'),
           logging.StreamHandler()
       ]
   )
   ```

### 2. Git 관리자 (backend/git_manager.py)

#### 구현 단계:
1. **비동기 Git 작업 클래스**
   ```python
   import asyncio
   import subprocess
   from pathlib import Path
   import logging

   class GitManager:
       def __init__(self, max_concurrent=5):
           self.semaphore = asyncio.Semaphore(max_concurrent)
           self.logger = logging.getLogger(__name__)

       async def pull_repository(self, repo_path):
           async with self.semaphore:
               try:
                   process = await asyncio.create_subprocess_exec(
                       'git', 'pull',
                       cwd=repo_path,
                       stdout=asyncio.subprocess.PIPE,
                       stderr=asyncio.subprocess.PIPE
                   )
                   stdout, stderr = await asyncio.wait_for(
                       process.communicate(), timeout=30
                   )

                   if process.returncode == 0:
                       return {'success': True, 'message': stdout.decode()}
                   else:
                       return {'success': False, 'error': stderr.decode()}

               except asyncio.TimeoutError:
                   return {'success': False, 'error': 'Timeout'}
               except Exception as e:
                   return {'success': False, 'error': str(e)}
   ```

2. **모든 저장소 업데이트**
   ```python
   async def update_all_repositories(self):
       students_dir = Path('students')
       tasks = []

       for student_dir in students_dir.iterdir():
           if student_dir.is_dir():
               repo_path = student_dir / 'repo'
               if repo_path.exists():
                   task = self.pull_repository(repo_path)
                   tasks.append((student_dir.name, task))

       results = {}
       for student_id, task in tasks:
           result = await task
           results[student_id] = result

       return results
   ```

### 3. 채점 관리자 (backend/grader.py)

#### 구현 단계:
1. **샌드박스 실행 환경**
   ```python
   import subprocess
   import resource
   import os
   from pathlib import Path

   class Grader:
       def __init__(self, timeout=30):
           self.timeout = timeout
           self.logger = logging.getLogger(__name__)

       def limit_resources(self):
           # CPU 시간 제한 (30초)
           resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
           # 메모리 제한 (512MB)
           resource.setrlimit(resource.RLIMIT_AS, (512*1024*1024, 512*1024*1024))
   ```

2. **채점 실행 로직**
   ```python
   def grade_student(self, student_id):
       student_dir = Path(f'students/{student_id}')
       driver_path = student_dir / 'driver.py'

       if not driver_path.exists():
           self.logger.error(f"Driver script not found for {student_id}")
           return False

       try:
           # 기존 결과 파일 제거
           for result_file in student_dir.glob('result.*'):
               result_file.unlink()

           # 채점 실행
           result = subprocess.run([
               'python3', str(driver_path)
           ],
           cwd=student_dir,
           timeout=self.timeout,
           capture_output=True,
           text=True,
           preexec_fn=self.limit_resources
           )

           # 결과 확인
           pass_file = student_dir / 'result.pass'
           fail_file = student_dir / 'result.fail'

           if pass_file.exists():
               return True
           elif fail_file.exists():
               return False
           else:
               # 결과 파일이 없으면 실패로 처리
               fail_file.touch()
               return False

       except subprocess.TimeoutExpired:
           self.logger.warning(f"Grading timeout for {student_id}")
           (student_dir / 'result.fail').touch()
           return False
       except Exception as e:
           self.logger.error(f"Grading error for {student_id}: {e}")
           (student_dir / 'result.fail').touch()
           return False
   ```

### 4. 스케줄러 (backend/scheduler.py)

#### 구현 단계:
1. **비동기 스케줄러 클래스**
   ```python
   import asyncio
   import yaml
   from pathlib import Path
   from .git_manager import GitManager
   from .grader import Grader

   class GradingScheduler:
       def __init__(self):
           self.config = self.load_config()
           self.git_manager = GitManager()
           self.grader = Grader()
           self.student_states = {}
           self.running = False

       def load_config(self):
           with open('config.yaml', 'r') as file:
               return yaml.safe_load(file)
   ```

2. **주기적 작업 실행**
   ```python
   async def start_monitoring(self):
       self.running = True

       while self.running:
           try:
               # Git pull 실행
               git_results = await self.git_manager.update_all_repositories()

               # 성공한 저장소에 대해 채점 실행
               for student_id, result in git_results.items():
                   if result['success']:
                       grade_result = self.grader.grade_student(student_id)
                       self.student_states[student_id] = {
                           'status': 'pass' if grade_result else 'fail',
                           'last_update': time.time()
                       }

               # 설정된 간격만큼 대기
               await asyncio.sleep(self.config['scheduler']['pull_interval'])

           except Exception as e:
               logger.error(f"Scheduler error: {e}")
               await asyncio.sleep(10)  # 오류 시 10초 대기
   ```

---

## 프론트엔드 구현 지침

### 1. FastAPI 애플리케이션 (frontend/main.py)

#### 구현 단계:
1. **기본 FastAPI 앱 설정**
   ```python
   from fastapi import FastAPI, WebSocket
   from fastapi.responses import HTMLResponse
   from fastapi.templating import Jinja2Templates
   import json
   import asyncio

   app = FastAPI()
   templates = Jinja2Templates(directory="frontend/templates")

   # 연결된 웹소켓 클라이언트 관리
   connected_clients = set()
   ```

2. **API 엔드포인트 구현**
   ```python
   @app.get("/", response_class=HTMLResponse)
   async def dashboard(request: Request):
       return templates.TemplateResponse("dashboard.html", {"request": request})

   @app.get("/api/status")
   async def get_status():
       # 스케줄러에서 현재 상태 가져오기
       return scheduler.get_current_states()

   @app.get("/health")
   async def health_check():
       return {"status": "healthy", "timestamp": time.time()}
   ```

3. **웹소켓 구현**
   ```python
   @app.websocket("/ws")
   async def websocket_endpoint(websocket: WebSocket):
       await websocket.accept()
       connected_clients.add(websocket)

       try:
           while True:
               # 클라이언트로부터 메시지 대기 (연결 유지용)
               await websocket.receive_text()
       except:
           pass
       finally:
           connected_clients.remove(websocket)

   async def broadcast_updates(data):
       """모든 연결된 클라이언트에게 업데이트 브로드캐스트"""
       if connected_clients:
           message = json.dumps(data)
           for client in connected_clients.copy():
               try:
                   await client.send_text(message)
               except:
                   connected_clients.remove(client)
   ```

### 2. 대시보드 HTML (frontend/templates/dashboard.html)

#### 구현 단계:
1. **기본 HTML 구조**
   ```html
   <!DOCTYPE html>
   <html lang="ko">
   <head>
       <meta charset="UTF-8">
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <title>학생 실습 모니터링 대시보드</title>
       <style>
           /* CSS 스타일 */
       </style>
   </head>
   <body>
       <div id="dashboard">
           <h1>학생 실습 모니터링</h1>
           <div id="students-grid"></div>
           <div id="status">연결 중...</div>
       </div>
   </body>
   </html>
   ```

2. **CSS 스타일링**
   ```css
   body {
       font-family: Arial, sans-serif;
       margin: 0;
       padding: 20px;
       background-color: #f5f5f5;
   }

   #students-grid {
       display: grid;
       grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
       gap: 15px;
       margin: 20px 0;
   }

   .student-card {
       background: white;
       border-radius: 8px;
       padding: 15px;
       box-shadow: 0 2px 4px rgba(0,0,0,0.1);
       text-align: center;
   }

   .student-card.pass {
       border-left: 4px solid #28a745;
   }

   .student-card.fail {
       border-left: 4px solid #dc3545;
   }

   .student-card.unknown {
       border-left: 4px solid #6c757d;
   }
   ```

3. **JavaScript 웹소켓 연결**
   ```javascript
   let socket;
   let reconnectInterval = 3000;

   function connectWebSocket() {
       const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
       const wsUrl = `${protocol}//${window.location.host}/ws`;

       socket = new WebSocket(wsUrl);

       socket.onopen = function(event) {
           console.log('WebSocket 연결됨');
           document.getElementById('status').textContent = '연결됨';
       };

       socket.onmessage = function(event) {
           const data = JSON.parse(event.data);
           updateDashboard(data);
       };

       socket.onclose = function(event) {
           console.log('WebSocket 연결 끊김');
           document.getElementById('status').textContent = '연결 끊김 - 재연결 시도 중...';
           setTimeout(connectWebSocket, reconnectInterval);
       };

       socket.onerror = function(error) {
           console.error('WebSocket 오류:', error);
       };
   }

   function updateDashboard(studentStates) {
       const grid = document.getElementById('students-grid');
       grid.innerHTML = '';

       for (const [studentId, state] of Object.entries(studentStates)) {
           const card = document.createElement('div');
           card.className = `student-card ${state.status}`;
           card.innerHTML = `
               <h3>${studentId}</h3>
               <p class="status">${state.status === 'pass' ? '통과' : '실패'}</p>
               <p class="timestamp">${new Date(state.last_update * 1000).toLocaleString()}</p>
           `;
           grid.appendChild(card);
       }
   }

   // 페이지 로드 시 연결 시작
   window.addEventListener('load', function() {
       connectWebSocket();

       // 초기 데이터 로드
       fetch('/api/status')
           .then(response => response.json())
           .then(data => updateDashboard(data))
           .catch(error => console.error('초기 데이터 로드 실패:', error));
   });
   ```

---

## 구성 및 배포 지침

### 1. 환경 변수 설정
```bash
# .env 파일 생성
export GITHUB_TOKEN="your_personal_access_token"
export LOG_LEVEL="INFO"
export MAX_WORKERS="5"
```

### 2. 배포 스크립트 (run.sh)
```bash
#!/bin/bash

# Python 버전 확인
python3 --version || {
    echo "Python 3이 필요합니다"
    exit 1
}

# 가상 환경 활성화
source venv/bin/activate || {
    echo "가상 환경을 생성합니다"
    python3 -m venv venv
    source venv/bin/activate
}

# 의존성 설치
pip install -r requirements.txt

# 로그 디렉터리 생성
mkdir -p logs

# 부트스트랩 실행 (필요한 경우)
if [ ! -d "students" ]; then
    echo "부트스트랩 실행 중..."
    python bootstrap.py
fi

# 백엔드 스케줄러 시작
echo "스케줄러 시작 중..."
python -m backend.scheduler &
SCHEDULER_PID=$!

# FastAPI 서버 시작
echo "웹 서버 시작 중..."
uvicorn frontend.main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# 종료 시그널 처리
trap 'kill $SCHEDULER_PID $SERVER_PID' EXIT

echo "시스템이 시작되었습니다. http://localhost:8000에서 확인하세요"
wait
```

### 3. 시스템 모니터링
```bash
# 시스템 상태 확인 스크립트
#!/bin/bash

echo "=== 학생 상태 요약 ==="
echo "통과: $(find students -name "result.pass" | wc -l)"
echo "실패: $(find students -name "result.fail" | wc -l)"

echo "=== 최근 Git Pull 시간 ==="
find students -type d -name ".git" -exec stat -c "%n %y" {} \; | head -5

echo "=== 프로세스 상태 ==="
ps aux | grep -E "(uvicorn|python.*scheduler)" | grep -v grep

echo "=== 메모리 사용량 ==="
ps -o pid,ppid,cmd,%mem,%cpu --sort=-%mem | head -10
```

---

## 주요 고려사항

### 1. 필수 구현 요소
- 모든 외부 작업에 타임아웃 설정 (git, 채점)
- 누락/손상된 저장소의 우아한 처리
- 각 학생 상태에 대한 명확한 시각적 피드백
- 일시적 장애로부터 자동 복구

### 2. 피해야 할 사항
- 코드에 민감한 데이터 (비밀번호, 토큰) 저장
- 샌드박싱 없이 신뢰할 수 없는 코드 실행
- 비동기 컨텍스트에서 블로킹 작업
- 로그 누적으로 인한 과도한 메모리 사용

### 3. 예외 상황 처리
- 학생이 저장소를 삭제한 경우
- 저장소가 비공개로 변경된 경우
- 학생 코드의 무한 루프
- 잘못된 형식의 roster.csv 항목
- git 작업 중 네트워크 중단
- 디스크 공간 부족