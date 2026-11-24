"""
stats.py : 기록 계산 담당

[이 파일은 어떤 과정이야?]
저장된 경기·득점·평점 기록을 모아서 선수별 출전 수, 골, 도움, 승/무/패, 승률,
평균 평점, MOM(경기 최우수 선수) 횟수, 클린시트(골키퍼 무실점)를 계산한다.
순위표·선수 프로필·선수 비교·자동 팀 나누기 화면이 모두 이 계산 결과를 가져다 쓴다.
'종료'된 경기만 계산에 넣는다. (진행 중인 경기는 아직 결과가 확정되지 않았으니까)
"""

import pandas as pd

from data import split_names
from formations import goalkeeper

STAT_COLUMNS = ["이름", "학년", "포지션", "출전", "골", "도움", "공격포인트", "승", "무", "패",
                "승률(%)", "경기당 공격포인트", "평균평점", "MOM", "클린시트"]


def finished_matches(matches: pd.DataFrame) -> pd.DataFrame:
    return matches[matches["status"] == "종료"]


def player_result(match: pd.Series, name: str):
    """그 경기에서 이 선수가 어느 팀이었고 결과가 뭐였는지. 안 뛰었으면 None."""
    if name in split_names(match["players_a"]):
        mine, other, team = match["score_a"], match["score_b"], "A"
    elif name in split_names(match["players_b"]):
        mine, other, team = match["score_b"], match["score_a"], "B"
    else:
        return None
    result = "승" if mine > other else ("무" if mine == other else "패")
    return team, result


def match_ratings(ratings: pd.DataFrame, match_id: int) -> pd.DataFrame:
    """한 경기의 선수별 평균 평점 (높은 순)"""
    r = ratings[ratings["match_id"] == match_id]
    if r.empty:
        return pd.DataFrame(columns=["선수", "평균평점", "투표수"])
    g = r.groupby("player")["rating"].agg(["mean", "count"]).reset_index()
    g.columns = ["선수", "평균평점", "투표수"]
    g["평균평점"] = g["평균평점"].round(1)
    return g.sort_values(["평균평점", "투표수"], ascending=False).reset_index(drop=True)


def mom_of(ratings: pd.DataFrame, match_id: int) -> str:
    """경기 MOM = 그 경기 평균 평점 1위. 평점이 없으면 ''"""
    t = match_ratings(ratings, match_id)
    return "" if t.empty else t.iloc[0]["선수"]


def player_stats(players: pd.DataFrame, matches: pd.DataFrame, goals: pd.DataFrame,
                 ratings: pd.DataFrame = None) -> pd.DataFrame:
    if ratings is None:
        ratings = pd.DataFrame(columns=["match_id", "player", "rating", "voter"])
    fm = finished_matches(matches)
    g = goals[goals["match_id"].isin(fm["match_id"])]
    r = ratings[ratings["match_id"].isin(fm["match_id"])]
    moms = [mom_of(r, mid) for mid in fm["match_id"]]

    # 클린시트: 라인업에 GK로 들어간 선수의 팀이 0실점이면 +1
    clean = {}
    for _, m in fm.iterrows():
        for side, conceded in (("a", m["score_b"]), ("b", m["score_a"])):
            gk = goalkeeper(m[f"lineup_{side}"])
            if gk and conceded == 0:
                clean[gk] = clean.get(gk, 0) + 1

    rows = []
    for _, p in players.iterrows():
        name = p["name"]
        win = draw = lose = 0
        for _, m in fm.iterrows():
            res = player_result(m, name)
            if res is None:
                continue
            win += res[1] == "승"
            draw += res[1] == "무"
            lose += res[1] == "패"
        apps = win + draw + lose
        n_goals = int((g["scorer"] == name).sum())
        n_assists = int((g["assist"] == name).sum())
        my_r = r[r["player"] == name]["rating"]
        rows.append({
            "이름": name,
            "학년": f"{p['grade']}학년",
            "포지션": p["position"],
            "출전": apps,
            "골": n_goals,
            "도움": n_assists,
            "공격포인트": n_goals + n_assists,
            "승": win, "무": draw, "패": lose,
            # 0으로 나누면 오류가 나니까 출전이 0이면 0
            "승률(%)": round(win / apps * 100, 1) if apps else 0.0,
            "경기당 공격포인트": round((n_goals + n_assists) / apps, 2) if apps else 0.0,
            "평균평점": round(float(my_r.mean()), 1) if len(my_r) else 0.0,
            "MOM": moms.count(name),
            "클린시트": clean.get(name, 0),
        })
    return pd.DataFrame(rows, columns=STAT_COLUMNS)


def ranking(stats: pd.DataFrame, by: str, min_apps: int = 0, top: int = 10) -> pd.DataFrame:
    """by 기준으로 순위를 매긴다. 같은 기록이면 출전이 적은 선수가 위 (더 효율적이니까)."""
    df = stats[stats["출전"] >= min_apps]
    df = df[df[by] > 0].sort_values([by, "출전"], ascending=[False, True]).head(top)
    df = df.reset_index(drop=True)
    df.insert(0, "순위", range(1, len(df) + 1))
    return df


def power(row: pd.Series) -> float:
    """자동 팀 나누기용 실력 점수 (기록이 없는 선수는 기본 1점)
    = 1 + 경기당 공격포인트 + 승률/100 + (평균평점-6)/4"""
    score = 1.0 + row["경기당 공격포인트"] + row["승률(%)"] / 100
    if row["평균평점"]:
        score += (row["평균평점"] - 6) / 4
    return round(score, 2)


def balance_teams(names: list, stats: pd.DataFrame, positions: dict):
    """실력 점수가 비슷하도록 두 팀으로 나눈다 (스네이크 드래프트 방식).
    골키퍼가 여러 명이면 먼저 양 팀에 한 명씩 나눈다."""
    from formations import category
    score = {n: 1.0 for n in names}
    for _, row in stats[stats["이름"].isin(names)].iterrows():
        score[row["이름"]] = power(row)
    gks = [n for n in names if category(positions.get(n, "")) == "GK"]
    others = sorted([n for n in names if n not in gks[:2]], key=lambda n: -score[n])
    team_a, team_b = [], []
    if len(gks) >= 2:
        team_a.append(gks[0])
        team_b.append(gks[1])
    # 스네이크: A B B A A B B A ... 순서로 뽑으면 강한 선수가 한쪽에 몰리지 않는다
    for i, n in enumerate(others):
        (team_a if i % 4 in (0, 3) else team_b).append(n)
    # 인원이 2명 이상 차이 나면 맞춰 준다
    while len(team_a) - len(team_b) > 1:
        team_b.append(team_a.pop())
    while len(team_b) - len(team_a) > 1:
        team_a.append(team_b.pop())
    return team_a, team_b, score
