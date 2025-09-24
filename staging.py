from db import supabase

# Insert a parsed or raw hand into staging
def insert_into_staging(raw_text, parsed=None, status="pending", errors=None):
    data = {
        "raw_text": raw_text,
        "parsed": parsed,
        "status": status,
        "errors": errors,
    }
    return supabase.table("staging_hands").insert(data).execute()


# Fetch all staging records (useful for debugging)
def fetch_all_staging():
    return supabase.table("staging_hands").select("*").execute()


# Fetch only failed parses
def fetch_failed():
    return supabase.table("staging_hands").select("*").eq("status", "failed").execute()


# Mark a staging record as reprocessed
def update_status(record_id, status, parsed=None, errors=None):
    return supabase.table("staging_hands").update({
        "status": status,
        "parsed": parsed,
        "errors": errors
    }).eq("id", record_id).execute()
