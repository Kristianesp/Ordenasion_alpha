"""Página Organizar durante la migración a Fluent."""

from PyQt6.QtWidgets import QWidget

from src.gui.drop_zone import DropZone
from src.gui.v2.pages.legacy_page import LegacyPage
from src.utils.app_config import AppConfig


class OrganizePage(LegacyPage):
    """Mantiene el flujo actual de análisis y organización."""

    def __init__(
        self,
        legacy_widget: QWidget,
        config: AppConfig,
        controller=None,
        parent=None,
    ):
        super().__init__(
            "Organizar",
            "Analiza, revisa y organiza tus archivos con control antes de moverlos.",
            legacy_widget,
            config,
            parent,
        )
        self.drop_zone = DropZone()
        if controller is not None:
            self.drop_zone.folder_dropped.connect(
                lambda path: controller.folder_input.setText(path)
            )
        self.add_top_widget(self.drop_zone)
