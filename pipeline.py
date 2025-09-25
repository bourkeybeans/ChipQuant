from parse import parse_file_to_staging_blocks, parse_hand
from staging import insert_into_staging
from transform import staging_to_clean
from utils import make_json_safe

def run_pipeline(file_path, user_id, session_notes=None):
    # 1. Parse raw file into blocks
    blocks = parse_file_to_staging_blocks(file_path)

    # 2. Insert into staging
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

    # 3. Move successful staging rows → clean schema
    staging_to_clean(user_id, session_notes=session_notes)

    print("✅ Pipeline complete: raw → staging → clean")


if __name__ == "__main__":
    run_pipeline("hands.txt")
