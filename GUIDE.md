# User guide

How to use the bookmark app day to day: save links and files with a description, have one
written for you, and find them again later. For setup and how things work inside, see
[README.md](README.md).

There are three parts:

- **The bookmark app** saves what you copied, with a description, when you press
  **Cmd+Shift+V**.
- **The description server** runs quietly in the background and writes descriptions for you
  when you press **Tab**. It uses OpenAI, so it needs the internet.
- **The viewer** (`view_json.py`) searches and edits what you saved, in Terminal.

## 1. Starting up

1. In Finder, open the `twitter bookmark app` folder (in Google Drive, under `python stuff`).
2. Double-click `run_twitter_app2.command`. A Terminal window opens.
3. It says either "Description server already running." or "Description server is up.", and
   then the app starts. You won't see a window: the app hides until you press the hotkey.

**Keep that Terminal window open.** Closing it quits the app, and so does **File → Exit** in the
app's menu. The description server keeps running in the background after the app quits, which is
harmless. The next start just finds it already running.

Run only one copy. If you double-click the launcher twice, two apps listen for the hotkey.

If the Terminal window says "WARNING: server did not start", saving still works, but **Tab**
won't. See [Troubleshooting](#9-troubleshooting).

## 2. Saving a link

1. Copy a link (for example, select the address bar in Safari and press **Cmd+C**).
2. Press **Cmd+Shift+V**, from any app. The window opens with the link filled in and the
   cursor in the **Description** box.
3. Type a description.
   - **Shift+Enter** starts a new line.
4. Press **Enter**. A small **Done?** window appears.
5. Press **Enter** again to save. "Entry Saved" appears briefly, the window hides, and you are
   back in the app you were using.
   - **Esc** in the Done? window takes you back to editing.

To give up without saving, press **Esc** or **Cmd+W** in the Description box.

If the clipboard holds no link or file, you hear the **Frog** sound and nothing opens.

**Always type a description.** If you press Enter with the box empty, a "Please fill in both
fields" warning appears. After you click OK, "Entry Saved" appears anyway, but **nothing was
saved** and the link is gone from the window. Press Cmd+Shift+V again to start over.

## 3. Automatic descriptions (Tab)

Press **Tab** instead of Enter, and the description server writes the description for you.

1. Copy a link and press **Cmd+Shift+V** as usual.
2. If you like, type a few words first: a draft or a hint ("the part about sleep"). You can
   also leave it empty.
3. Press **Tab**. The window hides right away. Ignore the "Entry Saved" message for now: it
   comes too early.
4. After a few seconds (longer for big PDFs), a box called **Description obtained** opens with
   the server's description.
5. Edit it if you want, then press **Enter** to save it. **Shift+Enter** starts a new line.

What you typed in step 2 is kept with the entry as its **draft**.

If you press **Esc** (or **Cmd+W**) in the Description obtained box, the server's text is
thrown away and **what you typed in step 2 is saved instead**. If you typed nothing, you get the
"Please fill in both fields" warning and nothing is saved.

The server must be running (see [Starting up](#1-starting-up)). If something goes wrong, the box
shows `Error: …` or `Exception: …` instead of a description. **Don't press Enter on an error**,
or the error text is saved as the description. Press Esc to keep what you typed, or replace the
text with your own. [Troubleshooting](#9-troubleshooting) explains the common errors.

## 4. Links you saved before

If the link is already in the file you're saving to, the window says so when it opens:

> Already saved (2026-11-02 14:31:07). Saving will update that entry.

The Description box shows what you wrote then. Change it and save as usual (Enter, or Tab), and
**that entry is updated** instead of a second copy being added. Its original date stays, and an
`updated` date is added. If the link was saved several times, the newest copy is the one updated.

The app only checks the file chosen in **Save to:** (see [section 6](#6-choosing-which-file-to-save-to)),
and only JSON files. If you switch files with the window open, it checks again.

## 5. Saving PDFs and images

You can bookmark files of these types: **.pdf .png .jpg .jpeg .heic .gif .webp**.

1. In Finder, select the file and press **Cmd+C**. Or copy its full path with **Option+Cmd+C**.
2. Press **Cmd+Shift+V**. The window opens with the file's full path in the link field.
3. Type a description and press **Enter** twice, or press **Tab** to have the server read the
   file and describe it.

**The entry points to the file where it is now; no copy is made.** If you later move or rename
the file, the saved path no longer leads to it. The description will still help you find it.

Other file types (a Word document, say) aren't supported. Depending on the file's name, you
either hear the Frog sound, or the window opens with just the bare file name (like
`report.docx`) as the link. That's useless as a bookmark, so press **Esc**.

## 6. Choosing which file to save to

At the bottom of the window, **Save to:** shows the file your entries go to. Click it to choose
another:

- every JSON file in the `output` folder, with `merged.json` first;
- **New file…** creates a new, empty file (save it in `output` so it shows up in the list next
  time);
- **Other file…** picks any JSON (or CSV) file anywhere.

The **File** menu has the same choices: **Open...** and **New...**.

Your choice stays for the following saves, until the app restarts. **Each time the app starts, it
goes back to `merged.json`.** (If `merged.json` is missing, it asks you to pick a file at start.)

If you add a file to `output` while the app is running, it appears in the list the next time you
press Cmd+Shift+V.

## 7. Finding things later: the viewer

The viewer runs in Terminal. Open Terminal (a new window, not the app's), then paste these two
lines:

```bash
cd "/Users/guykindler/My Drive/python stuff/twitter bookmark app"
```

```bash
~/.local/share/venvs/twitter-bookmark-app/bin/python view_json.py
```

The first line matters: the viewer only finds the `output` folder when run from the app's folder.

### Which files

With nothing after `view_json.py`, it opens `merged.json`. To open others, add their names after
it:

| Add this | To view |
| --- | --- |
| *(nothing)* | `merged.json` |
| `AI` | `output/AI.json` (the folder and `.json` can be left out) |
| `AI merged` | both files together |
| `--all` | every JSON file in `output` |
| a full path | any JSON file, also outside `output` |

When more than one file is open, each entry shows which file it's in, e.g.
`Entry 3 of 40   [AI.json]`.

### Searching

1. The viewer asks for a search word. Type one and press **Enter**. It finds entries containing
   that text anywhere (description, draft, link, date), ignoring upper and lower case.
2. Or just press **Enter** to go through everything.
3. Typing **Q** quits, so you can't search for the letter "q" on its own.

### Keys

While an entry is shown, press a single key (no Enter needed):

| Key | Does |
| --- | --- |
| **N** or **Enter** | next entry |
| **P** | previous entry |
| **S** | new search |
| **C** | copy the link (or file path) to the clipboard |
| **L** | open the link (or file) in Safari |
| **E** | edit the description |
| **R** | edit the draft |
| **D** | delete the entry: **at once, with no "are you sure?"**, but a backup is made first |
| **Q** | quit |

### Editing (E and R)

1. Press **E** (description) or **R** (draft). The text opens in a simple editor in the same
   Terminal window.
2. Change the text. Use the arrow keys to move around; the mouse doesn't work here.
3. Press **Ctrl+X**, then **Y** to save, then **Enter**.
   - To leave without saving, press **Ctrl+X**; if it asks whether to save, press **N**.
4. Back in the viewer, it says "Description saved to …".

What happens behind the scenes:
- The entry gets an `updated` date, as when the app updates it.
- The link and the original date never change, so the app still recognises the entry.
- If you leave without changes, nothing is written. An empty description isn't saved (an empty
  draft is).
- If the app or another viewer changed that entry while you were editing, your text is **not**
  saved. Instead it's printed on screen so you can copy it, and you can try again.

### Safe to leave open

You can keep the viewer open while saving with the app. Before each key press it checks whether
a file changed and re-reads it, saying "changed on disk - reloaded". If the entry on screen was
changed elsewhere, you see the new version. If it was deleted elsewhere, the viewer says so and
moves on. Deleting or editing never wipes out something the app saved in the meantime.

## 8. Where your data lives, and backups

- Everything you save is in the `output` folder inside the app's folder: `merged.json`,
  `AI.json` and any others you created. Files you picked with **Other file…** stay wherever they
  are.
- The folder is in **Google Drive**, so Drive syncs it. Your entries are **not** in git or on
  GitHub; only the code is.
- **Backups:** before each delete or edit in the viewer, the file is copied to `output/backups/`,
  named with the date and time, for example `merged.2026-11-22_153000.json`. The newest 30 per
  file are kept and older ones deleted. Drive syncs these too.
- The app itself makes **no** backup when it saves or updates an entry. For those changes, Drive
  is the only safety net (Drive also keeps earlier versions of each file; on drive.google.com,
  right-click the file → **File information → Manage versions**).

### Undoing a change made in the viewer

1. Quit the viewer (**Q**).
2. In Finder, open `output/backups` and find the newest backup from before the mistake.
3. Copy it over the real file. In Terminal (in the app's folder, as in section 7), for example:

   ```bash
   cp output/backups/merged.2026-11-22_153000.json output/merged.json
   ```

Anything saved to that file after the backup was made is lost, so pick the newest backup that is
still good.

## 9. Troubleshooting

### The hotkey does nothing

1. **Is the app running?** Its Terminal window (from `run_twitter_app2.command`) must be open.
   If not, double-click the launcher.
2. **Is the clipboard right?** If you hear the Frog sound, the app is fine; the clipboard just
   doesn't hold a link or a supported file.
3. **Is keyboard access allowed?** Open **System Settings → Privacy & Security**. Under both
   **Input Monitoring** and **Accessibility**, make sure **Terminal** is listed and switched on.
   Then quit Terminal completely with **Cmd+Q** and double-click the launcher again.
4. If that still fails, add and switch on the Homebrew **Python** app in the same two lists too.

The Terminal window always shows "This process is not trusted! Input event monitoring will not
be possible…" at start, **even when the hotkey works**. Ignore it and just try the hotkey.

### Tab gives "Error: …"

The message says what went wrong.

- **`Error: 403`** means the description server isn't running. Something else on your Mac (the
  AirPlay Receiver) answered instead. Close the app's Terminal window, then double-click
  `run_twitter_app2.command` again: it starts the server.
- **`Exception: …Connection refused…`** also means the server isn't running. Do the same.
- **`Error: …` with a longer message** comes from the server itself (for example, the page
  couldn't be opened, or OpenAI refused). Try again later, or write the description yourself.

In every case, press **Esc** rather than Enter, so the error text isn't saved (see
[section 3](#3-automatic-descriptions-tab)).

### Logs

If something odd happens, the details are in two files (open them in TextEdit or Console):

- `~/Library/Logs/twitter-bookmark-app/app.log`: the app
- `~/Library/Logs/twitter-bookmark-app/server.log`: the description server

(In Finder: **Go → Go to Folder…** and paste `~/Library/Logs/twitter-bookmark-app`.)

### Don't pick a CSV the app didn't create

In **Other file…**, choose a CSV file only if the app itself made it. In any other CSV, the app
adds its own header row in the middle of the file. This happened once.

### Deleted entries came back

Running `csv_to_json.py` again adds back any entry you deleted from `merged.json`, if it is still
in a CSV in the `input` folder. The script can't tell a deleted entry from a new one. It prints
the links it added; check that list and delete them again in the viewer if needed.

## 10. Rarely used: importing old bookmarks

These scripts brought the old Safari bookmarks in, mostly in July 2025. You probably won't need
them again. They run by hand, in this order:

1. `import_from_safari.py` turns a copy of Safari's `Bookmarks.plist` into
   `safari_bookmarks.csv`. It reads the plist from the **app's folder**, despite what its comment
   says about your home folder, so copy it there first.
2. `descriptions_for_bookmarks.py` sends each bookmark to the description server and writes
   `safari_bookmarks_described.csv`. The server must be running.
3. Move that CSV into the `input` folder yourself.
4. `csv_to_json.py` adds new rows from every CSV in `input` to `merged.json`. It never removes or
   changes entries, but see [Deleted entries came back](#deleted-entries-came-back).

Details are in [README.md](README.md#one-off-import-scripts) and `README_csv_to_json.md`.
