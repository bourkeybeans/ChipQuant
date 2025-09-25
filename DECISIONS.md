# ⚖️ Design Decisions — ChipQuant

This file records all key design decisions made during the development of the ChipQuant data pipeline, along with pros, cons, and alternatives considered.

---

## 1. Parsing Strategy (Regex vs Grammar Parser vs Manual Split)

**Decision:** Use **regex-based parsing** for hand histories.  

- ✅ Pros:  
  - Simple and lightweight.  
  - Transparent and easy to debug.  
  - Fast for line-by-line parsing.  
  - Unit-testable in isolation.  

- ❌ Cons:  
  - Regexes can become complex and fragile.  
  - Harder to maintain as formats evolve.  
  - No built-in grammar validation.  

- 🔄 Alternatives:  
  - **Grammar-based parser** (ANTLR/PLY)  
    - More robust and self-documenting grammar.  
    - But much heavier setup and learning curve.  
  - **Manual string splits**  
    - Easier to write quickly.  
    - Harder to maintain, brittle with formatting changes.  

---

## 2. Intermediate Data Structure (Python Dicts vs Custom Classes)

**Decision:** Store parsed hands as **Python dictionaries with nested lists** (`players`, `actions`).  

- ✅ Pros:  
  - Flexible and fast to prototype.  
  - Easy to convert into JSON for DB insertion.  
  - No boilerplate code (compared to classes).  

- ❌ Cons:  
  - No type safety or IDE autocomplete.  
  - Structure relies on convention.  

- 🔄 Alternatives:  
  - **Dataclasses / Pydantic models**  
    - Type validation, schema enforcement.  
    - Adds complexity early on.  
  - **Custom classes per entity (Hand, Player, Action)**  
    - OOP-friendly but overkill until schema stabilizes.  

---

## 3. Error Handling (Skip vs Crash vs Log)

**Decision:** **Log errors into a list** with stage, line, and message.  

- ✅ Pros:  
  - Pipeline keeps running, doesn’t crash on bad input.  
  - Debuggable — can trace exact failure.  
  - Fits with staging DB “success/failed” pattern.  

- ❌ Cons:  
  - Silent data issues may accumulate.  
  - Requires discipline to monitor error logs.  

- 🔄 Alternatives:  
  - **Crash on error** → strict but brittle.  
  - **Skip silently** → no crashes, but data integrity unknown.  

---

## 4. Staging Database (Use vs Skip)

**Decision:** Implement a **staging table** before clean schema.  

- ✅ Pros:  
  - Debugging: raw text and parsed JSON stored together.  
  - Separates ingestion from transformation.  
  - Future ML experiments possible using raw vs parsed.  
  - Common industry practice (mirrors data pipelines at scale).  

- ❌ Cons:  
  - Extra DB writes and storage overhead.  
  - Adds one more layer of complexity.  

- 🔄 Alternatives:  
  - **Skip staging** → insert directly into clean schema.  
    - Faster, but no audit trail for debugging.  

---

## 5. Database Schema (Normalized vs JSON-only)

**Decision:** **Normalized relational schema** (sessions, hands, players, actions).  

- ✅ Pros:  
  - Supports rich SQL queries (e.g., VPIP/PFR).  
  - Scales better for analytics.  
  - Clean separation of entities.  

- ❌ Cons:  
  - More work to design and maintain.  
  - Need joins for queries.  

- 🔄 Alternatives:  
  - **JSON-only schema** → store parsed dicts as JSONB.  
    - Faster to implement.  
    - But harder to query for analytics.  

---

## 6. Sessions (Per Upload vs Derived Later)

**Decision:** Create a **session row per pipeline run**.  

- ✅ Pros:  
  - Easy grouping of hands into sessions.  
  - Aligns with player psychology (sessions are natural units of play).  
  - Supports bankroll/session tracking later.  

- ❌ Cons:  
  - “Session” = file upload, not always true to actual play sessions.  

- 🔄 Alternatives:  
  - **Derive sessions later** → group by time gaps in hand timestamps.  
    - More accurate to real play, but harder to implement early.  

---

## 7. Insert Method (Insert vs Upsert)

**Decision:** Use **UPSERT** for `hands`.  

- ✅ Pros:  
  - Avoids duplicate errors if the same hand is reprocessed.  
  - Pipeline is idempotent (safe to re-run).  

- ❌ Cons:  
  - Slight performance overhead vs plain insert.  

- 🔄 Alternatives:  
  - **Insert only** → faster, but duplicate crashes likely.  
  - **Delete + insert** → works, but dangerous if deletes too much.  

---

## 8. Action Tracking (Detailed vs Simplified)

**Decision:** Capture **detailed player actions with streets**.  

- ✅ Pros:  
  - Enables calculation of advanced stats (VPIP, PFR, Aggression).  
  - Flexible for future ML use cases.  

- ❌ Cons:  
  - Regex complexity increases.  
  - Storage overhead for every action.  

- 🔄 Alternatives:  
  - **Simplified results-only model** → only track winners & pot sizes.  
    - Lighter, but limits analytics.  

---

## 9. Supabase (Supabase vs Local Postgres vs Other Cloud DB)

**Decision:** Use **Supabase (Postgres + SDK)**.  

- ✅ Pros:  
  - Managed hosting, no local setup required.  
  - JSONB support out of the box.  
  - Easy integration via Python SDK.  

- ❌ Cons:  
  - Internet dependency.  
  - Leaks keys if not handled securely.  

- 🔄 Alternatives:  
  - **Local PostgreSQL (pgAdmin)** → full control, but harder to share.  
  - **Neon/Cloud providers** → similar to Supabase.  

---

## 10. Data Format for DB (Dicts → JSON Safe)

**Decision:** Sanitize Python dicts into **JSON-safe structures** before insert.  

- ✅ Pros:  
  - Prevents Supabase inserts silently failing.  
  - Standardized representation (ISO strings for datetimes).  

- ❌ Cons:  
  - Adds preprocessing step.  

- 🔄 Alternatives:  
  - **Store raw text only** → no parsed JSON in staging.  
  - **Custom serialization** → more control, but overkill.  



