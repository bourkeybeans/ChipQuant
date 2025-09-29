import re
from datetime import datetime


RE_HEADER = re.compile(
    r"^PokerStars Hand #(\d+):\s+(.+?)\s+\(\$(\d+(?:\.\d+)?)/\$(\d+(?:\.\d+)?) USD\)\s+-\s+"
    r"(\d{4}/\d{2}/\d{2}) (\d{2}:\d{2}:\d{2}) ET"
)
RE_SEAT = re.compile(r"^Seat (\d+): ([^(]+) \(\$(\d+(?:\.\d+)?) in chips\)$")
RE_DEALT = re.compile(r"^Dealt to (.+) \[([2-9TJQKA][cdhs]) ([2-9TJQKA][cdhs])\]$")
RE_COLLECT = re.compile(r"^(.+) collected \$(\d+\.\d+) from pot$")

RE_POST_BLIND = re.compile(r"^(.+): posts (small blind|big blind|ante) \$(\d+\.?\d*)$")
RE_CALL = re.compile(r"^(.+): calls \$(\d+\.?\d*)$")
RE_BET = re.compile(r"^(.+): bets \$(\d+\.?\d*)$")
RE_RAISE = re.compile(r"^(.+): raises \$(\d+\.?\d*) to \$(\d+\.?\d*)$")
RE_CHECK = re.compile(r"^(.+): checks$")
RE_FOLD = re.compile(r"^(.+): folds$")
RE_UNCALLED = re.compile(r"^Uncalled bet \(\$(\d+(?:\.\d+)?)\) returned to (.+)$")



def log_error(errors, stage, line, error):
    errors.append({
        "stage": stage,
        "line": line,
        "error": str(error)
    })


def insert_action(hand, street, line):
    """Parse action lines, update actions + contributions"""
    m = RE_POST_BLIND.match(line)
    if m:
        name, blind_type, amount = m.groups()
        amount = float(amount)
        hand["actions"].append({
            "street": street,
            "player": name,
            "action": f"post_{blind_type.replace(' ', '_')}",
            "amount": amount
        })
        hand["contributions"][name] += amount
        return True

    m = RE_CALL.match(line)
    if m:
        name, amount = m.groups()
        amount = float(amount)
        hand["actions"].append({
            "street": street,
            "player": name,
            "action": "call",
            "amount": amount
        })
        hand["contributions"][name] += amount
        return True

    m = RE_BET.match(line)
    if m:
        name, amount = m.groups()
        amount = float(amount)
        hand["actions"].append({
            "street": street,
            "player": name,
            "action": "bet",
            "amount": amount
        })
        hand["contributions"][name] += amount
        return True

    m = RE_RAISE.match(line)
    if m:
        name, inc, total = m.groups()
        total = float(total)
        hand["actions"].append({
            "street": street,
            "player": name,
            "action": "raise",
            "amount": total
        })
        # For raises, contribution is total committed, not increment
        hand["contributions"][name] = max(hand["contributions"][name], total)
        return True

    m = RE_CHECK.match(line)
    if m:
        name = m.group(1)
        hand["actions"].append({
            "street": street,
            "player": name,
            "action": "check",
            "amount": 0.0
        })
        return True

    m = RE_FOLD.match(line)
    if m:
        name = m.group(1)
        hand["actions"].append({
            "street": street,
            "player": name,
            "action": "fold",
            "amount": 0.0
        })
        return True
    m = RE_UNCALLED.match(line)
    if m:
        amount, name = m.groups()
        amount = float(amount)
        # subtract refunded bet from contributions
        if name in hand["contributions"]:
            hand["contributions"][name] -= amount


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
    hand = {"players": [], "actions": [], "contributions": {}}
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
                hand["contributions"][player["name"]] = 0.0

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


# ---------------- DEMO ----------------

if __name__ == "__main__":
    sample_hand = """

*********** # 2 **************
PokerStars Hand #257563701388:  Hold'em No Limit ($0.02/$0.05 USD) - 2025/08/31 17:23:23 ET
Table 'Jovita VII' 6-max Seat #6 is the button
Seat 1: NoBadBlood ($5.12 in chips)
Seat 2: joeO10 ($4.29 in chips)
Seat 3: farquan66 ($6.74 in chips)
Seat 4: iBlindfrog ($4 in chips)
Seat 5: NICOREZENDE ($6.71 in chips)
Seat 6: viniciusmri ($5.88 in chips)
NoBadBlood: posts small blind $0.02
joeO10: posts big blind $0.05
*** HOLE CARDS ***
Dealt to farquan66 [4c 5h]
farquan66: folds
iBlindfrog: folds
NICOREZENDE: raises $0.07 to $0.12
viniciusmri: folds
NoBadBlood: folds
joeO10: calls $0.07
*** FLOP *** [3c Jh Js]
joeO10: checks
NICOREZENDE: bets $0.08
joeO10: calls $0.08
*** TURN *** [3c Jh Js] [2s]
joeO10: checks
NICOREZENDE: bets $0.28
joeO10: folds
Uncalled bet ($0.28) returned to NICOREZENDE
NICOREZENDE collected $0.40 from pot
*** SUMMARY ***
Total pot $0.42 | Rake $0.02
Board [3c Jh Js 2s]
Seat 1: NoBadBlood (small blind) folded before Flop
Seat 2: joeO10 (big blind) folded on the Turn
Seat 3: farquan66 folded before Flop (didn't bet)
Seat 4: iBlindfrog folded before Flop (didn't bet)
Seat 5: NICOREZENDE collected ($0.40)
Seat 6: viniciusmri (button) folded before Flop (didn't bet)


*********** # 3 **************
PokerStars Hand #257563680302:  Hold'em No Limit ($0.02/$0.05 USD) - 2025/08/31 17:22:12 ET
Table 'Jovita VII' 6-max Seat #5 is the button
Seat 1: NoBadBlood ($5.17 in chips)
Seat 2: joeO10 ($4.29 in chips)
Seat 3: farquan66 ($7.43 in chips)
Seat 4: iBlindfrog ($4 in chips)
Seat 5: NICOREZENDE ($6.71 in chips)
Seat 6: viniciusmri ($5.21 in chips)
viniciusmri: posts small blind $0.02
NoBadBlood: posts big blind $0.05
*** HOLE CARDS ***
Dealt to farquan66 [Ks 9s]
joeO10: folds
farquan66: calls $0.05
iBlindfrog: folds
NICOREZENDE: folds
viniciusmri: raises $0.15 to $0.20
NoBadBlood: folds
farquan66: calls $0.15
*** FLOP *** [5d Qc 2h]
viniciusmri: bets $0.14
farquan66: calls $0.14
*** TURN *** [5d Qc 2h] [3s]
viniciusmri: checks
farquan66: bets $0.35
viniciusmri: calls $0.35
*** RIVER *** [5d Qc 2h 3s] [9c]
viniciusmri: checks
farquan66: checks
*** SHOW DOWN ***
viniciusmri: shows [Qs Ts] (a pair of Queens)
farquan66: mucks hand
viniciusmri collected $1.36 from pot
*** SUMMARY ***
Total pot $1.43 | Rake $0.07
Board [5d Qc 2h 3s 9c]
Seat 1: NoBadBlood (big blind) folded before Flop
Seat 2: joeO10 folded before Flop (didn't bet)
Seat 3: farquan66 mucked [Ks 9s]
Seat 4: iBlindfrog folded before Flop (didn't bet)
Seat 5: NICOREZENDE (button) folded before Flop (didn't bet)
Seat 6: viniciusmri (small blind) showed [Qs Ts] and won ($1.36) with a pair of Queens


*********** # 4 **************
PokerStars Hand #257563663387:  Hold'em No Limit ($0.02/$0.05 USD) - 2025/08/31 17:21:15 ET
Table 'Jovita VII' 6-max Seat #4 is the button
Seat 1: NoBadBlood ($5.32 in chips)
Seat 2: joeO10 ($4.29 in chips)
Seat 3: farquan66 ($7.43 in chips)
Seat 4: iBlindfrog ($3.70 in chips)
Seat 5: NICOREZENDE ($6.73 in chips)
Seat 6: viniciusmri ($5.36 in chips)
NICOREZENDE: posts small blind $0.02
viniciusmri: posts big blind $0.05
*** HOLE CARDS ***
Dealt to farquan66 [9c 3c]
NoBadBlood: raises $0.10 to $0.15
joeO10: folds
farquan66: folds
iBlindfrog: calls $0.15
NICOREZENDE: folds
viniciusmri: calls $0.10
*** FLOP *** [7d Td 4d]
viniciusmri: checks
NoBadBlood: checks
iBlindfrog: bets $0.23
viniciusmri: folds
NoBadBlood: folds
Uncalled bet ($0.23) returned to iBlindfrog
iBlindfrog collected $0.45 from pot
iBlindfrog: doesn't show hand
*** SUMMARY ***
Total pot $0.47 | Rake $0.02
Board [7d Td 4d]
Seat 1: NoBadBlood folded on the Flop
Seat 2: joeO10 folded before Flop (didn't bet)
Seat 3: farquan66 folded before Flop (didn't bet)
Seat 4: iBlindfrog (button) collected ($0.45)
Seat 5: NICOREZENDE (small blind) folded before Flop
Seat 6: viniciusmri (big blind) folded on the Flop
"""

    blocks = sample_hand.strip().split("\n\n\n")
    for raw in blocks:
        hand, errors = parse_hand(raw)

        print("\n--- Parsed Hand ---")
        print(f"Hand ID: {hand.get('id')}")
        print(f"Gamemode: {hand.get('gamemode')}")
        print(f"Stakes: {hand.get('stakes')}")
        print(f"Datetime: {hand.get('datetime')}")

        print("\nPlayers:")
        for p in hand["players"]:
            contrib = hand["contributions"].get(p["name"], 0.0)
            collect = p["result"]
            net = collect - contrib
            print(f"  Seat {p['seat']}: {p['name']} "
                  f"(stack_start={p['stack_start']}, cards={p['cards']}, "
                  f"put_in={contrib}, won={collect}, net={net})")

        print("\nActions:")
        for a in hand["actions"]:
            print(f"  [{a['street']}] {a['player']} -> {a['action']} {a['amount']}")

        if errors:
            print("\nErrors:", errors)
