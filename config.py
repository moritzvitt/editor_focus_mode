from __future__ import annotations

import sys

from aqt import mw

CHATGPT_MODE_OFF = "OFF"
CHATGPT_MODE_SINGLE = "SINGLE"
CHATGPT_MODE_BATCH = "BATCH"

CHATGPT_CONFIG_MODE = "chatgpt_helper_mode"
CHATGPT_CONFIG_SHORTCUT = "chatgpt_helper_shortcut"
CHATGPT_CONFIG_LEMMA_FIELD = "chatgpt_field_lemma"
CHATGPT_CONFIG_SUBTITLE_FIELD = "chatgpt_field_subtitle"
CHATGPT_CONFIG_QUESTION_FIELD = "chatgpt_field_question"
CHATGPT_CONFIG_GRAMMAR_FIELD = "chatgpt_field_grammar"
FIELD_VISIBILITY_MAP = "field_visibility_map"
FIELD_VISIBILITY_DISABLED = "field_visibility_disabled"

CHATGPT_DEFAULT_SHORTCUT = (
    "Meta+Shift+G" if sys.platform == "darwin" else "Ctrl+Shift+G"
)


ADDON_NAME = __name__.split(".")[0]


def get_addon_config() -> dict[str, str]:
    config = mw.addonManager.getConfig(ADDON_NAME) or {}
    if CHATGPT_CONFIG_MODE not in config:
        config[CHATGPT_CONFIG_MODE] = CHATGPT_MODE_SINGLE
    if CHATGPT_CONFIG_SHORTCUT not in config or not str(
        config.get(CHATGPT_CONFIG_SHORTCUT) or ""
    ).strip():
        config[CHATGPT_CONFIG_SHORTCUT] = CHATGPT_DEFAULT_SHORTCUT
    if CHATGPT_CONFIG_LEMMA_FIELD not in config or not str(
        config.get(CHATGPT_CONFIG_LEMMA_FIELD) or ""
    ).strip():
        config[CHATGPT_CONFIG_LEMMA_FIELD] = "Lemma"
    if CHATGPT_CONFIG_SUBTITLE_FIELD not in config or not str(
        config.get(CHATGPT_CONFIG_SUBTITLE_FIELD) or ""
    ).strip():
        config[CHATGPT_CONFIG_SUBTITLE_FIELD] = "Subtitle"
    if CHATGPT_CONFIG_QUESTION_FIELD not in config or not str(
        config.get(CHATGPT_CONFIG_QUESTION_FIELD) or ""
    ).strip():
        config[CHATGPT_CONFIG_QUESTION_FIELD] = "Question"
    if CHATGPT_CONFIG_GRAMMAR_FIELD not in config or not str(
        config.get(CHATGPT_CONFIG_GRAMMAR_FIELD) or ""
    ).strip():
        config[CHATGPT_CONFIG_GRAMMAR_FIELD] = "Grammar"
    if FIELD_VISIBILITY_MAP not in config or not isinstance(
        config.get(FIELD_VISIBILITY_MAP), dict
    ):
        config[FIELD_VISIBILITY_MAP] = {
            "Moritz Language Reactor": ["Lemma", "Cloze", "Synonyms", "Japanese Notes"]
        }
    if FIELD_VISIBILITY_DISABLED not in config or not isinstance(
        config.get(FIELD_VISIBILITY_DISABLED), list
    ):
        config[FIELD_VISIBILITY_DISABLED] = []
    return config


def save_addon_config(config: dict[str, str]) -> None:
    mw.addonManager.writeConfig(ADDON_NAME, config)


def chatgpt_required_fields(config: dict[str, str]) -> dict[str, str]:
    return {
        "lemma": str(config.get(CHATGPT_CONFIG_LEMMA_FIELD, "Lemma")),
        "subtitle": str(config.get(CHATGPT_CONFIG_SUBTITLE_FIELD, "Subtitle")),
        "question": str(config.get(CHATGPT_CONFIG_QUESTION_FIELD, "Question")),
        "grammar": str(config.get(CHATGPT_CONFIG_GRAMMAR_FIELD, "Grammar")),
    }


def get_field_visibility_map(config: dict[str, str]) -> dict[str, list[str]]:
    raw = config.get(FIELD_VISIBILITY_MAP)
    if isinstance(raw, dict):
        return {str(k): [str(vv) for vv in v] for k, v in raw.items() if isinstance(v, list)}
    return {}


def get_field_visibility_disabled(config: dict[str, str]) -> list[str]:
    raw = config.get(FIELD_VISIBILITY_DISABLED)
    if isinstance(raw, list):
        return [str(v) for v in raw]
    return []
