# ⚽ 학교 전용 풋몹

우리 학교 주말 축구 경기를 실시간으로 기록하고, 순위표와 선수 프로필로 보여 주는 Streamlit 웹앱.

## 파일 구조 (어떤 파일이 무슨 일을 하는지)

| 파일 | 하는 일 |
|---|---|
| `app.py` | 앱의 시작점. 메뉴(페이지 목록)를 만든다 |
| `data.py` | 데이터 저장·불러오기 (선수, 경기, 득점 세 개의 표) |
| `stats.py` | 기록 계산 (출전, 골, 도움, 승률, 순위) |
| `home.py` | 홈 화면 (LIVE 경기, 최근 경기, 득점 TOP 3) |
| `live.py` | **핵심 기능 1** 실시간 경기 기록 |
| `rankings.py` | **핵심 기능 2** 순위표 (득점왕, 도움왕, 공격포인트, 승률) |
| `player_profile.py` | **핵심 기능 3** 선수 프로필 (누적 기록, 누적 골 그래프) |
| `players.py` | 선수 등록 |
| `requirements.txt` | Streamlit Cloud가 설치할 라이브러리 목록 |
| `.streamlit/config.toml` | 앱 색깔(초록) 설정 |

---

## 과정 1. GitHub에 저장소 만들기

**이건 어떤 과정이야?** 코드를 올려 둘 온라인 폴더(저장소, repository)를 만드는 단계. Streamlit Cloud는 이 저장소에 있는 코드를 가져가서 앱을 실행한다.

1. github.com 로그인
2. 오른쪽 위 `+` → `New repository`
3. Repository name: `school-fotmob` (원하는 영어 이름)
4. **Public** 선택 (무료 배포는 공개 저장소여야 편하다)
5. `Create repository`

## 과정 2. 코드 파일 올리기

**이건 어떤 과정이야?** 내 컴퓨터에 있는 코드를 저장소에 올리고 '커밋(commit)'하는 단계. 커밋은 "이 시점의 코드를 저장한다"는 기록이라서, 나중에 문제가 생기면 이전 커밋으로 되돌릴 수 있다. (계획서 5번에 쓴 '이전 버전으로 되돌리기'가 바로 이것)

1. 저장소 첫 화면의 `uploading an existing file` 링크 클릭
2. 받은 파일 10개(`.py` 8개, `requirements.txt`, `README.md`)를 한꺼번에 끌어다 놓기
3. 아래 `Commit changes` 클릭

> `.streamlit` 폴더는 이름이 점(.)으로 시작해서 맥 Finder에서 안 보일 수 있다. 안 올라갔다면
> `Add file` → `Create new file` → 이름 칸에 `.streamlit/config.toml` 입력 → 내용에 아래 두 줄 → `Commit changes`
> ```
> [theme]
> primaryColor = "#198754"
> ```
> (안 올려도 앱은 돌아간다. 버튼 색이 빨간색이 될 뿐)

## 과정 3. Streamlit Community Cloud로 배포하기

**이건 어떤 과정이야?** GitHub에 있는 코드를 인터넷 서버에서 실행시켜서 누구나 링크로 접속할 수 있게 만드는 단계 (배포, deploy).

1. share.streamlit.io 접속 → GitHub 계정으로 로그인 (처음이면 GitHub 접근 권한 허용)
2. `Create app` → GitHub에서 배포하기 선택
3. Repository: `내아이디/school-fotmob`, Branch: `main`, Main file path: `app.py`
4. App URL을 원하는 주소로 정하고 `Deploy`
5. 몇 분 기다리면 앱 주소가 생긴다 → 휴대폰으로도 열어 보기

## 과정 4. 코드 고치기

**이건 어떤 과정이야?** GitHub에서 파일을 고치고 커밋하면 Streamlit Cloud가 자동으로 새 코드를 반영한다.

1. GitHub 저장소에서 고칠 파일 클릭 → 연필 아이콘(Edit)
2. 수정 → `Commit changes` (커밋 메시지에 뭘 고쳤는지 적기 → 제작일지 쓸 때도 도움)
3. 앱 새로고침해서 확인

## ⚠️ 꼭 알아 둘 점: 데이터 초기화

지금 버전은 데이터를 서버 안의 CSV 파일에 저장한다. Streamlit Cloud는 **코드를 고쳐서 앱이 다시 시작되거나, 오래 접속이 없어서 잠들었다가 깨어날 때** 이 파일이 지워질 수 있다.

그래서 다음 단계에서 저장 위치를 구글 스프레드시트로 바꿀 예정이다. 그때는 `data.py`만 고치면 된다. 그 전까지는 코드 수정을 다 끝낸 뒤 실제 경기를 기록하는 게 안전하다.

## 내 컴퓨터에서 실행해 보기 (선택)

```
pip install -r requirements.txt
streamlit run app.py
```

## AI 사용 기록

- Claude: 기능 구성 조언, 코드 작성 도움, 오류 해결
