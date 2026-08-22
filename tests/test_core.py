from pathlib import Path

from dry4python.core import find_duplicates


def test_cross_file_duplicate_is_found(tmp_path: Path) -> None:
    first = tmp_path / ("a_" + 'sample.py')
    second = tmp_path / ("b_" + 'sample.py')
    first.write_text('def choose(a: bool, b: bool) -> int:\n    if a and b:\n        return 1\n    return 0\n', encoding="utf-8")
    second.write_text('def decide(a: bool, b: bool) -> int:\n    if a and b:\n        return 1\n    return 0\n', encoding="utf-8")
    duplicates = find_duplicates(tmp_path, min_tokens=8)
    assert duplicates


def test_non_overlapping_same_file_duplicate_is_found(tmp_path: Path) -> None:
    path = tmp_path / 'sample.py'
    path.write_text('def choose(a: bool, b: bool) -> int:\n    if a and b:\n        return 1\n    return 0\n' + "\n" + 'def decide(a: bool, b: bool) -> int:\n    if a and b:\n        return 1\n    return 0\n', encoding="utf-8")
    duplicates = find_duplicates(tmp_path, min_tokens=8)
    assert any(item.locations[0].file == item.locations[1].file for item in duplicates)
