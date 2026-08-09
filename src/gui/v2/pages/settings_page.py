"""Configuración visual y accesos a la configuración avanzada."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ComboBox,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    PrimaryPushButton,
    ScrollArea,
    SubtitleLabel,
)

from src.gui.v2.components import PageHeader
from src.gui.v2.theme import apply_fluent_theme
from src.utils.app_config import AppConfig


class SettingsPage(ScrollArea):
    """Ajustes de apariencia y puente hacia la configuración existente."""

    theme_changed = pyqtSignal()
    advanced_settings_requested = pyqtSignal()

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setObjectName("settingsPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setWidgetResizable(True)
        self.setFrameShape(ScrollArea.Shape.NoFrame)
        self.enableTransparentBackground()

        self.content = QWidget()
        self.content.setObjectName("settingsContent")
        self.setWidget(self.content)
        self._build_ui()
        self._load_values()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(18)
        layout.addWidget(
            PageHeader(
                "Configuración",
                "Personaliza la apariencia y accede a todas las opciones de Ordenasion.",
            )
        )

        appearance = CardWidget()
        appearance_layout = QVBoxLayout(appearance)
        appearance_layout.setContentsMargins(20, 18, 20, 18)
        appearance_layout.setSpacing(10)
        appearance_layout.addWidget(SubtitleLabel("Apariencia"))
        appearance_layout.addWidget(
            BodyLabel("Elige el modo visual, el acento y la densidad de la interfaz.")
        )

        self.theme_mode = ComboBox()
        self.theme_mode.setAccessibleName("Modo de tema")
        for label, mode in (
            ("Sistema", "system"),
            ("Claro", "light"),
            ("Oscuro", "dark"),
        ):
            self.theme_mode.addItem(label)
            self.theme_mode.setItemData(self.theme_mode.count() - 1, mode)
        appearance_layout.addWidget(self.theme_mode)

        self.density = ComboBox()
        self.density.setAccessibleName("Densidad de interfaz")
        for label, density in (
            ("Cómoda", "comfortable"),
            ("Compacta", "compact"),
        ):
            self.density.addItem(label)
            self.density.setItemData(self.density.count() - 1, density)
        appearance_layout.addWidget(self.density)

        self.accent = LineEdit()
        self.accent.setAccessibleName("Color de acento")
        self.accent.setPlaceholderText("Color de acento, por ejemplo #0078D4")
        appearance_layout.addWidget(self.accent)

        self.apply_button = PrimaryPushButton(FluentIcon.PALETTE, "Aplicar apariencia")
        self.apply_button.setAccessibleName("Aplicar apariencia")
        self.apply_button.clicked.connect(self.apply_appearance)
        appearance_layout.addWidget(self.apply_button)
        layout.addWidget(appearance)

        advanced = CardWidget()
        advanced_layout = QVBoxLayout(advanced)
        advanced_layout.setContentsMargins(20, 18, 20, 18)
        advanced_layout.setSpacing(10)
        advanced_layout.addWidget(SubtitleLabel("Organización y audio"))
        advanced_layout.addWidget(
            BodyLabel(
                "Las opciones avanzadas siguen disponibles en el panel original mientras terminamos su migración visual."
            )
        )
        advanced_button = PrimaryPushButton(
            FluentIcon.SETTING,
            "Abrir configuración avanzada",
        )
        advanced_button.clicked.connect(self.advanced_settings_requested.emit)
        advanced_layout.addWidget(advanced_button)
        layout.addWidget(advanced)
        layout.addStretch()

    def _load_values(self) -> None:
        mode = self.config.get_theme_mode()
        density = self.config.get_interface_density()
        self.theme_mode.setCurrentIndex(
            max(0, self.theme_mode.findData(mode))
        )
        self.density.setCurrentIndex(max(0, self.density.findData(density)))
        self.accent.setText(self.config.get_accent_color())

    def apply_appearance(self) -> None:
        mode = self.theme_mode.currentData()
        density = self.density.currentData()
        self.config.set_theme_mode(mode)
        self.config.set_interface_density(density)
        self.config.set_accent_color(self.accent.text().strip() or "#0078D4")
        apply_fluent_theme(self.config)
        InfoBar.success(
            "Apariencia actualizada",
            "El tema, acento y densidad se aplicaron correctamente.",
            position=InfoBarPosition.TOP_RIGHT,
            parent=self,
        )
        self.theme_changed.emit()
