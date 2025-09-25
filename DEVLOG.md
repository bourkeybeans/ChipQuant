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


✅ What you’ve built

Raw ingestion

Parse PokerStars hand histories into structured dicts.

Store both raw + parsed into staging_hands.

Validation

Errors logged in staging (good vs bad parses).

Status field (success / failed).

Transform → Clean schema

Create new session per parse.

Load hands, players, actions into normalized tables.

Keep staging intact for debugging & ML later.

Idempotency

Using upsert avoids duplicate hand errors.

Pipeline can be rerun safely.

⚡ Why it’s a real pipeline

Extract → raw .txt → Python parser.

Transform → parsed dicts → JSON safe → normalized DB.

Load → Supabase staging + clean schema.

That’s literally ETL. It’s the same pattern used at big hedge funds & data teams (just scaled up with Kafka/Spark/Airflow).

🚀 What’s next (beyond the pipeline)

Now you can layer on:

Analytics: Queries for VPIP, PFR, Aggression, Winrate.

Dashboard: Flask/Streamlit/React page to visualize sessions.

Leak detection: Rule-based (and later ML).


# Dev Log

## [2025-09-25] Actions Normalization + ETL Safety Net
- **Decision:** Added a safety normalization layer in ETL to standardize actions.
- **Reasoning:**
  - Ensures database constraints are respected even if staging data is stale or partially malformed.
  - Keeps the DB consistent while allowing the parser to evolve.
- **Options Considered:**
  1. Only rely on the parser for normalization (simpler, but fails if staging has old data).
  2. Add ETL-level normalization (extra safety at cost of duplicate logic).
- **Choice:** Implement ETL normalization as a safeguard.
- **Pros:** More robust, handles legacy staging rows, prevents constraint errors.
- **Cons:** Duplicate normalization logic exists in both parser and ETL (must keep consistent).
- **Next Step:** Consider adding a reprocessor to automatically re-parse any staging rows with outdated structure.

## [2025-09-25] Staging Reset Strategy
- **Decision:** Delete/reparse staging rows after schema or parser changes.
- **Reasoning:** Old parsed JSON in staging was incompatible with new schema rules.
- **Options Considered:**
  1. Patch staging data in place.
  2. Clear staging and re-run the parser.
- **Choice:** Clear staging and re-run for simplicity.
- **Pros:** Guaranteed fresh, consistent data.
- **Cons:** Loses original staging history (unless archived).
- **Lesson Learned:** Staging is *ephemeral* by design — it’s safe to wipe/refresh after logic changes.


## [2025-09-25] Including Actions with Normalized Amounts

- **Decision:** Extend the parser to capture **every player action** (`post_small_blind`, `call`, `raise`, `bet`, `check`, `fold`) along with a normalized **numeric amount**.
- **Reasoning:**
  - Initial schema only tracked results (who collected the pot).
  - To compute *net gain/loss*, *VPIP*, *PFR*, and positional stats, the database must know how much each player contributed per street.
  - This also enables deeper analysis like EV calculation, aggression frequency, and leak detection models later.
- **Options Considered:**
  1. Only store **end results** (simpler, smaller schema, but no insight into *how* the result happened).
  2. Store actions but leave amounts as raw text (`"raises $0.05 to $0.10"`) — loses numeric structure, harder queries.
  3. Store actions with **normalized action labels** + **numeric amounts** (best for analytics).
- **Choice:** Option 3 (normalized actions + amounts).
- **Pros:**
  - Rich analytics possible (VPIP, PFR, c-bet frequency, 3-bet ranges, etc.).
  - Schema supports future ML models without refactoring.
  - Normalized values are query-friendly in SQL.
- **Cons:**
  - More parsing complexity and regex maintenance.
  - Bigger storage footprint (extra action rows per hand).
- **Lesson Learned:** Investing in action-level granularity makes the project *future-proof* for both analytics and ML leak detection.


## [2025-09-25] Normalizing Player Schema (hand_players Join Table)

- **Decision:** Replace storing players directly inside `hands` with a **normalized schema**:
  - `players` table (unique player identities).
  - `hand_players` table (join table linking `hands` ↔ `players` with seat, stack, cards, and result).
- **Reasoning:**
  - Original design stored `players` inline in each `hand` row → created a *many-to-many problem* (duplicate player names across hands).
  - Querying for stats by player name (e.g., bankroll, VPIP, win rate) would require searching across JSON blobs or denormalized rows.
- **Options Considered:**
  1. Keep `players` nested inside `hands` (simpler, no joins).
  2. Flat `players` table only (breaks because same player plays in multiple hands).
  3. Normalized `players` + `hand_players` join table (relationally correct).
- **Choice:** Option 3 (normalized schema with join table).
- **Pros:**
  - Eliminates duplication of player data.
  - Queries by player name become simple (`JOIN` on `hand_players`).
  - Easier to extend later (e.g., global player stats vs per-hand stats).
- **Cons:**
  - More complex inserts (must insert to `players` and `hand_players`).
  - Requires managing foreign keys between hands ↔ players ↔ actions.
- **Lesson Learned:** Proper normalization early prevents pain later. Separating identities (`players`) from participation (`hand_players`) aligns with relational design best practices and supports analytics/ML.
