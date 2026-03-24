from __future__ import annotations


_ACTIVE_FIELD_CONTEXT: dict[str, object] | None = None
_BATCH_LIMIT = 5


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