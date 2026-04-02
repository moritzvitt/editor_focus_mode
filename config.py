from __future__ import annotations

from aqt import mw

FIELD_VISIBILITY_MAP = "field_visibility_map"
FIELD_VISIBILITY_LAYOUTS = "field_visibility_layouts"
FIELD_VISIBILITY_ACTIVE_LAYOUTS = "field_visibility_active_layouts"
FIELD_VISIBILITY_DISABLED = "field_visibility_disabled"


ADDON_NAME = __name__.split(".")[0]


def default_layout_name(index: int) -> str:
    return f"Layout {index + 1}"


def default_toggle_visible_fields(field_names: list[str]) -> list[str]:
    return list(field_names[:1])


def default_layouts_from_field_names(field_names: list[str]) -> list[dict[str, object]]:
    layouts: list[dict[str, object]] = []
    for index, visible_count in enumerate((2, 3, 4)):
        visible_fields = list(field_names[:visible_count])
        if not visible_fields:
            continue
        if layouts and layouts[-1]["visible_fields"] == visible_fields:
            continue
        layouts.append(
            {
                "name": default_layout_name(index),
                "visible_fields": visible_fields,
                "field_order": list(field_names),
            }
        )
    return layouts or [
        {
            "name": default_layout_name(0),
            "visible_fields": list(field_names[:1]),
            "field_order": list(field_names),
        }
    ]


def get_addon_config() -> dict[str, str]:
    config = mw.addonManager.getConfig(ADDON_NAME) or {}
    if FIELD_VISIBILITY_LAYOUTS not in config or not isinstance(
        config.get(FIELD_VISIBILITY_LAYOUTS), dict
    ):
        config[FIELD_VISIBILITY_LAYOUTS] = _initial_layouts_from_config(config)
    if FIELD_VISIBILITY_MAP not in config or not isinstance(config.get(FIELD_VISIBILITY_MAP), dict):
        config[FIELD_VISIBILITY_MAP] = _first_layout_map(config[FIELD_VISIBILITY_LAYOUTS])
    if FIELD_VISIBILITY_ACTIVE_LAYOUTS not in config or not isinstance(
        config.get(FIELD_VISIBILITY_ACTIVE_LAYOUTS), dict
    ):
        config[FIELD_VISIBILITY_ACTIVE_LAYOUTS] = {}
    if FIELD_VISIBILITY_DISABLED not in config or not isinstance(
        config.get(FIELD_VISIBILITY_DISABLED), list
    ):
        config[FIELD_VISIBILITY_DISABLED] = []
    return config


def save_addon_config(config: dict[str, str]) -> None:
    mw.addonManager.writeConfig(ADDON_NAME, config)


def get_field_visibility_map(config: dict[str, str]) -> dict[str, list[str]]:
    raw = config.get(FIELD_VISIBILITY_MAP)
    if isinstance(raw, dict):
        return {str(k): [str(vv) for vv in v] for k, v in raw.items() if isinstance(v, list)}
    return {}


def get_field_visibility_layouts(config: dict[str, str]) -> dict[str, list[dict[str, object]]]:
    raw = config.get(FIELD_VISIBILITY_LAYOUTS)
    if isinstance(raw, dict):
        layouts: dict[str, list[dict[str, object]]] = {}
        for key, value in raw.items():
            if not isinstance(value, list):
                continue
            normalized = _normalize_layout_entries(value)
            if normalized:
                layouts[str(key)] = normalized
        if layouts:
            return layouts
    return _layouts_from_legacy_map(config)


def get_field_visibility_active_layouts(config: dict[str, str]) -> dict[str, int]:
    raw = config.get(FIELD_VISIBILITY_ACTIVE_LAYOUTS)
    if isinstance(raw, dict):
        active: dict[str, int] = {}
        for key, value in raw.items():
            try:
                active[str(key)] = max(0, int(value))
            except (TypeError, ValueError):
                continue
        return active
    return {}


def get_field_visibility_disabled(config: dict[str, str]) -> list[str]:
    raw = config.get(FIELD_VISIBILITY_DISABLED)
    if isinstance(raw, list):
        return [str(v) for v in raw]
    return []


def set_field_visibility_layouts(
    config: dict[str, str],
    note_type_name: str,
    layouts: list[dict[str, object]],
    *,
    active_index: int | None = None,
) -> None:
    layout_map = get_field_visibility_layouts(config)
    layout_map[note_type_name] = _normalize_layout_entries(layouts)
    config[FIELD_VISIBILITY_LAYOUTS] = layout_map
    config[FIELD_VISIBILITY_MAP] = _first_layout_map(layout_map)
    if active_index is not None:
        active_layouts = get_field_visibility_active_layouts(config)
        active_layouts[note_type_name] = max(0, active_index)
        config[FIELD_VISIBILITY_ACTIVE_LAYOUTS] = active_layouts


def ensure_note_type_defaults(
    config: dict[str, str],
    note_type_name: str,
    field_names: list[str],
) -> bool:
    changed = False

    layout_map = get_field_visibility_layouts(config)
    if note_type_name not in layout_map:
        layout_map[note_type_name] = default_layouts_from_field_names(field_names)
        config[FIELD_VISIBILITY_LAYOUTS] = layout_map
        changed = True

    field_map = get_field_visibility_map(config)
    if note_type_name not in field_map:
        field_map[note_type_name] = default_toggle_visible_fields(field_names)
        config[FIELD_VISIBILITY_MAP] = field_map
        changed = True

    return changed


def _initial_layouts_from_config(config: dict[str, str]) -> dict[str, list[dict[str, object]]]:
    return _layouts_from_legacy_map(config)


def _first_layout_map(layouts: object) -> dict[str, list[str]]:
    if not isinstance(layouts, dict):
        return {}
    normalized: dict[str, list[str]] = {}
    for key, value in layouts.items():
        if not isinstance(value, list) or not value:
            continue
        first = value[0]
        visible_fields = layout_visible_fields(first, [])
        if visible_fields:
            normalized[str(key)] = visible_fields
    return normalized


def _layouts_from_legacy_map(config: dict[str, str]) -> dict[str, list[dict[str, object]]]:
    legacy_map = get_field_visibility_map(config)
    if not legacy_map:
        return {}
    return {
        key: [
            {
                "name": default_layout_name(0),
                "visible_fields": [str(item) for item in value],
            }
        ]
        for key, value in legacy_map.items()
    }


def layout_name(layout: object, index: int) -> str:
    if isinstance(layout, dict):
        name = layout.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    return default_layout_name(index)


def layout_visible_fields(layout: object, all_field_names: list[str]) -> list[str]:
    if isinstance(layout, dict):
        visible_fields = layout.get("visible_fields")
        if isinstance(visible_fields, list):
            return [str(item) for item in visible_fields if str(item).strip()]
        hidden_fields = layout.get("hidden_fields")
        if isinstance(hidden_fields, list):
            hidden = {str(item) for item in hidden_fields if str(item).strip()}
            return [field for field in all_field_names if field not in hidden]
    if isinstance(layout, list):
        return [str(item) for item in layout if str(item).strip()]
    return []


def layout_field_order(layout: object, all_field_names: list[str]) -> list[str]:
    if isinstance(layout, dict):
        field_order = layout.get("field_order")
        if isinstance(field_order, list):
            return _normalize_field_order(field_order, all_field_names)
    return list(all_field_names)


def _normalize_layout_entries(entries: list[object]) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for index, entry in enumerate(entries):
        visible_fields = layout_visible_fields(entry, [])
        if not visible_fields:
            continue
        field_order = layout_field_order(entry, visible_fields)
        visible_set = set(field_order)
        visible_fields = [field for field in visible_fields if field in visible_set]
        normalized.append(
            {
                "name": layout_name(entry, index),
                "visible_fields": visible_fields,
                "field_order": field_order,
            }
        )
    return normalized


def _normalize_field_order(field_order: list[object], all_field_names: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in field_order:
        name = str(item).strip()
        if not name or name in seen:
            continue
        ordered.append(name)
        seen.add(name)
    for field_name in all_field_names:
        if field_name not in seen:
            ordered.append(field_name)
            seen.add(field_name)
    return ordered
