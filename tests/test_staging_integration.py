import pytest
from staging import insert_into_staging, fetch_all_staging

@pytest.mark.integration
def test_insert_and_fetch_roundtrip():
    raw_text = "PokerStars Hand #999999: Hold'em No Limit ($0.01/$0.02 USD) - 2025/09/23 10:00:00 ET"
    parsed = {"id": 999999, "gamemode": "Hold'em No Limit", "stakes": {"sb": 0.01, "bb": 0.02}}

    # Insert into Supabase staging table
    insert_response = insert_into_staging(raw_text, parsed, status="success")
    assert insert_response.data is not None

    record_id = insert_response.data[0]["id"]

    # Fetch back from Supabase
    fetch_response = fetch_all_staging()
    ids = [r["id"] for r in fetch_response.data]
    assert record_id in ids

    # Clean up (optional, so you don’t pollute staging)
    from db import supabase
   # supabase.table("staging_hands").delete().eq("id", record_id).execute()
