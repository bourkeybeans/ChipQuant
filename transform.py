from datetime import datetime
from db import supabase
from utils import make_json_safe


def get_player(name: str):
    
    existing = supabase.table("poker_players").select("id").eq("name", name).execute()
    if existing.data:
        return existing.data[0]["id"]
    
    new = supabase.table("poker_players").insert({"name": name}).execute()
    return new.data[0]["id"]


def staging_to_clean(user_id, session_notes=None):
    # 1. Create session
    session_row = {
        "started_at": datetime.utcnow(),
        "notes": session_notes or "",
        "user_id": user_id,
    }
    session_row = make_json_safe(session_row)
    session = supabase.table("sessions").insert(session_row).execute()
    session_id = session.data[0]["id"]

    # 2. Fetch all successful parsed hands
    successful_parse = (
        supabase.table("staging_hands")
        .select("id, parsed")
        .eq("status", "success")
        .execute()
    )

    # Collect rows
    all_hands = []
    all_players = []
    all_actions = []
    all_names = set()

    for record in successful_parse.data:
        parsed = record["parsed"] or {}
        if not parsed or not parsed.get("datetime"):
            continue

        hand_id = parsed["id"]

        # hands
        all_hands.append({
            "id": hand_id,
            "session_id": session_id,
            "gamemode": parsed.get("gamemode"),
            "sb": parsed.get("stakes", {}).get("sb"),
            "bb": parsed.get("stakes", {}).get("bb"),
            "hand_datetime": parsed.get("datetime"),
        })

        # collect player rows
        for p in parsed.get("players", []):
            all_names.add(p["name"])
            all_players.append({
                "hand_id": hand_id,
                "player_name": p["name"],  # temporarily use name, will swap to id later
                "seat": p.get("seat"),
                "stack_start": p.get("stack_start"),
                "result": p.get("result"),
                "cards": p.get("cards"),
            })

        # collect action rows
        for a in parsed.get("actions", []):
            all_names.add(a["player"])
            all_actions.append({
                "hand_id": hand_id,
                "player_name": a["player"],  # temporarily use name
                "street": a.get("street"),
                "action": a.get("action"),
                "amount": a.get("amount"),
            })

    # 3. Bulk resolve player IDs
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

    # Swap player_name → player_id
    for p in all_players:
        p["player_id"] = name_to_id[p.pop("player_name")]
    for a in all_actions:
        a["player_id"] = name_to_id[a.pop("player_name")]

    # 4. Bulk insert hands, players, actions
    if all_hands:
        supabase.table("hands").upsert(all_hands).execute()
    if all_players:
        supabase.table("hand_players").insert(all_players).execute()
    if all_actions:
        supabase.table("actions").insert(all_actions).execute()

    print(f"✅ Moved {len(all_hands)} hands into session {session_id}")
