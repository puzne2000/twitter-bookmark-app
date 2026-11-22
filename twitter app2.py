import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from datetime import datetime
import pyperclip
import re
import threading
from pynput import keyboard  # Use pynput for the hotkey
import subprocess
import os
import csv 


# Global variable to store the previous application
previous_app = None

# The saved entry the window is currently editing (None = a new entry).
# Holds its url/date/time so saving can find and update it.
existing_entry = None
# The link the description box currently belongs to
desc_for_link = None
# The "Save to:" drop-down (created with the window, below)
save_to_menu = None
save_to_var = None
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

import threading
import requests


class EntryWindow:
    """
    A class to handle the main entry-editing window for tweet links and descriptions.
    Supports initializing the window, getting/setting entry values, and associating
    functions with key presses and button clicks.
    """

    def __init__(self, master, on_done=None, on_cancel=None):
        """
        Initialize the entry window.

        Args:
            master: The parent Tkinter window or root.
            on_done: Function to call when the user confirms (Done).
            on_cancel: Function to call when the user cancels/closes.
        """
        self.master = master
        self.on_done = on_done
        self.on_cancel = on_cancel

        self.window = tk.Toplevel(master)
        self.window.title("Edit Entry")
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self._handle_cancel)
        self.window.transient(master)
        self.window.grab_set()

        # Link label and entry
        self.label_link = tk.Label(self.window, text="Tweet Link:", anchor="w", font=("Helvetica", 12))
        self.label_link.grid(row=0, column=0, padx=(15, 5), pady=(15, 5), sticky="w")
        self.link_entry = tk.Entry(self.window, width=55, font=("Helvetica", 11))
        self.link_entry.grid(row=0, column=1, padx=(5, 15), pady=(15, 5), sticky="ew")

        # Description label and text box
        self.label_desc = tk.Label(self.window, text="Description:", anchor="nw", font=("Helvetica", 12))
        self.label_desc.grid(row=1, column=0, padx=(15, 5), pady=(5, 10), sticky="nw")
        self.desc_entry = tk.Text(self.window, width=55, height=5, font=("Helvetica", 11))
        self.desc_entry.grid(row=1, column=1, padx=(5, 15), pady=(5, 10), sticky="ew")

        # Done and Cancel buttons
        self.done_btn = tk.Button(self.window, text="Done", command=self._handle_done)
        self.done_btn.grid(row=2, column=1, sticky="e", padx=(5, 15), pady=(0, 10))

        # Key bindings
        self.desc_entry.bind("<Return>", self._return_handler)
        self.desc_entry.bind("<Shift-Return>", self._shift_return_handler)
        self.window.bind("<Escape>", lambda e: self._handle_cancel())
        self.window.bind("<Command-w>", lambda e: self._handle_cancel())

        # Focus
        self.window.lift()
        self.window.attributes("-topmost", True)
        self.link_entry.focus_set()

    def _handle_done(self, event=None):
        if self.on_done:
            self.on_done(self.get_link(), self.get_description())
        self.window.grab_release()
        self.window.destroy()

    def _handle_cancel(self, event=None):
        if self.on_cancel:
            self.on_cancel()
        self.window.grab_release()
        self.window.destroy()

    def _return_handler(self, event):
        # Only trigger done if Shift is not held
        if not (event.state & 0x0001):  # Shift not held
            self._handle_done()
            return "break"  # Prevent newline

    def _shift_return_handler(self, event):
        # Allow Shift+Return to insert a newline (default behavior)
        pass

    def get_link(self):
        return self.link_entry.get().strip()

    def set_link(self, value):
        self.link_entry.delete(0, tk.END)
        self.link_entry.insert(0, value or "")

    def get_description(self):
        return self.desc_entry.get("1.0", tk.END).strip()

    def set_description(self, value):
        self.desc_entry.delete("1.0", tk.END)
        self.desc_entry.insert("1.0", value or "")

    def set_on_done(self, func):
        self.on_done = func

    def set_on_cancel(self, func):
        self.on_cancel = func

    def bind_key(self, sequence, func):
        self.window.bind(sequence, func)

    def bind_button(self, button, func):
        button.config(command=func)

    def show(self):
        self.window.deiconify()
        self.window.wait_window()











# How get_description_from_server's answer starts when the server failed
ERROR_PREFIXES = ("Error:", "Exception:")


def get_description_from_server(address, draft_description, when_done):
    """
    Asynchronously requests a website description from the server.

    Args:
        address (str): The website address.
        draft_description (str): An optional draft description.
        when_done (function): A callback function to be called with (address, draft_description, result_description).
    """
    def worker():
        # print("i'm the worker, will ask the server on my own time")
        try:
            # Adjust the server URL as needed
            url = "http://127.0.0.1:5000/"
            data = {
                "address": address,
                "draft": draft_description or ""
            }
            response = requests.post(url, data=data)
            result_description = None
            if response.ok:
                # print("yay i got a response from the server")
                # Try to extract the result from the response HTML
                import re
                match = re.search(r'<textarea[^>]*id="resultTextarea"[^>]*>(.*?)</textarea>', response.text, re.DOTALL)
                if match:
                    result_description = match.group(1).strip()
                else:
                    result_description = response.text
            else:
                result_description = f"Error: {response.status_code}"
        except Exception as e:
            result_description = f"Exception: {e}"
        # print("worker is done, will call when_done")
        when_done(result_description)

    thread = threading.Thread(target=worker)
    thread.start()


# Function to get the currently active application
def get_active_app():
    try:
        result = subprocess.run(['osascript', '-e', 'tell application "System Events" to get name of first application process whose frontmost is true'], 
                              capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return None

# Function to restore focus to the previous application
def restore_previous_app():
    global previous_app
    if previous_app:
        try:
            subprocess.run(['osascript', '-e', f'tell application "{previous_app}" to activate'], 
                         capture_output=True)
        except:
            pass

# Function to validate if a string is a URL
def is_url(string):
    if not isinstance(string, str):
        return False
    url_pattern = re.compile(
        r'^(https?://)?(www\.)?([a-zA-Z0-9_-]+)+(\.[a-zA-Z]{2,})+(/[a-zA-Z0-9#?=_-]*)*'
    )
    text = string.strip()
    match = url_pattern.match(text)
    if not match:
        return False
    # A bare name like report.docx or notes.txt (what Finder puts on the clipboard
    # when you copy a file) also fits the pattern. Without http(s)://, www. or a
    # /path, refuse it if it ends in a common file extension.
    scheme, www = match.group(1), match.group(2)
    if not scheme and not www and "/" not in text:
        if text.rsplit(".", 1)[-1].lower() in FILE_NAME_EXTENSIONS:
            return False
    return True


# Endings of file names that are not web addresses (some, like .md or .zip, are also
# real domain endings; a link with one still works with http(s)://, www. or a /path).
FILE_NAME_EXTENSIONS = {
    'doc', 'docx', 'dot', 'dotx', 'rtf', 'txt', 'md', 'pages', 'numbers', 'key', 'odt', 'ods',
    'odp', 'xls', 'xlsx', 'xlsm', 'csv', 'tsv', 'ppt', 'pptx', 'pdf', 'png', 'jpg', 'jpeg',
    'heic', 'gif', 'webp', 'tif', 'tiff', 'bmp', 'svg', 'psd', 'mov', 'mp4', 'm4v', 'avi',
    'mkv', 'mp3', 'm4a', 'wav', 'aif', 'aiff', 'flac', 'zip', 'rar', 'tar', 'gz', 'tgz',
    'dmg', 'pkg', 'app', 'py', 'ipynb', 'js', 'json', 'xml', 'yaml', 'yml', 'tex', 'bib',
    'epub', 'mobi', 'log', 'sh', 'command', 'html', 'htm', 'eml', 'vcf', 'ics', 'plist',
}

# Files that can be bookmarked (the description server reads PDFs and images)
FILE_EXTENSIONS = ('.pdf', '.png', '.jpg', '.jpeg', '.heic', '.gif', '.webp')


def finder_file_on_clipboard():
    """Return the path of a file or folder copied in Finder (Cmd+C), or None."""
    try:
        result = subprocess.run(
            ['osascript', '-e', 'POSIX path of (the clipboard as «class furl»)'],
            capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            path = result.stdout.strip()
            if path and os.path.exists(path):
                return path
    except Exception:
        pass
    return None


def file_from_clipboard(finder_path=None):
    """
    Return the full path of a supported file on the clipboard, or None.
    Accepts a file copied in Finder (Cmd+C; pass finder_file_on_clipboard() as
    finder_path) or a copied path (Option+Cmd+C).
    """
    candidates = [finder_path] if finder_path else []
    text = (pyperclip.paste() or "").strip().strip('"\'')  # a copied path
    if text.startswith("file://"):
        from urllib.parse import unquote, urlparse
        text = unquote(urlparse(text).path)
    candidates.append(os.path.expanduser(text))
    for path in candidates:
        if path and path.lower().endswith(FILE_EXTENSIONS) and os.path.isfile(path):
            return path
    return None


# Function to check clipboard and auto-fill link field if valid
def autofill_link(link_entry):
    '''
    fills the link_entry label with a link or a supported file path from the
    clipboard, if one exists there
    '''
    print("autofill")
    clipboard_content = pyperclip.paste()
    # Check for a file first: a Finder copy also puts the bare file name (e.g. report.pdf)
    # on the clipboard as text, which could pass the is_url check.
    finder_path = finder_file_on_clipboard()
    found = file_from_clipboard(finder_path)
    if not found and not finder_path and is_url(clipboard_content):
        # (a file of an unsupported type copied in Finder is not a link: Frog)
        found = clipboard_content.strip()
    if found:
        link_entry.delete(0, tk.END)
        link_entry.insert(0, found)
        return(True)
    else:
        ## just enter text to description instead!
        print("autofill unsuccessful")
        return False


def ensure_path(path):
    """
    Ensures that the provided file path points to an existing, accessible file.
    If the file does not exist or cannot be opened for reading and writing,
    prompts the user with a file dialog to select or create a valid RTF file.
    The function will keep prompting the user until a valid file is selected or
    the user cancels the dialog, in which case an empty string is returned.

    Args:
        path (str): The initial file path to check.

    Returns:
        str: The path to a valid, accessible file, or an empty string if the user cancels.
    """
    success = False
    while not success:
        if not os.path.isfile(path):
            print(f"current file name {path} doesn't work will ask user")
            selected_path = open_file()
            if not selected_path:
                print("user did not select file, aborting")
                return ""
            path = selected_path
        try:
            with open(path, "r+"):
                success = True
                print(f"now {path} seems to work")
        except Exception:
            pass

    return path



def find_existing_entry(url):
    """
    Return the newest entry in the current JSON notes file whose url equals url,
    or None. (CSV files are not searched.)
    """
    import json
    if not notes_file or not notes_file.lower().endswith('.json') or not os.path.isfile(notes_file):
        return None
    try:
        with open(notes_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None
    if not isinstance(data, list):
        return None
    url = url.strip()
    for entry in reversed(data):
        if isinstance(entry, dict) and str(entry.get("url", "")).strip() == url:
            return dict(entry)
    return None


def same_entry(a, b):
    """True if a and b are the same saved entry (same url, date and time)."""
    return all(a.get(k) == b.get(k) for k in ("url", "date", "time"))


def save_entry(url, description, date, draft = "", update=None):
    """
    Save a tweet entry to the notes file in RTF format.

    This function writes a new entry containing the tweet link (url), description, and date
    to the global notes_file. If a draft description is provided, it is included as a separate
    field. The function ensures the file starts with the RTF header and appends the new entry
    in a format compatible with RTF readers.

    Args:
        url (str): The tweet link to save.
        description (str): The main description of the tweet.
        date (str): The date and time of the entry.
        draft (str, optional): An optional draft description to include. Defaults to "".
        update (dict, optional): An existing entry (from find_existing_entry) to update instead
            of adding a new one. Its description (and draft, if given) are replaced and an
            "updated" date is added; its original date is kept. JSON files only; if the entry
            is no longer in the file, a new entry is added.

    Returns:
        str: The path to the notes file if successful, or an empty string if an error occurs.

    Side Effects:
        - Shows a warning message box if url or description is missing.
        - Modifies the global notes_file.
        - Writes to the notes file in-place, updating its content.

    Notes:
        - If the notes file does not start with the RTF header, it is added.
        - If the notes file ends with a closing brace, it is temporarily removed to append the new entry.
        - The function expects the notes file to be in RTF format.
    """
    global notes_file

    if not url or not description:
        messagebox.showwarning("Input Error", "Please fill in both fields.")
        return

    path = notes_file

    # Prepare row data
    # If date contains both date and time, split; else, time is empty
    if " " in date:
        date_part, time_part = date.split(" ", 1)
    else:
        date_part, time_part = date, ""
    row = [date_part, time_part, url, draft, description]

    # Only proceed if the path ends with '.csv' (case-insensitive)
    if path.lower().endswith('.csv'):
        # Check if file exists and if it has a header
        file_exists = os.path.isfile(path)
        needs_header = True
        if file_exists:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    first_line = f.readline()
                    if first_line.strip().lower().replace(" ", "") == "date,time,url,draft,description":
                        needs_header = False
            except Exception:
                pass
        try:
            with open(path, "a", newline='', encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                if needs_header:
                    writer.writerow(["date", "time", "url", "draft", "description"])
                writer.writerow(row)
            return path
        except Exception as e:
            return ""
    else:
        # If the file is a JSON, save the row as a dictionary
        if path.lower().endswith('.json'):
            import json
            entry = {
                "date": date_part,
                "time": time_part,
                "url": url,
                "draft": draft,
                "description": description
            }
            try:
                # Read existing data if file exists and is valid JSON
                if os.path.isfile(path):
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        if not isinstance(data, list):
                            data = []
                    except Exception:
                        data = []
                else:
                    data = []
                target = None
                if update is not None:
                    target = next((e for e in reversed(data)
                                   if isinstance(e, dict) and same_entry(e, update)), None)
                if target is not None:
                    target["description"] = description
                    if draft:
                        target["draft"] = draft
                    target["updated"] = date
                else:
                    data.append(entry)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return path
            except Exception as e:
                return ""
        else:
            # If the file is not a CSV or JSON, do nothing and return empty string
            return ""


def clear_entry_and_withdraw(saved=True):
    """
    Empty the window, hide it and return to the previous app. With saved=True,
    also flash "Entry Saved" (only call it that way after a save succeeded).
    """
    global existing_entry, desc_for_link
    link_entry.delete(0, tk.END)
    desc_entry.delete("1.0", tk.END)
    existing_entry = None
    desc_for_link = None
    status_label.config(text="")
    if saved:
        show_saved_message()
    root.withdraw()  # Hide the main window
    restore_previous_app()


def show_saved_message():
    """Flash a small "Entry Saved" window that fades out."""
    saved_window = tk.Toplevel(root)
    saved_window.overrideredirect(True)  # Remove window decorations
    saved_window.attributes("-topmost", True)
    saved_window.configure(bg="white")
    saved_window.geometry(f"200x60+{root.winfo_x() + 100}+{root.winfo_y() + 100}")

    label = tk.Label(saved_window, text="Entry Saved", font=("Helvetica", 16), bg="white")
    label.pack(expand=True, fill="both", padx=10, pady=10)

    def fade_out(alpha=1.0):
        if alpha > 0:
            saved_window.attributes("-alpha", alpha)
            saved_window.after(50, fade_out, alpha - 0.02)
        else:
            saved_window.destroy()

    fade_out()

# Function to bring up the app window with autofill from clipboard
def attempt_app_to_front():
    '''
    called from on_hotkey when applications' hotkey is pressed. 
    autofills link if exists, and restores previous app with a beep otherwise
    '''
    global previous_app

    # Store the currently active application before showing our window
    previous_app = get_active_app()

    if autofill_link(link_entry): #the clipboard contains a link
        refresh_file_menu()  # pick up files added to output/ since last time
        load_existing_entry(link_entry.get())
        root.deiconify()
        root.lift()
        root.focus_force()
        desc_entry.focus_set()  # Set focus to the description entry so user can type immediately
        return (True)
    else:
        print("bell sound")
        subprocess.Popen(['afplay', '/System/Library/Sounds/Frog.aiff']) # Make an error sound (non-blocking)
        restore_previous_app()  # Return focus to the previous app
        return (False)

def load_existing_entry(url):
    """
    If url is already saved in the notes file, show its description and when it was
    saved, and remember the entry so saving updates it instead of adding a duplicate.
    """
    global existing_entry, desc_for_link
    found = find_existing_entry(url)
    if found is not None:
        existing_entry = found
        desc_entry.delete("1.0", tk.END)
        desc_entry.insert("1.0", found.get("description") or "")
        when = " ".join(x for x in (found.get("date"), found.get("time")) if x) or "an earlier import"
        status_label.config(text=f"Already saved ({when}). Saving will update that entry.")
    else:
        existing_entry = None
        if desc_for_link is not None and desc_for_link != url:
            # leftover text from a different, cancelled link
            desc_entry.delete("1.0", tk.END)
        status_label.config(text="")
    desc_for_link = url

# This is called by the hotkey listener when the hotkey is pressed
def on_hotkey():
    """
    Callback for the global hotkey.
    Called by: pynput's GlobalHotKeys listener when the hotkey is pressed, as defined in hotkey_listener
    Performs: attempt_app_to_front to show the app window
    """
    print("hotkey pressed")
    attempt_app_to_front()


def verify_done_window(root, f_run):
    '''
    pops a modal window child of root. if user confirms (by clicking or typing enter) then
    f_run is run and the confirmation window closes; root is hidden only if f_run
    returns True (otherwise root stays open for another try). Escape just closes it.
    '''
    done_win = tk.Toplevel(root)
    done_win.title("Done?")
    done_win.transient(root)
    done_win.grab_set()
    done_win.geometry("200x100+{}+{}".format(root.winfo_x() + 120, root.winfo_y() + 120))
    done_win.resizable(False, False)

    def on_done(event=None):
        done_win.grab_release()
        ok = f_run()
        done_win.destroy()
        if ok:
            root.withdraw()
        else:
            root.lift()
            root.focus_force()
            desc_entry.focus_set()

    def on_cancel(event=None):
        done_win.grab_release()
        done_win.destroy()

    # Button
    btn = tk.Button(done_win, text="Done?", command=on_done)
    btn.pack(expand=True, fill="both", padx=20, pady=20)
    btn.focus_set()

    ## verify done shoudl just return whether verification was successfull, it shouldn't call other functions
    # Bind Enter to confirm
    done_win.bind("<Return>", on_done)
    # Bind Escape to cancel
    done_win.bind("<Escape>", on_cancel)
    # Handle window close (X)
    done_win.protocol("WM_DELETE_WINDOW", on_cancel)



def on_window_activated(event):
    '''
    this is bound to be called on a FocusIn event
    '''
    print("Window activated!")
    # show root window
    #root.deiconify()
    #root.lift()
    #root.focus_force()


# Bind window close event to restore focus
def on_closing(arg = ""):
    root.withdraw()
    #feels like there's too much calls to restore previous app
    #who calls on_closing?? when??
    #what happens when used presses done? is previous app restored then?
    restore_previous_app()

def entry_from_interface():
    tweet_link = link_entry.get()
    description = desc_entry.get("1.0", tk.END).strip()
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return tweet_link, description, date

def entry_is_done():
    ## thess should be read elsewhere and passed as parameters to save_entry
    tweet_link, description, date = entry_from_interface() 
    saved = save_entry(tweet_link, description, date, update=existing_entry)
    if saved:
        clear_entry_and_withdraw()
        return True
    # Not saved (save_entry already warned about an empty field; "" means the file
    # could not be written): keep the window open with the link and text, so the
    # user can fix it and press Enter again.
    if saved == "":
        messagebox.showerror("Not saved", f"Could not write to:\n{notes_file}\n\nThe entry was not saved.")
    return False

def return_pressed(event=None):
    # Only triggered if Shift is NOT held
    #print("enter entered")
    verify_done_window(root, entry_is_done)
    return "break"  # Prevent newline, it's a tkinter thing

def shift_return_pressed(event=None):
    # Allow default behavior (insert newline)
    pass  # No action needed, just let it through

def auto_description_requested(arg):
    print(f"autro description with arg {arg}")
    
    tweet_link, description, date = entry_from_interface() 
    editing = existing_entry  # captured now: the window is cleared before the server answers
    def when_done(result):
        print("server called me to save the entry")
        # Create a modal dialog for editing the description
        # Store the currently active application before showing our window
        previous_app = get_active_app()

        def show_editable_description_dialog(initial_text):
            root.deiconify()  # Show the main window
            root.lift()
            root.focus_force()


            dialog = tk.Toplevel(root)
            dialog.title("Description obtained")
            dialog.transient(root)
            dialog.grab_set()
            dialog.resizable(False, False)

            # Result variable to store the edited text
            result_var = {'value': initial_text}

            # Text box
            text_box = tk.Text(dialog, width=60, height=8, wrap="word")
            text_box.insert("1.0", initial_text)
            text_box.pack(padx=10, pady=(10, 5))

            # The server failed: say so, and don't let Enter save the error as the description
            is_error = (initial_text or "").startswith(ERROR_PREFIXES)
            if is_error:
                tk.Label(dialog, fg="red3", justify="left", wraplength=460,
                         text="This is an error from the description server, not a description. "
                              "Replace it with your own text and press Enter, or press Esc to "
                              "save what you typed before pressing Tab.").pack(padx=10, pady=(0, 5))

            # Focus the text box
            dialog.lift()  # Brings the window to the top of the stacking order
            dialog.focus_force()
            dialog.attributes("-topmost", True)
            text_box.focus_set()

            # Handler for Done button or Return
            def on_done(event=None):
                text = text_box.get("1.0", tk.END).strip()
                if is_error and text.startswith(ERROR_PREFIXES):
                    dialog.bell()  # still the error text: keep the box open
                    return
                result_var['value'] = text
                dialog.grab_release()
                dialog.destroy()

                root.withdraw()
                restore_previous_app()

            # Handler for Escape or window close
            def on_cancel(event=None):
                result_var['value'] = None
                dialog.grab_release()
                dialog.destroy()

                root.withdraw()
                restore_previous_app()

            # Done button
            done_btn = tk.Button(dialog, text="Done", command=on_done)
            done_btn.pack(pady=(0, 10))

            # Bind Return (but not Shift+Return) to on_done
            def return_handler(event):
                if not (event.state & 0x0001):  # Shift not held
                    on_done()
                    return "break"  # Prevent newline
            text_box.bind("<Return>", return_handler)
            # Allow Shift+Return to insert newline (default behavior)

            # Bind Escape to cancel
            dialog.bind("<Escape>", on_cancel)
            dialog.bind("<Command-w>", on_cancel)
            dialog.protocol("WM_DELETE_WINDOW", on_cancel)

            # Wait for the dialog to close
            root.wait_window(dialog)
            return result_var['value']

        # Show the dialog and get the possibly edited description
        edited_result = show_editable_description_dialog(result)
        print(f"result: {result} \nEditted result: {edited_result}")
        if edited_result is not None:
            saved = save_entry(tweet_link, edited_result, date, description, update=editing)
        else:
            saved = save_entry(tweet_link, description, date, update=editing)
        if saved:
            show_saved_message()
        elif saved == "":
            messagebox.showerror("Not saved", f"Could not write to:\n{notes_file}\n\nThe entry was not saved.")

    get_description_from_server(tweet_link, description, when_done)
    clear_entry_and_withdraw(saved=False)  # nothing is saved until the server answers
    return "break"  # Prevent the default tab insertion


def open_file():
    global notes_file
    filetypes = [
        ("JSON files", "*.json"),
        ("CSV files", "*.csv")
   ]
    selected_path = filedialog.askopenfilename(
        title="Open CSV or JSON File",
        defaultextension=".json",
        filetypes=filetypes
    )
    if selected_path:
        notes_file = selected_path
    return selected_path

def new_file():
    global notes_file
    filetypes = [("JSON files", "*.json")]
    selected_path = filedialog.asksaveasfilename(
        title="Create New JSON File",
        defaultextension=".json",
        filetypes=filetypes
    )
    if selected_path:
        try:
            with open(selected_path, "w", encoding="utf-8") as f:
                f.write("[]")
            notes_file = selected_path
        except Exception as e:
            messagebox.showerror("Error", f"Could not create file:\n{e}")



def file_label(path):
    """Short name for the drop-down: the file name for files in output/, else parent/name."""
    if os.path.dirname(os.path.abspath(path)) == OUTPUT_DIR:
        return os.path.basename(path)
    return os.path.join(os.path.basename(os.path.dirname(path)), os.path.basename(path))


def refresh_file_menu():
    """Rebuild the "Save to:" drop-down: every JSON file in output/, the current file, new/other."""
    if save_to_menu is None:
        return
    try:
        paths = sorted((os.path.join(OUTPUT_DIR, f) for f in os.listdir(OUTPUT_DIR)
                        if f.lower().endswith(".json")),
                       key=lambda p: (os.path.basename(p) != "merged.json", os.path.basename(p).lower()))
    except OSError:
        paths = []
    if notes_file and os.path.abspath(notes_file) not in [os.path.abspath(p) for p in paths]:
        paths.append(notes_file)
    menu = save_to_menu["menu"]
    menu.delete(0, "end")
    for path in paths:
        menu.add_command(label=file_label(path), command=lambda p=path: choose_file(p))
    menu.add_separator()
    menu.add_command(label="New file…", command=lambda: choose_file(None, new_file))
    menu.add_command(label="Other file…", command=lambda: choose_file(None, open_file))
    save_to_var.set(file_label(notes_file) if notes_file else "(no file)")


def choose_file(path, picker=None):
    """Switch the file entries are saved to (from the drop-down or the File menu)."""
    global notes_file
    if picker is not None:
        picker()  # open_file / new_file set notes_file themselves; cancelling keeps the old one
    elif path:
        notes_file = path
    refresh_file_menu()
    link = link_entry.get().strip()
    if link:
        load_existing_entry(link)  # "already saved?" depends on the file



########################################
#
#  Script execution starts here
#
########################################

# Default file to save entries to. If it is missing or not writable,
# ensure_path() below asks the user to pick one; File > Open switches files.
notes_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "merged.json")

####
#### Create a menu bar
####

# Initialize Tkinter GUI (main application window)
root = tk.Tk()
menu_bar = tk.Menu(root)

# Create a "File" menu
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Open...", command=lambda: choose_file(None, open_file))
file_menu.add_command(label="New...", command=lambda: choose_file(None, new_file))
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

menu_bar.add_cascade(label="File", menu=file_menu)

# Set the menu bar on the root window
root.config(menu=menu_bar)


####
#### root window
####

root.title("Tweet Logger")  # Set the window title
root.resizable(False, False)  # Prevent window resizing for a cleaner look

# Set up window close protocol to call on_closing when user tries to close the window
root.protocol("WM_DELETE_WINDOW", on_closing)

# Create and place the "Tweet Link" label and entry field
label_link = tk.Label(root, text="Link or file:", anchor="w", font=("Helvetica", 12))
label_link.grid(row=0, column=0, padx=(15, 5), pady=(15, 5), sticky="w")
link_entry = tk.Entry(root, width=55, font=("Helvetica", 11))
link_entry.grid(row=0, column=1, padx=(5, 15), pady=(15, 5), sticky="ew")

# Create and place the "Description" label and text box
label_desc = tk.Label(root, text="Description:", anchor="nw", font=("Helvetica", 12))
label_desc.grid(row=1, column=0, padx=(15, 5), pady=(5, 10), sticky="nw")
desc_entry = tk.Text(root, width=55, height=5, font=("Helvetica", 11))
desc_entry.grid(row=1, column=1, padx=(5, 15), pady=(5, 10), sticky="ew")

# Shows when the link is already saved (and that saving will update it)
status_label = tk.Label(root, text="", anchor="w", fg="gray40", font=("Helvetica", 11))
status_label.grid(row=2, column=1, padx=(5, 15), pady=(0, 10), sticky="w")

# "Save to:" drop-down: which file entries go to
label_save_to = tk.Label(root, text="Save to:", anchor="w", font=("Helvetica", 12))
label_save_to.grid(row=3, column=0, padx=(15, 5), pady=(0, 15), sticky="w")
save_to_var = tk.StringVar(root)
save_to_menu = tk.OptionMenu(root, save_to_var, "")
save_to_menu.grid(row=3, column=1, padx=(5, 15), pady=(0, 15), sticky="w")

# Configure grid weights for better resizing behavior (optional, since resizing is disabled)
root.grid_columnconfigure(1, weight=1) #does nothing as long as root resiable is set to (false, flase) as above

#
# # Bind keys in the description box
#
# Enter (without Shift) triggers the done window, Shift+Enter allows a newline
# return_pressed and shift_return_pressed are defined above
desc_entry.bind("<Return>", return_pressed)
desc_entry.bind("<Shift-Return>", shift_return_pressed)
desc_entry.bind("<Tab>", auto_description_requested)
desc_entry.bind("<Escape>", on_closing)
desc_entry.bind("<Command-w>", on_closing)


# Bind the <FocusIn> event to the root window to autofill link when window gains focus
root.bind("<FocusIn>", on_window_activated)

# Start the hotkey listener in a separate thread so it doesn't block the GUI
# It will call on_hotkey when pressed
def hotkey_listener(callback = on_hotkey):
    print("listener being activated")
    listener = keyboard.GlobalHotKeys({
            '<cmd>+<shift>+v': callback
        })
    listener.start()
    print("listener activated")
    return listener

hotkey_thread = threading.Thread(target=hotkey_listener, args=(on_hotkey,), daemon=True)
hotkey_thread.start()



# Hide the main window at startup (it will be shown by the hotkey)
root.withdraw()

notes_file = ensure_path(notes_file)
refresh_file_menu()


# Start the Tkinter main loop (this keeps the app running and responsive)
root.mainloop()
