"""
Tests for `twitter app2.py`: what the entry window says and does when saving.

The app is one script that builds its window when run, so these tests load it with
the hotkey, clipboard, description server, sounds and app switching faked, and with
the notes file pointed at a temporary JSON file. Nothing in output/ and nothing on
the real clipboard is touched. Windows may flash on screen while the tests run.

Run from the app's folder:
    ~/.local/share/venvs/twitter-bookmark-app/bin/python -m unittest discover tests
"""
import json
import os
import stat
import sys
import tempfile
import tkinter as tk
import types
import unittest

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "twitter app2.py")
ORIGINAL_NOTES_LINE = \
    'notes_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "merged.json")'


class FakeSubprocess:
    """Records commands; answers the Finder-clipboard query from finder_path."""

    class Result:
        def __init__(self, out="", rc=0):
            self.stdout, self.returncode = out, rc

    def __init__(self):
        self.calls = []
        self.finder_path = None

    def run(self, cmd, *args, **kwargs):
        self.calls.append(cmd)
        if "furl" in " ".join(cmd):
            return self.Result(self.finder_path or "", 0 if self.finder_path else 1)
        return self.Result("")

    def Popen(self, cmd, *args, **kwargs):
        self.calls.append(cmd)


class FakeMessagebox:
    def __init__(self):
        self.shown = []

    def showwarning(self, title, message, **kwargs):
        self.shown.append(("warning", message))

    def showerror(self, title, message, **kwargs):
        self.shown.append(("error", message))


def load_app(tmpdir, notes_file):
    """Run the app script up to (not including) its main loop; return its globals."""
    with open(APP, encoding="utf-8") as f:
        src = f.read()
    assert ORIGINAL_NOTES_LINE in src, "default notes_file line changed; update the tests"
    src = src.replace(ORIGINAL_NOTES_LINE, f"notes_file = {notes_file!r}")
    src = src.replace("root.mainloop()", "")

    class NoHotKeys:
        def __init__(self, *args, **kwargs): pass
        def start(self): pass

    fake_keyboard = types.SimpleNamespace(GlobalHotKeys=NoHotKeys)
    saved = {k: sys.modules.get(k) for k in ("pynput", "pynput.keyboard")}
    sys.modules["pynput"] = types.SimpleNamespace(keyboard=fake_keyboard)
    sys.modules["pynput.keyboard"] = fake_keyboard
    try:
        # __file__ in the temp folder, so the app's output/ folder is one that doesn't exist
        app = {"__name__": "twitter_app2", "__file__": os.path.join(tmpdir, "app.py")}
        exec(compile(src, APP, "exec"), app)
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
    # Replace what the app's functions look up at call time
    app["subprocess"] = FakeSubprocess()
    app["messagebox"] = FakeMessagebox()
    app["clipboard"] = {"text": ""}
    app["pyperclip"] = types.SimpleNamespace(paste=lambda: app["clipboard"]["text"])
    return app


class AppTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.notes = os.path.join(cls.tmp.name, "notes.json")
        with open(cls.notes, "w") as f:
            f.write("[]")
        cls.app = load_app(cls.tmp.name, cls.notes)
        cls.root = cls.app["root"]

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()
        cls.tmp.cleanup()

    def setUp(self):
        with open(self.notes, "w") as f:
            json.dump([{"date": "2026-01-01", "time": "10:00:00", "url": "https://old.example.com/a",
                        "draft": "", "description": "old"}], f)
        self.app["notes_file"] = self.notes
        self.app["messagebox"].shown.clear()
        self.app["subprocess"].calls.clear()
        self.app["subprocess"].finder_path = None
        self.app["existing_entry"] = None
        self.app["desc_for_link"] = None
        self.remove_toplevels()

    def tearDown(self):
        os.chmod(self.notes, stat.S_IRUSR | stat.S_IWUSR)
        self.remove_toplevels()

    # --- helpers ---
    def remove_toplevels(self):
        for w in self.root.winfo_children():
            if isinstance(w, tk.Toplevel):
                w.destroy()
        self.root.update()

    def toplevel(self, title):
        found = [w for w in self.root.winfo_children()
                 if isinstance(w, tk.Toplevel) and w.winfo_exists() and w.title() == title]
        return found[0] if found else None

    def saved_flashes(self):
        return [w for w in self.root.winfo_children() if isinstance(w, tk.Toplevel)
                and any(isinstance(c, tk.Label) and c.cget("text") == "Entry Saved"
                        for c in w.winfo_children())]

    def fill(self, link, description):
        link_entry, desc_entry = self.app["link_entry"], self.app["desc_entry"]
        link_entry.delete(0, tk.END)
        link_entry.insert(0, link)
        desc_entry.delete("1.0", tk.END)
        desc_entry.insert("1.0", description)
        self.root.deiconify()
        self.root.update()

    def entries(self):
        with open(self.notes) as f:
            return json.load(f)

    def press_done(self):
        """Enter in the description box, then Enter (the button) in the Done? window."""
        self.app["verify_done_window"](self.root, self.app["entry_is_done"])
        done_win = self.toplevel("Done?")
        [b for b in done_win.winfo_children() if isinstance(b, tk.Button)][0].invoke()
        self.root.update()

    def tab_with_server_answer(self, answer, in_dialog):
        """Press Tab; the fake server answers `answer`; in_dialog(dialog) runs in the box."""
        self.app["get_description_from_server"] = \
            lambda address, draft, when_done: self.root.after(50, when_done, answer)
        self.app["auto_description_requested"](None)
        self.root.update()
        after_tab = {"flashes": len(self.saved_flashes()), "hidden": self.root.state() == "withdrawn"}

        def run_dialog():
            try:
                in_dialog(self.toplevel("Description obtained"))
            finally:
                self.root.after(300, self.root.quit)
        self.root.after(300, run_dialog)
        self.root.after(5000, self.root.quit)  # safety net
        self.root.mainloop()
        self.root.update()
        return after_tab


class TestEnterSaving(AppTestCase):
    """Quirk 1: only say "Entry Saved" (and clear the window) when something was saved."""

    def test_empty_description_keeps_window_open(self):
        before = self.entries()
        self.fill("https://new.example.com/x", "")
        self.press_done()
        self.assertEqual(self.app["messagebox"].shown[0][0], "warning")
        self.assertFalse(self.saved_flashes())
        self.assertNotEqual(self.root.state(), "withdrawn")
        self.assertEqual(self.app["link_entry"].get(), "https://new.example.com/x")
        self.assertEqual(self.entries(), before)

    def test_write_failure_shows_error_and_keeps_text(self):
        self.fill("https://new.example.com/x", "a description")
        os.chmod(self.notes, stat.S_IRUSR)
        self.press_done()
        self.assertEqual(self.app["messagebox"].shown[0][0], "error")
        self.assertFalse(self.saved_flashes())
        self.assertNotEqual(self.root.state(), "withdrawn")
        self.assertEqual(self.app["desc_entry"].get("1.0", tk.END).strip(), "a description")

    def test_good_save_writes_and_says_saved(self):
        self.fill("https://new.example.com/x", "a description")
        self.press_done()
        self.assertEqual(self.entries()[-1]["description"], "a description")
        self.assertTrue(self.saved_flashes())
        self.assertEqual(self.root.state(), "withdrawn")
        self.assertEqual(self.app["link_entry"].get(), "")


class TestTabSaving(AppTestCase):
    """Quirks 2 and 3: Tab doesn't claim an early save; server errors aren't saved."""

    def test_tab_says_nothing_until_saved(self):
        self.fill("https://tab.example.com/z", "")

        def accept(dialog):
            self.assertFalse(any(isinstance(c, tk.Label) for c in dialog.winfo_children()),
                             "no error note for a normal answer")
            [c for c in dialog.winfo_children() if isinstance(c, tk.Button)][0].invoke()
        after_tab = self.tab_with_server_answer("A nice description", accept)
        self.assertEqual(after_tab["flashes"], 0, "'Entry Saved' shown before the server answered")
        self.assertTrue(after_tab["hidden"])
        self.assertEqual(self.entries()[-1]["description"], "A nice description")
        self.assertTrue(self.saved_flashes(), "'Entry Saved' shown after the save")

    def test_server_error_is_not_saved(self):
        self.fill("https://tab.example.com/y", "my own words")
        n_before = len(self.entries())
        seen = {}

        def press_enter_then_replace(dialog):
            labels = [c.cget("text") for c in dialog.winfo_children() if isinstance(c, tk.Label)]
            seen["note"] = any("error from the description server" in t for t in labels)
            button = [c for c in dialog.winfo_children() if isinstance(c, tk.Button)][0]
            box = [c for c in dialog.winfo_children() if isinstance(c, tk.Text)][0]
            button.invoke()  # Enter with the error text still there
            self.root.update()
            seen["still_open"] = bool(dialog.winfo_exists())
            seen["saved_meanwhile"] = len(self.entries()) != n_before
            box.delete("1.0", tk.END)
            box.insert("1.0", "replacement text")
            button.invoke()
        self.tab_with_server_answer("Error: 403", press_enter_then_replace)
        self.assertTrue(seen["note"], "error note shown")
        self.assertTrue(seen["still_open"], "Enter on the error keeps the box open")
        self.assertFalse(seen["saved_meanwhile"], "nothing saved while the error was there")
        self.assertEqual(self.entries()[-1]["description"], "replacement text")
        self.assertEqual(self.entries()[-1]["draft"], "my own words")

    def test_server_exception_then_esc_saves_typed_text(self):
        self.fill("https://tab.example.com/w", "my own words")

        def press_esc(dialog):
            dialog.event_generate("<Escape>")
        self.tab_with_server_answer("Exception: Connection refused", press_esc)
        self.assertEqual(self.entries()[-1]["description"], "my own words")


class TestClipboard(AppTestCase):
    """Quirk 4: only links and supported files open the window."""

    def test_is_url(self):
        is_url = self.app["is_url"]
        for text in ["example.com/page", "example.com", "https://x.com/a/status/1?s=20",
                     "http://foo.md", "www.notes.md", "github.io/x.zip",
                     "https://example.com/file.pdf", " https://a.org \n"]:
            self.assertTrue(is_url(text), text)
        for text in ["report.docx", "notes.txt", "My_File.pages", "my.report.v2.docx",
                     "data.json", "hello"]:
            self.assertFalse(is_url(text), text)

    def autofill(self, text, finder_name=None):
        self.app["clipboard"]["text"] = text
        path = None
        if finder_name:
            path = os.path.join(self.tmp.name, finder_name)
            open(path, "w").close()
        self.app["subprocess"].finder_path = path
        return self.app["autofill_link"](self.app["link_entry"])

    def test_file_names_do_not_open(self):
        self.assertFalse(self.autofill("report.docx"))
        self.assertFalse(self.autofill("notes.txt"))
        self.assertFalse(self.autofill("report.docx", finder_name="report.docx"))

    def test_links_and_supported_files_open(self):
        self.assertTrue(self.autofill("example.com/page"))
        self.assertTrue(self.autofill("https://x.com/u/status/1"))
        self.assertTrue(self.autofill("paper.pdf", finder_name="paper.pdf"))
        self.assertTrue(self.app["link_entry"].get().endswith("paper.pdf"))

    def test_file_name_plays_frog(self):
        self.app["clipboard"]["text"] = "report.docx"
        self.app["attempt_app_to_front"]()
        self.assertTrue(any("Frog.aiff" in " ".join(c) for c in self.app["subprocess"].calls))


if __name__ == "__main__":
    unittest.main()
