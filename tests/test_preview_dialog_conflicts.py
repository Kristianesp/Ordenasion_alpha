import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from src.gui.preview_dialog import PreviewDialog


def _app():
    app = QApplication.instance()
    return app or QApplication([])


def test_preview_dialog_exposes_conflict_policy_and_resolves_names(tmp_path):
    _app()
    source = tmp_path / "source"
    source.mkdir()
    category_dir = source / "IMAGENES"
    category_dir.mkdir()
    existing = category_dir / "photo.png"
    existing.write_text("old", encoding="utf-8")

    file_path = source / "photo.png"
    file_path.write_text("new", encoding="utf-8")

    dialog = PreviewDialog(
        folder_movements=[],
        file_movements=[{"file": file_path, "category": "IMAGENES", "size": 3}],
        folder_path=str(source),
        organize_by_date=False,
        check_duplicates=False,
    )

    assert dialog.preview_rows[0]["status"] == "Se renombrará a photo (1).png"
    assert Path(dialog.preview_rows[0]["destination_path"]).name == "photo (1).png"

    dialog.conflict_policy_combo.setCurrentIndex(1)
    assert dialog.get_conflict_policy() == "overwrite"
    assert dialog.preview_rows[0]["status"] == "Se sobrescribirá el archivo existente"


def test_preview_dialog_enables_confirm_button_when_checkbox_is_checked(tmp_path):
    _app()
    source = tmp_path / "source"
    source.mkdir()

    file_path = source / "photo.png"
    file_path.write_text("new", encoding="utf-8")

    dialog = PreviewDialog(
        folder_movements=[],
        file_movements=[{"file": file_path, "category": "IMAGENES", "size": 3}],
        folder_path=str(source),
        organize_by_date=False,
        check_duplicates=False,
    )

    assert dialog.confirm_btn.isEnabled() is False
    dialog.confirm_checkbox.setChecked(True)
    assert dialog.confirm_btn.isEnabled() is True
