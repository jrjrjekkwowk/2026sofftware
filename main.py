import streamlit as st
import time
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="학생용 학습 타이머",
    page_icon="⏱️",
    layout="centered"
)

# 세션 상태 초기화
if "running" not in st.session_state:
    st.session_state.running = False
if "elapsed_seconds" not in st.session_state:
    st.session_state.elapsed_seconds = 0
if "last_tick" not in st.session_state:
    st.session_state.last_tick = None
if "records" not in st.session_state:
    st.session_state.records = []

# 타이머 업데이트 함수
def update_timer():
    if st.session_state.running and st.session_state.last_tick:
        now = time.time()
        st.session_state.elapsed_seconds += int(now - st.session_state.last_tick)
        st.session_state.last_tick = now

update_timer()

# 타이틀 및 타이머 표시
st.title("⏱️ 학생용 공부 학습 타이머")
st.write("과목을 선택하고 공부 시간을 기록해보세요!")

# 과목 선택
subject = st.selectbox(
    "공부할 과목을 선택하세요:",
    ["국어", "수학", "영어", "과학", "사회", "기타"]
)

# 시간 포맷팅 (HH:MM:SS)
hours = st.session_state.elapsed_seconds // 3600
minutes = (st.session_state.elapsed_seconds % 3600) // 60
seconds = st.session_state.elapsed_seconds % 60
time_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

st.markdown(f"<h1 style='text-align: center; font-size: 80px; color: #4CAF50;'>{time_display}</h1>", unsafe_allow_html=True)

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

# 과목별 학습 기록 표시
st.subheader("📊 과목별 공부 기록")

if st.session_state.records:
    df = pd.DataFrame(st.session_state.records)
    st.dataframe(df[["날짜", "과목", "공부 시간"]], use_container_width=True)
    
    # 총 공부 시간 요약
    total_sec = sum(r["총 초"] for r in st.session_state.records)
    t_h = total_sec // 3600
    t_m = (total_sec % 3600) // 60
    t_s = total_sec % 60
    st.info(f"💡 오늘 총 공부 시간: **{t_h}시간 {t_m}분 {t_s}초**")
else:
    st.info("아직 기록된 공부 시간이 없습니다. 타이머를 시작해보세요!")
