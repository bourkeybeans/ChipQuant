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
    session_row = {"started_at": datetime.utcnow(), "notes": session_notes or "", "user_id": user_id}
    session_row = make_json_safe(session_row)
    session = supabase.table("sessions").insert(session_row).execute()
    session_id = session.data[0]["id"]

    successful_parse = supabase.table("staging_hands").select("id, parsed").eq("status", "success").execute()

    all_hands = []
    all_players = []
    all_actions = []
    player_cache = {}

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
            "hand_datetime": parsed.get("datetime")
        })

        # players
        for p in parsed.get("players", []):
            player_id = get_player(p["name"])  # cached version
            all_players.append({
                "hand_id": hand_id,
                "player_id": player_id,
                "seat": p.get("seat"),
                "stack_start": p.get("stack_start"),
                "result": p.get("result"),
                "cards": p.get("cards"),
            })

        # actions
        for a in parsed.get("actions", []):
            player_id = get_player(a["player"])
            all_actions.append({
                "hand_id": hand_id,
                "player_id": player_id,
                "street": a.get("street"),
                "action": a.get("action"),
                "amount": a.get("amount"),
            })

    # bulk insert
    if all_hands:
        supabase.table("hands").upsert(all_hands).execute()
    if all_players:
        supabase.table("hand_players").insert(all_players).execute()
    if all_actions:
        supabase.table("actions").insert(all_actions).execute()

    print(f"✅ Moved {len(successful_parse.data)} hands into session {session_id}")
