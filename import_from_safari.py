# -----------------------------------------------------------------------------
# import_from_safari.py
#
# This script extracts bookmarks from the local Safari browser's Bookmarks.plist
# file and exports them to a CSV file named 'safari_bookmarks.csv'.
#
# How to use:
#   1. Ensure you have access to your Safari 'Bookmarks.plist' file. By default,
#      this script looks for 'Bookmarks.plist' in your home directory. If your
#      file is elsewhere, update the 'plist_path' variable accordingly.
#   2. Run the script:
#         python import_from_safari.py
#   3. The script will create (or overwrite) 'safari_bookmarks.csv' in the
#      current directory, containing all bookmarks with their URLs, folders,
#      and titles.
#
# Requirements:
#   - Python 3 (uses standard libraries: plistlib, csv, os)
#
# Note: This script does not modify your Safari bookmarks or any browser data.
# -----------------------------------------------------------------------------




import plistlib
import csv
import os

# Path to Safari bookmarks
plist_path = os.path.expanduser('Bookmarks.plist')
csv_path = 'safari_bookmarks.csv'

def walk_bookmarks(children, folder, rows):
    for item in children:
        item_type = item.get('WebBookmarkType')
        if item_type == 'WebBookmarkTypeList':
            # It's a folder
            folder_name = item.get('Title', folder)
            walk_bookmarks(item.get('Children', []), folder_name, rows)
        elif item_type == 'WebBookmarkTypeLeaf':
            # It's a bookmark
            url = item.get('URLString', '')
            title = item.get('URIDictionary', {}).get('title', '')
            rows.append([url, folder, title])

def main():
    with open(plist_path, 'rb') as f:
        plist = plistlib.load(f)
    rows = []
    # Top-level folders: BookmarksBar, BookmarksMenu, etc.
    for root in plist.get('Children', []):
        folder = root.get('Title', '')
        walk_bookmarks(root.get('Children', []), folder, rows)
    # Write to CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['url', 'folder', 'title'])
        writer.writerows(rows)
    print(f"Wrote {len(rows)} bookmarks to {csv_path}")

if __name__ == '__main__':
    main()