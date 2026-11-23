"""
rankings.py : 순위표 화면

[이 화면은 어떤 과정이야?]
1) stats.player_stats()로 선수별 기록을 계산한다.
2) 탭마다 기준(골, 도움, 공격포인트, 승률)을 바꿔서 순위를 보여 준다.
3) 득점 순위는 Plotly 막대그래프로도 보여 준다.
4) 맨 아래에 지금까지 끝난 경기 결과 목록을 보여 준다.
"""

import plotly.express as px
import streamlit as st

import data
import stats

st.title("🏆 순위표")

players, matches, goals = data.load("players"), data.load("matches"), data.load("goals")
table = stats.player_stats(players, matches, goals)
done = stats.finished_matches(matches)

if done.empty:
    st.info("아직 끝난 경기가 없어요. '실시간 경기 기록'에서 첫 경기를 기록해 보세요.")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("끝난 경기", f"{len(done)}경기")
c2.metric("총 골", f"{int(done['score_a'].sum() + done['score_b'].sum())}골")
c3.metric("참가 선수", f"{int((table['출전'] > 0).sum())}명")

tab_goal, tab_assist, tab_point, tab_win = st.tabs(["득점왕", "도움왕", "공격포인트", "승률"])

with tab_goal:
    top = stats.ranking(table, "골")
    if top.empty:
        st.caption("아직 골 기록이 없어요.")
    else:
        fig = px.bar(top, x="이름", y="골", text="골", color_discrete_sequence=["#198754"])
        fig.update_layout(height=300, margin=dict(t=10, b=10), xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig, width="stretch")
        st.dataframe(top[["순위", "이름", "학년", "골", "출전"]], hide_index=True,
                     width="stretch")

with tab_assist:
    top = stats.ranking(table, "도움")
    if top.empty:
        st.caption("아직 도움 기록이 없어요.")
    else:
        st.dataframe(top[["순위", "이름", "학년", "도움", "출전"]], hide_index=True,
                     width="stretch")

with tab_point:
    top = stats.ranking(table, "공격포인트")
    if top.empty:
        st.caption("아직 공격포인트 기록이 없어요.")
    else:
        st.dataframe(top[["순위", "이름", "학년", "공격포인트", "골", "도움", "출전"]],
                     hide_index=True, width="stretch")

with tab_win:
    # 1경기 뛰고 1승 = 100% 같은 왜곡을 막으려고 최소 출전 수 조건을 둔다
    min_apps = st.slider("최소 출전 경기 수", 1, 10, 3)
    top = stats.ranking(table, "승률(%)", min_apps=min_apps)
    if top.empty:
        st.caption(f"{min_apps}경기 이상 뛰고 1승 이상 한 선수가 아직 없어요.")
    else:
        st.dataframe(top[["순위", "이름", "승률(%)", "승", "무", "패", "출전"]],
                     hide_index=True, width="stretch")

st.subheader("경기 결과")
for _, m in done.sort_values("match_id", ascending=False).iterrows():
    with st.expander(f"#{m['match_id']}  {m['date']}   {m['team_a']} {m['score_a']} : "
                     f"{m['score_b']} {m['team_b']}"):
        g = goals[goals["match_id"] == m["match_id"]]
        for _, row in g.iterrows():
            team = m["team_a"] if row["team"] == "A" else m["team_b"]
            assist = f" (도움 {row['assist']})" if row["assist"] else ""
            st.write(f"⚽ {row['time']} {team} · {row['scorer']}{assist}")
        st.caption(f"{m['team_a']}: {', '.join(data.split_names(m['players_a']))}")
        st.caption(f"{m['team_b']}: {', '.join(data.split_names(m['players_b']))}")
