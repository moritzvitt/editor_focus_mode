from __future__ import annotations

from aqt import mw
from aqt.qt import QTimer
from aqt.utils import askUser, showInfo, tooltip

from .browser_utils import (
    current_browser,
    get_selected_notes,
    refresh_browser_note,
    refresh_other_editors,
    unwrap_editor,
)
from .chatgpt_app import focus_and_paste_chatgpt
from .clipboard_utils import copy_to_clipboard, normalize_response_text, read_clipboard_payload
from .config import (
    CHATGPT_MODE_BATCH,
    CHATGPT_MODE_OFF,
    CHATGPT_MODE_SINGLE,
    chatgpt_required_fields,
    get_addon_config,
)
from .utils.chatgpt_helper import (
    build_batch_prompt,
    build_prompt_for_note,
    parse_batch_response,
)

_CHATGPT_WAIT_TIMER: QTimer | None = None
_CHATGPT_PENDING: dict[str, object] | None = None
_ACTIVE_FIELD_CONTEXT: dict[str, object] | None = None





def on_editor_did_focus_field(note, field_idx) -> None:
    global _ACTIVE_FIELD_CONTEXT
    field_name = None
    try:
        field_name = note.model()["flds"][field_idx]["name"]
    except Exception:
        field_name = None
    note_id = getattr(note, "id", None)
    _ACTIVE_FIELD_CONTEXT = {
        "note_id": int(note_id) if note_id else None,
        "field_index": field_idx,
        "field_name": field_name,
    }


