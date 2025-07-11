import csv
import requests
import re
import time
import os

INPUT_CSV = 'safari_bookmarks.csv'
OUTPUT_CSV = 'safari_bookmarks_descripbed.csv'
SERVER_URL = 'http://127.0.0.1:5000/'


def get_description(address, draft_description=None):
    data = {
        'address': address,
        'draft': draft_description or ''
    }
    try:
        response = requests.post(SERVER_URL, data=data)
        if response.ok:
            match = re.search(r'<textarea[^>]*id="resultTextarea"[^>]*>(.*?)</textarea>', response.text, re.DOTALL)
            if match:
                return match.group(1).strip()
            else:
                return response.text.strip()
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Exception: {e}"
    
def save_current_stack(rows_to_write, fieldnames):
    # Write all rows (existing and new) to output
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows_to_write:
            print(f"writing entry:\n  {row}")
            writer.writerow(row)
    return

def main():
    # Load already described URLs if output file exists
    described = {}
    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, newline='', encoding='utf-8') as outf:
            reader = csv.DictReader(outf)
            for row in reader:
                url = row.get('url')
                desc = row.get('description', '')
                if url:
                    described[url] = row
    # Prepare to update or append
    with open(INPUT_CSV, newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ['description'] if 'description' not in reader.fieldnames else reader.fieldnames
        rows_to_write = []
        for idx, row in enumerate(reader):
            if None in row:
                print(f"Skipping malformed row: {row}")
                continue
            url = row.get('url')
            if url in described and described[url].get('description'):
                # Already described, use existing
                row['description'] = described[url]['description']
                print(f"Already described: {url}")
            else:
                description = get_description(url) if url else ''
                row['description'] = description
                print(f"Described new: {url}")
                time.sleep(0.5)
            rows_to_write.append(row)
            if idx % 10 == 0 and idx != 0:
                save_current_stack(rows_to_write, fieldnames)
    # Write all rows (existing and new) to output
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows_to_write:
            writer.writerow(row)

if __name__ == '__main__':
    main() 