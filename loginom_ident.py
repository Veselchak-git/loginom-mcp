"""Loginom column identifier generation (Name / InputColumnInfoName).

Loginom requires Name to be a valid identifier: ``[A-Za-z_][A-Za-z0-9_]*``.
Cyrillic headers become Latin via phonetic transliteration; DisplayName keeps
the original label. Matching observed Loginom 7.4 import of ``продажи.txt``.
"""
from __future__ import annotations

import re

# Lowercase Cyrillic → Latin (multi-char for digraphs). Soft/hard signs drop.
_CYR: dict[str, str] = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}


def _is_valid_ident(name: str) -> bool:
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name))


def _transliterate_word(word: str) -> str:
    """Transliterate one alphabetic word (no separators)."""
    low = word.lower()
    # Digraph before singles: ый → iy (Первый → Perviy, not Pervyy)
    low = low.replace("ый", "iy")
    out: list[str] = []
    for ch in low:
        if ch in _CYR:
            out.append(_CYR[ch])
        elif "a" <= ch <= "z" or "0" <= ch <= "9":
            out.append(ch)
        # ignore unexpected
    return "".join(out)


def _cap_word(latin: str, *, upper_first: bool) -> str:
    if not latin:
        return ""
    if not upper_first:
        return latin
    # ю at word start → YU… (Юрлицо → YUrlitso)
    if latin.startswith("yu"):
        return "YU" + latin[2:]
    return latin[0].upper() + latin[1:]


def loginom_ident(label: str) -> str:
    """Convert a column label to a Loginom ``Name`` identifier.

    Already-valid ASCII identifiers (e.g. ``Client_ID``) are returned unchanged.

    Capitalization rules (from Loginom 7.4):
    - first word: Capitalized
    - word after spaces: lowercase
    - word after other punctuation: Capitalized
    - each non-alphanumeric char becomes one ``_``
    """
    if not label:
        raise ValueError("empty column label")
    if _is_valid_ident(label):
        return label

    parts: list[str] = []
    i = 0
    n = len(label)
    first_word = True
    # After space-only separators → next word lower; after other seps → Capitalized
    next_upper = True

    while i < n:
        ch = label[i]
        if ch.isalpha() or ("0" <= ch <= "9") or ("\u0400" <= ch <= "\u04ff"):
            j = i + 1
            while j < n and (
                label[j].isalpha()
                or ("0" <= label[j] <= "9")
                or ("\u0400" <= label[j] <= "\u04ff")
            ):
                j += 1
            word = _transliterate_word(label[i:j])
            if word:
                if first_word:
                    parts.append(_cap_word(word, upper_first=True))
                    first_word = False
                else:
                    parts.append(_cap_word(word, upper_first=next_upper))
            i = j
            next_upper = False  # until we see separators
        else:
            # separator run
            only_spaces = True
            while i < n and not (
                label[i].isalpha()
                or ("0" <= label[i] <= "9")
                or ("\u0400" <= label[i] <= "\u04ff")
            ):
                if label[i] != " " and label[i] != "\t":
                    only_spaces = False
                parts.append("_")
                i += 1
            next_upper = not only_spaces

    raw = "".join(parts)
    if not raw:
        raw = "Field"
    if raw[0].isdigit():
        raw = "F_" + raw
    return raw


def resolve_column_names(label: str) -> tuple[str, str | None]:
    """Return ``(Name, DisplayName)``.

    DisplayName is ``None`` when the label is already a bare identifier
    (Loginom then omits DisplayName on import ColumnDefs).
    """
    if _is_valid_ident(label):
        return label, None
    return loginom_ident(label), label
