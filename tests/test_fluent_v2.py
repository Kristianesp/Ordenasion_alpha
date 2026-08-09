import os
import shutil
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from src.core.organization_profiles import ProfileManager
from src.gui.filter_bar import FilterBar
from src.gui.v2.pages.home_page import HomePage
from src.gui.v2.theme import apply_fluent_theme
from src.utils.app_config import AppConfig


APP = None


def _application():
    global APP
    application = QApplication.instance()
    APP = application or QApplication([])
    return APP


def _temporary_directory() -> Path:
    return Path(tempfile.mkdtemp(prefix="ordenasion-fluent-"))


def test_fluent_theme_modes_are_persisted():
    _application()
    temp_dir = _temporary_directory()
    config = AppConfig(str(temp_dir / "config.json"))

    try:
        assert config.get_theme_mode() == "system"
        assert config.set_theme_mode("dark")
        assert config.set_interface_density("compact")
        assert config.set_accent_color("#123456")

        assert config.get_theme_mode() == "dark"
        assert config.get_interface_density() == "compact"
        assert config.get_accent_color() == "#123456"
        assert apply_fluent_theme(config).accent == "#123456"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_home_page_exposes_primary_actions():
    _application()
    temp_dir = _temporary_directory()
    try:
        config = AppConfig(str(temp_dir / "config.json"))
        profiles = ProfileManager(str(temp_dir / "profiles.json"))
        page = HomePage(config, profiles)
        received_paths = []
        page.analyze_requested.connect(received_paths.append)

        page.path_input.setText(str(temp_dir))
        page._analyze()

        assert received_paths == [str(temp_dir)]
        assert page.recent_metric.value_label.text() == "0"
        assert page.profile_metric.value_label.text() == "3"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_filter_bar_keeps_legacy_signal_contract():
    _application()
    bar = FilterBar(["DOCUMENTOS", "MUSICA"])
    filters = []
    bar.filter_changed.connect(lambda text, category: filters.append((text, category)))

    bar.search_input.setText("informe")
    bar.category_filter.setCurrentText("DOCUMENTOS")
    bar._emit_filter()

    assert filters[-1] == ("informe", "DOCUMENTOS")
    assert bar.category_filter.count() == 3
