from db import supabase

#inset data into staging table
def insert_into_staging(raw_text, parsed=None, status="pending", errors=None):
    data = {
        "raw_text": raw_text,
        "parsed": parsed or {},
        "status": status,
        "errors": errors or [],
    }
    return supabase.table("staging_hands").insert(data).execute()


# fetching staging records
def fetch_all_staging():
    return supabase.table("staging_hands").select("*").execute()


# fetching failed blocks
def fetch_failed():
    return supabase.table("staging_hands").select("*").eq("status", "failed").execute()