from __future__ import annotations

import json

from aqt import mw
from aqt.qt import QDialog, QDialogButtonBox, QFormLayout, QPlainTextEdit
from aqt.utils import showInfo

from .config import FIELD_VISIBILITY_MAP, get_addon_config, get_field_visibility_map, save_addon_config


def run_open_config() -> None:
    config = get_addon_config()
    dialog = QDialog(mw)
    dialog.setWindowTitle("Editor Focus Mode Configuration")
    layout = QFormLayout(dialog)
    layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

    field_map_edit = QPlainTextEdit()
    field_map_edit.setPlaceholderText('{"Note Type Name": ["Field1", "Field2"]}')
    field_map_edit.setPlainText(
        json.dumps(get_field_visibility_map(config), indent=2, ensure_ascii=False)
    )
    layout.addRow("Visible Fields by Note Type (JSON):", field_map_edit)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec() != QDialog.DialogCode.Accepted:
        return

    try:
        parsed = json.loads(field_map_edit.toPlainText().strip() or "{}")
        if not isinstance(parsed, dict):
            raise ValueError("Field visibility map must be a JSON object.")
        normalized: dict[str, list[str]] = {}
        for key, value in parsed.items():
            if not isinstance(value, list):
                raise ValueError(f"Notetype '{key}' must map to a list of fields.")
            normalized[str(key)] = [str(item) for item in value]
    except Exception as exc:
        showInfo(f"Invalid field visibility map. {exc}")
        return

    config[FIELD_VISIBILITY_MAP] = normalized
    save_addon_config(config)
    showInfo("Configuration saved.")
