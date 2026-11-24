"""
home.py : 홈 화면

[이 화면은 어떤 과정이야?]
앱을 열자마자 보이는 첫 화면. 풋몹 첫 화면처럼
진행 중인 경기, 최근 결과(MOM 포함), 득점 TOP 3, 이달의 선수를 한눈에 보여 준다.
"""

from datetime import datetime

import streamlit as st

import data
import stats

st.title("⚽ 킥로그 KickLog")
st.caption("우리 학교 전용 풋몹 · 주말 축구, 이제 기록으로 남기자")

# ---- 개발자 후원 버튼 (홈 화면 맨 위에 크게) ----
# 계좌는 코드에 적지 않고 Streamlit Cloud의 Secrets(비밀 설정)에 넣는다 → GitHub에 공개되지 않는다
try:
    DONATE_BANK = st.secrets.get("DONATE_BANK", "")
    DONATE_ACCOUNT = st.secrets.get("DONATE_ACCOUNT", "")
except Exception:  # Secrets 설정이 아예 없을 때도 앱이 멈추지 않게
    DONATE_BANK = DONATE_ACCOUNT = ""


@st.dialog("💸 개발자 서버비 내주기")
def donate_popup():
    st.write("킥로그가 도움이 됐다면 서버비를 보태 주세요. 보내 주신 마음은 서버 유지와 새 기능 개발에 쓸게요.")
    if DONATE_ACCOUNT:
        st.caption(DONATE_BANK)
        st.code(DONATE_ACCOUNT, language=None)  # 오른쪽 복사 아이콘으로 계좌번호 복사
        st.caption("👆 오른쪽 아이콘을 누르면 계좌번호가 복사돼요")
    else:
        st.info("후원 계좌는 준비 중이에요. 마음만으로도 감사해요 🙏")


st.markdown("""<style>
.st-key-donate button {
    padding: 1rem 0; border: none; border-radius: 14px;
    background: linear-gradient(90deg, #198754, #20c997); color: white !important;
}
.st-key-donate p { font-size: 1.35rem; font-weight: 800; }
</style>""", unsafe_allow_html=True)
with st.container(key="donate"):
    if st.button("💸 개발자 서버비 내주기", width="stretch"):
        donate_popup()
st.caption("킥로그는 학생 개발자가 직접 만들고 운영해요. 후원금은 서버비와 새 기능 개발에 쓰여요.")

players, matches = data.load("players"), data.load("matches")
goals, ratings = data.load("goals"), data.load("ratings")

live = data.get_live_match()
if live is not None:
    minute = data.minutes_played(live["kickoff"])
    st.error(f"🔴 LIVE {minute}'  {live['team_a']} {live['score_a']} : {live['score_b']} {live['team_b']}")
    st.page_link("live.py", label="경기 기록하러 가기", icon="⏱️")

done = stats.finished_matches(matches)
c1, c2, c3 = st.columns(3)
c1.metric("등록 선수", f"{len(players)}명")
c2.metric("끝난 경기", f"{len(done)}경기")
c3.metric("총 골", f"{int(done['score_a'].sum() + done['score_b'].sum()) if not done.empty else 0}골")

st.subheader("최근 경기")
if done.empty:
    st.caption("아직 끝난 경기가 없어요.")
else:
    for _, m in done.sort_values("match_id", ascending=False).head(3).iterrows():
        mom = stats.mom_of(ratings, m["match_id"])
        st.write(f"**{m['team_a']}** {m['score_a']} : {m['score_b']} **{m['team_b']}**  ·  {m['date']}"
                 + (f"  ·  🏅 {mom}" if mom else ""))

table = stats.player_stats(players, matches, goals, ratings)

st.subheader("득점 TOP 3")
top = stats.ranking(table, "골", top=3)
if top.empty:
    st.caption("아직 골 기록이 없어요.")
else:
    medals = ["🥇", "🥈", "🥉"]
    for i, (_, r) in enumerate(top.iterrows()):
        st.write(f"{medals[i]} {r['이름']} ({r['학년']}) · {r['골']}골")

# 이달의 선수: 이번 달 경기만 따로 계산해서 공격포인트 1위
this_month = datetime.now().strftime("%Y-%m")
month = stats.player_stats(players, matches[matches["date"].str.startswith(this_month)], goals, ratings)
best = stats.ranking(month, "공격포인트", top=1)
st.subheader(f"이달의 선수 ({datetime.now().month}월)")
if best.empty:
    st.caption("이번 달 기록이 아직 없어요.")
else:
    b = best.iloc[0]
    st.success(f"🌟 {b['이름']}  ·  {b['골']}골 {b['도움']}도움 ({b['출전']}경기)")

if players.empty:
    st.info("처음이라면 왼쪽 메뉴의 '선수 등록'부터 시작하세요.")
