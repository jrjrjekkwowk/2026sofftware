"""
live.py : 실시간 경기 기록 화면 (핵심 기능)

[이 화면은 어떤 과정이야?]
상황 A. 진행 중인 경기가 없을 때 -> 팀 이름과 참가 선수를 골라서 경기를 '시작'한다.
상황 B. 진행 중인 경기가 있을 때 -> 골이 날 때마다 득점자·도움을 고르고 '골!' 버튼을 누른다.
         버튼을 누를 때마다 골이 바로 저장되고, 스코어는 골 기록을 세서 자동으로 계산된다.
         경기가 끝나면 '경기 종료'를 눌러 결과를 확정한다.

st.rerun() : 데이터를 바꾼 뒤 화면을 처음부터 다시 그려서 최신 스코어가 보이게 하는 명령
"""

import streamlit as st

import data

st.title("⏱️ 실시간 경기 기록")

players = data.load("players")
live = data.get_live_match()

# -----------------------------------------------------------------
# 상황 A : 새 경기 시작
# -----------------------------------------------------------------
if live is None:
    if len(players) < 2:
        st.warning("선수가 2명 이상 등록되어 있어야 경기를 시작할 수 있어요. '선수 등록' 메뉴로 가 주세요.")
        st.stop()

    st.subheader("새 경기 시작")
    names = sorted(players["name"].tolist())

    col_a, col_b = st.columns(2)
    team_a = col_a.text_input("A팀 이름", value="A팀")
    team_b = col_b.text_input("B팀 이름", value="B팀")

    picked_a = col_a.multiselect("A팀 선수", names, key="pick_a", placeholder="선수 선택")
    # 같은 선수가 양쪽 팀에 들어가지 않도록 A팀에서 고른 선수는 B팀 목록에서 뺀다
    picked_b = col_b.multiselect("B팀 선수", [n for n in names if n not in picked_a], key="pick_b", placeholder="선수 선택")

    st.caption(f"A팀 {len(picked_a)}명 vs B팀 {len(picked_b)}명")

    if st.button("⚽ 경기 시작", type="primary", width="stretch"):
        if not picked_a or not picked_b:
            st.error("양 팀에 최소 1명씩은 선수를 넣어 주세요.")
        elif team_a.strip() and team_a.strip() == team_b.strip():
            st.error("두 팀 이름이 같아요. 다르게 정해 주세요.")
        else:
            data.start_match(team_a, team_b, picked_a, picked_b)
            st.rerun()
    st.stop()  # 여기서 화면 그리기를 멈춘다 (아래 상황 B 코드는 실행 안 됨)

# -----------------------------------------------------------------
# 상황 B : 경기 진행 중
# -----------------------------------------------------------------
match_id = int(live["match_id"])
players_a = data.split_names(live["players_a"])
players_b = data.split_names(live["players_b"])

# 전광판
st.markdown(
    f"""
    <div style="text-align:center; padding:12px; border-radius:12px; background:#0f5132; color:white;">
        <div style="font-size:0.9rem; opacity:0.8;">🔴 LIVE · 경기 #{match_id} · {live['date']}</div>
        <div style="font-size:2.4rem; font-weight:700;">
            {live['team_a']} &nbsp; {live['score_a']} : {live['score_b']} &nbsp; {live['team_b']}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

NO_ASSIST = "도움 없음"


def goal_panel(column, team_key: str, team_name: str, roster: list):
    """한 팀의 득점 입력 칸. A팀, B팀에 똑같이 쓰려고 함수로 만들었다."""
    with column:
        st.markdown(f"**{team_name}**")
        scorer = st.selectbox("득점", roster, key=f"scorer_{team_key}")
        assist_options = [NO_ASSIST] + [p for p in roster if p != scorer]
        assist = st.selectbox("도움", assist_options, key=f"assist_{team_key}")
        if st.button(f"⚽ {team_name} 골!", key=f"goal_{team_key}", type="primary",
                     width="stretch"):
            data.add_goal(match_id, team_key, scorer, "" if assist == NO_ASSIST else assist)
            st.toast(f"골! {scorer}" + (f" (도움 {assist})" if assist != NO_ASSIST else ""))
            st.rerun()


col_a, col_b = st.columns(2)
goal_panel(col_a, "A", live["team_a"], players_a)
goal_panel(col_b, "B", live["team_b"], players_b)

# 이번 경기 득점 기록
goals = data.load("goals")
mine = goals[goals["match_id"] == match_id]
st.subheader("득점 기록")
if mine.empty:
    st.caption("아직 골이 없어요.")
else:
    for _, g in mine.iterrows():
        team_name = live["team_a"] if g["team"] == "A" else live["team_b"]
        assist = f" · 도움 {g['assist']}" if g["assist"] else ""
        st.write(f"`{g['time']}` **{team_name}** ⚽ {g['scorer']}{assist}")

st.divider()
c1, c2 = st.columns(2)
if c1.button("↩️ 마지막 골 취소", width="stretch"):
    if data.undo_last_goal(match_id):
        st.rerun()
    else:
        st.info("취소할 골이 없어요.")

# 실수로 종료하지 않도록 체크박스를 한 번 더 확인
confirm = c2.checkbox("경기를 끝낼게요")
if c2.button("🏁 경기 종료", disabled=not confirm, width="stretch"):
    data.finish_match(match_id)
    st.success("경기가 저장됐어요! 순위표에서 확인해 보세요.")
    st.balloons()
    st.rerun()

with st.expander("경기 자체를 취소하기"):
    st.caption("잘못 만든 경기라면 득점 기록까지 모두 지워요.")
    if st.button("이 경기 삭제"):
        data.cancel_match(match_id)
        st.rerun()
