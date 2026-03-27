from __future__ import annotations

import json
import time

from aqt.qt import QTimer
from pathlib import Path

from .browser_utils import current_browser
from .config import (
    get_addon_config,
    get_field_visibility_map,
    get_field_visibility_disabled,
    save_addon_config,
    FIELD_VISIBILITY_DISABLED,
)

DEFAULT_NOTE_TYPE = "Moritz Language Reactor"
DEFAULT_ALLOWED_FIELDS = {"Lemma", "Cloze", "Synonyms", "Japanese Notes"}

_TOGGLE_BYPASS_UNTIL = 0.0


def apply_field_visibility(editor) -> None:
    global _TOGGLE_BYPASS_UNTIL
    if _TOGGLE_BYPASS_UNTIL and _TOGGLE_BYPASS_UNTIL > time.time():
        _reset_visibility(editor, _all_field_names_from_note(getattr(editor, "note", None)))
        return
    browser = current_browser()
    if browser is None or getattr(browser, "editor", None) is None:
        return
    if editor is not browser.editor:
        return
    note = getattr(editor, "note", None)
    if note is None:
        return
    note_type_name = _note_type_name(note)
    if not note_type_name:
        return
    config = get_addon_config()
    field_map = get_field_visibility_map(config)
    if not field_map:
        field_map = {DEFAULT_NOTE_TYPE: sorted(DEFAULT_ALLOWED_FIELDS)}
    if note_type_name not in field_map:
        _update_toggle_button_label(editor)
        _, _, all_names = _allowed_field_indices(note, [])
        _reset_visibility(editor, all_names)
        return
    if note_type_name in get_field_visibility_disabled(config):
        _update_toggle_button_label(editor)
        _, _, all_names = _allowed_field_indices(note, [])
        _reset_visibility(editor, all_names)
        return
    allowed = field_map.get(note_type_name) or []
    allowed_indices, field_count, all_names = _allowed_field_indices(note, allowed)
    js = _hide_fields_js(allowed_indices, field_count, all_names, allowed)
    try:
        editor.web.eval(js)
        editor.web.eval(f"setTimeout(function(){{ {js} }}, 50);")
        editor.web.eval(f"setTimeout(function(){{ {js} }}, 200);")
    except Exception:
        pass
    _update_toggle_button_label(editor)
    _debug_dump_fields(editor)


def editor_will_load_note(js: str, note, editor) -> str:
    global _TOGGLE_BYPASS_UNTIL
    if _TOGGLE_BYPASS_UNTIL and _TOGGLE_BYPASS_UNTIL > time.time():
        _, _, all_names = _allowed_field_indices(note, [])
        return js + _reset_fields_js(all_names)
    browser = current_browser()
    if browser is None or getattr(browser, "editor", None) is None:
        return js
    if editor is not browser.editor:
        return js
    note_type_name = _note_type_name(note)
    if not note_type_name:
        return js
    config = get_addon_config()
    field_map = get_field_visibility_map(config)
    if not field_map:
        field_map = {DEFAULT_NOTE_TYPE: sorted(DEFAULT_ALLOWED_FIELDS)}
    if note_type_name in get_field_visibility_disabled(config) or note_type_name not in field_map:
        _, _, all_names = _allowed_field_indices(note, [])
        return js + _reset_fields_js(all_names)
    allowed = field_map.get(note_type_name) or []
    allowed_indices, field_count, all_names = _allowed_field_indices(note, allowed)
    return js + _hide_fields_js(allowed_indices, field_count, all_names, allowed)


def _reset_visibility(editor, all_names: list[str]) -> None:
    js = _reset_fields_js(all_names)
    try:
        editor.web.eval(js)
    except Exception:
        pass


def _debug_dump_fields(editor) -> None:
    js = """
    (function() {
      const rows = Array.from(document.querySelectorAll('.field-container'));
      const names = rows.map((row) => {
        const nameEl = row.querySelector('.label-name');
        return nameEl ? nameEl.textContent.trim() : null;
      }).filter(Boolean);
      const rowIndices = rows.map((row) => row.getAttribute('data-index'));
      const editorFields = Array.from(document.querySelectorAll('.editor-field'));
      const labels = Array.from(document.querySelectorAll('.label-name')).map((el) => el.textContent.trim());
      return JSON.stringify({
        rowCount: rows.length,
        editorFieldCount: editorFields.length,
        labelCount: labels.length,
        names,
        rowIndices
      });
    })();
    """
    def _write(result: str) -> None:
        try:
            path = Path(__file__).with_name("field_visibility_debug.txt")
            path.write_text(str(result), encoding="utf-8")
        except Exception:
            pass
    try:
        editor.web.evalWithCallback(js, _write)
    except Exception:
        pass


def _hide_fields_js(
    allowed_indices: list[int],
    field_count: int,
    all_names: list[str],
    allowed_fields: list[str],
) -> str:
    allowed = json.dumps(sorted(allowed_fields or list(DEFAULT_ALLOWED_FIELDS)))
    allowed_idx = json.dumps(sorted(allowed_indices))
    return f"""
    (function() {{
      const allowed = new Set({allowed});
      const allowedIdx = new Set({allowed_idx});
      const totalFields = {int(field_count)};
      const hiddenMarker = 'data-efm-hidden';
      const rowSelector = '.field-container';
      const labelSelector = '.label-name';
      const toInt = (value) => {{
        const parsed = Number.parseInt(value ?? '', 10);
        return Number.isNaN(parsed) ? null : parsed;
      }};
      const setVisible = (el) => {{
        if (!el) return;
        el.removeAttribute(hiddenMarker);
        el.style.display = '';
      }};
      const setHidden = (el) => {{
        if (!el) return;
        el.setAttribute(hiddenMarker, '1');
        el.style.display = 'none';
      }};
      const apply = () => {{
        const rows = Array.from(document.querySelectorAll(rowSelector));
        rows.forEach((row, idx) => {{
          const nameEl = row.querySelector(labelSelector);
          const name = nameEl && nameEl.textContent ? nameEl.textContent.trim() : '';
          const dataIndex = toInt(row.getAttribute('data-index'));
          const fallbackIndex = dataIndex === null ? idx : dataIndex;
          const matchesByName = Boolean(name) && allowed.has(name);
          const matchesByIndex = Boolean(totalFields && rows.length >= totalFields && allowedIdx.has(fallbackIndex));
          if (matchesByName || matchesByIndex) {{
            setVisible(row);
          }} else {{
            setHidden(row);
          }}
        }});
      }};
      apply();
      setTimeout(apply, 50);
      setTimeout(apply, 200);
    }})();
    """


def _allowed_field_indices(note, allowed_fields: list[str]) -> tuple[list[int], int, list[str]]:
    try:
        flds = note.model().get("flds") or []
    except Exception:
        return [], 0, []
    allowed = []
    all_names: list[str] = []
    for idx, fld in enumerate(flds):
        name = fld.get("name")
        if name:
            all_names.append(str(name))
        if fld.get("name") in set(allowed_fields):
            allowed.append(idx)
    return allowed, len(flds), all_names


def _all_field_names_from_note(note) -> list[str]:
    if note is None:
        return []
    try:
        flds = note.model().get("flds") or []
    except Exception:
        return []
    return [str(f.get("name")) for f in flds if f.get("name")]


def _note_type_name(note) -> str | None:
    try:
        return note.model().get("name")
    except Exception:
        return None


def toggle_field_visibility(editor) -> None:
    global _TOGGLE_BYPASS_UNTIL
    note = getattr(editor, "note", None)
    if note is None:
        return
    note_type_name = _note_type_name(note)
    if not note_type_name:
        return
    config = get_addon_config()
    disabled = get_field_visibility_disabled(config)
    field_map = get_field_visibility_map(config)
    if not field_map:
        field_map = {DEFAULT_NOTE_TYPE: sorted(DEFAULT_ALLOWED_FIELDS)}
    if note_type_name in disabled:
        disabled = [n for n in disabled if n != note_type_name]
    else:
        disabled.append(note_type_name)
    config[FIELD_VISIBILITY_DISABLED] = disabled
    save_addon_config(config)
    if note_type_name in disabled:
        _TOGGLE_BYPASS_UNTIL = time.time() + 0.5
    else:
        _TOGGLE_BYPASS_UNTIL = 0.0
    allowed = field_map.get(note_type_name) or []
    allowed_indices, field_count, all_names = _allowed_field_indices(note, allowed)
    if note_type_name in disabled:
        _reset_visibility(editor, all_names)
    else:
        js = _hide_fields_js(allowed_indices, field_count, all_names, allowed)
        try:
            editor.web.eval(js)
        except Exception:
            pass
        QTimer.singleShot(150, lambda: editor.web.eval(js))
        QTimer.singleShot(350, lambda: editor.web.eval(js))
        try:
            if hasattr(editor, "call_after_note_saved"):
                editor.call_after_note_saved(lambda: editor.loadNote(), keepFocus=True)
            else:
                editor.loadNote()
        except Exception:
            pass
    QTimer.singleShot(150, lambda: _update_toggle_button_label(editor))
    QTimer.singleShot(300, lambda: _update_toggle_button_label(editor))




def editor_init_buttons(buttons: list[str], editor) -> None:
    b = editor.addButton(
        icon=None,
        cmd="prompt_addon_toggle_fields",
        func=lambda ed: toggle_field_visibility(ed),
        tip="Toggle hidden fields",
        label="Hide Fields",
        id="prompt-addon-toggle-fields",
        toggleable=True,
        rightside=True,
    )
    buttons.append(b)


def _update_toggle_button_label(editor) -> None:
    note = getattr(editor, "note", None)
    if note is None:
        return
    note_type_name = _note_type_name(note)
    if not note_type_name:
        return
    config = get_addon_config()
    field_map = get_field_visibility_map(config)
    if not field_map:
        field_map = {DEFAULT_NOTE_TYPE: sorted(DEFAULT_ALLOWED_FIELDS)}
    if note_type_name not in field_map:
        return
    disabled = note_type_name in get_field_visibility_disabled(config)
    label = "Show Fields" if disabled else "Hide Fields"
    js = f"""
    (function() {{
      const label = "{label}";
      const apply = () => {{
        const btn = document.getElementById("prompt-addon-toggle-fields");
        if (btn) {{
          btn.textContent = label;
          return true;
        }}
        return false;
      }};
      if (!apply()) {{
        setTimeout(apply, 50);
        setTimeout(apply, 200);
      }}
    }})();
    """
    try:
        editor.web.eval(js)
    except Exception:
        pass


def _reset_fields_js(all_names: list[str]) -> str:
    return f"""
    (function() {{
      const hiddenMarker = 'data-efm-hidden';
      const reset = () => {{
        const rows = Array.from(document.querySelectorAll('.field-container'));
        rows.forEach((row) => {{
          row.removeAttribute(hiddenMarker);
          row.style.display = '';
        }});
        const marked = Array.from(document.querySelectorAll('[' + hiddenMarker + '="1"]'));
        marked.forEach((el) => {{
          el.removeAttribute(hiddenMarker);
          el.style.display = '';
        }});
      }};
      reset();
      setTimeout(reset, 50);
      setTimeout(reset, 200);
    }})();
    """
