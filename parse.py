import re
from datetime import datetime

import re
from datetime import datetime

def log_error(errors, stage, line, error):
    errors.append({
        "stage": stage,
        "line": line,
        "error": str(error)
    })

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

    # drop dummy divider-only blocks
    return [b for b in blocks if b.strip().startswith("PokerStars Hand #")]


def parse_hand(raw_text: str):
    """
    Parse a single hand (string) into a dict + errors.
    """
    errors = []
    hand = {"players": [], "actions": []}

    # Regexes
    header = re.compile(r"^PokerStars Hand #(\d+):\s+(.+?)\s+\(\$(\d+(?:\.\d+)?)/\$(\d+(?:\.\d+)?) USD\)\s+-\s+(\d{4}/\d{2}/\d{2}) (\d{2}:\d{2}:\d{2}) ET")
    seat = re.compile(r"^Seat (\d+): ([^(]+) \(\$(\d+(?:\.\d+)?) in chips\)$")
    dealt = re.compile(r"^Dealt to (.+) \[([2-9TJQKA][cdhs]) ([2-9TJQKA][cdhs])\]$")
    collect = re.compile(r"^(.+) collected \$(\d+\.\d+) from pot$")
    action = re.compile(r"^(.+?): (bets|calls|raises|checks|folds)(.*)$")

    current_street = "preflop"

    try:
        for line in raw_text.splitlines():
            line = line.strip()

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
            m = header.match(line)
            if m:
                hand["id"] = int(m.group(1))
                hand["gamemode"] = m.group(2)
                hand["stakes"] = {"sb": float(m.group(3)), "bb": float(m.group(4))}
                dt_str = f"{m.group(5)} {m.group(6)}"
                hand["datetime"] = datetime.strptime(dt_str, "%Y/%m/%d %H:%M:%S")

            # Seats
            m = seat.match(line)
            if m:
                hand["players"].append({
                    "seat": int(m.group(1)),
                    "name": m.group(2).strip(),
                    "stack_start": float(m.group(3)),
                    "cards": [],
                    "result": 0.0
                })

            # Hole cards
            m = dealt.match(line)
            if m:
                name, c1, c2 = m.group(1), m.group(2), m.group(3)
                for p in hand["players"]:
                    if p["name"] == name:
                        p["cards"] = [c1, c2]

            # Pot collection
            m = collect.match(line)
            if m:
                name, amount = m.group(1), float(m.group(2))
                for p in hand["players"]:
                    if p["name"] == name:
                        p["result"] += amount

            #Action Collection
            # Action Collection
            if insert_action(hand, current_street, line):
                continue

    except Exception as e:
        log_error(errors, "parse_hand", line, e)

    return hand, errors


blocks = parse_file_to_staging_blocks("hands.txt")
parsed, errs = parse_hand(blocks[0])
print(parsed)

def insert_action(hand, street, line):
    """
    Try to parse a single action line and append to hand["actions"].
    Returns True if matched, False otherwise.
    """
    # Regexes
    post_blind = re.compile(r"^(.+): posts (small blind|big blind|ante) \$(\d+\.?\d*)$")
    call = re.compile(r"^(.+): calls \$(\d+\.?\d*)$")
    bet = re.compile(r"^(.+): bets \$(\d+\.?\d*)$")
    raise_re = re.compile(r"^(.+): raises \$(\d+\.?\d*) to \$(\d+\.?\d*)$")
    check = re.compile(r"^(.+): checks$")
    fold = re.compile(r"^(.+): folds$")

    # Posts
    m = post_blind.match(line)
    if m:
        name, blind_type, amount = m.group(1), m.group(2), float(m.group(3))
        hand["actions"].append({
            "street": street,
            "player": name,
            "action": f"post_{blind_type.replace(' ', '_')}",
            "amount": amount
        })
        return True

    # Calls
    m = call.match(line)
    if m:
        name, amount = m.group(1), float(m.group(2))
        hand["actions"].append({
            "street": street,
            "player": name,
            "action": "call",
            "amount": amount
        })
        return True

    # Bets
    m = bet.match(line)
    if m:
        name, amount = m.group(1), float(m.group(2))
        hand["actions"].append({
            "street": street,
            "player": name,
            "action": "bet",
            "amount": amount
        })
        return True

    # Raises
    m = raise_re.match(line)
    if m:
        name, inc, total = m.group(1), float(m.group(2)), float(m.group(3))
        hand["actions"].append({
            "street": street,
            "player": name,
            "action": "raise",
            "amount": total
        })
        return True

    # Checks
    m = check.match(line)
    if m:
        name = m.group(1)
        hand["actions"].append({
            "street": street,
            "player": name,
            "action": "check",
            "amount": 0.0
        })
        return True

    # Folds
    m = fold.match(line)
    if m:
        name = m.group(1)
        hand["actions"].append({
            "street": street,
            "player": name,
            "action": "fold",
            "amount": 0.0
        })
        return True

    return False
