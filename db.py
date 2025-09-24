from supabase import create_client
import os

url = os.getenv("https://oqfyxbkyupiafnvnixqf.supabase.co")
key = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9xZnl4Ymt5dXBpYWZudm5peHFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg3MjcxMzcsImV4cCI6MjA3NDMwMzEzN30.oDUvy-_tqPgrtfYuEHb4sRIRpoxr4nyefYSVHKWJvzE")

supabase = create_client(url, key)
