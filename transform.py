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
    session_row = make_json_safe(session_row) #prevent datetime from bugging
    session = supabase.table("sessions").insert(session_row).execute() # insert new session
    session_id = session.data[0]["id"] # fetch the unique session id

    # fetch all succesfully parsed from staging table

    successful_parse = (
        supabase.table("staging_hands")
        .select("id, parsed")
        .eq("status", "success")
        .execute()
    )

    # collect all data into main memory first
    all_hands = []
    all_players = []
    all_actions = []
    all_names = set()

    # for every block that is succesfully parsed

    for record in successful_parse.data:
        parsed = record["parsed"] or {}  #if parsed exists
        if not parsed:
            continue

        hand_id = parsed["id"]

        all_hands.append({ #appending hand information
            "id": hand_id,
            "session_id": session_id,
            "gamemode": parsed.get("gamemode"),
            "sb": parsed.get("stakes", {}).get("sb"),
            "bb": parsed.get("stakes", {}).get("bb"),
            "hand_datetime": parsed.get("datetime"),
        })

        for p in parsed.get("players", []):
            all_names.add(p["name"]) #add each new plauer to all names
            all_players.append({
                "hand_id": hand_id,
                "player_name": p["name"],
                "seat": p.get("seat"),
                "stack_start": p.get("stack_start"),
                "result": p.get("result"),
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
                "amount": a.get("amount"),
                "action_order": action_counter,
            })
            action_counter += 1 

    
    #premap existing pokerplayers  to their ids, so no requerying the supabase table with getplayer
    existing = (
        supabase.table("poker_players")
        .select("id, name")
        .in_("name", list(all_names)) #where name is in all names select the id
        .execute()
    )
    name_to_id = {row["name"]: row["id"] for row in existing.data}  #mapping name to id where they already exist

    missing = [{"name": n} for n in all_names if n not in name_to_id]
    if missing:
        inserted = supabase.table("poker_players").insert(missing).execute()  #inserting missing players
        for row in inserted.data:
            name_to_id[row["name"]] = row["id"] #for all added platers map there name to id, so we have a dictionary of all players to ids

    for p in all_players: # for each player replace the player_name with a player id
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
