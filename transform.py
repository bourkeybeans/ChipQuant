from datetime import datetime
from db import supabase
from utils import make_json_safe
from collections import Counter


def get_player(name: str):
    existing = supabase.table("poker_players").select("id").eq("name", name).execute()
    if existing.data:
        return existing.data[0]["id"]

    new = supabase.table("poker_players").insert({"name": name}).execute()
    return new.data[0]["id"]


def staging_to_clean(user_id, session_notes=None):
    session_row = {
        "started_at": datetime.utcnow(),
        "notes": session_notes or "",
        "user_id": user_id,
    }
    session_row = make_json_safe(session_row)
    session = supabase.table("sessions").insert(session_row).execute()
    session_id = session.data[0]["id"]

    successful_parse = (
        supabase.table("staging_hands")
        .select("id, parsed")
        .eq("status", "success")
        .execute()
    )

    all_hands = []
    all_players = []
    all_actions = []
    all_names = set()

    for record in successful_parse.data:
        parsed = record["parsed"] or {}
        if not parsed:
            continue

        hand_id = parsed["id"]

        all_hands.append({
            "id": hand_id,
            "session_id": session_id,
            "gamemode": parsed.get("gamemode"),
            "sb": round(parsed.get("stakes", {}).get("sb", 0), 2),
            "bb": round(parsed.get("stakes", {}).get("bb", 0), 2),
            "hand_datetime": parsed.get("datetime"),
        })

        contribs = parsed.get("contributions", {})
        for p in parsed.get("players", []):
            name = p["name"]
            put_in = round(contribs.get(name, 0.0), 2)
            won = round(p.get("result", 0.0), 2)
            net = round(won - put_in, 2)

            all_names.add(name)
            all_players.append({
                "hand_id": hand_id,
                "player_name": name,
                "seat": p.get("seat"),
                "stack_start": round(p.get("stack_start", 0.0), 2),
                "result": net,
                "cards": p.get("cards"),
            })

        action_counter = 1
        for a in parsed.get("actions", []):
            all_names.add(a["player"])
            all_actions.append({
                "hand_id": hand_id,
                "player_name": a["player"],
                "street": a.get("street"),
                "action": a.get("action"),
                "amount": round(a.get("amount", 0.0), 2),
                "action_order": action_counter,
            })
            action_counter += 1

    existing = (
        supabase.table("poker_players")
        .select("id, name")
        .in_("name", list(all_names))
        .execute()
    )
    name_to_id = {row["name"]: row["id"] for row in existing.data}

    missing = [{"name": n} for n in all_names if n not in name_to_id]
    if missing:
        inserted = supabase.table("poker_players").insert(missing).execute()
        for row in inserted.data:
            name_to_id[row["name"]] = row["id"]

    for p in all_players:
        p["player_id"] = name_to_id[p.pop("player_name")]
    for a in all_actions:
        a["player_id"] = name_to_id[a.pop("player_name")]

    if all_hands:
        supabase.table("hands").upsert(all_hands).execute()
    if all_players:
        supabase.table("hand_players").insert(all_players).execute()
    if all_actions:
        supabase.table("actions").insert(all_actions).execute()

    print(f"✅ Moved {len(all_hands)} hands into session {session_id}")
