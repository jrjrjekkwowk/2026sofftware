# 📚 Streamlit 학생용 학습 올인원 앱 개발 대화록

---

## 📌 1. 프로젝트 개요 및 목적
* **목적**: Streamlit Cloud에서 실행할 수 있는 학생용 학습 타이머 및 학습 관리 통합 웹 앱 개발
* **주요 기능**: 
  1. 과목별 공부 타이머 (시작/일시정지/초기화 및 기록 누적)
  2. 과목별 오늘 할 일 관리 (추가/체크/삭제)
  3. KPT 기반 공부 회고 및 만족도 기록 (히스토리 모아보기)

---

## 💬 2. 대화 세션 및 진행 과정

### 📍 [1단계] 공부 타이머 기본 앱 구현
* **요청**: 학생용 학습 타이머 (시작, 일시정지, 초기화, 과목별 기록), `main.py` 및 `requirements.txt` 생성.
* **구현 내용**:
  * `st.session_state`를 이용한 시간 추적 및 데이터 보존.
  * 과목(국어, 수학, 영어, 과학, 사회, 기타) 선택 기능 및 pandas DataFrame을 활용한 총 공부 시간 계산.

---

### 📍 [2단계] 다중 메뉴 구조 확장
* **요청**: `공부 타이머`, `오늘 할 일`, `공부 회고` 3가지 메뉴 추가.
* **구현 내용**:
  * 사이드바 라디오 버튼 (`st.sidebar.radio`) 기반 navigation 구성.
  * 타이머 기능 이관 및 나머지 메뉴 뼈대 생성.

---

### 📍 [3단계] '오늘 할 일' 메뉴 구현
* **요청**: 과목 및 할 일 입력 후 다중 추가, 전체 소스 코드 요구.
* **구현 내용**:
  * `st.form(clear_on_submit=True)`을 활용하여 입력 후 입력창 자동 초기화.
  * 체크박스를 통한 완료 상태(취소선 표시) 조작 및 ❌ 삭제 버튼 구현.

---

### 📍 [4단계] '공부 회고' 메뉴 기획 및 최종 완성
* **기획 논의**: 학습 효율 극대화를 위한 **KPT (Keep / Problem / Try) + 5단계 만족도 평가 + 히스토리 모아보기** 조합 선정.
* **구현 내용**:
  * `reflection_list` 세션 관리를 통해 데이터 보존.
  * `st.expander`와 `reversed()`를 사용해 최신 작성순으로 작성 내역 모아보기 기능 완성.

---

## 📂 3. 프로젝트 최종 소스 코드 (`main.py`)

```python
import streamlit as st
import time
import pandas as pd
from datetime import datetime

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="학생용 학습 올인원 앱",
    page_icon="📚",
    layout="centered"
)

# 2. 세션 상태 (Session State) 초기화
if "running" not in st.session_state:
    st.session_state.running = False
if "elapsed_seconds" not in st.session_state:
    st.session_state.elapsed_seconds = 0
if "last_tick" not in st.session_state:
    st.session_state.last_tick = None
if "records" not in st.session_state:
    st.session_state.records = []
if "todo_list" not in st.session_state:
    st.session_state.todo_list = []
if "reflection_list" not in st.session_state:
    st.session_state.reflection_list = []

# 타이머 실시간 업데이트 함수
def update_timer():
    if st.session_state.running and st.session_state.last_tick:
        now = time.time()
        st.session_state.elapsed_seconds += int(now - st.session_state.last_tick)
        st.session_state.last_tick = now

update_timer()

# 3. 사이드바 메뉴 생성
st.sidebar.title("📌 메뉴")
menu = st.sidebar.radio(
    "원하는 메뉴를 선택하세요:",
    ["⏱️ 공부 타이머", "✅ 오늘 할 일", "📝 공부 회고"]
)

# 4. 메뉴별 페이지 구현
# ---------------------------------------------------------
# [메뉴 1] 공부 타이머
# ---------------------------------------------------------
if menu == "⏱️ 공부 타이머":
    st.title("⏱️ 학생용 공부 학습 타이머")
    st.write("과목을 선택하고 공부 시간을 기록해보세요!")

    subject = st.selectbox(
        "공부할 과목을 선택하세요:",
        ["국어", "수학", "영어", "과학", "사회", "기타"],
        key="timer_subject"
    )

    hours = st.session_state.elapsed_seconds // 3600
    minutes = (st.session_state.elapsed_seconds % 3600) // 60
    seconds = st.session_state.elapsed_seconds % 60
    time_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    st.markdown(
        f"<h1 style='text-align: center; font-size: 80px; color: #4CAF50;'>{time_display}</h1>",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("▶️ 시작", use_container_width=True):
            if not st.session_state.running:
                st.session_state.running = True
                st.session_state.last_tick = time.time()
                st.rerun()

    with col2:
        if st.button("⏸️ 일시정지", use_container_width=True):
            if st.session_state.running:
                st.session_state.running = False
                st.session_state.last_tick = None
                st.rerun()

    with col3:
        if st.button("⏹️ 저장 및 초기화", use_container_width=True):
            if st.session_state.elapsed_seconds > 0:
                new_record = {
                    "날짜": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "과목": subject,
                    "공부 시간": f"{hours:02d}시간 {minutes:02d}분 {seconds:02d}초",
                    "총 초": st.session_state.elapsed_seconds
                }
                st.session_state.records.append(new_record)
            
            st.session_state.running = False
            st.session_state.elapsed_seconds = 0
            st.session_state.last_tick = None
            st.rerun()

    st.divider()
    st.subheader("📊 과목별 공부 기록")

    if st.session_state.records:
        df = pd.DataFrame(st.session_state.records)
        st.dataframe(df[["날짜", "과목", "공부 시간"]], use_container_width=True)
        
        total_sec = sum(r["총 초"] for r in st.session_state.records)
        t_h = total_sec // 3600
        t_m = (total_sec % 3600) // 60
        t_s = total_sec % 60
        st.info(f"💡 오늘 총 공부 시간: **{t_h}시간 {t_m}분 {t_s}초**")
    else:
        st.info("아직 기록된 공부 시간이 없습니다. 타이머를 시작해보세요!")

# ---------------------------------------------------------
# [메뉴 2] 오늘 할 일
# ---------------------------------------------------------
elif menu == "✅ 오늘 할 일":
    st.title("✅ 오늘 할 일")
    st.write("오늘 달성할 목표와 할 일 목록을 작성해보세요!")

    with st.form("todo_form", clear_on_submit=True):
        col_subject, col_task = st.columns([1, 2])
        
        with col_subject:
            todo_subject = st.selectbox(
                "과목 선택",
                ["국어", "수학", "영어", "과학", "사회", "기타"]
            )
        
        with col_task:
            todo_text = st.text_input("할 일 내용을 입력하세요", placeholder="예: 25페이지까지 문제 풀기")
        
        submit_button = st.form_submit_button("➕ 할 일 추가", use_container_width=True)
        
        if submit_button:
            if todo_text.strip() != "":
                st.session_state.todo_list.append({
                    "subject": todo_subject,
                    "task": todo_text,
                    "done": False
                })
                st.toast("새로운 할 일이 추가되었습니다! 🎉")
                st.rerun()
            else:
                st.warning("할 일 내용을 입력해주세요!")

    st.divider()
    st.subheader("📋 나의 할 일 목록")

    if st.session_state.todo_list:
        for idx, item in enumerate(st.session_state.todo_list):
            col_check, col_content, col_del = st.columns([0.5, 3, 0.5])
            
            with col_check:
                is_done = st.checkbox("", value=item["done"], key=f"todo_check_{idx}")
                if is_done != item["done"]:
                    st.session_state.todo_list[idx]["done"] = is_done
                    st.rerun()
            
            with col_content:
                if item["done"]:
                    st.markdown(f"~~**[{item['subject']}]** {item['task']}~~")
                else:
                    st.markdown(f"**[{item['subject']}]** {item['task']}")
            
            with col_del:
                if st.button("❌", key=f"todo_del_{idx}"):
                    st.session_state.todo_list.pop(idx)
                    st.rerun()
    else:
        st.info("등록된 할 일이 없습니다. 상단에서 새로운 할 일을 추가해보세요!")

# ---------------------------------------------------------
# [메뉴 3] 공부 회고
# ---------------------------------------------------------
elif menu == "📝 공부 회고":
    st.title("📝 KPT 공부 회고")
    st.write("오늘 하루 학습을 돌아보고 더 나은 내일을 위한 피드백을 남겨보세요!")

    with st.form("reflection_form", clear_on_submit=True):
        st.subheader("1️⃣ 오늘 공부 만족도")
        satisfaction = st.radio(
            "오늘 공부에 얼마나 만족하시나요?",
            ["⭐⭐⭐⭐⭐ (매우 만족)", "⭐⭐⭐⭐ (만족)", "⭐⭐⭐ (보통)", "⭐⭐ (아쉬움)", "⭐ (매우 아쉬움)"],
            horizontal=True
        )

        st.subheader("2️⃣ KPT 회고 작성")
        keep_text = st.text_area(
            "🟢 Keep (잘한 점 / 지속할 점)",
            placeholder="예: 시간 타이머를 지켜서 집중력을 잘 유지했다, 수학 20문제를 끝까지 풀었다."
        )
        problem_text = st.text_area(
            "🔴 Problem (아쉬운 점 / 방해 요소)",
            placeholder="예: 중간에 유튜브를 보느라 30분을 낭비했다, 졸음이 많이 왔다."
        )
        try_text = st.text_area(
            "🔵 Try (내일 시도할 점 / 개선책)",
            placeholder="예: 공부할 때는 스마트폰을 다른 방에 두기, 50분 공부 후 10분 스트레칭하기."
        )

        submit_ref = st.form_submit_button("💾 회고 저장하기", use_container_width=True)

        if submit_ref:
            if keep_text.strip() or problem_text.strip() or try_text.strip():
                st.session_state.reflection_list.append({
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "satisfaction": satisfaction,
                    "keep": keep_text,
                    "problem": problem_text,
                    "try": try_text
                })
                st.toast("오늘의 회고가 성공적으로 저장되었습니다! 👍")
                st.rerun()
            else:
                st.warning("최소 한 가지 항목 이상의 내용을 입력해주세요!")

    st.divider()
    st.subheader("📜 지나온 회고 기록")

    if st.session_state.reflection_list:
        for idx, ref in enumerate(reversed(st.session_state.reflection_list)):
            with st.expander(f"📅 {ref['date']} | 만족도: {ref['satisfaction']}"):
                st.markdown(f"**🟢 Keep (잘한 점)**\n{ref['keep'] if ref['keep'] else '작성 내용 없음'}")
                st.markdown(f"**🔴 Problem (아쉬운 점)**\n{ref['problem'] if ref['problem'] else '작성 내용 없음'}")
                st.markdown(f"**🔵 Try (시도할 점)**\n{ref['try'] if ref['try'] else '작성 내용 없음'}")
    else:
        st.info("아직 작성된 회고가 없습니다. 오늘 공부를 마치고 첫 회고를 남겨보세요!")
```

---

## 📦 4. 의존성 패키지 명세 (`requirements.txt`)

```text
streamlit
pandas
```