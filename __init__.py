from __future__ import annotations

from aqt import gui_hooks

from .browser_utils import register_browser_instance
from .field_visibility import (
    apply_field_visibility,
    editor_will_load_note,
    editor_init_buttons,
)

if hasattr(gui_hooks, "browser_menus_did_init"):
    gui_hooks.browser_menus_did_init.append(register_browser_instance)
elif hasattr(gui_hooks, "browser_will_show"):
    gui_hooks.browser_will_show.append(register_browser_instance)
if hasattr(gui_hooks, "editor_did_load_note"):
    gui_hooks.editor_did_load_note.append(apply_field_visibility)
if hasattr(gui_hooks, "editor_will_load_note"):
    gui_hooks.editor_will_load_note.append(editor_will_load_note)
if hasattr(gui_hooks, "editor_did_init_buttons"):
    gui_hooks.editor_did_init_buttons.append(editor_init_buttons)
