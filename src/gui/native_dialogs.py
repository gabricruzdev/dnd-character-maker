"""
Native file dialogs (tkinter) for desktop platforms.
"""

from __future__ import annotations

from pathlib import Path


def pick_json_file(initial_dir: Path) -> str | None:
    """Opens a file picker for .json files; returns path or None if cancelled."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        return None

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.update_idletasks()
    try:
        path = filedialog.askopenfilename(
            parent=root,
            initialdir=str(initial_dir) if initial_dir.is_dir() else None,
            title="Load Sheet",
            filetypes=[
                ("JSON Sheet", "*.json"),
                ("All files", "*.*"),
            ],
        )
    finally:
        root.destroy()
    return path if path else None


def save_json_file(initial_dir: Path, default_name: str) -> str | None:
    """Save as .json dialog."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        return None

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.update_idletasks()
    try:
        path = filedialog.asksaveasfilename(
            parent=root,
            initialdir=str(initial_dir) if initial_dir.is_dir() else None,
            initialfile=default_name,
            defaultextension=".json",
            title="Save Sheet",
            filetypes=[("JSON Sheet", "*.json")],
        )
    finally:
        root.destroy()
    return path if path else None


def save_pdf_file(initial_dir: Path, default_name: str) -> str | None:
    """Save as .pdf dialog."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        return None

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.update_idletasks()
    try:
        path = filedialog.asksaveasfilename(
            parent=root,
            initialdir=str(initial_dir) if initial_dir.is_dir() else None,
            initialfile=default_name,
            defaultextension=".pdf",
            title="Export PDF",
            filetypes=[("PDF", "*.pdf")],
        )
    finally:
        root.destroy()
    return path if path else None
