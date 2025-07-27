# CSV to JSON Merger

This script (`csv_to_json.py`) merges all CSV files from an input folder into a single JSON file.

## Setup

1. **Install dependencies:**
   ```bash
   pip install pandas
   ```

2. **Create input folder:**
   ```bash
   mkdir input
   ```

3. **Place your CSV files in the `input` folder**

## Usage

Run the script:
```bash
python csv_to_json.py
```

The script will:
- Read all `.csv` files from the `./input` folder
- Merge all rows into a single JSON array
- Save the result to `./output/merged.json`
- Create the `output` folder if it doesn't exist

## Output Format

Each row from the CSV files becomes an object in the JSON array, with:
- **Keys:** Column names from the CSV headers
- **Values:** The data from each row
- **Additional field:** `_source_file` - shows which CSV file the record came from

## Example

**Input CSV files:**
```
# file1.csv
name,age
Alice,25
Bob,30

# file2.csv
name,city
Charlie,NYC
Diana,LA
```

**Output JSON:**
```json
[
  {
    "name": "Alice",
    "age": 25,
    "_source_file": "file1.csv"
  },
  {
    "name": "Bob", 
    "age": 30,
    "_source_file": "file1.csv"
  },
  {
    "name": "Charlie",
    "city": "NYC",
    "_source_file": "file2.csv"
  },
  {
    "name": "Diana",
    "city": "LA", 
    "_source_file": "file2.csv"
  }
]
```

## Error Handling

The script includes error handling for:
- Missing input folder
- No CSV files found
- Invalid CSV files
- File writing errors

Each error is reported with helpful messages. 