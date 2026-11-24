"""
manage.py : 데이터 백업 · 복원 화면

[이 화면은 어떤 과정이야?]
Streamlit Cloud는 코드를 고치거나 앱이 오래 잠들었다 깨어나면 저장된 CSV 파일이 지워질 수 있다.
그래서 1) 코드를 고치기 전에 '백업 다운로드'로 기록을 zip 파일로 받아 두고
       2) 앱이 다시 켜지면 '백업 복원'으로 그 zip 파일을 올려서 기록을 되살린다.
경기 기록을 CSV로 따로 받아서 엑셀·구글 스프레드시트에서 열어 볼 수도 있다.
"""

from datetime import datetime

import streamlit as st

import data

st.title("💾 데이터 백업 · 복원")
st.warning("코드를 고치기 전에는 꼭 백업을 먼저 받아 두세요! 앱이 다시 시작되면 기록이 지워질 수 있어요.")

counts = {"선수": len(data.load("players")), "경기": len(data.load("matches")),
          "골": len(data.load("goals")), "평점": len(data.load("ratings"))}
cols = st.columns(4)
for col, (k, v) in zip(cols, counts.items()):
    col.metric(k, v)

st.subheader("1. 백업 다운로드")
st.download_button("📦 전체 기록 zip으로 받기", data=data.backup_zip(),
                   file_name=f"kicklog_backup_{datetime.now():%Y%m%d_%H%M}.zip",
                   mime="application/zip", type="primary", width="stretch")
with st.expander("표 하나씩 CSV로 받기 (엑셀에서 열기용)"):
    for t in data.TABLES:
        # utf-8-sig : 엑셀에서 열어도 한글이 안 깨지게 하는 저장 방식
        st.download_button(f"{t}.csv", data=data.load(t).to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"{t}.csv", mime="text/csv", key=f"dl_{t}")

st.subheader("2. 백업 복원")
up = st.file_uploader("백업 zip 파일 올리기", type="zip")
if up is not None and st.button("이 백업으로 되살리기", width="stretch"):
    try:
        restored = data.restore_zip(up.getvalue())
        st.success(f"되살렸어요: {', '.join(restored) if restored else '없음'}")
    except Exception as e:  # 잘못된 파일을 올렸을 때 앱이 멈추지 않게
        st.error(f"복원하지 못했어요. 킥로그에서 받은 백업 zip이 맞는지 확인해 주세요. ({e})")

st.subheader("3. 전체 초기화")
with st.expander("모든 기록 지우기 (되돌릴 수 없어요)"):
    sure = st.text_input("정말 지우려면 '초기화'라고 입력하세요")
    if st.button("전부 지우기", disabled=sure != "초기화"):
        data.reset_all()
        st.success("모든 기록을 지웠어요.")
        st.rerun()
