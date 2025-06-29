# Twitter Bookmark App

A simple cross-platform desktop app for quickly saving tweet links and descriptions to a log file, using a global hotkey and a user-friendly Tkinter interface.

## Features
- **Global Hotkey Activation**: Press `Cmd+Shift+V` (macOS) to bring up the app from anywhere.
- **Clipboard Autofill**: If your clipboard contains a valid URL, it is automatically inserted into the link field.
- **Quick Entry**: Add a description and save the entry with a confirmation dialog.
- **RTF Log File**: Entries are saved in `tweet_log.rtf` with date, link, and description.
- **Focus Restoration**: After saving, the app returns focus to the application you were using before.
- **Sound Feedback**: Plays a system sound if the clipboard does not contain a valid URL.

## Requirements
- Python 3.7+
- macOS (tested; hotkey and sound features are macOS-specific)
- The following Python packages:
  - `tkinter` (usually included with Python)
  - `pyperclip`
  - `pynput`
  - `playsound`

Install dependencies with:
```bash
pip install -r requirements.txt
```

## Usage
1. **Start the App**
   - Run the script:
     ```bash
     python3 twitter\ app2.py
     ```
   - The app will hide itself and run in the background, listening for the hotkey.

2. **Save a Tweet**
   - Copy a tweet link to your clipboard.
   - Press `Cmd+Shift+V`.
   - The app window will appear with the link autofilled.
   - Enter a description.
   - Press `Enter` (or click "Done?") to confirm and save.
   - The entry is saved to `tweet_log.rtf` and the app hides itself, returning you to your previous app.

3. **Multi-line Descriptions**
   - Press `Shift+Enter` to insert a newline in the description box.

4. **Error Sound**
   - If the clipboard does not contain a valid URL, a system sound will play and the app will not appear.

## Customization
- **Hotkey**: Change the hotkey by editing the `hotkey_listener` function in the script.
- **Sound**: Change the error sound by editing the path in the `playsound` call (e.g., `/System/Library/Sounds/Frog.aiff`).
- **Log File**: Entries are saved in `tweet_log.rtf` in the script directory.

## Notes
- The app is designed for macOS. Hotkey and sound features may need adjustment for Windows/Linux.
- The app uses AppleScript via `osascript` to restore focus to the previous application (macOS only).
- The GUI is built with Tkinter for simplicity and portability.

## License
MIT License (add your own if desired) 