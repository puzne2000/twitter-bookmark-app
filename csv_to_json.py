#!/usr/bin/env python3
"""
csv_to_json.py

Adds the rows of every CSV file in ./input to ./output/merged.json.

Entries already in merged.json are never removed or changed, so entries saved by the
bookmark app are safe. A CSV row is added only if merged.json doesn't already hold an
identical row from the same CSV file (all of the CSV's columns equal). Each added row
gets a `_source_file` field naming its CSV.

Note: a row you deleted from merged.json (e.g. in view_json.py) is added again the next
time you run this, because the script can't tell a deleted row from a new one.

Empty CSV cells are written as JSON null.

Usage:
    python csv_to_json.py
"""

import json
import math
from collections import Counter
from pathlib import Path

import pandas as pd

INPUT_FOLDER = Path("./input")
OUTPUT_FILE = Path("./output") / "merged.json"
SOURCE_KEY = "_source_file"


def clean(value):
    """Turn pandas' NaN (an empty cell) into None so the JSON stays valid."""
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def row_key(source, columns, record):
    """What makes two rows 'the same': their CSV file and every CSV column's value."""
    return (source,) + tuple(
        None if clean(record.get(col)) is None else str(clean(record.get(col)))
        for col in columns
    )


def load_existing():
    if not OUTPUT_FILE.exists():
        return []
    with open(OUTPUT_FILE, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise SystemExit(f"{OUTPUT_FILE} is not a JSON list; not touching it.")
    # Older versions of this script wrote empty cells as NaN, which isn't valid JSON.
    return [{k: clean(v) for k, v in entry.items()} for entry in data]


def main():
    if not INPUT_FOLDER.exists():
        print(f"Error: input folder '{INPUT_FOLDER}' does not exist.")
        return

    csv_files = sorted(INPUT_FOLDER.glob("*.csv"))
    if not csv_files:
        print(f"No CSV files found in '{INPUT_FOLDER}'.")
        return

    existing = load_existing()
    print(f"{OUTPUT_FILE} has {len(existing)} entries.\n")

    added_total = 0
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            print(f"  {csv_file.name}: could not read ({e}), skipped")
            continue

        columns = list(df.columns)
        # How many identical copies of each row merged.json already holds for this file
        have = Counter(
            row_key(csv_file.name, columns, e)
            for e in existing if e.get(SOURCE_KEY) == csv_file.name
        )

        added = []
        for record in df.to_dict("records"):
            key = row_key(csv_file.name, columns, record)
            if have[key] > 0:
                have[key] -= 1  # matched an entry that's already there
                continue
            entry = {k: clean(v) for k, v in record.items()}
            entry[SOURCE_KEY] = csv_file.name
            added.append(entry)

        existing.extend(added)
        added_total += len(added)
        print(f"  {csv_file.name}: {len(df)} rows, {len(added)} added")
        for entry in added[:10]:
            print(f"      + {entry.get('url', '')}")
        if len(added) > 10:
            print(f"      ... and {len(added) - 10} more")

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False, allow_nan=False)

    print(f"\nAdded {added_total} entries; {OUTPUT_FILE} now has {len(existing)}.")


if __name__ == "__main__":
    main()
