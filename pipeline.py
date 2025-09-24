from parse import parse_file_to_staging_blocks, parse_hand
from staging import insert_into_staging

def run_pipeline(file_path="raw/hands.txt"):
    raw_blocks = parse_file_to_staging_blocks(file_path)

    for raw_text in raw_blocks:
        try:
            parsed, errs = parse_hand(raw_text)
            if errs:
                insert_into_staging(raw_text, parsed, status="failed")
            else:
                insert_into_staging(raw_text, parsed, status="success")
        except Exception:
            insert_into_staging(raw_text, None, status="failed")

    print("✅ Ingestion finished. Data now in staging_hands.")

if __name__ == "__main__":
    run_pipeline()
