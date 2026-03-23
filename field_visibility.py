from __future__ import annotations

import json

from .browser_utils import current_browser

TARGET_NOTE_TYPE = "Moritz Language Reactor"
ALLOWED_FIELDS = {"Lemma", "Cloze", "Synonyms", "Japanese Notes"}


def apply_field_visibility(editor) -> None:
    browser = current_browser()
    if browser is None or getattr(browser, "editor", None) is None:
        return
    if editor is not browser.editor:
        return
    note = getattr(editor, "note", None)
    if note is None:
        return
    try:
        note_type_name = note.model().get("name")
    except Exception:
        return
    if note_type_name != TARGET_NOTE_TYPE:
        _reset_visibility(editor)
        return
    allowed = json.dumps(sorted(ALLOWED_FIELDS))
    js = f"""
    (function() {{
      const allowed = new Set({allowed});
      const candidates = document.querySelectorAll('[data-field-name]');
      if (candidates.length) {{
        candidates.forEach((el) => {{
          const name = el.getAttribute('data-field-name');
          el.style.display = allowed.has(name) ? '' : 'none';
        }});
        return;
      }}
      const rowSelectors = ['.field', '.editor-field', '.field-row'];
      let rows = [];
      rowSelectors.forEach((sel) => {{
        rows = rows.concat(Array.from(document.querySelectorAll(sel)));
      }});
      rows.forEach((row) => {{
        const nameEl = row.querySelector('.fieldname, .field-name, .name');
        const name = nameEl ? nameEl.textContent.trim() : null;
        if (!name) return;
        row.style.display = allowed.has(name) ? '' : 'none';
      }});
    }})();
    """
    try:
        editor.web.eval(js)
    except Exception:
        pass


def _reset_visibility(editor) -> None:
    js = """
    (function() {
      const candidates = document.querySelectorAll('[data-field-name]');
      if (candidates.length) {
        candidates.forEach((el) => { el.style.display = ''; });
        return;
      }
      const rowSelectors = ['.field', '.editor-field', '.field-row'];
      let rows = [];
      rowSelectors.forEach((sel) => { rows = rows.concat(Array.from(document.querySelectorAll(sel))); });
      rows.forEach((row) => { row.style.display = ''; });
    })();
    """
    try:
        editor.web.eval(js)
    except Exception:
        pass
