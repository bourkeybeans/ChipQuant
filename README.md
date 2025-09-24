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
```
QuantChip/
├── parse.py             # Parsing logic (regex → dict)
├── staging.py           # Staging DB functions
├── db.py                # Supabase client setup
├── ingest.py            # ETL: parse blocks → staging
│
├── hands.txt            # Sample raw hand history (local only)
│
├── tests/
│   └── test_parse.py    # Pytest suite
│
├── BUGLOG.md
├── DECISIONS.md
├── DEVLOG.md
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup

### 1. Clone the repo
```bash
git clone https://github.com/bourkeybeans/QuantChip.git
cd QuantChip
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
Create a `.env` file:
```env
SUPABASE_URL=your-url-here
SUPABASE_KEY=your-key-here
```

### 4. Run parser + staging ingestion
```bash
python ingest.py
```

### 5. Run tests
```bash
pytest -v
```

---

## 🏗️ Roadmap
- [x] Parse PokerStars hand histories with regex.
- [x] Split into blocks + add unit tests.
- [x] Insert parsed/failed hands into staging DB.
- [ ] Design clean relational schema (`hands`, `players`, `actions`).
- [ ] Transform staging → clean DB.
- [ ] Add analytics (bankroll trends, VPIP/PFR, positional stats).
- [ ] Optional ML layer (leak detection, strategy insights).

---

## 📜 License
MIT — free to use and adapt.
