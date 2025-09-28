import re
from datetime import datetime


RE_HEADER = re.compile(
    r"^PokerStars Hand #(\d+):\s+(.+?)\s+\(\$(\d+(?:\.\d+)?)/\$(\d+(?:\.\d+)?) USD\)\s+-\s+"
    r"(\d{4}/\d{2}/\d{2}) (\d{2}:\d{2}:\d{2}) ET"
)
RE_SEAT = re.compile(r"^Seat (\d+): ([^(]+) \(\$(\d+(?:\.\d+)?) in chips\)$")
RE_DEALT = re.compile(r"^Dealt to (.+) \[([2-9TJQKA][cdhs]) ([2-9TJQKA][cdhs])\]$")
RE_COLLECT = re.compile(
    r"^(.+?) collected \(\$(\d+\.\d+)\) from (?:pot|side pot(?:-\d+)?)$"
)

RE_POST_BLIND = re.compile(r"^(.+): posts (small blind|big blind|ante) \$(\d+\.?\d*)$")
RE_CALL = re.compile(r"^(.+): calls \$(\d+\.?\d*)$")
RE_BET = re.compile(r"^(.+): bets \$(\d+\.?\d*)$")
RE_RAISE = re.compile(r"^(.+): raises \$(\d+\.?\d*) to \$(\d+\.?\d*)$")
RE_CHECK = re.compile(r"^(.+): checks$")
RE_FOLD = re.compile(r"^(.+): folds$")


def log_error(errors, stage, line, error):
    errors.append({
        "stage": stage,
        "line": line,
        "error": str(error)
    })


def normalize_action(act: str) -> str:
    mapping = {
        "calls": "call",
        "bets": "bet",
        "raises": "raise",
        "checks": "check",
        "folds": "fold"
    }
    return mapping.get(act, act)


def insert_action(hand, street, line):
    m = RE_POST_BLIND.match(line)
    if m:
        name, blind_type, amount = m.groups()
        hand["actions"].append({
            "street": street,
            "player": name,
            "action": f"post_{blind_type.replace(' ', '_')}",
            "amount": float(amount)
        })
        return True

    m = RE_CALL.match(line)
    if m:
        name, amount = m.groups()
        hand["actions"].append({
            "street": street,
            "player": name,
            "action": "call",
            "amount": float(amount)
        })
        return True

    m = RE_BET.match(line)
    if m:
        name, amount = m.groups()
        hand["actions"].append({
            "street": street,
            "player": name,
            "action": "bet",
            "amount": float(amount)
        })
        return True

    m = RE_RAISE.match(line)
    if m:
        name, inc, total = m.groups()
        hand["actions"].append({
            "street": street,
            "player": name,
            "action": "raise",
            "amount": float(total)
        })
        return True

    if RE_CHECK.match(line):
        name = RE_CHECK.match(line).group(1)
        hand["actions"].append({
            "street": street,
            "player": name,
            "action": "check",
            "amount": 0.0
        })
        return True

    if RE_FOLD.match(line):
        name = RE_FOLD.match(line).group(1)
        hand["actions"].append({
            "street": street,
            "player": name,
            "action": "fold",
            "amount": 0.0
        })
        return True

    return False

def parse_file_to_staging_blocks(file_path):
    blocks = []
    current_block = []

    with open(file_path, "r") as f:
        for line in f:
            if line.startswith("PokerStars Hand #") and current_block:
                blocks.append("".join(current_block))
                current_block = []
            current_block.append(line)

    if current_block:
        blocks.append("".join(current_block))

    return [b for b in blocks if b.strip().startswith("PokerStars Hand #")]


def parse_hand(raw_text: str):
    errors = []
    hand = {"players": [], "actions": []}
    player_lookup = {}

    current_street = "preflop"

    try:
        for line in raw_text.splitlines():
            line = line.strip()

            # Street changes
            if line.startswith("*** HOLE CARDS ***"):
                current_street = "preflop"
            elif line.startswith("*** FLOP ***"):
                current_street = "flop"
            elif line.startswith("*** TURN ***"):
                current_street = "turn"
            elif line.startswith("*** RIVER ***"):
                current_street = "river"
            elif line.startswith("*** SHOW DOWN ***"):
                current_street = "showdown"
            elif line.startswith("*** SUMMARY ***"):
                current_street = "summary"

            # Header
            m = RE_HEADER.match(line)
            if m:
                hand["id"] = int(m.group(1))
                hand["gamemode"] = m.group(2)
                hand["stakes"] = {"sb": float(m.group(3)), "bb": float(m.group(4))}
                dt_str = f"{m.group(5)} {m.group(6)}"
                hand["datetime"] = datetime.strptime(dt_str, "%Y/%m/%d %H:%M:%S")

            # Seats
            m = RE_SEAT.match(line)
            if m:
                seat, name, stack = m.groups()
                player = {
                    "seat": int(seat),
                    "name": name.strip(),
                    "stack_start": float(stack),
                    "cards": [],
                    "result": 0.0
                }
                hand["players"].append(player)
                player_lookup[player["name"]] = player

            # Hole cards
            m = RE_DEALT.match(line)
            if m:
                name, c1, c2 = m.groups()
                if name in player_lookup:
                    player_lookup[name]["cards"] = [c1, c2]

            # Pot collection
            m = RE_COLLECT.match(line)
            if m:
                name, amount = m.groups()
                if name in player_lookup:
                    player_lookup[name]["result"] += float(amount)

            # Actions
            insert_action(hand, current_street, line)

    except Exception as e:
        log_error(errors, "parse_hand", line, e)

    return hand, errors
