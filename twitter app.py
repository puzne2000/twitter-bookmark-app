import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import pyperclip
import re
from pynput import keyboard  # Use pynput for the hotkey

# Function to validate if a string is a URL
def is_url(string):
    url_pattern = re.compile(
        r'^(https?://)?(www\.)?([a-zA-Z0-9_-]+)+(\.[a-zA-Z]{2,})+(/[a-zA-Z0-9#?=_-]*)*'
    )
    return bool(url_pattern.match(string))

# Function to check clipboard and auto-fill link field if valid
def autofill_link():
    print('autofill called')
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
        # Read the entire file content
        content = file.read()

        # Check if the file has the RTF header; if not, add it
        if not content.startswith("{\\rtf1"):
            content = "{\\rtf1\n" + content

        # Remove the last closing brace if it exists
        if content.endswith("}"):
            content = content[:-1]  # Remove the last brace

        # Move the file cursor to the start to overwrite with updated content
        file.seek(0)

        # Write the modified content back, minus the last closing brace
        file.write(content)

        # Append the new entry with formatting
        file.write(f"\\fs24 \\b Date:\\b0 {date}\\par\n")
        file.write(f"\\b Link:\\b0 {tweet_link}\\par\n")
        file.write(f"\\b Description:\\b0 {description}\\par\n\\par\n")

        # Add the final closing brace to complete the RTF structure
        file.write("}")

        # Truncate in case the new content is shorter than the original
        file.truncate()

    link_entry.delete(0, tk.END)
    desc_entry.delete("1.0", tk.END)
    messagebox.showinfo("Saved", "Your entry has been saved.")

# Function to bring up the app window with autofill from clipboard
def show_app():
    autofill_link()
    root.deiconify()
    root.lift()

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

# root.mainloop() ### gk added
root.withdraw()

# Define the hotkey with pynput
def on_activate():
    show_app()

# Setup hotkey listener
with keyboard.GlobalHotKeys({'<ctrl>+<shift>+t': on_activate}) as h:
    root.mainloop()
