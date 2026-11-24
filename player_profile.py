"""
player_profile.py : 선수 프로필 화면

[이 화면은 어떤 과정이야?]
1) 선수를 고르면 그 선수의 누적 기록(출전, 골, 도움, 승률, 평점, MOM, 클린시트)을 숫자 카드로 보여 준다.
2) '누적 골 그래프'와 '경기별 평점 그래프'로 성장 과정을 보여 준다.
3) 골 유형(헤더, 중거리 등) 비율과 '찰떡 파트너'(내 골을 가장 많이 도와준 친구)를 보여 준다.
4) 그 선수가 뛴 경기별 결과를 표로 보여 준다.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

import data
import stats

st.title("👤 선수 프로필")

players, matches = data.load("players"), data.load("matches")
goals, ratings = data.load("goals"), data.load("ratings")
if players.empty:
    st.info("등록된 선수가 없어요.")
    st.stop()

name = st.selectbox("선수 선택", sorted(players["name"].tolist()))
info = players[players["name"] == name].iloc[0]
table = stats.player_stats(players, matches, goals, ratings)
me = table[table["이름"] == name].iloc[0]

st.markdown(f"## {name}")
st.caption(f"{info['grade']}학년 · {info['position']}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("출전", me["출전"])
c2.metric("골", me["골"])
c3.metric("도움", me["도움"])
c4.metric("승률", f"{me['승률(%)']}%")
c5, c6, c7, c8 = st.columns(4)
c5.metric("평균 평점", me["평균평점"] or "-")
c6.metric("MOM", me["MOM"])
c7.metric("클린시트", me["클린시트"])
c8.metric("실력 점수", stats.power(me))

# 경기별 기록 만들기
rows = []
for _, m in stats.finished_matches(matches).sort_values("match_id").iterrows():
    r = stats.player_result(m, name)
    if r is None:
        continue
    team, result = r
    g = goals[goals["match_id"] == m["match_id"]]
    my_r = ratings[(ratings["match_id"] == m["match_id"]) & (ratings["player"] == name)]["rating"]
    rows.append({
        "경기": f"#{m['match_id']}",
        "날짜": m["date"],
        "상대": m["team_b"] if team == "A" else m["team_a"],
        "스코어": f"{m['score_a']}:{m['score_b']}" if team == "A" else f"{m['score_b']}:{m['score_a']}",
        "결과": result,
        "골": int((g["scorer"] == name).sum()),
        "도움": int((g["assist"] == name).sum()),
        "평점": round(float(my_r.mean()), 1) if len(my_r) else None,
        "MOM": "🏅" if stats.mom_of(ratings, m["match_id"]) == name else "",
    })
history = pd.DataFrame(rows)

if history.empty:
    st.info("아직 끝난 경기에 출전한 기록이 없어요.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["누적 골", "경기별 평점", "골 분석"])
with tab1:
    history["누적 골"] = history["골"].cumsum()
    fig = px.line(history, x="경기", y="누적 골", markers=True, color_discrete_sequence=["#198754"])
    fig.update_layout(height=280, margin=dict(t=10, b=10), xaxis_title=None)
    st.plotly_chart(fig, width="stretch")
with tab2:
    rated = history.dropna(subset=["평점"])
    if rated.empty:
        st.caption("아직 받은 평점이 없어요.")
    else:
        fig = px.bar(rated, x="경기", y="평점", text="평점", color_discrete_sequence=["#f0b429"])
        fig.update_layout(height=280, margin=dict(t=10, b=10), xaxis_title=None, yaxis_range=[0, 10])
        st.plotly_chart(fig, width="stretch")
with tab3:
    my_goals = goals[(goals["scorer"] == name) & goals["match_id"].isin(stats.finished_matches(matches)["match_id"])]
    if my_goals.empty:
        st.caption("아직 골이 없어요.")
    else:
        kinds = my_goals["goal_type"].replace("", "일반").value_counts().reset_index()
        kinds.columns = ["골 유형", "골"]
        fig = px.pie(kinds, names="골 유형", values="골", hole=0.45)
        fig.update_layout(height=280, margin=dict(t=10, b=10))
        st.plotly_chart(fig, width="stretch")
        helpers = my_goals[my_goals["assist"] != ""]["assist"].value_counts()
        if not helpers.empty:
            st.write(f"🤝 찰떡 파트너: **{helpers.index[0]}** (내 골 {int(helpers.iloc[0])}개 도움)")

st.subheader("경기별 기록")
st.dataframe(history.drop(columns="누적 골").iloc[::-1], hide_index=True, width="stretch")
