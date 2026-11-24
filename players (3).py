"""
players.py : 선수 등록 화면

[이 화면은 어떤 과정이야?]
1) 입력 폼(form)으로 이름·학년·포지션을 받는다.
2) 등록 버튼을 누르면 data.add_player()가 빈칸·중복 이름을 검사한 뒤 저장한다.
3) 아래에 지금까지 등록된 선수 목록을 보여 준다.
"""

import streamlit as st

import data

st.title("📝 선수 등록 · 수정")

# st.form 안의 입력은 '등록' 버튼을 눌렀을 때 한꺼번에 처리된다
with st.form("add_player", clear_on_submit=True):
    name = st.text_input("이름")
    col1, col2 = st.columns(2)
    grade = col1.selectbox("학년", [1, 2, 3], format_func=lambda g: f"{g}학년")
    position = col2.selectbox("주 포지션", data.POSITIONS)
    submitted = st.form_submit_button("등록하기", type="primary", width="stretch")

if submitted:
    ok, msg = data.add_player(name, grade, position)
    (st.success if ok else st.error)(msg)

players = data.load("players")
st.subheader(f"등록된 선수 ({len(players)}명)")

if players.empty:
    st.info("아직 등록된 선수가 없어요. 위에서 첫 선수를 등록해 보세요.")
else:
    show = players.rename(columns={"name": "이름", "grade": "학년", "position": "포지션"})
    show["학년"] = show["학년"].astype(str) + "학년"
    st.dataframe(show.sort_values(["학년", "이름"]), hide_index=True, width="stretch")

    with st.expander("✏️ 선수 수정 / 삭제"):
        target = st.selectbox("선수 선택", sorted(players["name"].tolist()), key="edit_target")
        cur = players[players["name"] == target].iloc[0]
        # key에 선수 이름을 넣어야 다른 선수를 고르면 입력칸이 그 선수 정보로 바뀐다
        new_name = st.text_input("이름", value=target, key=f"edit_name_{target}")
        c1, c2 = st.columns(2)
        new_grade = c1.selectbox("학년", [1, 2, 3], index=[1, 2, 3].index(int(cur["grade"])),
                                 format_func=lambda g: f"{g}학년", key=f"edit_grade_{target}")
        pos_index = data.POSITIONS.index(cur["position"]) if cur["position"] in data.POSITIONS else 0
        new_pos = c2.selectbox("주 포지션", data.POSITIONS, index=pos_index,
                               key=f"edit_pos_{target}")
        b1, b2 = st.columns(2)
        if b1.button("수정 저장", type="primary", width="stretch"):
            ok, msg = data.update_player(target, new_name, new_grade, new_pos)
            if ok:
                st.toast(msg)
                st.rerun()
            else:
                st.error(msg)
        if b2.button("삭제", width="stretch"):
            data.delete_player(target)
            st.rerun()

# 테스트용: 계획서 5번에 쓴 '가짜 데이터로 시험하기'를 버튼 하나로 할 수 있게
with st.expander("🧪 테스트용 샘플 선수 18명 넣기 (9대9 두 팀)"):
    st.caption("기능 시험용이에요. 실제 사용 전에는 위의 '선수 수정 / 삭제'로 지우면 돼요.")
    if st.button("샘플 선수 넣기"):
        # 9대9 두 팀이 나오도록 골키퍼 2명 + 수비·미드·공격을 골고루
        sample = ["GK", "GK", "CB", "CB", "LB", "RB", "SW", "LWB", "DM", "CM", "CM", "AM",
                  "LM", "RM", "CF", "CF", "LW", "RW"]
        for i, code in enumerate(sample, start=1):
            pos = next(p for p in data.POSITIONS if p.startswith(code + " "))
            data.add_player(f"테스트{i:02d}", (i % 3) + 1, pos)
        st.rerun()
