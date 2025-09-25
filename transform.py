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

    #creating a session
    session_row = {"started_at": datetime.utcnow(), "notes": session_notes or "", "user_id": user_id or None}
    session_row = make_json_safe(session_row)
    session = supabase.table("sessions").insert(session_row).execute()
    session_id = session.data[0]["id"] #grab id of the created session

    #fetch successfully parsed hands
    successful_parse = supabase.table("staging_hands").select("id, parsed").eq("status", "success").execute()

    for record in successful_parse.data:
        parsed = record["parsed"] or {}
        if not parsed or not parsed.get("datetime"):
            print(f"⚠️ Skipping hand {parsed.get('id')} — missing datetime")
            continue

        hand_id = parsed["id"]

       # 3. Insert into hands
        supabase.table("hands").upsert({
            "id": hand_id,
            "session_id": session_id,
            "gamemode": parsed.get("gamemode"),
            "sb": parsed.get("stakes", {}).get("sb"),
            "bb": parsed.get("stakes", {}).get("bb"),
            "hand_datetime": parsed.get("datetime")
        }).execute()

        # 4. Insert hand_players
        for p in parsed.get("players", []):
            player_id = get_player(p["name"])
            supabase.table("hand_players").insert({
                "hand_id": hand_id,
                "player_id": player_id,
                "seat": p.get("seat"),
                "stack_start": p.get("stack_start"),
                "result": p.get("result"),
                "cards": p.get("cards"),
            }).execute()

        # 5. Insert actions
        for a in parsed.get("actions", []):
            player_id = get_player(a["player"])
            supabase.table("actions").insert({
                "hand_id": hand_id,
                "player_id": player_id,
                "street": a.get("street"),
                "action": a.get("action"),
                "amount": a.get("amount"),
            }).execute()
        print(f"✅ Moved {len(successful_parse.data)} hands into session {session_id}")