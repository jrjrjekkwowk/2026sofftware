"""
stats.py : 기록 계산 담당

[이 파일은 어떤 과정이야?]
저장된 경기·득점 기록을 모아서 선수별 출전 수, 골, 도움, 승/무/패, 승률을 계산한다.
순위표 화면과 선수 프로필 화면이 모두 이 계산 결과를 가져다 쓴다.
'종료'된 경기만 계산에 넣는다. (진행 중인 경기는 아직 결과가 확정되지 않았으니까)
"""

import pandas as pd

from data import split_names


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


def player_stats(players: pd.DataFrame, matches: pd.DataFrame, goals: pd.DataFrame) -> pd.DataFrame:
    fm = finished_matches(matches)
    g = goals[goals["match_id"].isin(fm["match_id"])]

    rows = []
    for _, p in players.iterrows():
        name = p["name"]
        win = draw = lose = 0
        for _, m in fm.iterrows():
            r = player_result(m, name)
            if r is None:
                continue
            win += r[1] == "승"
            draw += r[1] == "무"
            lose += r[1] == "패"
        apps = win + draw + lose
        n_goals = int((g["scorer"] == name).sum())
        n_assists = int((g["assist"] == name).sum())
        rows.append({
            "이름": name,
            "학년": f"{p['grade']}학년",
            "포지션": p["position"],
            "출전": apps,
            "골": n_goals,
            "도움": n_assists,
            "공격포인트": n_goals + n_assists,
            "승": win, "무": draw, "패": lose,
            # 0으로 나누면 오류가 나니까 출전이 0이면 승률도 0
            "승률(%)": round(win / apps * 100, 1) if apps else 0.0,
        })
    return pd.DataFrame(rows, columns=["이름", "학년", "포지션", "출전", "골", "도움",
                                       "공격포인트", "승", "무", "패", "승률(%)"])


def ranking(stats: pd.DataFrame, by: str, min_apps: int = 0, top: int = 10) -> pd.DataFrame:
    """by 기준으로 순위를 매긴다. 같은 기록이면 출전이 적은 선수가 위 (더 효율적이니까)."""
    df = stats[stats["출전"] >= min_apps]
    df = df[df[by] > 0].sort_values([by, "출전"], ascending=[False, True]).head(top)
    df = df.reset_index(drop=True)
    df.insert(0, "순위", range(1, len(df) + 1))
    return df
