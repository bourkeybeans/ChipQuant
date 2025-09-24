# 📓 Design Decisions — Poker Hand Data Pipeline

## 1. Regex-Based Parsing (vs. Grammar Libraries)
We chose **regular expressions** to parse PokerStars hand histories into structured data.  
- **Why:** Regex is fast, deterministic, easy to unit test, and well-suited to fixed-format logs.  
- **Trade-off:** Less flexible than grammar parsers if formats change, but quicker to implement and explain.  
- **Future:** If logs diversify, a grammar-based parser (e.g., `lark`, `antlr`) could replace regex with minimal disruption.

---

## 2. Block Splitting by Hand Header
Hand histories are processed one at a time by splitting the raw text file into **blocks**, each beginning with `"PokerStars Hand #"`.
- **Why:** Prevents partial parses from corrupting entire files. Each block can be validated independently.  
- **Benefit:** Cleaner error handling (failed hands don’t block the pipeline).  
- **Lesson:** Early tests revealed extra “divider lines” inflated counts; we fixed this by splitting strictly on `"PokerStars Hand #"` only.

---

## 3. Error Logging Instead of Silent Fails
Parsing errors are captured in an `errors` structure rather than stopping execution.  
- **Why:** Real-world hand histories are messy. Failures should be visible, not ignored.  
- **Benefit:** Pipeline resilience — one malformed hand doesn’t stop ingestion of others.  
- **Future:** Error data can help improve parsing rules or detect corrupted hand histories.

---

## 4. Unit Testing with Pytest
We created a suite of **pytest tests** covering:  
- Splitting into the correct number of blocks.  
- Parsing a single hand.  
- Parsing all hands without failure.  
- Extracting player stacks and results correctly.  

**Why:** Guarantees correctness and catches hidden assumptions (e.g., header format variations).  
**Lesson:** Tests exposed three bugs (extra blocks, header regex too strict, seat regex mismatch), which were fixed and documented in `BUGLOG.md`.

---

## 5. Staging Database with JSONB
All parsed hands are first loaded into a **staging table** (`staging_hands`) before entering the clean relational schema.  
- **Why:** Staging ensures auditability, recoverability, and separates “raw/quarantined” data from validated analytics data.  
- **How:** Store raw text, parsed dict (as JSONB), status (`success`/`failed`), errors, and timestamp.  
- **Benefit:**  
  - Production tables stay clean.  
  - Failed parses can be retried later.  
  - Staging doubles as a research source for ML.  
