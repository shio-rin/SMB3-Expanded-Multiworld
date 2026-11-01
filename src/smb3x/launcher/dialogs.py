# SPDX-License-Identifier: MPL-2.0
"""launcher / dialogs implementation for managed SMB3X sessions."""
from pathlib import Path
from ..shared.resources import RESOURCE_ROOT as ROOT

class SetupCancelled(ValueError):
    """The player chose to stop setup; no fatal launcher exception."""


def select(title, patterns):
    import Utils
    value = Utils.open_filename(title, patterns)
    if not value:
        raise SetupCancelled('Selection cancelled; existing saves were preserved')
    return Path(value).resolve()

def question(title, prompt, initial='', secret=False):
    import tkinter as tk
    from tkinter import simpledialog
    root = tk.Tk()
    root.withdraw()
    try:
        value = simpledialog.askstring(title, prompt, initialvalue=initial, show='*' if secret else None, parent=root)
    finally:
        root.destroy()
    if value is None:
        raise SetupCancelled('Setup cancelled; existing saves were preserved')
    return value if secret else value.strip()

def confirm(prompt):
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    try:
        return messagebox.askyesno('SMB3X', prompt, parent=root)
    finally:
        root.destroy()
