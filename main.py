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
# 2-1. 타이머 관련 상태
if "running" not in st.session_state:
    st.session_state.running = False
if "elapsed_seconds" not in st.session_state:
    st.session_state.elapsed_seconds = 0
if "last_tick" not in st.session_state:
    st.session_state.last_tick = None
if "records" not in st.session_state:
    st.session_state.records = []

# 2-2. 오늘 할 일 (To-Do) 관련 상태
if "todo_list" not in st.session_state:
    st.session_state.todo_list = []

# 2-3. 공부 회고 (Reflection) 관련 상태
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

    # 과목 선택
    subject = st.selectbox(
        "공부할 과목을 선택하세요:",
        ["국어", "수학", "영어", "과학", "사회", "기타"],
        key="timer_subject"
    )

    # 시간 포맷팅 (HH:MM:SS)
    hours = st.session_state.elapsed_seconds // 3600
    minutes = (st.session_state.elapsed_seconds % 3600) // 60
    seconds = st.session_state.elapsed_seconds % 60
    time_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    # 타이머 시계 표시
    st.markdown(
        f"<h1 style='text-align: center; font-size: 80px; color: #4CAF50;'>{time_display}</h1>",
        unsafe_allow_html=True
    )

    # 컨트롤 버튼 (시작, 일시정지, 저장 & 초기화)
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
                # 기록 저장
                new_record = {
                    "날짜": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "과목": subject,
                    "공부 시간": f"{hours:02d}시간 {minutes:02d}분 {seconds:02d}초",
                    "총 초": st.session_state.elapsed_seconds
                }
                st.session_state.records.append(new_record)
            
            # 타이머 초기화
            st.session_state.running = False
            st.session_state.elapsed_seconds = 0
            st.session_state.last_tick = None
            st.rerun()

    st.divider()

    # 과목별 학습 기록 테이블
    st.subheader("📊 과목별 공부 기록")

    if st.session_state.records:
        df = pd.DataFrame(st.session_state.records)
        st.dataframe(df[["날짜", "과목", "공부 시간"]], use_container_width=True)
        
        # 총 공부 시간 합산
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

    # 입력 폼 생성 (입력 후 제출 시 텍스트 상자 자동 초기화)
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

    # 할 일 목록 표시
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
# [메뉴 3] 공부 회고 (KPT + 만족도 + 히스토리 모아보기)
# ---------------------------------------------------------
elif menu == "📝 공부 회고":
    st.title("📝 KPT 공부 회고")
    st.write("오늘 하루 학습을 돌아보고 더 나은 내일을 위한 피드백을 남겨보세요!")

    # 1. 회고 작성 폼
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

    # 2. 히스토리 모아보기
    st.subheader("📜 지나온 회고 기록")

    if st.session_state.reflection_list:
        for idx, ref in enumerate(reversed(st.session_state.reflection_list)):
            with st.expander(f"📅 {ref['date']} | 만족도: {ref['satisfaction']}"):
                st.markdown(f"**🟢 Keep (잘한 점)**\n{ref['keep'] if ref['keep'] else '작성 내용 없음'}")
                st.markdown(f"**🔴 Problem (아쉬운 점)**\n{ref['problem'] if ref['problem'] else '작성 내용 없음'}")
                st.markdown(f"**🔵 Try (시도할 점)**\n{ref['try'] if ref['try'] else '작성 내용 없음'}")
    else:
        st.info("아직 작성된 회고가 없습니다. 오늘 공부를 마치고 첫 회고를 남겨보세요!")
