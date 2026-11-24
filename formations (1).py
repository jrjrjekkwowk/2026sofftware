"""
formations.py : 포메이션 데이터와 경기장 그림 담당

[이 파일은 어떤 과정이야?]
1) "3-3-2" 같은 포메이션 글자를 받아서, 골키퍼 + 필드 선수 자리(포지션 이름과 경기장 위 좌표)를 만든다.
2) 선수들의 주 포지션을 보고 비슷한 자리에 자동으로 배치한다.
3) Plotly로 초록색 경기장을 그리고, 그 위에 선수 이름을 찍는다.

좌표 약속: x는 왼쪽(0) ~ 오른쪽(100), y는 우리 골대(0) ~ 상대 골대(100)
"""

import plotly.graph_objects as go

# 경기 인원(골키퍼 포함)별 포메이션 목록. 숫자는 수비-미드-공격 순서
FORMATIONS = {
    5: ["2-2", "1-2-1", "3-1", "2-1-1"],
    6: ["2-2-1", "2-1-2", "3-1-1", "1-2-2", "2-3"],
    7: ["2-3-1", "3-2-1", "3-1-2", "2-2-2", "2-1-2-1"],
    8: ["3-3-1", "4-2-1", "3-2-2", "2-3-2", "3-1-2-1", "2-4-1"],
    9: ["3-3-2", "3-2-3", "2-4-2", "4-3-1", "3-4-1", "4-2-2", "2-3-3",
        "3-1-3-1", "3-2-2-1", "4-1-2-1"],
    11: ["4-4-2", "4-3-3", "4-2-3-1", "3-5-2", "3-4-3", "5-3-2", "4-1-4-1", "4-5-1"],
}
GAME_SIZES = list(FORMATIONS.keys())

# 포지션 → 큰 분류 (자동 배치할 때 비슷한 자리를 찾는 데 쓴다)
CATEGORY = {
    "GK": "GK",
    "SW": "DF", "CB": "DF", "LB": "DF", "RB": "DF", "LWB": "DF", "RWB": "DF",
    "DM": "MF", "CM": "MF", "LM": "MF", "RM": "MF", "AM": "MF",
    "CF": "FW", "SS": "FW", "LW": "FW", "RW": "FW",
}


def short(position: str) -> str:
    """'CB (센터백)' -> 'CB'. 예전 형식 '공격수(FW)'는 'FW'처럼 괄호 안을 쓴다."""
    p = str(position).strip()
    if " (" in p:
        return p.split(" (")[0]
    if "(" in p and p.endswith(")"):
        return p[p.index("(") + 1:-1]
    return p


def category(position: str) -> str:
    code = short(position)
    return CATEGORY.get(code, code if code in ("GK", "DF", "MF", "FW") else "MF")


# 줄(라인)마다 인원수에 맞는 포지션 이름
DEF_LINE = {1: ["CB"], 2: ["CB", "CB"], 3: ["LB", "CB", "RB"], 4: ["LB", "CB", "CB", "RB"],
            5: ["LWB", "CB", "CB", "CB", "RWB"]}
ATT_LINE = {1: ["CF"], 2: ["CF", "CF"], 3: ["LW", "CF", "RW"], 4: ["LW", "CF", "CF", "RW"]}
MID_LINE = {1: ["CM"], 2: ["CM", "CM"], 3: ["LM", "CM", "RM"], 4: ["LM", "CM", "CM", "RM"],
            5: ["LM", "CM", "CM", "CM", "RM"]}
DEEP_MID = {1: ["DM"], 2: ["DM", "DM"], 3: ["LM", "DM", "RM"], 4: ["LM", "DM", "DM", "RM"]}
HIGH_MID = {1: ["AM"], 2: ["AM", "AM"], 3: ["LM", "AM", "RM"], 4: ["LM", "AM", "AM", "RM"]}


def slots(formation: str) -> list:
    """'3-3-2' -> [{'label':'GK','x':50,'y':6}, {'label':'LB',...}, ...]  (골키퍼가 항상 첫 번째)"""
    lines = [int(n) for n in formation.split("-")]
    result = [{"label": "GK", "x": 50, "y": 10}]
    k = len(lines)
    for i, n in enumerate(lines):
        if i == 0:
            names = DEF_LINE.get(n, ["CB"] * n)
        elif i == k - 1:
            names = ATT_LINE.get(n, ["CF"] * n)
        elif k == 3:
            names = MID_LINE.get(n, ["CM"] * n)
        elif i == 1:
            names = DEEP_MID.get(n, ["DM"] * n)
        else:
            names = HIGH_MID.get(n, ["AM"] * n)
        y = 24 + (78 - 24) * i / max(k - 1, 1)  # 줄 사이 간격을 고르게
        for j, label in enumerate(names):
            result.append({"label": label, "x": 100 * (j + 1) / (n + 1), "y": y})
    return result


def auto_assign(formation: str, players: list, positions: dict) -> list:
    """선수 주 포지션을 보고 자리마다 선수를 정한다. 반환: 자리 순서대로 이름 ('' = 빈자리)
    1순위 포지션이 정확히 같은 선수 -> 2순위 같은 분류(수비/미드/공격) -> 3순위 남은 아무나"""
    spots = slots(formation)
    left = list(players)
    chosen = [""] * len(spots)
    for rule in ("exact", "category", "any"):
        for i, s in enumerate(spots):
            if chosen[i] or not left:
                continue
            for p in left:
                pos = positions.get(p, "")
                if (rule == "exact" and short(pos) == s["label"]) or \
                   (rule == "category" and category(pos) == category(s["label"])) or \
                   (rule == "any" and (category(pos) != "GK" or s["label"] == "GK")):
                    chosen[i] = p
                    left.remove(p)
                    break
    # 골키퍼만 남은 경우처럼 위 규칙으로 못 채운 자리는 남은 선수로 채운다
    for i in range(len(chosen)):
        if not chosen[i] and left:
            chosen[i] = left.pop(0)
    return chosen


def lineup_to_text(formation: str, names: list) -> str:
    """저장용 글자로 바꾸기: 'GK=서준|LB=민준|...' (빈자리는 뺀다)"""
    return "|".join(f"{s['label']}={n}" for s, n in zip(slots(formation), names) if n)


def text_to_lineup(formation: str, text: str) -> list:
    """저장된 글자를 다시 자리 순서대로의 이름 목록으로"""
    pairs = [p.split("=", 1) for p in str(text).split("|") if "=" in p]
    spots = slots(formation) if formation else []
    names = [""] * len(spots)
    used = [False] * len(pairs)
    for i, s in enumerate(spots):
        for j, (label, name) in enumerate(pairs):
            if not used[j] and label == s["label"]:
                names[i], used[j] = name, True
                break
    return names


def goalkeeper(text: str) -> str:
    for p in str(text).split("|"):
        if p.startswith("GK="):
            return p[3:]
    return ""


def draw_pitch(teams: list, height: int = 560) -> go.Figure:
    """teams = [{'formation':'3-3-2','names':[...],'color':'#...','name':'A팀'}, ...]
    팀이 1개면 경기장 전체, 2개면 첫 팀은 아래쪽 절반, 두 번째 팀은 위쪽 절반(뒤집어서)에 그린다."""
    fig = go.Figure()
    line = dict(color="rgba(255,255,255,0.85)", width=2)
    # 잔디, 하프라인, 센터서클, 양쪽 페널티 박스
    fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100, fillcolor="#3f8f4a", line=line, layer="below")
    fig.add_shape(type="line", x0=0, y0=50, x1=100, y1=50, line=line, layer="below")
    fig.add_shape(type="circle", x0=40, y0=44, x1=60, y1=56, line=line, layer="below")
    for y0, y1 in ((0, 14), (86, 100)):
        fig.add_shape(type="rect", x0=25, y0=y0, x1=75, y1=y1, line=line, layer="below")

    two = len(teams) == 2
    for t_index, team in enumerate(teams):
        spots = slots(team["formation"])
        xs, ys, texts = [], [], []
        for s, n in zip(spots, team["names"]):
            x, y = s["x"], s["y"]
            if two:  # 우리 팀은 아래쪽 절반(8~44), 상대 팀은 위쪽 절반(56~92)에 들어가게 줄인다
                y = 8 + (y - 10) * 36 / 68
                if t_index == 1:  # 위쪽 팀은 거울처럼 뒤집기
                    x, y = 100 - x, 100 - y
            xs.append(x)
            ys.append(y)
            texts.append(f"<b>{s['label']}</b><br>{n or '-'}")
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers+text", text=texts, textposition="bottom center",
            textfont=dict(color="white", size=11),
            marker=dict(size=22, color=team.get("color", "#1f6feb"), line=dict(color="white", width=2)),
            name=f"{team.get('name', '')} {team['formation']}", hoverinfo="skip",
        ))
    fig.update_xaxes(range=[-3, 103], visible=False, fixedrange=True)
    fig.update_yaxes(range=[-8, 104], visible=False, fixedrange=True)
    fig.update_layout(height=height, margin=dict(l=5, r=5, t=5, b=5), plot_bgcolor="white",
                      showlegend=two, legend=dict(orientation="h", y=-0.02))
    return fig
