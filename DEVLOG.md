# DEVLOG

This file documents the development process of the Poker Hand Data Pipeline project.  
It is meant to track completed work, design decisions, and next steps.

---

## Stage 1 – Raw Data Capture
**Date:** 2025-09-23  
- **What we did:**  
  - Created `hands.txt` containing raw PokerStars hand history logs.  
  - Confirmed real-world formatting (multiple sessions, summaries, etc.).  
- **Why:**  
  - This is the "source of truth" for the entire pipeline.  
  - Needed a realistic dataset to drive parser development.  
- **Next:**  
  - Build parser to reliably split this raw text into structured blocks.

---

## Stage 2 – Parsing & Error Handling
**Date:** 2025-09-24  
- **What we did:**  
  - Wrote regex-based parser (`parse.py`) to extract hand headers, seats, hole cards, and results.  
  - Added `log_error` for robust error tracking.  
  - Implemented block-splitting (`parse_file_to_staging_blocks`) so each hand is independent.  
- **Why:**  
  - Needed structured data before storing in a database.  
  - Error logging prevents silent failures and helps debugging malformed hands.  
- **Next:**  
  - Validate parsing against `hands.txt`.  
  - Add tests with pytest.

---

## Stage 3 – Testing & Debugging
**Date:** 2025-09-25  
- **What we did:**  
  - Wrote `tests/test_parse.py` with 4 key tests:
    1. Split into correct number of hand blocks.
    2. Parse a single hand successfully.
    3. Ensure *all* hands parse cleanly.
    4. Check players/stacks/results extracted correctly.  
  - Ran pytest, found bugs (see `BUGLOG.md`).  
  - Fixed off-by-one in block splitting.  
  - Fixed parser returning empty dict when no header found.  
- **Why:**  
  - Reliable unit tests ensure parser correctness.  
  - Each regression caught early.  
- **Next:**  
  - Extend parser to handle actions (bets, raises, folds).  
  - Store parsed hands in a staging database.

---

## Stage 4 – Data Pipeline Architecture (Planned)
**Date:** TBD  
- **Planned Work:**  
  - **Staging DB:** Store raw blocks, parsed JSON, parse status.  
  - **ETL Flow:**  
    - Extract raw hand block.  
    - Parse into structured dict.  
    - Transform into relational schema (hands, players, actions).  
    - Load into Postgres/Supabase.  
  - **Why:**  
    - Ensures recoverability.  
    - Separates raw data from cleaned relational DB.  
- **Next:**  
  - Write schema migrations.  
  - Implement Python ingestion functions.  

---

## Stage 5 – Insights & Analytics (Future)
**Date:** TBD  
- **Planned Features:**  
  - Compute win/loss per session.  
  - Track hands played per hour.  
  - Visualize bankroll graph.  
  - Potential pipeline to ML (hand clustering, tilt detection).  
- **Why:**  
  - Turn raw data into actionable insights.  
  - Adds project value beyond simple parsing.

---

## Stage 6 – Productionization (Future)
**Date:** TBD  
- **Planned Work:**  
  - Expose REST API for inserting and retrieving parsed hands.  
  - Frontend integration (upload hand history → view dashboard).  
  - CI/CD with GitHub Actions for tests and schema migrations.  
- **Why:**  
  - Make pipeline usable for end-users.  
  - Teach real-world deployment and data engineering skills.


### Decision: Staging Layer with JSONB
We introduced a staging table (`staging_hands`) where every raw hand block and its parsed output is stored. The parsed data is initially a Python dictionary, which we convert to JSONB before insertion. This ensures:
- **Auditability**: raw text and parsed results are always preserved.
- **Clean separation**: only validated data flows into the main relational schema.
- **Flexibility**: staging data can later be re-processed or pulled into ML pipelines without polluting production tables.

This mirrors real-world ETL pipelines and adds robustness for debugging and future analytics.
