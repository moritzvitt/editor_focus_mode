**Findings**

1. High: the DOM-hiding logic is broad enough to hide unrelated editor UI, not just fields. In [`field_visibility.py` lines 161-216](../field_visibility.py#L161), the selectors include generic targets like `label`, `.name`, `.title`, and then iterate over every element in `body` comparing `textContent`. If any non-field UI element happens to contain a field name, it can be hidden too. That makes the feature fragile across Anki versions and themes, and it risks breaking the editor chrome instead of only field rows.

2. Medium: the toggle bypass is global process state, so one toggle can temporarily affect a different editor/note load. [`_TOGGLE_BYPASS_UNTIL` in `field_visibility.py` lines 21, 24-28, 67-71, 258-280](../field_visibility.py#L21) is not scoped to the current editor instance or note type. If another browser/editor note loads during that 0.5s window, visibility can be reset incorrectly. This is the kind of race that only shows up intermittently.

3. Medium: the button label can become stale when switching to an unsupported note type. [`_update_toggle_button_label()` returns early when the note type is not in the map in `field_visibility.py` lines 331-332](../field_visibility.py#L331). If the previous note showed `Show Fields` and the next note type is unsupported, the old label can remain visible even though the button no longer reflects real state.

4. Low: debug instrumentation is still live in the normal path and writes to disk on every apply. [`apply_field_visibility()` always calls `_debug_dump_fields()` in `field_visibility.py` line 64](../field_visibility.py#L64), and `_debug_dump_fields()` writes [`field_visibility_debug.txt`](../field_visibility_debug.txt) next to the addon file. That adds unnecessary I/O and leaves a stray artifact in production behavior.

**What I’d do better now**

I’d tighten the implementation around actual field-row containers instead of hiding arbitrary text matches. The safest fix is to identify the editor’s real field wrapper structure once, then only toggle those nodes.

I’d also remove the global timeout flag and replace it with state scoped to the editor or note type, clean up the stale-label case by explicitly resetting the button text for unsupported notes, and gate the debug dump behind a debug flag or remove it entirely.

Residual gap: there are no tests around note switching, unsupported note types, or toggle timing, so these regressions are likely to recur. If you want, I can make those fixes now.
