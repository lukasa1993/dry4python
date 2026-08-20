from pathlib import Path

from dry4python.core import find_duplicates, tokenize_file


def test_normalizes_identifiers_and_literals(tmp_path: Path) -> None:
    path = tmp_path / "sample.py"
    path.write_text("answer = 42\n", encoding="utf-8")
    assert [token.value for token in tokenize_file(path)] == ["ID", "=", "NUM"]


def test_finds_duplicate_blocks(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("def a(x):\n    if x:\n        return x + 1\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("def b(y):\n    if y:\n        return y + 2\n", encoding="utf-8")
    duplicates = find_duplicates(tmp_path, min_tokens=8)
    assert duplicates
    assert len(duplicates[0].locations) >= 2
