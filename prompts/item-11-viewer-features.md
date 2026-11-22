# Task: viewer features for `view_json.py` (plan item 11)

## Goal

Add four features to `view_json.py`, the terminal viewer for saved bookmarks:

1. **Reload when the file changes.** If the file being viewed changes on disk while the viewer
   is open (the bookmark app saved an entry, another viewer deleted one), the viewer picks up the
   change instead of showing, and later writing back, stale data.
2. **View several files at once.** `--all` already loads every `.json` in `output/`. Add a way
   to pick several specific files (e.g. several file arguments), so not only "one" or "all".
3. **Edit entries.** Change an entry's description (and possibly draft) from inside the viewer.
4. **Save backups.** Protect the files against a bad delete or edit.

The work is done when all four work, are tested on copies of the data, are documented in
`README.md`, and are committed (not pushed) in the `twitter-bookmark-app` repo.

## Decisions to take to the user first

The user wants each decision explained in chat **one at a time**, in plain language that assumes
no knowledge of the code, with a recommendation and the reason, and waits for the answer before
the next one. Don't use a question tool for these, since answering in chat lets them push back.
Check the facts a choice rests on in the code, or by running it, before presenting it, and say
which you did. Write each answer into the code comments or README where it applies.

Decisions that come up in this task:

- **Editing:** how you edit a description in a terminal. Options include opening `$EDITOR` or
  `nano` on a temporary file, or typing a replacement line. Also whether the draft is editable,
  and whether an edit sets the `updated` field (see the data notes below).
- **Backups:** when (before every write, or once per session), where (next to the file in
  `output/`, or outside Google Drive), and how many to keep.
- **Reload:** whether to check before every action, poll in the background, or check only before
  writing. Also what happens if the entry on screen was deleted or changed by someone else.
- **Several files:** how they're chosen (arguments, an interactive picker, a pattern).

## Where things are

- Project: `/Users/guykindler/My Drive/python stuff/twitter bookmark app`. Git repo
  `puzne2000/twitter-bookmark-app`, branch `main`. The folder is synced by Google Drive.
- `view_json.py`, about 220 lines. It uses `click` for options, reads single keys with
  `get_key()`, searches with `search_rows()` and prints with `print_entry()`. Keys starting
  with `_` are hidden from search and display. Each loaded entry is tagged with `FILE_KEY`
  (`_viewer_file`), which is never saved. `save_file(data, json_file)` writes back only the
  entries belonging to that file, and delete uses it.
- `twitter app2.py` is the Tkinter bookmark app (hotkey Cmd+Shift+V). It writes to the same
  files, usually `output/merged.json`, while the viewer may be open.
- Data in `output/`: `merged.json` (about 2,400 entries), `AI.json` (9), `שג.json` (empty
  list). Files are JSON arrays written with `json.dump(..., ensure_ascii=False, indent=2)`.
  Keep that format so diffs stay small.
- Python environment, outside Drive on purpose:
  `~/.local/share/venvs/twitter-bookmark-app/bin/python`. Add any new package there and to
  `requirements.txt`, but prefer the standard library.

## Data notes that affect the design

- **Entry fields.** App-saved entries have `date`, `time`, `url`, `draft`, `description`, and
  `updated` after an edit in the app. Entries imported from Safari have `url`, `folder`, `title`,
  `description` and `_source_file`, usually with no date.
- **The app finds an entry by `url` + `date` + `time`.** When the hotkey brings up a saved
  link, the app updates the newest entry with that url, and finds it again at save time by
  matching all three fields. An edit in the viewer must not change those three fields, or the
  app will add a duplicate instead of updating.
- **URLs repeat.** 662 URLs appear more than once, so never use the URL alone to identify an
  entry.
- **Some `url` values are local file paths** to PDFs or images. The viewer's L key, `open -a
  Safari <url>`, works for those too.
- **`csv_to_json.py` re-adds rows deleted from `merged.json`** when it's run again. That's
  documented and accepted, so don't change it here.
- **Hebrew text appears in descriptions and file names.** Keep everything UTF-8.

## How to work

- **Never test against the real files in `output/`.** Copy them to a scratch folder and point
  the viewer there (it uses the relative `output/` folder, so run it from the scratch
  directory). The user's data is not in git, and Google Drive is its only backup.
- The viewer is interactive. Test the logic by importing its functions, or by driving it with
  piped input where that works.
- Commit in logical steps with clear messages. Don't push: the user approves pushes.
- When done, report what changed, what you tested and how, and anything you didn't verify.
