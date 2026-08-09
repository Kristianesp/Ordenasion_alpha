"""Páginas adaptadoras para las herramientas especializadas."""

from PyQt6.QtWidgets import QWidget

from src.gui.v2.pages.legacy_page import LegacyPage
from src.utils.app_config import AppConfig


class DisksPage(LegacyPage):
    def __init__(self, legacy_widget: QWidget, config: AppConfig, parent=None):
        super().__init__(
            "Discos",
            "Supervisa espacio, temperatura y salud SMART de tus unidades.",
            legacy_widget,
            config,
            parent,
        )


class MusicPage(LegacyPage):
    def __init__(self, legacy_widget: QWidget, config: AppConfig, parent=None):
        super().__init__(
            "Música",
            "Organiza tu biblioteca, compara duplicados y mejora metadatos.",
            legacy_widget,
            config,
            parent,
        )


class DuplicatesPage(LegacyPage):
    def __init__(self, legacy_widget: QWidget, config: AppConfig, parent=None):
        super().__init__(
            "Duplicados",
            "Recupera espacio con análisis rápido, híbrido o profundo.",
            legacy_widget,
            config,
            parent,
        )
