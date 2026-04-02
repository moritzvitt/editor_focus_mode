from __future__ import annotations

from copy import deepcopy

from aqt.qt import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    Qt,
)
from aqt.utils import showCritical

from .config import default_layout_name, layout_name, layout_visible_fields


class LayoutDialog(QDialog):
    def __init__(
        self,
        *,
        parent: QWidget,
        note_type_name: str,
        field_names: list[str],
        layouts: list[dict[str, object]],
        active_index: int,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Configure Layouts: {note_type_name}")
        self.resize(640, 620)

        self.note_type_name = note_type_name
        self.field_names = list(field_names)
        self.layouts = deepcopy(layouts) or [
            {
                "name": default_layout_name(0),
                "visible_fields": list(field_names),
            }
        ]
        self.active_index = max(0, min(active_index, len(self.layouts) - 1))
        self.current_index = self.active_index
        self._loading_layout = False

        self.layout_list = QListWidget()
        self.layout_name_edit = QLineEdit()
        self.active_layout_checkbox = QCheckBox("Use this as the active layout")
        self.visible_fields_list = QListWidget()
        self.visible_fields_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

        self._loading_layout = True
        self._build_ui()
        self._populate_layouts()
        self._load_layout(self.current_index)
        self._loading_layout = False

    def result_payload(self) -> tuple[list[dict[str, object]], int]:
        return self.layouts, self.active_index

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        intro = QLabel(
            "Choose which fields should stay visible for each layout. "
            "Checked fields stay visible while editing."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        top = QHBoxLayout()
        layout.addLayout(top, stretch=1)

        left_group = QGroupBox("Layouts")
        left_layout = QVBoxLayout(left_group)
        self.layout_list.currentRowChanged.connect(self._on_layout_changed)
        left_layout.addWidget(self.layout_list)

        left_buttons = QHBoxLayout()
        add_button = QPushButton("Add")
        duplicate_button = QPushButton("Duplicate")
        delete_button = QPushButton("Delete")
        add_button.clicked.connect(self._add_layout)
        duplicate_button.clicked.connect(self._duplicate_layout)
        delete_button.clicked.connect(self._delete_layout)
        left_buttons.addWidget(add_button)
        left_buttons.addWidget(duplicate_button)
        left_buttons.addWidget(delete_button)
        left_layout.addLayout(left_buttons)

        right_group = QGroupBox("Current Layout")
        right_layout = QVBoxLayout(right_group)
        form = QFormLayout()
        form.addRow("Layout name", self.layout_name_edit)
        form.addRow("", self.active_layout_checkbox)
        right_layout.addLayout(form)

        hide_help = QLabel("Checked fields are shown in this layout.")
        hide_help.setWordWrap(True)
        right_layout.addWidget(hide_help)
        fields_row = QHBoxLayout()
        fields_row.addWidget(self.visible_fields_list, stretch=1)

        order_buttons = QVBoxLayout()
        move_up_button = QPushButton("Move Up")
        move_down_button = QPushButton("Move Down")
        move_up_button.clicked.connect(lambda: self._move_selected_field(-1))
        move_down_button.clicked.connect(lambda: self._move_selected_field(1))
        order_buttons.addWidget(move_up_button)
        order_buttons.addWidget(move_down_button)
        order_buttons.addStretch(1)
        fields_row.addLayout(order_buttons)
        right_layout.addLayout(fields_row)

        top.addWidget(left_group, stretch=2)
        top.addWidget(right_group, stretch=3)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate_layouts(self) -> None:
        self.layout_list.clear()
        for index, layout in enumerate(self.layouts):
            self.layout_list.addItem(layout_name(layout, index))
        self.layout_list.setCurrentRow(self.current_index)

    def _load_layout(self, index: int) -> None:
        if index < 0 or index >= len(self.layouts):
            return
        self.current_index = index
        layout = self.layouts[index]
        visible_fields = set(layout_visible_fields(layout, self.field_names))
        field_order = self._layout_field_order(layout)
        self.layout_name_edit.setText(layout_name(layout, index))
        self.active_layout_checkbox.setChecked(index == self.active_index)
        self.visible_fields_list.clear()
        for field_name in field_order:
            item = QListWidgetItem(field_name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked
                if field_name in visible_fields
                else Qt.CheckState.Unchecked
            )
            self.visible_fields_list.addItem(item)

    def _store_current_layout(self) -> bool:
        if self.current_index < 0 or self.current_index >= len(self.layouts):
            return False

        layout_name_value = self.layout_name_edit.text().strip() or default_layout_name(self.current_index)
        visible_fields: list[str] = []
        field_order: list[str] = []
        for row in range(self.visible_fields_list.count()):
            item = self.visible_fields_list.item(row)
            field_order.append(item.text())
            if item.checkState() == Qt.CheckState.Checked:
                visible_fields.append(item.text())

        if not visible_fields:
            showCritical("At least one field must remain visible in a layout.", parent=self)
            return False

        self.layouts[self.current_index] = {
            "name": layout_name_value,
            "visible_fields": visible_fields,
            "field_order": field_order,
        }
        if self.active_layout_checkbox.isChecked():
            self.active_index = self.current_index
        return True

    def _on_layout_changed(self, index: int) -> None:
        if self._loading_layout or index < 0:
            return
        if not self._store_current_layout():
            self._loading_layout = True
            self.layout_list.setCurrentRow(self.current_index)
            self._loading_layout = False
            return
        self._loading_layout = True
        current_item = self.layout_list.item(self.current_index)
        if current_item is not None:
            current_item.setText(layout_name(self.layouts[self.current_index], self.current_index))
        self._load_layout(index)
        self._loading_layout = False

    def _add_layout(self) -> None:
        if not self._store_current_layout():
            return
        new_index = len(self.layouts)
        self.layouts.append(
            {
                "name": default_layout_name(new_index),
                "visible_fields": list(self.field_names),
                "field_order": list(self.field_names),
            }
        )
        self._populate_layouts()
        self.layout_list.setCurrentRow(new_index)

    def _duplicate_layout(self) -> None:
        if not self._store_current_layout():
            return
        source = deepcopy(self.layouts[self.current_index])
        source["name"] = f"{layout_name(source, self.current_index)} Copy"
        self.layouts.append(source)
        new_index = len(self.layouts) - 1
        self._populate_layouts()
        self.layout_list.setCurrentRow(new_index)

    def _delete_layout(self) -> None:
        if len(self.layouts) <= 1:
            showCritical("At least one layout must exist.", parent=self)
            return
        reply = QMessageBox.question(
            self,
            "Delete Layout",
            "Remove the selected layout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        del self.layouts[self.current_index]
        if self.active_index >= len(self.layouts):
            self.active_index = len(self.layouts) - 1
        if self.current_index >= len(self.layouts):
            self.current_index = len(self.layouts) - 1
        self._populate_layouts()
        self._load_layout(self.current_index)

    def _save_and_accept(self) -> None:
        if not self._store_current_layout():
            return
        self.accept()

    def _layout_field_order(self, layout: dict[str, object]) -> list[str]:
        field_order = layout.get("field_order")
        if isinstance(field_order, list):
            ordered: list[str] = []
            seen: set[str] = set()
            for item in field_order:
                field_name = str(item).strip()
                if not field_name or field_name in seen:
                    continue
                ordered.append(field_name)
                seen.add(field_name)
            for field_name in self.field_names:
                if field_name not in seen:
                    ordered.append(field_name)
            if ordered:
                return ordered
        return list(self.field_names)

    def _move_selected_field(self, direction: int) -> None:
        current_row = self.visible_fields_list.currentRow()
        if current_row < 0:
            return
        new_row = current_row + direction
        if new_row < 0 or new_row >= self.visible_fields_list.count():
            return
        item = self.visible_fields_list.takeItem(current_row)
        self.visible_fields_list.insertItem(new_row, item)
        self.visible_fields_list.setCurrentRow(new_row)
