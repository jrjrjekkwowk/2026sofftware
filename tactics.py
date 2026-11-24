"""
tactics.py : 전술판 (팀 나누기 + 포메이션 + 라인업 + 경기 시작)

[이 화면은 어떤 과정이야?]
1단계 경기 인원 정하기 (기본 9대9)
2단계 오늘 온 선수 고르기 → '자동 팀 나누기'를 누르면 실력이 비슷하게 A/B팀으로 나눈다
3단계 팀마다 포메이션(3-3-2 등)을 고르고 '자동 배치'를 누르면 주 포지션에 맞게 자리를 채운다
      자리마다 선수를 직접 바꿀 수도 있다. 경기장 그림에 바로 반영된다.
4단계 '이 라인업으로 경기 시작' → 실시간 경기 기록 화면으로 넘어간다

st.session_state : 버튼을 눌러 화면이 다시 그려져도 고른 값이 사라지지 않게 기억하는 저장소
on_click 콜백   : 버튼을 누른 '직후, 화면을 다시 그리기 전에' 실행되는 함수 (입력칸 값을 바꿀 때 사용)
"""

import streamlit as st

import data
import formations as fm
import stats

st.title("📋 전술판")
st.caption("팀 나누기 → 포메이션 → 라인업 → 경기 시작까지 한 번에")

players = data.load("players")
if len(players) < 2:
    st.warning("선수가 2명 이상 등록되어 있어야 해요. '선수 등록' 메뉴로 가 주세요.")
    st.stop()

names = sorted(players["name"].tolist())
positions = data.positions_map()
EMPTY = "(비움)"
ss = st.session_state

# ---------------------------------------------------------------
# 1단계 경기 인원
# ---------------------------------------------------------------
size = st.radio("경기 인원 (골키퍼 포함)", fm.GAME_SIZES, index=fm.GAME_SIZES.index(9),
                format_func=lambda n: f"{n}대{n}", horizontal=True, key="tac_size")

# ---------------------------------------------------------------
# 2단계 팀 나누기
# ---------------------------------------------------------------
st.subheader("1. 팀 나누기")
people = st.multiselect("오늘 온 선수", names, key="tac_people", placeholder="선수 선택")


def do_split():
    table = stats.player_stats(players, data.load("matches"), data.load("goals"), data.load("ratings"))
    a, b, score = stats.balance_teams(ss.tac_people, table, positions)
    ss.tac_a, ss.tac_b, ss.tac_score = a, b, score


st.button("⚖️ 실력 비슷하게 자동 팀 나누기", on_click=do_split, disabled=len(people) < 2,
          width="stretch")
st.caption(f"오늘 {len(people)}명 · {size}대{size}라면 {size * 2}명이 필요해요")

col_a, col_b = st.columns(2)
team_a = col_a.multiselect("A팀", names, key="tac_a", placeholder="선수 선택")
team_b = col_b.multiselect("B팀", names, key="tac_b", placeholder="선수 선택")

overlap = set(team_a) & set(team_b)
if overlap:
    st.error(f"양쪽 팀에 모두 들어간 선수가 있어요: {', '.join(overlap)}")
if "tac_score" in ss and team_a and team_b:
    sa = sum(ss.tac_score.get(n, 1.0) for n in team_a)
    sb = sum(ss.tac_score.get(n, 1.0) for n in team_b)
    st.caption(f"실력 점수 합계  A팀 {sa:.1f} : {sb:.1f} B팀  (기록이 쌓일수록 정확해져요)")

# ---------------------------------------------------------------
# 3단계 포메이션과 라인업
# ---------------------------------------------------------------
st.subheader("2. 포메이션과 라인업")
options = fm.FORMATIONS[size]


def slot_key(team, formation, i):
    return f"slot_{team}_{formation}_{i}"


def auto_fill(team, formation, roster):
    chosen = fm.auto_assign(formation, roster, positions)
    for i, n in enumerate(chosen):
        ss[slot_key(team, formation, i)] = n or EMPTY


def lineup_editor(team, roster, column):
    """한 팀의 포메이션 선택 + 자리별 선수 선택. (포메이션, 자리 순서대로 이름 목록)을 돌려준다."""
    with column:
        formation = st.selectbox("포메이션", options, key=f"form_{team}")
        st.button("🪄 주 포지션대로 자동 배치", key=f"auto_{team}", width="stretch",
                  on_click=auto_fill, args=(team, formation, roster), disabled=not roster)
        chosen = []
        for i, s in enumerate(fm.slots(formation)):
            key = slot_key(team, formation, i)
            choices = [EMPTY] + roster
            if ss.get(key) not in choices:  # 팀에서 빠진 선수가 자리에 남아 있으면 비운다
                ss[key] = EMPTY
            picked = st.selectbox(s["label"], choices, key=key)
            chosen.append("" if picked == EMPTY else picked)
        dup = {n for n in chosen if n and chosen.count(n) > 1}
        if dup:
            st.warning(f"두 자리에 들어간 선수: {', '.join(dup)}")
        bench = [n for n in roster if n not in chosen]
        if bench:
            st.caption("교체 명단: " + ", ".join(bench))
    return formation, chosen


tab_a, tab_b, tab_both = st.tabs(["A팀 라인업", "B팀 라인업", "두 팀 한눈에"])
form_a, names_a = lineup_editor("A", team_a, tab_a)
form_b, names_b = lineup_editor("B", team_b, tab_b)

with tab_a:
    st.plotly_chart(fm.draw_pitch([{"formation": form_a, "names": names_a, "color": "#1f6feb",
                                    "name": "A팀"}]), width="stretch", key="pitch_a")
with tab_b:
    st.plotly_chart(fm.draw_pitch([{"formation": form_b, "names": names_b, "color": "#d1242f",
                                    "name": "B팀"}]), width="stretch", key="pitch_b")
with tab_both:
    st.plotly_chart(fm.draw_pitch([
        {"formation": form_a, "names": names_a, "color": "#1f6feb", "name": "A팀"},
        {"formation": form_b, "names": names_b, "color": "#d1242f", "name": "B팀"},
    ], height=640), width="stretch", key="pitch_both")

# ---------------------------------------------------------------
# 4단계 경기 시작
# ---------------------------------------------------------------
st.subheader("3. 경기 시작")
c1, c2 = st.columns(2)
name_a = c1.text_input("A팀 이름", value="A팀", key="tac_name_a")
name_b = c2.text_input("B팀 이름", value="B팀", key="tac_name_b")

live = data.get_live_match()
if live is not None:
    st.info("이미 진행 중인 경기가 있어요. 그 경기를 먼저 끝내 주세요.")
    st.page_link("live.py", label="진행 중인 경기로 가기", icon="⏱️")
elif st.button("⚽ 이 라인업으로 경기 시작", type="primary", width="stretch"):
    if not team_a or not team_b:
        st.error("양 팀에 최소 1명씩은 선수를 넣어 주세요.")
    elif overlap:
        st.error("양쪽 팀에 모두 들어간 선수를 먼저 정리해 주세요.")
    elif name_a.strip() and name_a.strip() == name_b.strip():
        st.error("두 팀 이름이 같아요. 다르게 정해 주세요.")
    else:
        data.start_match(name_a, name_b, team_a, team_b, form_a, form_b,
                         fm.lineup_to_text(form_a, names_a), fm.lineup_to_text(form_b, names_b))
        st.switch_page("live.py")
