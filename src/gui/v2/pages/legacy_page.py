"""Adaptador visual para reutilizar páginas existentes durante la migración."""

from PyQt6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import ScrollArea

from src.gui.v2.components import PageHeader
from src.gui.v2.theme import apply_legacy_surface_style
from src.utils.app_config import AppConfig


class LegacyPage(ScrollArea):
    """Envuelve una página existente con el shell visual Fluent."""

    def __init__(
        self,
        title: str,
        subtitle: str,
        legacy_widget: QWidget,
        config: AppConfig,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName(f"legacy_{title.lower().replace(' ', '_')}")
        self.setWidgetResizable(True)
        self.setFrameShape(ScrollArea.Shape.NoFrame)
        self.enableTransparentBackground()
        self.legacy_widget = legacy_widget

        content = QWidget()
        self.content = content
        self.setWidget(content)
        layout = QVBoxLayout(content)
        self.content_layout = layout
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(18)
        layout.addWidget(PageHeader(title, subtitle))

        apply_legacy_surface_style(self.legacy_widget, config)
        layout.addWidget(self.legacy_widget, 1)

    def add_top_widget(self, widget: QWidget) -> None:
        """Añade un control V2 encima del contenido heredado."""
        self.content_layout.insertWidget(1, widget)

    def refresh_theme(self, config: AppConfig) -> None:
        """Actualiza la capa heredada cuando cambia el tema."""
        apply_legacy_surface_style(self.legacy_widget, config)
