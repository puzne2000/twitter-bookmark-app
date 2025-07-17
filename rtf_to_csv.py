import re
import csv

# Input and output file names
rtf_file = 'poop.rtf'
csv_file = 'poop.csv'

# Regular expressions for extracting fields (allowing for any whitespace and RTF control words)
re_date = re.compile(r'Date:\s*(?:\\[a-zA-Z0-9]+[ ]*)*\\b0\s*([0-9\-: ]+)', re.IGNORECASE)
re_link = re.compile(r'Link:\s*(?:\\[a-zA-Z0-9]+[ ]*)*\\b0\s*(\S+)', re.IGNORECASE)
re_draft = re.compile(
    r'Draft:\s*(?:\\[a-zA-Z0-9]+[ ]*)*\\b0\s*(.*?)(?=(?:\\par)?\s*(?:Description:|Date:|Link:|Draft:|$))',
    re.IGNORECASE | re.DOTALL
)
re_description = re.compile(r'Description:\s*(?:\\[a-zA-Z0-9]+[ ]*)*\\b0\s*(.*?)(?:\\par|$)', re.IGNORECASE | re.DOTALL)

# Read the RTF file
with open(rtf_file, 'r', encoding='utf-8') as f:
    content = f.read()
    pattern = r'(?:^|\\par|\n)[^D]*Date:'
    matches = re.findall(pattern, content)

    print(f"Number of matches is {len(matches)}")

# Split entries by searching for the "Date:" field at the start of each entry,
# where the field starts with \f followed by a digit, then \b Date:

entries = re.split(r'(?:^|\\par|\n)[^D]*Date:', content)


# The first split part may be preamble, so we skip it and prepend "Date:" back to each entry
entries = ['\\f1\\b Date: ' + e for e in entries[1:]]


print(f"{len(entries)} entries")
print(entries[35])

rows = []
for i, entry in enumerate(entries):
    print(i)
    # Extract date and time
    date_match = re_date.search(entry)
    if date_match:
        date_time = date_match.group(1).strip()
        if ' ' in date_time:
            date, time = date_time.split(' ', 1)
        else:
            date, time = date_time, ''
    else:
        print("no date match")
        date, time = '', ''
    # Extract link
    link_match = re_link.search(entry)
    url = link_match.group(1).strip() if link_match else ''
    if url.endswith('\\par'):  # TODO would have been better to correct this by changing the regexp search
        url = url[:-4].rstrip()
    if url.endswith('\\'):
        url = url[:-1]
    # Extract draft (optional)
    draft_match = re_draft.search(entry)
    draft = draft_match.group(1).strip() if draft_match else ''
    # Remove RTF control words (e.g., \f0, \b, etc.)
    draft = re.sub(r'\\[a-zA-Z0-9]+\s*', '', draft)
    # Remove any backslash that may be followed by a newline
    draft = re.sub(r'\\\n', '', draft)
    # Extract description
    description_match = re_description.search(entry)
    description = description_match.group(1).strip() if description_match else ''
    # Only add rows with at least a date or url
    if date or url or description or draft:
        print(f"date: {date}\ntime: {time}\nurl: {url}\ndraft: {draft}\ndescription: {description}\n")
        rows.append([date, time, url, draft, description])
# Write to CSV
with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['date', 'time', 'url', 'draft', 'description'])
    writer.writerows(rows)

print(f'Wrote {len(rows)} rows to {csv_file}') 