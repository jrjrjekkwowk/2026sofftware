"""
data.py : 데이터 저장과 불러오기 담당

[이 파일은 어떤 과정이야?]
앱의 모든 화면은 데이터를 직접 만지지 않고 이 파일에 있는 함수만 불러서 쓴다.
그래서 나중에 저장 위치를 CSV 파일에서 구글 스프레드시트로 바꿀 때 이 파일만 고치면 된다.

저장하는 표는 네 개
  players.csv : 선수  -> 이름, 학년, 주 포지션
  matches.csv : 경기  -> 경기 번호, 날짜, 킥오프 시각, 팀 이름, 참가 선수, 포메이션, 라인업, 스코어, 상태
  goals.csv   : 득점  -> 득점 번호, 경기 번호, 팀, 득점 선수, 도움 선수, 시각, 몇 분, 골 유형
  ratings.csv : 평점  -> 경기 번호, 선수, 평점(1~10), 투표한 사람 표시
"""

import io
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# 표마다 어떤 칸(열)이 있는지 정해 두는 설계도
COLUMNS = {
    "players": ["name", "grade", "position"],
    "matches": ["match_id", "date", "kickoff", "team_a", "team_b", "players_a", "players_b",
                "formation_a", "formation_b", "lineup_a", "lineup_b",
                "score_a", "score_b", "status"],
    "goals": ["goal_id", "match_id", "team", "scorer", "assist", "time", "minute", "goal_type"],
    "ratings": ["match_id", "player", "rating", "voter"],
}
# 숫자로 다뤄야 하는 칸 (CSV는 전부 글자로 저장되기 때문에 읽을 때 숫자로 바꿔 준다)
NUMBER_COLS = {
    "players": ["grade"],
    "matches": ["match_id", "score_a", "score_b"],
    "goals": ["goal_id", "match_id", "minute"],
    "ratings": ["match_id", "rating"],
}
TABLES = list(COLUMNS.keys())

# 포지션 목록 (경기장 앞쪽 = 공격부터 뒤쪽 = 골키퍼 순서)
POSITIONS = [
    "CF (센터 포워드)", "SS (세컨드 스트라이커)", "LW (왼쪽 윙어)", "RW (오른쪽 윙어)",
    "AM (공격형 미드필더)", "LM (왼쪽 미드필더)", "CM (중앙 미드필더)", "RM (오른쪽 미드필더)",
    "DM (수비형 미드필더)", "LWB (왼쪽 윙백)", "RWB (오른쪽 윙백)",
    "LB (왼쪽 풀백)", "CB (센터백)", "RB (오른쪽 풀백)", "SW (스위퍼)",
    "GK (골키퍼)",
]
GOAL_TYPES = ["일반", "헤더", "중거리", "PK", "프리킥", "역습"]


# ---------------------------------------------------------------
# 1. 기본 읽기 / 쓰기
# ---------------------------------------------------------------
def load(table: str) -> pd.DataFrame:
    """표 하나를 읽어 온다. 파일이 없으면 빈 표를 만들어서 돌려준다.
    예전 버전에서 만든 파일에 새로 생긴 칸이 없으면 빈칸으로 채워 준다 (업데이트해도 안 깨지게)."""
    path = DATA_DIR / f"{table}.csv"
    try:
        df = pd.read_csv(path, dtype=str) if path.exists() else pd.DataFrame(columns=COLUMNS[table])
    except pd.errors.EmptyDataError:  # 파일은 있는데 내용이 비어 있는 경우
        df = pd.DataFrame(columns=COLUMNS[table])
    for col in COLUMNS[table]:
        if col not in df.columns:
            df[col] = ""
    df = df[COLUMNS[table]].copy()
    for col in COLUMNS[table]:
        if col in NUMBER_COLS[table]:
            num = pd.to_numeric(df[col], errors="coerce").fillna(0)
            df[col] = num if col == "rating" else num.astype(int)
        else:
            df[col] = df[col].fillna("").astype(str)
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


def _check_name(name: str):
    if not name:
        return "이름을 입력해 주세요."
    if "|" in name or "=" in name:
        return "이름에 | 나 = 기호는 쓸 수 없어요."
    return None


# ---------------------------------------------------------------
# 2. 선수
# ---------------------------------------------------------------
def add_player(name: str, grade: int, position: str):
    """선수를 등록한다. 성공하면 (True, 메시지), 실패하면 (False, 이유)를 돌려준다."""
    name = name.strip()
    problem = _check_name(name)
    if problem:
        return False, problem
    players = load("players")
    if name in players["name"].values:
        return False, f"'{name}' 선수는 이미 등록되어 있어요."
    new_row = pd.DataFrame([{"name": name, "grade": grade, "position": position}])
    save("players", pd.concat([players, new_row], ignore_index=True))
    return True, f"'{name}' 선수를 등록했어요!"


def delete_player(name: str) -> None:
    players = load("players")
    save("players", players[players["name"] != name])


def update_player(old_name: str, new_name: str, grade: int, position: str):
    """선수 정보를 수정한다. 이름이 바뀌면 지난 경기·득점·평점 기록 속 이름도 같이 바꾼다."""
    new_name = new_name.strip()
    problem = _check_name(new_name)
    if problem:
        return False, problem
    players = load("players")
    if new_name != old_name and new_name in players["name"].values:
        return False, f"'{new_name}' 선수는 이미 등록되어 있어요."
    idx = players["name"] == old_name
    players.loc[idx, ["name", "grade", "position"]] = [new_name, grade, position]
    save("players", players)
    if new_name != old_name:
        matches, goals, ratings = load("matches"), load("goals"), load("ratings")
        for col in ["players_a", "players_b"]:
            matches[col] = matches[col].apply(
                lambda t: "|".join(new_name if n == old_name else n for n in split_names(t)))
        for col in ["lineup_a", "lineup_b"]:
            matches[col] = matches[col].str.replace(f"={old_name}|", f"={new_name}|", regex=False)
            matches[col] = matches[col].apply(
                lambda t: t[: -len(old_name)] + new_name if t.endswith(f"={old_name}") else t)
        goals[["scorer", "assist"]] = goals[["scorer", "assist"]].replace(old_name, new_name)
        ratings["player"] = ratings["player"].replace(old_name, new_name)
        save("matches", matches)
        save("goals", goals)
        save("ratings", ratings)
    return True, f"'{new_name}' 선수 정보를 수정했어요!"


def positions_map() -> dict:
    """{선수 이름: 주 포지션} 사전"""
    p = load("players")
    return dict(zip(p["name"], p["position"]))


# ---------------------------------------------------------------
# 3. 경기 (실시간 기록)
# ---------------------------------------------------------------
def get_live_match():
    """지금 진행 중인 경기를 찾는다. 없으면 None."""
    matches = load("matches")
    live = matches[matches["status"] == "진행중"]
    return None if live.empty else live.iloc[-1]


def start_match(team_a: str, team_b: str, players_a: list, players_b: list,
                formation_a: str = "", formation_b: str = "",
                lineup_a: str = "", lineup_b: str = "") -> int:
    """경기를 시작하면 바로 '진행중' 상태로 저장한다 (중간에 새로고침해도 안 날아가게)."""
    matches = load("matches")
    match_id = _next_id(matches, "match_id")
    now = datetime.now()
    new_row = pd.DataFrame([{
        "match_id": match_id,
        "date": now.strftime("%Y-%m-%d"),
        "kickoff": now.strftime("%Y-%m-%d %H:%M:%S"),
        "team_a": team_a.strip() or "A팀",
        "team_b": team_b.strip() or "B팀",
        "players_a": "|".join(players_a),
        "players_b": "|".join(players_b),
        "formation_a": formation_a, "formation_b": formation_b,
        "lineup_a": lineup_a, "lineup_b": lineup_b,
        "score_a": 0, "score_b": 0,
        "status": "진행중",
    }])
    save("matches", pd.concat([matches, new_row], ignore_index=True))
    return match_id


def minutes_played(kickoff: str) -> int:
    """킥오프부터 지금까지 몇 분째인지 (축구 중계처럼 1분부터 센다)"""
    try:
        start = datetime.strptime(kickoff, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return 0
    return int((datetime.now() - start).total_seconds() // 60) + 1


def _update_score(match_id: int) -> None:
    """골 기록을 세어서 스코어를 다시 계산한다 (스코어를 따로 셀 필요가 없는 이유)."""
    matches, goals = load("matches"), load("goals")
    g = goals[goals["match_id"] == match_id]
    idx = matches["match_id"] == match_id
    matches.loc[idx, "score_a"] = int((g["team"] == "A").sum())
    matches.loc[idx, "score_b"] = int((g["team"] == "B").sum())
    save("matches", matches)


def add_goal(match_id: int, team: str, scorer: str, assist: str = "",
             goal_type: str = "일반", minute: int = 0) -> None:
    goals = load("goals")
    new_row = pd.DataFrame([{
        "goal_id": _next_id(goals, "goal_id"),
        "match_id": match_id,
        "team": team,  # "A" 또는 "B"
        "scorer": scorer,
        "assist": assist if assist and assist != scorer else "",
        "time": datetime.now().strftime("%H:%M"),
        "minute": minute,
        "goal_type": goal_type,
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
    for table in ("matches", "goals", "ratings"):
        df = load(table)
        save(table, df[df["match_id"] != match_id])


# ---------------------------------------------------------------
# 4. 평점
# ---------------------------------------------------------------
def already_voted(match_id: int, voter: str) -> bool:
    r = load("ratings")
    return bool(((r["match_id"] == match_id) & (r["voter"] == voter)).any())


def add_ratings(match_id: int, scores: dict, voter: str) -> None:
    """scores = {선수 이름: 평점}. 한 사람(voter)이 한 경기에 한 번만 투표하도록 화면에서 막는다."""
    r = load("ratings")
    rows = pd.DataFrame([{"match_id": match_id, "player": p, "rating": float(s), "voter": voter}
                         for p, s in scores.items()])
    save("ratings", pd.concat([r, rows], ignore_index=True))


# ---------------------------------------------------------------
# 5. 백업 / 복원 / 초기화
# ---------------------------------------------------------------
def backup_zip() -> bytes:
    """모든 표를 zip 파일 하나로 묶는다 (다운로드용)"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for t in TABLES:
            z.writestr(f"{t}.csv", load(t).to_csv(index=False))
    return buf.getvalue()


def restore_zip(raw: bytes):
    """백업 zip을 받아서 표를 되살린다. 반환: 되살린 표 이름 목록"""
    restored = []
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for t in TABLES:
            if f"{t}.csv" in z.namelist():
                (DATA_DIR / f"{t}.csv").write_bytes(z.read(f"{t}.csv"))
                restored.append(t)
    for t in restored:  # 형식 맞추기 (빠진 칸 채우기)
        save(t, load(t))
    return restored


def reset_all() -> None:
    for t in TABLES:
        (DATA_DIR / f"{t}.csv").unlink(missing_ok=True)
