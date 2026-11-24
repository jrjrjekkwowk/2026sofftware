"""
rankings.py : 순위표 화면

[이 화면은 어떤 과정이야?]
1) stats.player_stats()로 선수별 기록을 계산한다.
2) 포지션(공격/미드/수비/골키퍼)으로 거를 수 있다.
3) 탭마다 기준(골, 도움, 공격포인트, 승률, 평점, MOM, 클린시트)을 바꿔서 순위를 보여 준다.
4) 맨 아래에 끝난 경기 결과(몇 분에 누가 넣었는지, MOM)를 보여 준다.
"""

import plotly.express as px
import streamlit as st

import data
import formations as fm
import stats

st.title("🏆 순위표")

players, matches = data.load("players"), data.load("matches")
goals, ratings = data.load("goals"), data.load("ratings")
table = stats.player_stats(players, matches, goals, ratings)
done = stats.finished_matches(matches)

if done.empty:
    st.info("아직 끝난 경기가 없어요. '실시간 경기 기록'에서 첫 경기를 기록해 보세요.")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("끝난 경기", f"{len(done)}경기")
c2.metric("총 골", f"{int(done['score_a'].sum() + done['score_b'].sum())}골")
c3.metric("참가 선수", f"{int((table['출전'] > 0).sum())}명")

group = st.segmented_control("포지션", ["전체", "공격", "미드", "수비", "골키퍼"], default="전체")
code = {"공격": "FW", "미드": "MF", "수비": "DF", "골키퍼": "GK"}.get(group or "전체")
if code:
    table = table[table["포지션"].apply(fm.category) == code]


def show(by, cols, chart=False, min_apps=0, empty="아직 기록이 없어요."):
    top = stats.ranking(table, by, min_apps=min_apps)
    if top.empty:
        st.caption(empty)
        return
    if chart:
        fig = px.bar(top, x="이름", y=by, text=by, color_discrete_sequence=["#198754"])
        fig.update_layout(height=280, margin=dict(t=10, b=10), xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig, width="stretch")
    st.dataframe(top[["순위", "이름"] + cols], hide_index=True, width="stretch")


tabs = st.tabs(["득점왕", "도움왕", "공격포인트", "승률", "평점", "MOM", "클린시트"])
with tabs[0]:
    show("골", ["학년", "골", "출전"], chart=True, empty="아직 골 기록이 없어요.")
with tabs[1]:
    show("도움", ["학년", "도움", "출전"], chart=True, empty="아직 도움 기록이 없어요.")
with tabs[2]:
    show("공격포인트", ["공격포인트", "골", "도움", "경기당 공격포인트", "출전"])
with tabs[3]:
    # 1경기 뛰고 1승 = 100% 같은 왜곡을 막으려고 최소 출전 수 조건을 둔다
    n = st.slider("최소 출전 경기 수", 1, 10, 3, key="min_win")
    show("승률(%)", ["승률(%)", "승", "무", "패", "출전"], min_apps=n,
         empty=f"{n}경기 이상 뛰고 1승 이상 한 선수가 아직 없어요.")
with tabs[4]:
    n = st.slider("최소 출전 경기 수", 1, 10, 1, key="min_rating")
    show("평균평점", ["평균평점", "MOM", "출전"], chart=True, min_apps=n,
         empty="아직 평점이 없어요. '경기 평점 · MOM'에서 매겨 보세요.")
with tabs[5]:
    show("MOM", ["MOM", "평균평점", "출전"], empty="아직 MOM이 없어요.")
with tabs[6]:
    st.caption("전술판에서 GK 자리에 들어간 선수의 팀이 무실점이면 클린시트 1회")
    show("클린시트", ["클린시트", "출전"], empty="아직 클린시트가 없어요.")

st.subheader("경기 결과")
for _, m in done.sort_values("match_id", ascending=False).iterrows():
    mom = stats.mom_of(ratings, m["match_id"])
    title = f"#{m['match_id']}  {m['date']}   {m['team_a']} {m['score_a']} : {m['score_b']} {m['team_b']}"
    with st.expander(title + (f"   🏅 {mom}" if mom else "")):
        g = goals[goals["match_id"] == m["match_id"]]
        for _, row in g.iterrows():
            team = m["team_a"] if row["team"] == "A" else m["team_b"]
            assist = f" (도움 {row['assist']})" if row["assist"] else ""
            kind = f" · {row['goal_type']}" if row["goal_type"] and row["goal_type"] != "일반" else ""
            when = f"{row['minute']}'" if row["minute"] else row["time"]
            st.write(f"⚽ {when} {team} · {row['scorer']}{assist}{kind}")
        st.caption(f"{m['team_a']} {m['formation_a']}: {', '.join(data.split_names(m['players_a']))}")
        st.caption(f"{m['team_b']} {m['formation_b']}: {', '.join(data.split_names(m['players_b']))}")
