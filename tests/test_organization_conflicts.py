from pathlib import Path

from src.core.organization_conflicts import (
    CONFLICT_POLICY_OVERWRITE,
    CONFLICT_POLICY_RENAME,
    CONFLICT_POLICY_SKIP,
    build_numbered_name,
    find_available_name,
    resolve_destination,
)


def test_find_available_name_adds_numbered_suffix(tmp_path):
    target = tmp_path / "file.txt"
    target.write_text("a", encoding="utf-8")

    candidate = find_available_name(target)

    assert candidate.name == "file (1).txt"


def test_resolve_destination_supports_rename_skip_and_overwrite(tmp_path):
    target = tmp_path / "file.txt"
    target.write_text("a", encoding="utf-8")

    rename = resolve_destination(target, CONFLICT_POLICY_RENAME, is_folder=False)
    skip = resolve_destination(target, CONFLICT_POLICY_SKIP, is_folder=False)
    overwrite = resolve_destination(target, CONFLICT_POLICY_OVERWRITE, is_folder=False)

    assert rename.action == "rename"
    assert rename.destination.name == "file (1).txt"
    assert skip.action == "skip"
    assert overwrite.action == "overwrite"
