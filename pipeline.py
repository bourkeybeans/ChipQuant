from parse import parse_file_to_staging_blocks, parse_hand
from staging import insert_into_staging
from utils import make_json_safe

def run_pipeline(file_path="raw/hands.txt"):
    raw_blocks = parse_file_to_staging_blocks(file_path)

    for raw_text in raw_blocks:
            parsed, errs = parse_hand(raw_text)
            parsed = make_json_safe(parsed)
            if errs:
                insert_into_staging(raw_text, parsed, status="failed")
            else:
                insert_into_staging(raw_text, parsed, status="success")

    print("✅ Ingestion finished. Data now in staging_hands.")

if __name__ == "__main__":
    run_pipeline()
