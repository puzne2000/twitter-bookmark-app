# Task: a user guide for the bookmark app and description server (plan item 15)

## Goal

Write a plain-language guide to using the two tools day to day. The reader is the person who
owns them, not a developer: assume no knowledge of the code. The READMEs already cover setup and
internals; this guide covers use. It is done when it covers everything below, every instruction
in it has been checked against the current code (not this prompt), and it is saved in the place
the user chose.

Item 11 (viewer features: reload on change, several files, editing, backups) may have landed
before you start. Read the current `view_json.py` and README, and describe what is actually
there.

## Decisions to take to the user first

The user wants each decision explained in chat **one at a time**, in plain language, with a
recommendation and the reason, and waits for the answer before the next one. Don't use a
question tool for these. Check the facts behind a choice before presenting it, and say how you
checked.

- **Format and place.** For example: a `GUIDE.md` in the repo, next to `README.md`, that
  travels with the code; or a shareable document outside the repo. Ask; don't assume.
- **Scope.** Whether to include the one-off import scripts (`import_from_safari.py`,
  `descriptions_for_bookmarks.py`, `csv_to_json.py`), which are rarely used.

## What the guide must cover

1. **Starting up:** double-click `run_twitter_app2.command`. It starts the description server if
   needed, then the app. Keep that Terminal window open, because closing it quits the app.
2. **Saving a link:** copy a URL, press Cmd+Shift+V, type a description, then Enter and Enter
   again to confirm. Shift+Enter adds a new line; Esc or Cmd+W cancels. If the clipboard holds no
   link or file, the Frog sound plays and nothing opens.
3. **Automatic descriptions:** Tab instead of Enter. What you typed becomes the draft, and an
   edit box shows the result. The server must be running.
4. **Links already saved:** the window shows the saved description and when it was saved, and
   saving updates that entry instead of adding a duplicate.
5. **Saving files:** PDFs and images (.pdf .png .jpg .jpeg .heic .gif .webp), from a Finder copy
   (Cmd+C) or a copied path (Option+Cmd+C). The entry points to the file where it is, so moving
   the file breaks the path.
6. **Choosing the file:** the "Save to:" drop-down at the bottom of the window lists the JSON
   files in `output/`, plus New file… and Other file…. It goes back to `merged.json` when the app
   restarts.
7. **Finding things later:** `view_json.py`. Searching, the single-key commands, `--all`, and
   whatever item 11 added.
8. **Troubleshooting.** These all happened while the project was being set up:
   - **The hotkey does nothing.** Is the app running (is its Terminal window open)? Is keyboard
     access allowed? That's System Settings → Privacy & Security → Input Monitoring and
     Accessibility, for Terminal; quit Terminal with Cmd+Q after changing it. If that fails,
     allow the Homebrew Python app too. The startup message "This process is not trusted!"
     appears even when the hotkey works, so ignore it.
   - **Tab gives "Error: …".** The message says why. A 403 on port 5000 means the description
     server isn't running and macOS AirPlay Receiver answered instead; relaunch the `.command`.
   - **Logs:** `~/Library/Logs/twitter-bookmark-app/app.log` and `server.log`.
   - **Don't pick a CSV that the app didn't create** in Other file…. The app adds its own header
     row in the middle of such a file; this happened once.
   - **Rerunning `csv_to_json.py` brings back entries deleted from `merged.json`.** Check the list
     it prints.
9. **Where the data lives and how it's backed up:** `output/*.json` in Google Drive, not in git.
   Drive is the only backup, plus whatever backups item 11 added.

## Where things are

- Bookmark app: `/Users/guykindler/My Drive/python stuff/twitter bookmark app` (git repo
  `puzne2000/twitter-bookmark-app`). `twitter app2.py` is the app, `view_json.py` the viewer,
  `README.md` the technical reference.
- Description server: `/Users/guykindler/My Drive/python stuff/headless_scrapper` (git repo
  `puzne2000/headless_scrapper`). It's a Flask server on 127.0.0.1:5000 that uses OpenAI
  `gpt-6-luna`; its `README.md` has the technical details.

## How to work

- Check each step against the code. If you try things, use copies of the data in a scratch
  folder, never the real `output/` files, and don't overwrite the user's clipboard.
- Short sentences, numbered steps for procedures, exact key names and menu paths. Skip internals.
- If the guide goes in the repo, commit it but don't push: the user approves pushes. Report where
  it is and anything you couldn't verify.
