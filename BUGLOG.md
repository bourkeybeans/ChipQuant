# 🐛 Bug Log — Poker Hand Parser

## Bug 1: Incorrect hand count (51 instead of 50)
**Symptom:**  
`test_split_blocks` failed with  
```
assert 51 == 50
```  
The splitter was returning 51 blocks from a file with only 50 hands.  

**Cause:**  
The parser treated both `"*********** # X **************"` divider lines and `"PokerStars Hand #..."` headers as block starts, producing an extra dummy block.  

**Fix:**  
Adjusted `parse_file_to_staging_blocks` to only split on `"PokerStars Hand #"` and filter out non-hand blocks:  

```python
return [b for b in blocks if b.strip().startswith("PokerStars Hand #")]
```

---

## Bug 2: Header regex too strict (no `id` captured)
**Symptom:**  
`test_parse_single_hand` failed with  
```
AssertionError: assert 'id' in {'players': []}
```  

**Cause:**  
The header regex assumed stakes would always be floats with two decimals, and spacing after the colon would be consistent. Real hand histories included variations like `$5` or `$0.05`, and inconsistent spacing.  

**Fix:**  
Relaxed the regex to support integers or floats:  

```python
header = re.compile(
    r"^PokerStars Hand #(\d+):\s+(.+)\s+\(\$(\d+(?:\.\d+)?)/\$(\d+(?:\.\d+)?) USD\)\s+-\s+(\d{4}/\d{2}/\d{2}) (\d{2}:\d{2}:\d{2}) ET$"
)
```

---

## Bug 3: Player seats not captured (`players` empty)
**Symptom:**  
`test_player_data_extracted` failed with  
```
IndexError: list index out of range
```  
because `parsed["players"]` was empty.  

**Cause:**  
The seat regex did not properly capture seat lines due to greedy matching of player names.  

**Fix:**  
Updated seat regex to correctly capture seat number, player name, and stack (both integers and floats):  

```python
seat = re.compile(
    r"^Seat (\d+): ([^(]+) \(\$(\d+(?:\.\d+)?) in chips\)$"
)
```

---

## ✅ Lessons Learned
1. Real-world data is **messy** → regex patterns must allow variation in formatting.  
2. Tests catch hidden assumptions → the “51 vs 50” test revealed edge cases in block splitting.  
3. Iterative refinement works → fail → inspect → tweak → retest.  
4. Validation prevents silent data loss → without tests, bugs would have caused dropped or misparsed hands.  
