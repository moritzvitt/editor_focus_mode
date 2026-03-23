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
      const names = [];
      const candidates = document.querySelectorAll('[data-field-name]');
      candidates.forEach((el) => names.push(el.getAttribute('data-field-name')));
      let rows = [];
      const rowSelectors = ['.field', '.editor-field', '.field-row', '.field-row-wrapper'];
      rowSelectors.forEach((sel) => { rows = rows.concat(Array.from(document.querySelectorAll(sel))); });
      const editables = Array.from(document.querySelectorAll('[contenteditable="true"]'));
      const editableContainers = editables.map((el) => {
        const container = el.closest('.field, .editor-field, .field-row, .field-row-wrapper, .anki-field, .editor-row, .row') || el.parentElement;
        if (!container) return null;
        return {
          tag: container.tagName,
          id: container.id || null,
          class: container.className || null,
        };
      }).filter(Boolean);
      if (!names.length) {
        rows.forEach((row) => {
          const nameEl = row.querySelector('.fieldname, .field-name, .name, label, .label, .title');
          if (nameEl) names.push(nameEl.textContent.trim());
        });
      }
      return JSON.stringify({
        dataFieldCount: candidates.length,
        rowCount: rows.length,
        names,
        editableCount: editables.length,
        editableContainers
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
    all_fields = json.dumps(sorted(set(all_names)))
    allowed_idx = json.dumps(sorted(allowed_indices))
    return f"""
    (function() {{
      const allowed = new Set({allowed});
      const allFieldNames = new Set({all_fields});
      const allowedIdx = new Set({allowed_idx});
      const totalFields = {int(field_count)};
      const headerSelectors = '.fieldname, .field-name, .name, label, .label, .title';
      const apply = () => {{
        const candidates = document.querySelectorAll('[data-field-name]');
        if (candidates.length) {{
          candidates.forEach((el) => {{
            const name = el.getAttribute('data-field-name');
            el.style.display = allowed.has(name) ? '' : 'none';
          }});
        }}
        const rowSelectors = ['.field', '.editor-field', '.field-row', '.field-row-wrapper'];
        let rows = [];
        rowSelectors.forEach((sel) => {{
          const found = Array.from(document.querySelectorAll(sel));
          if (found.length > rows.length) rows = found;
        }});
        rows.forEach((row, idx) => {{
          let name = null;
          const nameEl = row.querySelector(headerSelectors);
          if (nameEl) {{
            name = nameEl.textContent.trim();
          }}
          if (!name) {{
            const dataName = row.getAttribute('data-field-name');
            if (dataName) name = dataName;
          }}
          if (name) {{
            row.style.display = allowed.has(name) ? '' : 'none';
            return;
          }}
          if (totalFields && rows.length >= totalFields) {{
            row.style.display = allowedIdx.has(idx) ? '' : 'none';
          }}
        }});
        const headers = Array.from(document.querySelectorAll(headerSelectors));
        headers.forEach((el) => {{
          const text = el.textContent ? el.textContent.trim() : '';
          if (!text) return;
          if (allowed.has(text)) return;
          el.style.display = 'none';
          const row = el.closest('.field, .editor-field, .field-row, .field-row-wrapper');
          if (row) {{
            row.style.display = 'none';
          }} else if (el.parentElement) {{
            el.parentElement.style.display = 'none';
          }}
        }});
        const allEls = Array.from(document.querySelectorAll('body *'));
        allEls.forEach((el) => {{
          const text = el.textContent ? el.textContent.trim() : '';
          if (!text) return;
          if (!allFieldNames.has(text)) return;
          if (allowed.has(text)) return;
          el.style.display = 'none';
          const row = el.closest('.field, .editor-field, .field-row, .field-row-wrapper');
          if (row) row.style.display = 'none';
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
    all_fields = json.dumps(sorted(set(all_names)))
    return f"""
    (function() {{
      const allFieldNames = new Set({all_fields});
      const reset = () => {{
        const candidates = document.querySelectorAll('[data-field-name]');
        if (candidates.length) {{
          candidates.forEach((el) => {{ el.style.display = ''; }});
        }}
        const rowSelectors = ['.field', '.editor-field', '.field-row', '.field-row-wrapper'];
        let rows = [];
        rowSelectors.forEach((sel) => {{ rows = rows.concat(Array.from(document.querySelectorAll(sel))); }});
        rows.forEach((row) => {{ row.style.display = ''; }});
        const allEls = Array.from(document.querySelectorAll('body *'));
        allEls.forEach((el) => {{
          const text = el.textContent ? el.textContent.trim() : '';
          if (!text) return;
          if (!allFieldNames.has(text)) return;
          el.style.display = '';
          const row = el.closest('.field, .editor-field, .field-row, .field-row-wrapper');
          if (row) row.style.display = '';
        }});
      }};
      reset();
      setTimeout(reset, 50);
      setTimeout(reset, 200);
    }})();
    """
