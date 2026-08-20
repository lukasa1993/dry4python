from __future__ import annotations

import hashlib
import io
import keyword
import os
import tokenize
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

EXCLUDED_DIRS = {".git", ".hg", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox", ".venv", "build", "dist", "node_modules", "target", "venv"}


@dataclass(frozen=True)
class Token:
    value: str
    line: int


@dataclass(frozen=True)
class Location:
    file: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class Duplicate:
    token_count: int
    locations: tuple[Location, ...]

    def to_dict(self) -> dict[str, object]:
        return {"token_count": self.token_count, "locations": [asdict(location) for location in self.locations]}


def discover_files(root: Path, filters: Sequence[str] = ()) -> list[Path]:
    files: list[Path] = []
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDED_DIRS)
        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue
            path = Path(directory, filename)
            relative = path.relative_to(root).as_posix()
            if filters and not any(fragment in relative for fragment in filters):
                continue
            files.append(path)
    return files


def tokenize_file(path: Path) -> list[Token]:
    text = path.read_text(encoding="utf-8")
    out: list[Token] = []
    for value in tokenize.generate_tokens(io.StringIO(text).readline):
        if value.type in {tokenize.ENCODING, tokenize.ENDMARKER, tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE, tokenize.NL, tokenize.COMMENT}:
            continue
        if value.type == tokenize.NAME:
            normalized = value.string if keyword.iskeyword(value.string) else "ID"
        elif value.type == tokenize.NUMBER:
            normalized = "NUM"
        elif value.type == tokenize.STRING:
            normalized = "STR"
        else:
            normalized = value.string
        out.append(Token(normalized, value.start[0]))
    return out


def find_duplicates(root: Path, min_tokens: int = 30, filters: Sequence[str] = (), max_groups: int = 50) -> list[Duplicate]:
    if min_tokens < 4:
        raise ValueError("min_tokens must be at least 4")
    groups: dict[str, list[Location]] = {}
    for path in discover_files(root, filters):
        tokens = tokenize_file(path)
        for start in range(0, max(0, len(tokens) - min_tokens + 1)):
            window = tokens[start : start + min_tokens]
            digest = hashlib.sha256("\0".join(token.value for token in window).encode()).hexdigest()
            groups.setdefault(digest, []).append(Location(path.as_posix(), window[0].line, window[-1].line))

    duplicates: list[Duplicate] = []
    for locations in groups.values():
        unique = tuple(dict.fromkeys(locations))
        if len(unique) < 2:
            continue
        files = {location.file for location in unique}
        if len(files) == 1:
            ordered = sorted(unique, key=lambda item: item.start_line)
            if all(next_.start_line <= current.end_line for current, next_ in zip(ordered, ordered[1:])):
                continue
        duplicates.append(Duplicate(min_tokens, unique))
    duplicates.sort(key=lambda item: (-len(item.locations), item.locations[0].file, item.locations[0].start_line))

    # Suppress the many adjacent windows that describe the same duplicate block.
    selected: list[Duplicate] = []
    seen_pairs: set[tuple[str, int, str, int]] = set()
    for duplicate in duplicates:
        first, second = duplicate.locations[:2]
        pair = (first.file, first.start_line, second.file, second.start_line)
        near_existing = any(
            pair[0] == old[0]
            and pair[2] == old[2]
            and abs(pair[1] - old[1]) <= 2
            and abs(pair[3] - old[3]) <= 2
            for old in seen_pairs
        )
        if near_existing:
            continue
        seen_pairs.add(pair)
        selected.append(duplicate)
        if len(selected) >= max_groups:
            break
    return selected
