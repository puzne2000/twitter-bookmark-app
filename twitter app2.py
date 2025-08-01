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
from playsound import playsound


# Global variable to store the previous application
previous_app = None

import threading
import requests

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
    return bool(url_pattern.match(string))

# Function to check clipboard and auto-fill link field if valid
def autofill_link(link_entry):
    '''
    fills the link_entry label with a link from the clipboard, if one exists there
    '''
    print("autofill")
    clipboard_content = pyperclip.paste()
    if is_url(clipboard_content):
        link_entry.delete(0, tk.END)
        link_entry.insert(0, clipboard_content)
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



def save_entry(url, description, date, draft = ""):
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
                data.append(entry)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return path
            except Exception as e:
                return ""
        else:
            # If the file is not a CSV or JSON, do nothing and return empty string
            return ""


def clear_entry_and_withdraw():
    link_entry.delete(0, tk.END)
    desc_entry.delete("1.0", tk.END)


    saved_window = tk.Toplevel(root)
    saved_window.overrideredirect(True)  # Remove window decorations
    saved_window.attributes("-topmost", True)
    saved_window.configure(bg="white")
    saved_window.geometry(f"200x60+{root.winfo_x() + 100}+{root.winfo_y() + 100}")

    label = tk.Label(saved_window, text="Entry Saved", font=("Helvetica", 16), bg="white")
    label.pack(expand=True, fill="both", padx=10, pady=10)


    root.withdraw()

    def fade_out(alpha=1.0):
        if alpha > 0:
#            print(alpha)
            saved_window.attributes("-alpha", alpha)
            saved_window.after(50, fade_out, alpha - 0.02)
        else:
            saved_window.destroy()

    fade_out()
    ### end of part that should be seperated
                   # Hide the main window
    #not sure why this should be here, the writing to file and the gui window release should be separated
    root.withdraw()
    # Restore focus to the previous application after the popup fades out
    restore_previous_app()

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
        root.deiconify()
        root.lift()
        root.focus_force()
        desc_entry.focus_set()  # Set focus to the description entry so user can type immediately
        return (True)
    else:
        print("bell sound")
        playsound('/System/Library/Sounds/Frog.aiff', block=False) # Make an error sound
        restore_previous_app()  # Return focus to the previous app
        return (False)

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
    the window is closed and f_run is run. Otherwise the confirmation window closes
    '''
    done_win = tk.Toplevel(root)
    done_win.title("Done?")
    done_win.transient(root)
    done_win.grab_set()
    done_win.geometry("200x100+{}+{}".format(root.winfo_x() + 120, root.winfo_y() + 120))
    done_win.resizable(False, False)

    def on_done(event=None):
        done_win.grab_release()
        f_run()
        done_win.destroy()
        root.withdraw()

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
    notes_file = save_entry(tweet_link, description, date)
    clear_entry_and_withdraw()

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

            # Focus the text box
            dialog.lift()  # Brings the window to the top of the stacking order
            dialog.focus_force()
            dialog.attributes("-topmost", True)
            text_box.focus_set()

            # Handler for Done button or Return
            def on_done(event=None):
                result_var['value'] = text_box.get("1.0", tk.END).strip()
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
            save_entry(tweet_link, edited_result, date, description)
        else:
            save_entry(tweet_link, description, date)

    get_description_from_server(tweet_link, description, when_done)
    clear_entry_and_withdraw()
    return "break"  # Prevent the default tab insertion


########################################
#
#  Script execution starts here
#
########################################

## for now, start with no notes file 
#notes_file = "tweet_log.rtf" #for now, filename is set here
notes_file =""


# Create a menu bar# Initialize Tkinter GUI (main application window)
root = tk.Tk()
menu_bar = tk.Menu(root)

# Create a "File" menu
file_menu = tk.Menu(menu_bar, tearoff=0)

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
        messagebox.showinfo("File Opened", f"Opened file:\n{notes_file}")
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
            messagebox.showinfo("File Created", f"Created new file:\n{notes_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not create file:\n{e}")

file_menu.add_command(label="Open...", command=open_file)
file_menu.add_command(label="New...", command=new_file)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

menu_bar.add_cascade(label="File", menu=file_menu)

# Set the menu bar on the root window
root.config(menu=menu_bar)






root.title("Tweet Logger")  # Set the window title
root.resizable(False, False)  # Prevent window resizing for a cleaner look

# Set up window close protocol to call on_closing when user tries to close the window
root.protocol("WM_DELETE_WINDOW", on_closing)

# Create and place the "Tweet Link" label and entry field
label_link = tk.Label(root, text="Tweet Link:", anchor="w", font=("Helvetica", 12))
label_link.grid(row=0, column=0, padx=(15, 5), pady=(15, 5), sticky="w")
link_entry = tk.Entry(root, width=55, font=("Helvetica", 11))
link_entry.grid(row=0, column=1, padx=(5, 15), pady=(15, 5), sticky="ew")

# Create and place the "Description" label and text box
label_desc = tk.Label(root, text="Description:", anchor="nw", font=("Helvetica", 12))
label_desc.grid(row=1, column=0, padx=(15, 5), pady=(5, 10), sticky="nw")
desc_entry = tk.Text(root, width=55, height=5, font=("Helvetica", 11))
desc_entry.grid(row=1, column=1, padx=(5, 15), pady=(5, 10), sticky="ew")

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


# Start the Tkinter main loop (this keeps the app running and responsive)
root.mainloop()
