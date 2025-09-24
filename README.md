# ♠️ QuantChip — Poker Hand Data Pipeline

QuantChip is a robust data pipeline for parsing, validating, and analyzing PokerStars hand histories.  
It is designed to demonstrate data engineering and analytics skills with a real-world style ETL flow.

---

## 🚀 Features
- **Regex-based parser** → Extracts hands, players, stakes, results from raw PokerStars logs.
- **Block splitting** → Each hand is processed independently for resilience.
- **Error handling** → Logs parsing errors without stopping ingestion.
- **Staging database (Supabase/Postgres)** → Stores raw + parsed hands in JSONB with status flags.
- **Unit tests with Pytest** → Ensures correctness and protects against regressions.
- **Full project logs** →  
  - [DEVLOG.md](DEVLOG.md) — development timeline  
  - [BUGLOG.md](BUGLOG.md) — parser bugs + fixes  
  - [DECISIONS.md](DECISIONS.md) — architectural decisions

---

## 📂 Project Structure
