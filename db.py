from supabase import create_client
import os

url = os.getenv("YOURURL")
key = os.getenv("YOURKEY")

supabase = create_client(url, key)
