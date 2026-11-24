"""
compare.py : 선수 비교 화면

[이 화면은 어떤 과정이야?]
1) 선수 두 명을 고른다.
2) 기록을 나란히 표로 보여 준다.
3) 레이더(거미줄) 차트로 두 선수의 강점을 한눈에 비교한다.
   항목마다 단위가 달라서(골 수, %, 점수) 전체 선수 중 최고 기록을 100으로 맞춰서 그린다.
4) 두 선수가 같은 팀이었을 때 / 상대 팀이었을 때 전적을 보여 준다.
"""

import plotly.graph_objects as go
import streamlit as st

import data
import stats

st.title("⚔️ 선수 비교")

players, matches = data.load("players"), data.load("matches")
goals, ratings = data.load("goals"), data.load("ratings")
if len(players) < 2:
    st.info("선수가 2명 이상 있어야 비교할 수 있어요.")
    st.stop()

names = sorted(players["name"].tolist())
c1, c2 = st.columns(2)
p1 = c1.selectbox("선수 1", names, index=0)
p2 = c2.selectbox("선수 2", names, index=1)
if p1 == p2:
    st.warning("서로 다른 두 선수를 골라 주세요.")
    st.stop()

table = stats.player_stats(players, matches, goals, ratings)
a = table[table["이름"] == p1].iloc[0]
b = table[table["이름"] == p2].iloc[0]

items = ["출전", "골", "도움", "경기당 공격포인트", "승률(%)", "평균평점", "MOM", "클린시트"]
st.dataframe(
    {"항목": items, p1: [a[i] for i in items], p2: [b[i] for i in items]},
    hide_index=True, width="stretch",
)

radar = ["골", "도움", "경기당 공격포인트", "승률(%)", "평균평점", "출전"]
best = {k: max(float(table[k].max()), 1e-9) for k in radar}
fig = go.Figure()
for row, color in ((a, "#1f6feb"), (b, "#d1242f")):
    values = [round(float(row[k]) / best[k] * 100, 1) for k in radar]
    fig.add_trace(go.Scatterpolar(r=values + values[:1], theta=radar + radar[:1], fill="toself",
                                  name=row["이름"], line=dict(color=color)))
fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100], showticklabels=False)),
                  height=380, margin=dict(t=20, b=20), legend=dict(orientation="h"))
st.plotly_chart(fig, width="stretch")
st.caption("전체 선수 중 최고 기록을 100으로 놓고 그린 그래프예요.")

# 같은 팀 / 상대 팀 전적
same = {"승": 0, "무": 0, "패": 0}
versus = {p1: 0, "무": 0, p2: 0}
for _, m in stats.finished_matches(matches).iterrows():
    r1, r2 = stats.player_result(m, p1), stats.player_result(m, p2)
    if r1 is None or r2 is None:
        continue
    if r1[0] == r2[0]:
        same[r1[1]] += 1
    elif r1[1] == "승":
        versus[p1] += 1
    elif r1[1] == "패":
        versus[p2] += 1
    else:
        versus["무"] += 1

c3, c4 = st.columns(2)
c3.markdown("**🤝 같은 팀일 때**")
c3.write(f"{same['승']}승 {same['무']}무 {same['패']}패")
c4.markdown("**⚔️ 맞대결**")
c4.write(f"{p1} {versus[p1]}승 · {versus['무']}무 · {p2} {versus[p2]}승")
