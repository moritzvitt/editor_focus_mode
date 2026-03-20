"""ChatGPT helper prompt building and parsing."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable


DEFAULT_PROMPT_TEMPLATE = (
    "You explain Japanese sentences for an advanced learner in English!\n"
    "Be very concise! (Maximum of 6 lines!)\n\n"
    "OUTPUT STRUCTURE\n\n"
    "[List difficult words in the sentence with furigana and short meaning.]\n"
    "Example format:\n\n"
    "戦闘機[せんとうき] — fighter jet\n"
    "願[ねが]い — Wish, please\n\n"
    "———**Grammar, Structure**\n"
    "Explain only the structure and grammar directly related to {lemma} in {subtitle}."
)

DEFAULT_BATCH_INSTRUCTIONS = (
    "For each card:\n"
    "- Keep the identifier EXACTLY as given\n"
    "- Repeat the identifier before each answer\n"
    "- Do NOT merge cards"
)

NOTE_ID_PREFIX = "NOTE_ID_"
NOTE_ID_PATTERN = re.compile(r"===NOTE_ID_(\d+)===")

_PROMPTS_CACHE: dict[str, str] | None = None


def _parse_simple_yaml(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    lines = text.splitlines()
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if not line.strip() or line.lstrip().startswith("#"):
            idx += 1
            continue
        if ":" not in line:
            idx += 1
            continue
        key, rest = line.split(":", 1)
        key = key.strip()
        rest = rest.strip()
        if rest.startswith("|"):
            block: list[str] = []
            idx += 1
            while idx < len(lines):
                next_line = lines[idx]
                if next_line.startswith("  ") or next_line.startswith("\t"):
                    block.append(next_line.lstrip("\t").lstrip(" "))
                    idx += 1
                    continue
                if next_line.strip() == "":
                    block.append("")
                    idx += 1
                    continue
                break
            result[key] = "\n".join(block).rstrip()
            continue
        if rest:
            result[key] = rest
        idx += 1
    return result


def _load_prompts() -> dict[str, str]:
    global _PROMPTS_CACHE
    if _PROMPTS_CACHE is not None:
        return _PROMPTS_CACHE
    prompt_path = Path(__file__).with_name("prompts.yaml")
    if not prompt_path.exists():
        _PROMPTS_CACHE = {}
        return _PROMPTS_CACHE
    content = prompt_path.read_text(encoding="utf-8")
    data: dict[str, str] = {}
    try:
        import yaml  # type: ignore

        parsed = yaml.safe_load(content) or {}
        if isinstance(parsed, dict):
            data = {str(k): str(v) for k, v in parsed.items()}
    except Exception:
        data = _parse_simple_yaml(content)
    _PROMPTS_CACHE = data
    return _PROMPTS_CACHE


def _get_prompt_template() -> str:
    prompts = _load_prompts()
    return prompts.get("prompt_template", DEFAULT_PROMPT_TEMPLATE)


def _get_batch_instructions() -> str:
    prompts = _load_prompts()
    return prompts.get("batch_instructions", DEFAULT_BATCH_INSTRUCTIONS)


def _normalize_text(value: str | None) -> str:
    return (value or "").strip()


def build_single_prompt(lemma: str, subtitle: str, question: str | None) -> str:
    prompt = _get_prompt_template().format(
        lemma=_normalize_text(lemma), subtitle=_normalize_text(subtitle)
    )
    q = _normalize_text(question)
    if q:
        prompt = f"{prompt}\nIf a question exists, answer it explicitly: {q}"
    return prompt


def build_prompt_for_note(
    note,
    *,
    lemma_field: str,
    subtitle_field: str,
    question_field: str,
) -> str:
    lemma = note[lemma_field]
    subtitle = note[subtitle_field]
    if question_field:
        question = (
            note.get(question_field) if hasattr(note, "get") else note[question_field]
        )
    else:
        question = ""
    return build_single_prompt(lemma, subtitle, question)


def build_batch_prompt(
    notes: Iterable,
    *,
    lemma_field: str,
    subtitle_field: str,
    question_field: str,
) -> tuple[str, list[int]]:
    note_ids: list[int] = []
    chunks: list[str] = []
    for note in notes:
        nid = int(note.id)
        note_ids.append(nid)
        prompt = build_prompt_for_note(
            note,
            lemma_field=lemma_field,
            subtitle_field=subtitle_field,
            question_field=question_field,
        )
        chunks.append(f"===NOTE_ID_{nid}===\n{prompt}")
    body = "\n\n".join(chunks)
    return f"{_get_batch_instructions()}\n\n{body}", note_ids


def parse_batch_response(text: str, note_ids: Iterable[int]) -> dict[int, str]:
    parts = re.split(NOTE_ID_PATTERN, text or "")
    if len(parts) < 3:
        raise ValueError("No note identifiers found in response.")
    mapping: dict[int, str] = {}
    for idx in range(1, len(parts), 2):
        try:
            nid = int(parts[idx])
        except ValueError:
            continue
        chunk = (parts[idx + 1] or "").strip()
        if not chunk:
            continue
        mapping[nid] = chunk
    expected = {int(nid) for nid in note_ids}
    missing = expected - set(mapping.keys())
    extra = set(mapping.keys()) - expected
    if missing or extra:
        detail = []
        if missing:
            detail.append(f"missing identifiers: {sorted(missing)}")
        if extra:
            detail.append(f"unexpected identifiers: {sorted(extra)}")
        raise ValueError("; ".join(detail))
    return mapping
