from parse import parse_file_to_staging_blocks, parse_hand
from staging import insert_into_staging
from transform import staging_to_clean
from utils import make_json_safe
import time

def run_pipeline(file_path, user_id, session_notes=None):
    t0 = time.time()

    # 1. Parse raw file into blocks
    blocks = parse_file_to_staging_blocks(file_path)
    t1 = time.time()
    print(f"⏱ Split file into {len(blocks)} blocks in {t1 - t0:.2f}s")

    # 2. Insert into staging
    insert_start = time.time()
    for raw_text in blocks:
        parsed, errs = parse_hand(raw_text)
        parsed = make_json_safe(parsed)

        status = "failed" if errs else "success"
        insert_into_staging(
            raw_text=raw_text,
            parsed=parsed,
            status=status,
            errors=errs
        )
    t2 = time.time()
    print(f"⏱ Parsed + inserted {len(blocks)} hands into staging in {t2 - insert_start:.2f}s")

    # 3. Move successful staging rows → clean schema
    transform_start = time.time()
    staging_to_clean(user_id, session_notes=session_notes)
    t3 = time.time()
    print(f"⏱ Transform staging → clean in {t3 - transform_start:.2f}s")

    total_time = t3 - t0
    print(f"✅ Pipeline complete in {total_time:.2f}s: raw → staging → clean")

if __name__ == "__main__":
    # Example call — don’t forget to pass a valid user_id
    run_pipeline("hands.txt", user_id=1)
