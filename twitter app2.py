import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import pyperclip
import re
import threading
from pynput import keyboard  # Use pynput for the hotkey

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

    link_entry.delete(0, tk.END)
    desc_entry.delete("1.0", tk.END)
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
            saved_window.after(50, fade_out, alpha - 0.03)
        else:
            saved_window.destroy()

    fade_out()

# Function to bring up the app window with autofill from clipboard
def show_app():
    print("show me the appppp1")
    autofill_link()
    root.deiconify()
    root.lift()

# Thread to run the hotkey listener
def on_activate():
    print("hot KEY!")
    show_app()

def hotkey_listener(callback = on_activate):
    print("listener being activated")
    
    listener = keyboard.GlobalHotKeys({
            '<cmd>+<shift>+u': callback
        })
    listener.start()
    print("listener activated")
    return listener



def on_window_activated(event):
    print("Window activated!")
    # You can perform any actions here when the window gains focus.
    autofill_link()


# Initialize Tkinter GUI
root = tk.Tk()
root.title("Tweet Logger")

tk.Label(root, text="Tweet Link:").grid(row=0, column=0, padx=10, pady=5)
link_entry = tk.Entry(root, width=50)
link_entry.grid(row=0, column=1, padx=10, pady=5)

tk.Label(root, text="Description:").grid(row=1, column=0, padx=10, pady=5)
desc_entry = tk.Text(root, width=50, height=5)
desc_entry.grid(row=1, column=1, padx=10, pady=5)

save_button = tk.Button(root, text="Save Entry", command=save_entry)
save_button.grid(row=2, column=1, pady=10)

# Bind the <FocusIn> event to the root window
root.bind("<FocusIn>", on_window_activated)


# Start the hotkey listener in a separate thread
hotkey_thread = threading.Thread(target=hotkey_listener, daemon=True)
hotkey_thread.start()

root.mainloop() #gk added this!
root.withdraw()

# Start the Tkinter main loop
root.mainloop()
