"""
rate.py : 경기 평점 · MOM 화면 (풋몹의 선수 평점 기능)

[이 화면은 어떤 과정이야?]
1) 끝난 경기를 하나 고른다 (경기를 막 끝냈으면 그 경기가 자동으로 선택된다).
2) 그 경기에 뛴 선수마다 1~10점 슬라이더로 평점을 매기고 제출한다.
3) 여러 사람이 낸 평점의 평균을 보여 주고, 1위를 그 경기의 MOM(Man of the Match)으로 뽑는다.

같은 사람이 같은 경기에 여러 번 투표하지 못하도록, 접속한 브라우저마다 '투표자 번호'를 하나씩 준다.
(새로고침하면 번호가 바뀌는 한계가 있다 → 가치분석의 '부정적 측면'으로 쓸 수 있다)
"""

import uuid

import streamlit as st

import data
import formations as fm
import stats

st.title("⭐ 경기 평점 · MOM")

matches, ratings = data.load("matches"), data.load("ratings")
done = stats.finished_matches(matches).sort_values("match_id", ascending=False)
if done.empty:
    st.info("아직 끝난 경기가 없어요.")
    st.stop()

if "voter" not in st.session_state:
    st.session_state["voter"] = uuid.uuid4().hex[:8]
voter = st.session_state["voter"]

ids = done["match_id"].tolist()
default = ids.index(st.session_state["rate_match"]) if st.session_state.get("rate_match") in ids else 0
label = {int(m["match_id"]): f"#{m['match_id']} {m['date']}  {m['team_a']} {m['score_a']}:{m['score_b']} {m['team_b']}"
         for _, m in done.iterrows()}
match_id = st.selectbox("경기 선택", ids, index=default, format_func=lambda i: label[int(i)])
m = done[done["match_id"] == match_id].iloc[0]
roster_a, roster_b = data.split_names(m["players_a"]), data.split_names(m["players_b"])

# 현재 평점과 MOM
table = stats.match_ratings(ratings, match_id)
if table.empty:
    st.caption("아직 평점이 없어요. 첫 번째로 매겨 주세요!")
else:
    top = table.iloc[0]
    st.success(f"🏅 MOM  {top['선수']}  ·  평균 {top['평균평점']}점 ({int(top['투표수'])}명 투표)")
    st.dataframe(table, hide_index=True, width="stretch")

st.divider()
if data.already_voted(match_id, voter):
    st.info("이 경기에는 이미 평점을 매겼어요. 고마워요!")
else:
    st.subheader("평점 매기기")
    st.caption("6점이 보통이에요. 10점은 오늘의 주인공!")
    with st.form(f"rate_{match_id}"):
        scores = {}
        for team_name, roster in ((m["team_a"], roster_a), (m["team_b"], roster_b)):
            st.markdown(f"**{team_name}**")
            for p in roster:
                scores[p] = st.slider(p, 1.0, 10.0, 6.0, 0.5, key=f"r_{match_id}_{p}")
        if st.form_submit_button("평점 제출", type="primary", width="stretch"):
            data.add_ratings(match_id, scores, voter)
            st.toast("평점을 제출했어요!")
            st.rerun()

if m["formation_a"] and m["formation_b"]:
    with st.expander("이 경기 포메이션 보기"):
        st.plotly_chart(fm.draw_pitch([
            {"formation": m["formation_a"], "names": fm.text_to_lineup(m["formation_a"], m["lineup_a"]),
             "color": "#1f6feb", "name": m["team_a"]},
            {"formation": m["formation_b"], "names": fm.text_to_lineup(m["formation_b"], m["lineup_b"]),
             "color": "#d1242f", "name": m["team_b"]},
        ], height=600), width="stretch")
