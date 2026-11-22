#!/usr/bin/env python3
"""
view_json.py ver1.1

Search, view and manage the bookmark entries saved by the bookmark app. Each JSON file is an
array of dictionaries (one per entry).

Usage:
    python view_json.py [json_file ...]   # e.g. "AI merged" = output/AI.json output/merged.json
    python view_json.py --all            # every .json file in the output folder

If no file is specified, defaults to 'output/merged.json'.

Features:
- Search entries by keyword
- Navigate through entries with N/P keys
- Copy URLs to clipboard
- Launch URLs in Safari
- Edit an entry's description (E) or draft (R)
- Delete entries
- View several files at once (each entry shows its file)
- Reload automatically when a file changes on disk (e.g. the bookmark app saved an entry)
- Back up a file before every change
"""

import json
import os
import re
import shlex
import shutil
import sys
import tempfile
import time
from datetime import datetime

try:
    import pyperclip
    HAS_CLIP = True
except ImportError:
    HAS_CLIP = False
import subprocess

# CONSTANTS
DEFAULT_FOLDER = 'output'
DEFAULT_FILENAME = 'merged.json'
FILE_KEY = '_viewer_file'  # which file an entry was loaded from; hidden, never saved
BACKUP_DIR = 'backups'     # subfolder next to each file
BACKUPS_TO_KEEP = 30       # per file




# Cross-platform immediate key input
def get_key():
    """Get a single key press without requiring Enter"""
    if os.name == 'nt':  # Windows
        import msvcrt
        return msvcrt.getch().decode('utf-8').lower()
    else:  # Unix-like systems (macOS, Linux)
        import tty
        import termios

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            return ch.lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def resolve_file(name):
    '''
    Turn a command-line file name into a path: an existing path is used as is; otherwise a
    short name is looked up in the output folder, with or without ".json"
    (so "AI" means output/AI.json). Returns None if nothing matches.
    '''
    candidates = [name, os.path.join(DEFAULT_FOLDER, name)]
    if not name.lower().endswith('.json'):
        candidates.append(os.path.join(DEFAULT_FOLDER, name + '.json'))
    return next((c for c in candidates if os.path.isfile(c)), None)

def get_files(names):
    '''
    The files to view: each name resolved with resolve_file (duplicates dropped), or
    output/merged.json when no names are given. Raises click.BadParameter for unknown names.
    Decided with the user: several files are chosen by listing them on the command line.
    '''
    if not names:
        return [os.path.join(DEFAULT_FOLDER, DEFAULT_FILENAME)]
    files, seen = [], set()
    for name in names:
        path = resolve_file(name)
        if path is None:
            available = ', '.join(os.path.basename(f) for f in get_filenames()) \
                if os.path.isdir(DEFAULT_FOLDER) else 'none'
            raise click.BadParameter(f"no such file: {name} (files in {DEFAULT_FOLDER}/: {available})",
                                     param_hint='JSON_FILES')
        if os.path.abspath(path) not in seen:
            seen.add(os.path.abspath(path))
            files.append(path)
    return files

def get_filenames():
    '''
    Return every .json file in DEFAULT_FOLDER, sorted by name.
    (Backups live in a subfolder, so they are not included.)
    '''
    return sorted(
        os.path.join(DEFAULT_FOLDER, name)
        for name in os.listdir(DEFAULT_FOLDER)
        if name.lower().endswith('.json')
    )


# ---------------------------------------------------------------------------
# Reading and writing files
# ---------------------------------------------------------------------------

def read_entries(json_file):
    '''
    Read a JSON array of entries as it is on disk (no tags). A missing or empty file is [].
    If the file can't be parsed (for instance the app is half-way through writing it), try
    once more after a short pause before giving up with the error.
    '''
    if not os.path.exists(json_file):
        return []
    for attempt in range(2):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                text = f.read()
            data = json.loads(text) if text.strip() else []
            break
        except json.JSONDecodeError:
            if attempt:
                raise
            time.sleep(0.3)
    if not isinstance(data, list):
        raise ValueError(f"{json_file} is not a list of entries")
    return data

def load_json(json_file):
    '''
    Load a JSON array of entries and tag each with the file it came from,
    so changes can be written back to the right file.
    '''
    data = read_entries(json_file)
    for entry in data:
        entry[FILE_KEY] = json_file
    return data

def write_entries(entries, json_file):
    '''
    Write entries in the same format the bookmark app uses (indent=2, UTF-8 kept as is), via a
    temporary file that then replaces the original, so a crash never leaves half a file.
    '''
    folder = os.path.dirname(os.path.abspath(json_file))
    fd, tmp = tempfile.mkstemp(prefix='.viewer-', suffix='.tmp', dir=folder)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
        os.replace(tmp, json_file)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise

def save_file(data, json_file):
    '''
    Write back the entries that belong to json_file, without the internal tag.
    '''
    write_entries([strip_tag(e) for e in data if e.get(FILE_KEY) == json_file], json_file)

def backup_file(json_file):
    '''
    Copy json_file into a "backups" folder next to it, as <name>.<YYYY-MM-DD_HHMMSS>.json,
    and delete all but the newest BACKUPS_TO_KEEP backups of that file.
    Decided with the user: back up before every write (delete or edit), in output/backups/
    (a subfolder, so neither the app's "Save to:" list nor --all picks the backups up), and
    keep the last 30 per file. Returns the backup's path, or None if there was no file.
    '''
    if not os.path.exists(json_file):
        return None
    folder = os.path.join(os.path.dirname(os.path.abspath(json_file)), BACKUP_DIR)
    os.makedirs(folder, exist_ok=True)
    stem = os.path.splitext(os.path.basename(json_file))[0]
    stamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    pattern = re.compile(re.escape(stem) + r'\.\d{4}-\d\d-\d\d_\d{6}(?:_(\d+))?\.json$')
    # Several writes in the same second get _2, _3, ... (one more than the highest so far).
    same_second = [pattern.match(name) for name in os.listdir(folder)
                   if name.startswith(f"{stem}.{stamp}") and pattern.match(name)]
    if same_second:
        n = 1 + max(int(m.group(1) or 1) for m in same_second)
        target = os.path.join(folder, f"{stem}.{stamp}_{n}.json")
    else:
        target = os.path.join(folder, f"{stem}.{stamp}.json")
    shutil.copy2(json_file, target)

    def sort_key(name):
        m = pattern.match(name)
        return (name[:len(stem) + 18], int(m.group(1) or 1))
    backups = sorted((name for name in os.listdir(folder) if pattern.match(name)), key=sort_key)
    for name in backups[:-BACKUPS_TO_KEEP]:
        os.remove(os.path.join(folder, name))
    return target


# ---------------------------------------------------------------------------
# Identifying entries
# ---------------------------------------------------------------------------

def strip_tag(entry):
    return {k: v for k, v in entry.items() if k != FILE_KEY}

def entry_id(entry):
    '''
    What identifies an entry even after its description is edited. App-saved entries:
    url + date + time (the same three fields the bookmark app uses to find an entry again,
    so they are never changed here). Safari imports have no date: url + title + folder.
    URLs alone repeat, so they are never enough.
    '''
    if entry.get('date') or entry.get('time'):
        key = ('app', entry.get('url'), entry.get('date'), entry.get('time'))
    else:
        key = ('other', entry.get('url'), entry.get('title'), entry.get('folder'))
    return (entry.get(FILE_KEY),) + key

def find_entry(rows, entry):
    '''
    Position of entry in rows: an identical entry if there is one, otherwise one with the
    same identity (url/date/time) whose content changed. None if it is not there.
    '''
    plain = strip_tag(entry)
    for i, row in enumerate(rows):
        if row.get(FILE_KEY) == entry.get(FILE_KEY) and strip_tag(row) == plain:
            return i
    ident = entry_id(entry)
    for i, row in enumerate(rows):
        if entry_id(row) == ident:
            return i
    return None

def change_entry(json_file, entry, change):
    '''
    Apply a change to one entry, working on the file as it is on disk right now (not on the
    viewer's copy), so nothing another program saved meanwhile is lost.
    change(e) edits e in place; change=None deletes the entry.
    Returns 'ok', 'changed' (someone else changed the entry since it was shown, so nothing
    was written) or 'gone' (the entry is no longer in the file, nothing was written).
    The file is backed up before it is written.
    '''
    entries = read_entries(json_file)
    plain = strip_tag(entry)
    pos = next((i for i, e in enumerate(entries) if e == plain), None)
    if pos is None:
        ident = entry_id(plain)
        if any(entry_id(e) == ident for e in entries if isinstance(e, dict)):
            return 'changed'
        return 'gone'
    if change is None:
        del entries[pos]
    else:
        change(entries[pos])
    backup_file(json_file)
    write_entries(entries, json_file)
    return 'ok'


# ---------------------------------------------------------------------------
# The loaded files
# ---------------------------------------------------------------------------

def file_signature(json_file):
    try:
        st = os.stat(json_file)
        return (st.st_mtime_ns, st.st_size)
    except FileNotFoundError:
        return None

class Library:
    '''
    The entries of one or more files, kept in step with the files on disk.
    Decided with the user: check every file's modification time before each key press and
    re-read a file whenever it changed, so the screen never shows (or acts on) stale data.
    '''

    def __init__(self, files):
        self.files = list(files)
        self.entries = {}
        self.signatures = {}
        for f in self.files:
            self.reload(f)

    @property
    def data(self):
        return [e for f in self.files for e in self.entries[f]]

    def reload(self, json_file):
        sig = file_signature(json_file)
        self.entries[json_file] = load_json(json_file)
        self.signatures[json_file] = sig

    def refresh(self):
        '''Re-read every file that changed on disk. Returns True if any did.'''
        changed = False
        for f in self.files:
            if file_signature(f) == self.signatures.get(f):
                continue
            try:
                self.reload(f)
            except (OSError, ValueError) as e:
                print(f"\n{f} changed on disk but could not be read ({e}); showing the old copy.")
                continue
            changed = True
            print(f"\n{f} changed on disk - reloaded (now {len(self.entries[f])} entries).")
        return changed


def relocate(old, idx, new, quiet=False):
    '''
    After the data changed, find where the entry that was on screen (old[idx]) is in the new
    search results. If it changed, say so and show the new version; if it is gone, say so
    and move on to the next entry that still exists. Returns the new index.
    '''
    current = old[idx]
    pos = find_entry(new, current)
    if pos is not None:
        if not quiet and strip_tag(new[pos]) != strip_tag(current):
            print("The entry on screen was changed by another program; showing the new version.")
        return pos
    if not quiet:
        print("The entry on screen was removed by another program.")
    for row in old[idx + 1:]:
        pos = find_entry(new, row)
        if pos is not None:
            return pos
    return max(0, len(new) - 1)


def search_rows(rows, keyword):
    if not keyword:
        return list(rows)
    keyword = keyword.lower()
    return [row for row in rows if any(keyword in (str(value) or '').lower() for key, value in row.items() if not key.startswith('_'))]

def print_entry(row, idx, total, show_file=False):
    where = f"   [{os.path.basename(row[FILE_KEY])}]" if show_file else ""
    print(f"\nEntry {idx+1} of {total}{where}")
    print("=" * 40)
    for key, value in row.items():
        if not key.startswith('_'):
            print(f"{key}:\n{value}\n")
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

def edit_text(text):
    '''
    Let the user edit text in a terminal editor: $VISUAL or $EDITOR if set, otherwise nano.
    Returns the edited text, or None if the editor could not be run or failed.
    Decided with the user: edit in an editor on a temporary file (comfortable for long and
    multi-line descriptions, and for Hebrew), rather than on a single input line.
    '''
    editor = os.environ.get('VISUAL') or os.environ.get('EDITOR') or 'nano'
    fd, path = tempfile.mkstemp(prefix='bookmark-', suffix='.txt')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(text)
        try:
            result = subprocess.run(shlex.split(editor) + [path])
        except OSError as e:
            print(f"Could not start the editor '{editor}': {e}")
            return None
        if result.returncode != 0:
            print(f"The editor '{editor}' exited with an error; nothing saved.")
            return None
        with open(path, 'r', encoding='utf-8') as f:
            new = f.read()
    finally:
        os.remove(path)
    if not text.endswith('\n'):
        new = new.rstrip('\n')  # editors add a final newline
    return new

def edit_field(row, field):
    '''
    Edit one field (description or draft) of the entry on screen and write it back.
    Decided with the user: E edits the description, R the draft; an edit sets "updated" to
    now, in the app's format; url, date and time are never changed (the app finds an entry
    again by those three). Returns the change_entry result, or None if nothing was written.
    '''
    old = str(row.get(field) or '')
    new = edit_text(old)
    if new is None:
        return None
    if new == old:
        print("No change.")
        return None
    if field == 'description' and not new.strip():
        print("Empty description - nothing saved.")
        return None
    updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    def change(entry):
        entry[field] = new
        entry['updated'] = updated
    result = change_entry(row[FILE_KEY], row, change)
    if result != 'ok':
        print(NOT_WRITTEN[result])
        print(f"Your {field} (not saved, copy it if you want it):\n{new}\n")
    return result

NOT_WRITTEN = {
    'changed': "Another program changed this entry since it was shown, so nothing was written. "
               "Here it is again:",
    'gone': "Another program removed this entry, so nothing was written.",
}

# command line options
import click
@click.command()
@click.argument('json_files', nargs=-1)
@click.option('--all', '-a', is_flag=True, default=False, help="If set, view all files in the output folder.")
def main(json_files, all):
    """
    View and search entries in one or more JSON files (default: output/merged.json).
    A file in the output folder can be given by its short name: "AI" means output/AI.json.
    """
    if all:
        files = get_filenames()
        source = f"{len(files)} files in {DEFAULT_FOLDER}/"
    else:
        files = get_files(json_files)
        source = files[0] if len(files) == 1 else f"{len(files)} files ({', '.join(os.path.basename(f) for f in files)})"
    lib = Library(files)
    show_file = len(files) > 1

    print(f"Loaded {len(lib.data)} entries from {source}.")
    while True:
        keyword = input("Enter search keyword (or press Enter to view all, or Q to quit): ").strip()
        if keyword.lower() == 'q':
            break
        lib.refresh()
        filtered = search_rows(lib.data, keyword)
        print(f"Found {len(filtered)} matching entries.")
        if not filtered:
            print("No entries to display. Try another search.")
            continue
        idx = 0
        while filtered:
            # Pick up changes other programs made since the last key press.
            if lib.refresh():
                old, filtered = filtered, search_rows(lib.data, keyword)
                if not filtered:
                    print("No more entries to display.")
                    break
                idx = relocate(old, idx, filtered)
            total = len(filtered)
            row = filtered[idx]
            # Get URL key from the current entry, fallback to first non-underscore key if no 'url' field
            url_key = 'url' if 'url' in row else next((key for key in row.keys() if not key.startswith('_')), None)

            print_entry(row, idx, total, show_file)
            print("[N]ext, [P]revious, [S]earch, [C]lipboard, [L]aunch, [E]dit description, d[R]aft, [D]elete, [Q]uit: ", end='', flush=True)
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
                url = row.get(url_key, '')
                copy_to_clipboard(url)
            elif cmd == 'l':
                url = row.get(url_key, '')
                launch_in_safari(url)
            elif cmd == 'd':
                entry_file = row[FILE_KEY]
                result = change_entry(entry_file, row, None)
                if result != 'ok':
                    print(NOT_WRITTEN[result])
                    continue  # the next refresh shows what changed
                lib.reload(entry_file)
                old, filtered = filtered, search_rows(lib.data, keyword)
                print(f"Entry deleted and {entry_file} updated (backup in {BACKUP_DIR}/).")
                if not filtered:
                    print("No more entries to display.")
                    break
                idx = relocate(old, idx, filtered, quiet=True)
            elif cmd in ('e', 'r'):
                field = 'description' if cmd == 'e' else 'draft'
                if edit_field(row, field) == 'ok':
                    entry_file = row[FILE_KEY]
                    lib.reload(entry_file)
                    old, filtered = filtered, search_rows(lib.data, keyword)
                    print(f"{field.capitalize()} saved to {entry_file} (backup in {BACKUP_DIR}/).")
                    if find_entry(filtered, row) is None:
                        print("(The entry no longer matches your search.)")
                    if not filtered:
                        print("No more entries to display.")
                        break
                    idx = relocate(old, idx, filtered, quiet=True)
            elif cmd == 'q':
                return
            else:
                print("Unknown command. Use N, P, S, C, L, E, R, D, or Q.")

if __name__ == '__main__':
    main()
