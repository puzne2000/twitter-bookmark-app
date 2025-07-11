import re
import csv

# Input and output file names
rtf_file = 'poop.rtf'
csv_file = 'poop.csv'

# Regular expressions for extracting fields (allowing for any whitespace)
re_date = re.compile(r'\\b\s*Date:\s*\\b0\s*([0-9\-: ]+)', re.IGNORECASE)
re_link = re.compile(r'\\b\s*Link:\s*\\b0\s*(\S+)', re.IGNORECASE)
re_draft = re.compile(r'\\b\s*Draft:\s*\\b0\s*(.*?)(?:\\par|$)', re.IGNORECASE | re.DOTALL)
re_description = re.compile(r'\\b\s*Description:\s*\\b0\s*(.*?)(?:\\par|$)', re.IGNORECASE | re.DOTALL)

# Read the RTF file
with open(rtf_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Split entries by double newlines (\par\n\par)
entries = re.split(r'\\par\s*\\par', content)

rows = []
for i, entry in enumerate(entries):
    # Extract date and time
    date_match = re_date.search(entry)
    if date_match:
        date_time = date_match.group(1).strip()
        if ' ' in date_time:
            date, time = date_time.split(' ', 1)
        else:
            date, time = date_time, ''
    else:
        date, time = '', ''
    # Extract link
    link_match = re_link.search(entry)
    url = link_match.group(1).strip() if link_match else ''
    # Extract draft (optional)
    draft_match = re_draft.search(entry)
    draft = draft_match.group(1).strip() if draft_match else ''
    # Extract description
    description_match = re_description.search(entry)
    description = description_match.group(1).strip() if description_match else ''
    # Only add rows with at least a date or url
    if date or url or description or draft:
        rows.append([date, time, url, draft, description])

# Write to CSV
with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['date', 'time', 'url', 'draft', 'description'])
    writer.writerows(rows)

print(f'Wrote {len(rows)} rows to {csv_file}') 