import csv
import requests
import re
import time

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

def main():
    with open(INPUT_CSV, newline='', encoding='utf-8') as infile, \
         open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ['description']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            if None in row:
                print(f"Skipping malformed row: {row}")
                continue
            url = row.get('url')
            if url:
                description = get_description(url)
                # Optionally, sleep to avoid hammering the server
                time.sleep(0.5)
            else:
                description = ''
            row['description'] = description
            print(f"entry:\n{row}")
            writer.writerow(row)

if __name__ == '__main__':
    main() 