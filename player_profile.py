"""
player_profile.py : 선수 프로필 화면

[이 화면은 어떤 과정이야?]
1) 선수를 고르면 그 선수의 누적 기록(출전, 골, 도움, 승률)을 숫자 카드로 보여 준다.
2) 경기를 할수록 골이 어떻게 쌓였는지 '누적 골 그래프'로 보여 준다 (성장하는 재미).
3) 그 선수가 뛴 경기별 결과를 표로 보여 준다.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

import data
import stats

st.title("👤 선수 프로필")

players, matches, goals = data.load("players"), data.load("matches"), data.load("goals")
if players.empty:
    st.info("등록된 선수가 없어요.")
    st.stop()

name = st.selectbox("선수 선택", sorted(players["name"].tolist()))
info = players[players["name"] == name].iloc[0]
table = stats.player_stats(players, matches, goals)
me = table[table["이름"] == name].iloc[0]

st.markdown(f"## {name}")
st.caption(f"{info['grade']}학년 · {info['position']}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("출전", me["출전"])
c2.metric("골", me["골"])
c3.metric("도움", me["도움"])
c4.metric("승률", f"{me['승률(%)']}%")

# 경기별 기록 만들기
rows = []
for _, m in stats.finished_matches(matches).sort_values("match_id").iterrows():
    r = stats.player_result(m, name)
    if r is None:
        continue
    team, result = r
    g = goals[goals["match_id"] == m["match_id"]]
    rows.append({
        "경기": f"#{m['match_id']}",
        "날짜": m["date"],
        "상대": m["team_b"] if team == "A" else m["team_a"],
        "스코어": f"{m['score_a']}:{m['score_b']}" if team == "A" else f"{m['score_b']}:{m['score_a']}",
        "결과": result,
        "골": int((g["scorer"] == name).sum()),
        "도움": int((g["assist"] == name).sum()),
    })
history = pd.DataFrame(rows)

if history.empty:
    st.info("아직 끝난 경기에 출전한 기록이 없어요.")
    st.stop()

history["누적 골"] = history["골"].cumsum()
fig = px.line(history, x="경기", y="누적 골", markers=True, color_discrete_sequence=["#198754"])
fig.update_layout(height=280, margin=dict(t=10, b=10), xaxis_title=None)
st.plotly_chart(fig, width="stretch")

st.subheader("경기별 기록")
st.dataframe(history.drop(columns="누적 골").iloc[::-1], hide_index=True, width="stretch")
