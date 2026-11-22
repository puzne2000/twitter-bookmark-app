# Twitter Bookmark App

A macOS tool for quickly saving links with a short description: press a global hotkey, type a
note, done. Entries go to a JSON file you can search later from the terminal. Despite the name,
it works for any URL.

It works together with [headless_scrapper](https://github.com/puzne2000/headless_scrapper), a
small local server that writes descriptions for you (see "Automatic descriptions" below).

## Setup

Both projects use Python 3.11 (Homebrew), each with its own virtual environment kept **outside
Google Drive** so Drive doesn't sync thousands of package files:

```bash
python3.11 -m venv ~/.local/share/venvs/twitter-bookmark-app
~/.local/share/venvs/twitter-bookmark-app/bin/pip install -r requirements.txt
```

Set up headless_scrapper the same way (its README has the steps), at
`~/.local/share/venvs/headless_scrapper`.

macOS must allow the hotkey: System Settings → Privacy & Security → **Input Monitoring** and
**Accessibility**, for the app that runs the launcher (usually Terminal). Quit and reopen
Terminal after changing this. The app prints "This process is not trusted!" at startup even when
the hotkey works, so ignore that line and just try the hotkey.

## Running

Double-click `run_twitter_app2.command`. It:

1. starts the headless_scrapper server if it isn't already running (port 5000),
2. starts the app, which hides itself and waits for the hotkey.

Keep that Terminal window open; closing it quits the app. Logs:
`~/Library/Logs/twitter-bookmark-app/app.log` and `server.log`.

## Saving a link

1. Copy a URL.
2. Press **Cmd+Shift+V**. The window opens with the link filled in. If the clipboard has no URL,
   you hear the Frog sound and nothing opens.
3. Type a description, press **Enter**, then **Enter** again to confirm.
   **Shift+Enter** adds a new line; **Esc** or **Cmd+W** cancels.

**Already saved?** If the link is already in the open file, the window shows its saved
description and a note saying when it was saved. Saving then updates that entry (its
description, and an `updated` date) instead of adding a duplicate. With several copies of a
link, the newest one is used. (JSON files only.)

### Saving files

PDFs and images (`.pdf .png .jpg .jpeg .heic .gif .webp`) can be bookmarked too: copy the file
in Finder (**Cmd+C**) or copy its path (**Option+Cmd+C**), then press **Cmd+Shift+V**. The entry
stores the file's full path where it is; no copy is made, so if you move or rename the file
later the path no longer works (the description still helps you find it). **Tab** sends the file
itself to the description server.

### Automatic descriptions

Press **Tab** in the description box instead of Enter. The app sends the link (and what you typed,
as a draft) to the headless_scrapper server, which reads the page and asks an AI model for a short
description. A box then shows the result for you to edit; Enter saves it. Your draft is saved in
the `draft` field.

## Where entries go

The **Save to:** drop-down at the bottom of the entry window shows the file entries go to and
lists every JSON file in `output/`; pick one and it stays selected for later saves. **New file…**
creates an empty one, **Other file…** picks any JSON (or CSV) file (also under the File menu).
Each time the app starts it goes back to `output/merged.json`. Each entry has `date`, `time`,
`url`, `draft` and `description` (plus `updated` once edited).

Only pick a CSV that the app itself created: in any other CSV it adds its own header row in the
middle of the file.

## Searching saved entries: `view_json.py`

```bash
~/.local/share/venvs/twitter-bookmark-app/bin/python view_json.py               # output/merged.json
~/.local/share/venvs/twitter-bookmark-app/bin/python view_json.py output/AI.json
~/.local/share/venvs/twitter-bookmark-app/bin/python view_json.py --all         # every .json in output/
```

Type a keyword (or Enter for everything), then use single keys:
**N**/Enter next, **P** previous, **S** new search, **C** copy URL, **L** open in Safari,
**D** delete (written back to the file the entry came from), **Q** quit.

`view_csv.py` is the older CSV version of the same viewer.

## One-off import scripts

| Script | What it does |
| --- | --- |
| `import_from_safari.py` | Reads `Bookmarks.plist` and writes `safari_bookmarks.csv` |
| `descriptions_for_bookmarks.py` | Sends each bookmark to the headless_scrapper server and writes a CSV with descriptions |
| `csv_to_json.py` | Adds rows from every CSV in `input/` to `output/merged.json` that aren't already there; never removes or changes existing entries (see `README_csv_to_json.md`) |
| `rtf_to_csv.py` | Converts the old RTF log format (no longer used) to CSV |

## License

MIT
