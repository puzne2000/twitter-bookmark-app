import csv
import sys

try:
    import pyperclip
    HAS_CLIP = True
except ImportError:
    HAS_CLIP = False
import subprocess

CSV_FILE = 'poop.csv'

def load_csv():
    with open(CSV_FILE, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    headers = rows[0]
    data = rows[1:]
    return headers, data

def search_rows(rows, keyword):
    if not keyword:
        return rows
    keyword = keyword.lower()
    return [row for row in rows if any(keyword in (cell or '').lower() for cell in row)]

def print_entry(headers, row, idx, total):
    print(f"\nEntry {idx+1} of {total}")
    print("=" * 40)
    for h, v in zip(headers, row):
        print(f"{h}:\n{v}\n")
    print("=" * 40)

def copy_to_clipboard(text):
    if HAS_CLIP:
        pyperclip.copy(text)
        print("URL copied to clipboard.")
    else:
        # Fallback for macOS
        try:
            p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
            p.communicate(input=text.encode('utf-8'))
            print("URL copied to clipboard (pbcopy).")
        except Exception as e:
            print("Clipboard copy not supported (install pyperclip for cross-platform support).", e)

def launch_in_safari(url):
    try:
        subprocess.run(['open', '-a', 'Safari', url], check=True)
        print(f"Launched Safari at {url}")
    except Exception as e:
        print(f"Failed to launch Safari: {e}")

def main():
    headers, data = load_csv()
    print(f"Loaded {len(data)} entries from {CSV_FILE}.")
    while True:
        keyword = input("Enter search keyword (or press Enter to view all, or Q to quit): ").strip()
        if keyword.lower() == 'q':
            break
        filtered = search_rows(data, keyword)
        print(f"Found {len(filtered)} matching entries.")
        if not filtered:
            print("No entries to display. Try another search.")
            continue
        idx = 0
        total = len(filtered)
        url_idx = headers.index('url') if 'url' in headers else 2
        while total > 0:
            print_entry(headers, filtered[idx], idx, total)
            cmd = input("[N]ext, [P]revious, [S]earch, [C]lipboard, [L]aunch, [Q]uit: ").strip().lower()
            if cmd == '' or cmd == 'n':
                if idx < total - 1:
                    idx += 1
                else:
                    print("Already at last entry.\a")
            elif cmd == 'p':
                if idx > 0:
                    idx -= 1
                else:
                    print("Already at first entry.\a")
            elif cmd == 's':
                break  # Break to outer search loop
            elif cmd == 'c':
                url = filtered[idx][url_idx]
                copy_to_clipboard(url)
            elif cmd == 'l':
                url = filtered[idx][url_idx]
                launch_in_safari(url)
            elif cmd == 'q':
                return
            else:
                print("Unknown command. Use N, P, S, C, L, or Q.")

if __name__ == '__main__':
    main() 