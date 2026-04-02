# Editor Focus Mode Config

This add-on stores its configuration as a JSON dictionary.

## Keys

### `field_visibility_layouts`

Maps note type names to one or more field layouts.

Example:

```json
{
  "Basic": [
    {
      "name": "Default",
      "visible_fields": ["Front", "Back"]
    },
    {
      "name": "Minimal",
      "visible_fields": ["Front"]
    }
  ],
  "Cloze": [
    {
      "name": "Reading",
      "visible_fields": ["Text", "Extra"]
    }
  ]
}
```

Each layout can now have a configurable `name`. Clicking the layout button in the editor opens a dialog where you can rename layouts and choose which fields should be hidden for the active layout.

Older list-only layouts are still migrated automatically by the add-on.

For note types that do not yet have saved settings, the add-on creates defaults automatically from the field order, so fresh installs do not need field names configured in advance:

- the regular hide-fields toggle shows only the first field
- `Layout 1` shows the first 2 fields
- `Layout 2` shows the first 3 fields
- `Layout 3` shows the first 4 fields

### `field_visibility_active_layouts`

Stores the currently selected layout index for each note type.

Example:

```json
{
  "Basic": 0,
  "Cloze": 1
}
```

### `field_visibility_disabled`

Stores note types for which field hiding is temporarily disabled.

This is managed by the add-on when the toggle button is used, and usually does not need to be edited manually.
