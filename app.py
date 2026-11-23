"""
app.py : 앱의 시작점 (Streamlit Cloud에 배포할 때 'Main file'로 지정하는 파일)

[이 파일은 어떤 과정이야?]
화면(페이지)을 등록하고 왼쪽 메뉴를 만드는 '안내 데스크' 역할만 한다.
실제 화면 내용은 home.py, live.py 같은 화면 파일들에 나눠서 들어 있다.

실행 방법(내 컴퓨터에서): 터미널에서  streamlit run app.py
"""

import streamlit as st

APP_NAME = "학교 전용 풋몹"  # 서비스 이름이 정해지면 여기만 바꾸면 된다

st.set_page_config(page_title=APP_NAME, page_icon="⚽", layout="centered")

pages = [
    st.Page("home.py", title="홈", icon="🏠", default=True),
    st.Page("live.py", title="실시간 경기 기록", icon="⏱️"),
    st.Page("rankings.py", title="순위표", icon="🏆"),
    st.Page("player_profile.py", title="선수 프로필", icon="👤"),
    st.Page("players.py", title="선수 등록", icon="📝"),
]

st.sidebar.markdown(f"### ⚽ {APP_NAME}")
st.navigation(pages).run()
