from db import supabase

resp = supabase.table("staging_hands").insert({
    "raw_text": "PokerStars Hand #111...",
    "parsed": {"id": 111, "gamemode": "Test"},
    "status": "success"
}).execute()



print(resp)