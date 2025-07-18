import csv
import sys
import os

try:
    import pyperclip
    HAS_CLIP = True
except ImportError:
    HAS_CLIP = False
import subprocess

# Cross-platform immediate key input
def get_key():
    """Get a single key press without requiring Enter"""
    if os.name == 'nt':  # Windows
        import msvcrt
        return msvcrt.getch().decode('utf-8').lower()
    else:  # Unix-like systems (macOS, Linux)
        import tty
        import termios
        import sys
        
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            return ch.lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def get_csv_file():
    if len(sys.argv) > 1:
        return sys.argv[1]
    else:
        return 'poop.csv'

def load_csv():
    csv_file = get_csv_file()
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    headers = rows[0]
    data = rows[1:]
    return headers, data

def search_rows(rows, keyword):
    if not keyword:
        return list(enumerate(rows))
    keyword = keyword.lower()
    return [(i, row) for i, row in enumerate(rows) if any(keyword in (cell or '').lower() for cell in row)]

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
    csv_file = get_csv_file()
    print(f"Loaded {len(data)} entries from {csv_file}.")
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
            orig_idx, row = filtered[idx]
            print_entry(headers, row, idx, total)
            print("[N]ext, [P]revious, [S]earch, [C]lipboard, [L]aunch, [D]elete, [Q]uit: ", end='', flush=True)
            cmd = get_key()
            print(cmd.upper())  # Show the key that was pressed
            if cmd == 'n' or cmd == '\r' or cmd == '\n':  # Enter or n
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
                url = row[url_idx]
                copy_to_clipboard(url)
            elif cmd == 'l':
                url = row[url_idx]
                launch_in_safari(url)
            elif cmd == 'd':
                print("Deleting entry...")
                # Remove from data using orig_idx
                del data[orig_idx]
                # Re-filter after deletion
                filtered = search_rows(data, keyword)
                total = len(filtered)
                if idx >= total:
                    idx = max(0, total - 1)
                # Save updated data to file
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    writer.writerows(data)
                print("Entry deleted and file updated.")
                if total == 0:
                    print("No more entries to display.")
                    break
            elif cmd == 'q':
                return
            else:
                print("Unknown command. Use N, P, S, C, L, D, or Q.")

if __name__ == '__main__':
    main() 