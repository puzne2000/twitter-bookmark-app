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
from playsound import playsound
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
 
client = OpenAI(api_key=api_key)


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
    success = False
        ## TODO: checking the path and finding another if it doesn't exist should be done in a separate function
    while not success:
        if not os.path.isfile(path):
            print(f"current file name {path} doesn't work will ask user")
            filetypes = [("RTF files", "*.rtf"), ("All files", "*.*")]
            selected_path = filedialog.askopenfilename(
                title="Select or Create RTF File",
                defaultextension=".rtf",
                filetypes=filetypes
            )
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



# Function to save the tweet link, description, and date
def save_entry(path = "tweet_log.rtf"):
    ## thess should be read elsewhere and passed as parameters to save_entry
    tweet_link = link_entry.get()
    description = desc_entry.get("1.0", tk.END).strip()
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not tweet_link or not description:
        messagebox.showwarning("Input Error", "Please fill in both fields.")
        return

    # If the file does not exist, open a file selection window to open or create an rtf file
    path = ensure_path(path)

    # Open the file in read+write mode
    try:
        with open(path, "r+") as file:
            ## TODO: should have a separate draft and nondraft description. allow a parameter for autogeneration, in which case use get_description_from_server
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
        return (path)
    except Exception as e:
        return ""


def clear_entry_and_withdraw():
    link_entry.delete(0, tk.END)
    desc_entry.delete("1.0", tk.END)


    ### the whole chunk below should be a separate function
    # Show a temporary window that says "Entry Saved" and fades out
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
def on_closing():
    root.withdraw()
    #feels like there's too much calls to restore previous app
    #who calls on_closing?? when??
    #what happens when used presses done? is previous app restored then?
    restore_previous_app()


def entry_is_done():
    global notes_file
    print(f"entry does will save to path {notes_file}")
    notes_file = save_entry(notes_file)
    clear_entry_and_withdraw()

def return_pressed(event=None):
    # Only triggered if Shift is NOT held
    #print("enter entered")
    verify_done_window(root, entry_is_done)
    return "break"  # Prevent newline, it's a tkinter thing

def shift_return_pressed(event=None):
    # Allow default behavior (insert newline)
    pass  # No action needed, just let it through



def auto_description(arg):
    """
    Uses ChatGPT to generate a concise description of the website whose address is in the link_entry widget.
    Assumes link_entry is a Tkinter Entry widget containing the URL.
    """
    print("auto-describe called")
    print(arg)
    url = link_entry.get().strip()
    if not url:
        messagebox.showwarning("No URL", "Please enter a website address.")
        return

    # Compose the prompt for ChatGPT
    prompt = f"Give a concise description of the website at this address: {url}"

    # Load OpenAI API key from .env file
  
    load_dotenv()
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
            ],
            max_tokens=60,
            temperature=0.7
            )
        description = response.choices[0].message.content.strip()
        print(f"description: {description}")
        # You can now use this description as needed, e.g., insert into a text field
        # For example, if you have a description_entry widget:
        if 'desc_entry' in globals():
            desc_entry.delete("1.0", 'end')
            desc_entry.insert(tk.END, description)
        else:
            messagebox.showinfo("Description", description)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to get description:\n{e}")


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
    filetypes = [("RTF files", "*.rtf"), ("All files", "*.*")]
    selected_path = filedialog.askopenfilename(
        title="Open RTF File",
        defaultextension=".rtf",
        filetypes=filetypes
    )
    if selected_path:
        notes_file = selected_path
        messagebox.showinfo("File Opened", f"Opened file:\n{notes_file}")

def new_file():
    global notes_file
    filetypes = [("RTF files", "*.rtf"), ("All files", "*.*")]
    selected_path = filedialog.asksaveasfilename(
        title="Create New RTF File",
        defaultextension=".rtf",
        filetypes=filetypes
    )
    if selected_path:
        # Create an empty RTF file with the RTF header
        try:
            with open(selected_path, "w") as f:
                f.write("{\\rtf1\n}")
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
desc_entry.bind("<Tab>", auto_description)


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

# Start the Tkinter main loop (this keeps the app running and responsive)
root.mainloop()
