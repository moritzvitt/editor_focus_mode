# Editor Focus Mode

An Anki add-on for the Browser editor that hides non-relevant note fields based on note type configuration.

This README is intentionally short. It is meant to give contributors just the context they need to help with the add-on.

## Current Goal

The add-on should:

- detect the current Browser editor note type
- show only the configured subset of fields for that note type
- let the user temporarily show all fields with a toggle button
- let the user hide non-allowed fields again on the next click

## Current Behavior

The core feature already exists:

- config is stored per note type in `field_visibility_map`
- temporary overrides are stored in `field_visibility_disabled`
- a toolbar button toggles between the configured hidden view and a fully visible view

Main implementation files:

- [`__init__.py`](/Users/moritzvitt/src/addons/editor_focus_mode/__init__.py): hook registration
- [`field_visibility.py`](/Users/moritzvitt/src/addons/editor_focus_mode/field_visibility.py): main hide/show logic
- [`config.py`](/Users/moritzvitt/src/addons/editor_focus_mode/config.py): config helpers
- [`browser_utils.py`](/Users/moritzvitt/src/addons/editor_focus_mode/browser_utils.py): Browser tracking
- [`ui.py`](/Users/moritzvitt/src/addons/editor_focus_mode/ui.py): config dialog

## What Is Tricky

The hard part is the Anki editor lifecycle and DOM timing:

- `editor_will_load_note()` is an early injection pass
- `apply_field_visibility()` is a live-DOM pass after load
- the modern editor DOM is Svelte-based and more structured than older Anki versions
- the rich-text editable uses shadow DOM, so broad `contenteditable` searches are unreliable

The add-on now targets current wrapper elements such as:

- `.field-container`
- `.label-name`
- `[data-index]`

## Help Wanted

The most useful help right now would be:

- making the hide/show toggle more robust across reload timing
- simplifying the two-pass hide logic if there is a cleaner Anki-native approach
- validating that the Browser-only scoping is the right design
- improving compatibility across Anki versions without falling back to fragile selectors

## Future Plans

- add a button that rotates through multiple field layouts for the same note type
- support multiple visibility presets per note type instead of only one

## Docs

- Detailed README: [`docs/README-detailed.md`](/Users/moritzvitt/src/addons/editor_focus_mode/docs/README-detailed.md)
- Architecture overview: [`docs/architecture.md`](/Users/moritzvitt/src/addons/editor_focus_mode/docs/architecture.md)
- Wrapper reference: [`docs/wrappers.md`](/Users/moritzvitt/src/addons/editor_focus_mode/docs/wrappers.md)
- User interaction walkthrough: [`docs/user-flow.md`](/Users/moritzvitt/src/addons/editor_focus_mode/docs/user-flow.md)
- Mermaid charts: [`docs/chart.mmd`](/Users/moritzvitt/src/addons/editor_focus_mode/docs/chart.mmd), [`docs/user-flow.mmd`](/Users/moritzvitt/src/addons/editor_focus_mode/docs/user-flow.mmd), [`docs/user-flow-flowchart.mmd`](/Users/moritzvitt/src/addons/editor_focus_mode/docs/user-flow-flowchart.mmd)

## Local Testing

1. Copy the add-on folder into Anki's `addons21` directory.
2. Restart Anki.
3. Open the Browser and select a note with a configured note type.
4. Verify the initial hidden layout, then toggle to show all fields, then hide again.
