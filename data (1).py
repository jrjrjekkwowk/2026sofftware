"""
data.py : 데이터 저장과 불러오기 담당

[이 파일은 어떤 과정이야?]
앱의 모든 화면은 데이터를 직접 만지지 않고 이 파일에 있는 함수만 불러서 쓴다.
그래서 나중에 저장 위치를 CSV 파일에서 구글 스프레드시트로 바꿀 때 이 파일만 고치면 된다.

저장하는 표는 세 개 (계획서 4번에 쓴 데이터 구조 그대로)
  players.csv : 선수  -> 이름, 학년, 주 포지션
  matches.csv : 경기  -> 경기 번호, 날짜, 팀 이름, 참가 선수, 최종 스코어, 상태(진행중/종료)
  goals.csv   : 득점  -> 득점 번호, 경기 번호, 팀, 득점 선수, 도움 선수, 시각
"""

from datetime import datetime
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# 표마다 어떤 칸(열)이 있는지 정해 두는 설계도
COLUMNS = {
    "players": ["name", "grade", "position"],
    "matches": ["match_id", "date", "team_a", "team_b", "players_a", "players_b",
                "score_a", "score_b", "status"],
    "goals": ["goal_id", "match_id", "team", "scorer", "assist", "time"],
}
# 숫자로 다뤄야 하는 칸 (CSV는 전부 글자로 저장되기 때문에 읽을 때 숫자로 바꿔 준다)
NUMBER_COLS = {
    "players": ["grade"],
    "matches": ["match_id", "score_a", "score_b"],
    "goals": ["goal_id", "match_id"],
}
POSITIONS = ["공격수(FW)", "미드필더(MF)", "수비수(DF)", "골키퍼(GK)"]


# ---------------------------------------------------------------
# 1. 기본 읽기 / 쓰기
# ---------------------------------------------------------------
def load(table: str) -> pd.DataFrame:
    """표 하나를 읽어 온다. 파일이 없으면 빈 표를 만들어서 돌려준다."""
    path = DATA_DIR / f"{table}.csv"
    if not path.exists():
        return pd.DataFrame(columns=COLUMNS[table])
    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:  # 파일은 있는데 내용이 비어 있는 경우
        return pd.DataFrame(columns=COLUMNS[table])
    for col in NUMBER_COLS[table]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    # 비어 있는 칸(NaN)은 빈 글자로 바꿔서 다루기 쉽게
    text_cols = [c for c in COLUMNS[table] if c not in NUMBER_COLS[table]]
    df[text_cols] = df[text_cols].fillna("").astype(str)
    return df


def save(table: str, df: pd.DataFrame) -> None:
    """표 하나를 파일에 저장한다."""
    df[COLUMNS[table]].to_csv(DATA_DIR / f"{table}.csv", index=False)


def _next_id(df: pd.DataFrame, col: str) -> int:
    """새 번호 = 지금까지 가장 큰 번호 + 1"""
    return 1 if df.empty else int(df[col].max()) + 1


def split_names(text: str) -> list:
    """'민준|서준|도윤' 처럼 저장된 참가 선수 목록을 리스트로 바꾼다."""
    return [n for n in str(text).split("|") if n]


# ---------------------------------------------------------------
# 2. 선수
# ---------------------------------------------------------------
def add_player(name: str, grade: int, position: str):
    """선수를 등록한다. 성공하면 (True, 메시지), 실패하면 (False, 이유)를 돌려준다."""
    name = name.strip()
    if not name:
        return False, "이름을 입력해 주세요."
    if "|" in name:
        return False, "이름에 | 기호는 쓸 수 없어요."
    players = load("players")
    if name in players["name"].values:
        return False, f"'{name}' 선수는 이미 등록되어 있어요."
    new_row = pd.DataFrame([{"name": name, "grade": grade, "position": position}])
    save("players", pd.concat([players, new_row], ignore_index=True))
    return True, f"'{name}' 선수를 등록했어요!"


def delete_player(name: str) -> None:
    players = load("players")
    save("players", players[players["name"] != name])


# ---------------------------------------------------------------
# 3. 경기 (실시간 기록)
# ---------------------------------------------------------------
def get_live_match():
    """지금 진행 중인 경기를 찾는다. 없으면 None."""
    matches = load("matches")
    live = matches[matches["status"] == "진행중"]
    return None if live.empty else live.iloc[-1]


def start_match(team_a: str, team_b: str, players_a: list, players_b: list) -> int:
    """경기를 시작하면 바로 '진행중' 상태로 저장한다 (중간에 새로고침해도 안 날아가게)."""
    matches = load("matches")
    match_id = _next_id(matches, "match_id")
    new_row = pd.DataFrame([{
        "match_id": match_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "team_a": team_a.strip() or "A팀",
        "team_b": team_b.strip() or "B팀",
        "players_a": "|".join(players_a),
        "players_b": "|".join(players_b),
        "score_a": 0, "score_b": 0,
        "status": "진행중",
    }])
    save("matches", pd.concat([matches, new_row], ignore_index=True))
    return match_id


def _update_score(match_id: int) -> None:
    """골 기록을 세어서 스코어를 다시 계산한다 (스코어를 따로 셀 필요가 없는 이유)."""
    matches, goals = load("matches"), load("goals")
    g = goals[goals["match_id"] == match_id]
    idx = matches["match_id"] == match_id
    matches.loc[idx, "score_a"] = int((g["team"] == "A").sum())
    matches.loc[idx, "score_b"] = int((g["team"] == "B").sum())
    save("matches", matches)


def add_goal(match_id: int, team: str, scorer: str, assist: str = "") -> None:
    goals = load("goals")
    new_row = pd.DataFrame([{
        "goal_id": _next_id(goals, "goal_id"),
        "match_id": match_id,
        "team": team,  # "A" 또는 "B"
        "scorer": scorer,
        "assist": assist if assist and assist != scorer else "",
        "time": datetime.now().strftime("%H:%M"),
    }])
    save("goals", pd.concat([goals, new_row], ignore_index=True))
    _update_score(match_id)


def undo_last_goal(match_id: int) -> bool:
    """실수로 누른 골을 취소한다. 취소할 골이 없으면 False."""
    goals = load("goals")
    mine = goals[goals["match_id"] == match_id]
    if mine.empty:
        return False
    save("goals", goals.drop(mine.index[-1]))
    _update_score(match_id)
    return True


def finish_match(match_id: int) -> None:
    matches = load("matches")
    matches.loc[matches["match_id"] == match_id, "status"] = "종료"
    save("matches", matches)


def cancel_match(match_id: int) -> None:
    """잘못 만든 경기를 기록까지 통째로 지운다."""
    matches, goals = load("matches"), load("goals")
    save("matches", matches[matches["match_id"] != match_id])
    save("goals", goals[goals["match_id"] != match_id])
