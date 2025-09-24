import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from parse import parse_file_to_staging_blocks, parse_hand

SAMPLE_FILE = os.path.join(os.path.dirname(__file__), "hands.txt")

def test_split_blocks():
    blocks = parse_file_to_staging_blocks(SAMPLE_FILE)
    assert len(blocks) == 50  # we know there are 50 hands
    assert blocks[0].startswith("PokerStars Hand #")
    assert "SUMMARY" in blocks[0]

def test_parse_single_hand():
    blocks = parse_file_to_staging_blocks(SAMPLE_FILE)
    parsed, errs = parse_hand(blocks[0])

    assert errs == []  # should parse cleanly
    assert "id" in parsed
    assert isinstance(parsed["players"], list)
    assert len(parsed["players"]) > 0

def test_all_hands_parse():
    blocks = parse_file_to_staging_blocks(SAMPLE_FILE)
    bad = []
    for raw in blocks:
        parsed, errs = parse_hand(raw)
        if errs:
            bad.append((parsed.get("id"), errs))

    assert bad == [], f"Some hands failed parsing: {bad}"

def test_player_data_extracted():
    blocks = parse_file_to_staging_blocks(SAMPLE_FILE)
    parsed, _ = parse_hand(blocks[0])

    # at least one player should have a stack and seat
    assert "seat" in parsed["players"][0]
    assert "stack_start" in parsed["players"][0]

    # ensure collected pot mapped
    any_collected = any(p["result"] > 0 for p in parsed["players"])
    assert any_collected
