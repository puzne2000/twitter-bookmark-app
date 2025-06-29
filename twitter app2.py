import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import pyperclip
import re
import threading
from pynput import keyboard  # Use pynput for the hotkey
import subprocess
import os
from playsound import playsound

# Global variable to store the previous application
previous_app = None

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
    url_pattern = re.compile(
        r'^(https?://)?(www\.)?([a-zA-Z0-9_-]+)+(\.[a-zA-Z]{2,})+(/[a-zA-Z0-9#?=_-]*)*'
    )
    return bool(url_pattern.match(string))

# Function to check clipboard and auto-fill link field if valid
def autofill_link():
    print("autofill")
    clipboard_content = pyperclip.paste()
    if is_url(clipboard_content):
        link_entry.delete(0, tk.END)
        link_entry.insert(0, clipboard_content)
        return(True)
    else:
        print("autofill unsuccessful")
        return False

# Function to save the tweet link, description, and date
def save_entry():
    tweet_link = link_entry.get()
    description = desc_entry.get("1.0", tk.END).strip()
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not tweet_link or not description:
        messagebox.showwarning("Input Error", "Please fill in both fields.")
        return

    # Open the file in read+write mode
    with open("tweet_log.rtf", "r+") as file:
        content = file.read()
        if not content.startswith("{\\rtf1"):
            content = "{\\rtf1\n" + content
        if content.endswith("}"):
            content = content[:-1]
        file.seek(0)
        file.write(content)
        file.write(f"\\fs24 \\b Date:\\b0 {date}\\par\n")
        file.write(f"\\b Link:\\b0 {tweet_link}\\par\n")
        file.write(f"\\b Description: \\b0 {description}\\par\n\\par\n")
        file.write("}")
        file.truncate()


def clear_entry_and_withdraw():
    link_entry.delete(0, tk.END)
    desc_entry.delete("1.0", tk.END)
    root.withdraw()


    ### the whole chunk below should be a separate function
    # Show a temporary window that says "Entry Saved" and fades out
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
            saved_window.after(50, fade_out, alpha - 0.04)
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
def show_app():
    global previous_app
    print("show me the appppp1")
    
    # Store the currently active application before showing our window
    previous_app = get_active_app()
    
    if autofill_link(): #the clipboard contains a link
        root.deiconify()
        root.lift()
        root.focus_force()
        return (True)
    else:
        print("bell sound")
        playsound('/System/Library/Sounds/Frog.aiff', block=False) # Make an error sound
        restore_previous_app()  # Return focus to the previous app
        return (False)

# This is called by the hotkey listener when the hotkey is pressed
def on_activate():
    """
    Callback for the global hotkey.
    Called by: pynput's GlobalHotKeys listener when the hotkey is pressed, as defined in hotkey_listener
    Performs: show_app to show the app window
    """
    show_app()

def hotkey_listener(callback = on_activate):
    print("listener being activated")
    listener = keyboard.GlobalHotKeys({
            '<cmd>+<shift>+v': callback
        })
    listener.start()
    print("listener activated")
    return listener

def show_done_window(root, f_run):
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

    # Bind Enter to confirm
    done_win.bind("<Return>", on_done)
    # Bind Escape to cancel
    done_win.bind("<Escape>", on_cancel)
    # Handle window close (X)
    done_win.protocol("WM_DELETE_WINDOW", on_cancel)



def on_window_activated(event):
    print("Window activated!")
    # You can perform any actions here when the window gains focus.
    autofill_link()


# Initialize Tkinter GUI
root = tk.Tk()
root.title("Tweet Logger")

# Bind window close event to restore focus
def on_closing():
    root.withdraw()
    #feels like there's too much calls to restore previous app
    #who calls on_closing?? when??
    restore_previous_app()

root.protocol("WM_DELETE_WINDOW", on_closing)

tk.Label(root, text="Tweet Link:").grid(row=0, column=0, padx=10, pady=5)
link_entry = tk.Entry(root, width=50)
link_entry.grid(row=0, column=1, padx=10, pady=5)

tk.Label(root, text="Description:").grid(row=1, column=0, padx=10, pady=5)
desc_entry = tk.Text(root, width=50, height=5)
desc_entry.grid(row=1, column=1, padx=10, pady=5)

def entry_is_done():
    save_entry()
    clear_entry_and_withdraw()

def on_desc_enter(event=None):
    # Only trigger if Shift is NOT held
    print("enter entered")
    if not (event.state & 0x0001):  # Shift is not pressed
        show_done_window(root, entry_is_done)
        return "break"  # Prevent newline
    else: #should not ever get here, because shift+enter is bound to allow_newline
        print("enter pressed but also shit was pressed")

def allow_newline(event=None):
    # Allow default behavior (insert newline)
    #print("new line with shirt+enter")
    pass  # No action needed, just let it through

desc_entry.bind("<Return>", on_desc_enter)
desc_entry.bind("<Shift-Return>", allow_newline)

# Bind the <FocusIn> event to the root window
root.bind("<FocusIn>", on_window_activated)


# Start the hotkey listener in a separate thread
hotkey_thread = threading.Thread(target=hotkey_listener, daemon=True)
hotkey_thread.start()

#root.mainloop() #gk added this!
root.withdraw()

# Start the Tkinter main loop
root.mainloop()
