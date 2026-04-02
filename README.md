# Editor Focus Mode

An Anki add-on for the Browser editor that hides non-relevant note fields based on note type configuration.

## What It Does

- shows only the configured subset of fields for a note type
- adds a toggle button to temporarily show all fields
- lets the user hide non-allowed fields again on the next click
- adds a layout button that opens a layout editor for the current note type
- lets you rename layouts and choose which fields should be hidden per layout
- works out of the box for unconfigured note types by generating defaults from field order

## Demo

[▶ Watch the demo video on YouTube](https://youtu.be/6XNraKFZiZc)

[![Show Only Specific Fields demo video](https://img.youtube.com/vi/6XNraKFZiZc/maxresdefault.jpg)](https://youtu.be/6XNraKFZiZc)

The thumbnail above links to the demo video.

## Main Files

- [`__init__.py`](./__init__.py): hook registration
- [`field_visibility.py`](./field_visibility.py): hide/show logic
- [`config.py`](./config.py): config helpers
- [`browser_utils.py`](./browser_utils.py): Browser tracking
## Help Wanted

The main hard parts are:

- Anki editor lifecycle timing
- reliable toggle behavior across note reloads
- keeping the DOM selectors robust across Anki versions

## Docs

- Detailed README: [`docs/README-detailed.md`](./docs/README-detailed.md)
- Architecture: [`docs/architecture.md`](./docs/architecture.md)
- Current problems: [`docs/current-problems.md`](./docs/current-problems.md)
- Wrapper reference: [`docs/wrappers.md`](./docs/wrappers.md)
- User flow: [`docs/user-flow.md`](./docs/user-flow.md)
- Charts: [`docs/charts/`](./docs/charts/)


## Release Workflow

Run `./scripts/release.sh` to validate the add-on and build a clean `editor_focus_mode.ankiaddon` package for AnkiWeb upload. The script also prints the latest tag, the top changelog entry, and the remaining manual release steps.

If you use VS Code, run the `Prepare release` task for the same workflow.
