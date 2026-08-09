"""Configuración visual centralizada para la interfaz Fluent."""

from dataclasses import dataclass

from PyQt6.QtGui import QColor, QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication, QWidget
from qfluentwidgets import Theme, isDarkTheme, setTheme, setThemeColor

from src.utils.app_config import AppConfig


@dataclass(frozen=True)
class FluentTokens:
    canvas: str
    surface: str
    surface_alt: str
    text_primary: str
    text_secondary: str
    stroke: str
    accent: str
    success: str
    warning: str
    danger: str


LIGHT_TOKENS = FluentTokens(
    canvas="#F3F3F3",
    surface="#FFFFFF",
    surface_alt="#F9F9F9",
    text_primary="#1B1B1B",
    text_secondary="#5D5D5D",
    stroke="#E1E1E1",
    accent="#0078D4",
    success="#0F7B0F",
    warning="#9D5D00",
    danger="#C42B1C",
)

DARK_TOKENS = FluentTokens(
    canvas="#202020",
    surface="#2B2B2B",
    surface_alt="#323232",
    text_primary="#FFFFFF",
    text_secondary="#C7C7C7",
    stroke="#414141",
    accent="#60CDFF",
    success="#6CCB5F",
    warning="#FCE100",
    danger="#FF99A4",
)


def _to_theme(mode: str) -> Theme:
    normalized = mode.lower()
    if normalized == "light":
        return Theme.LIGHT
    if normalized == "dark":
        return Theme.DARK
    return Theme.AUTO


def current_tokens(accent: str | None = None) -> FluentTokens:
    """Devuelve tokens resueltos para el tema efectivo."""
    base = DARK_TOKENS if isDarkTheme() else LIGHT_TOKENS
    if not accent:
        return base
    return FluentTokens(
        canvas=base.canvas,
        surface=base.surface,
        surface_alt=base.surface_alt,
        text_primary=base.text_primary,
        text_secondary=base.text_secondary,
        stroke=base.stroke,
        accent=accent,
        success=base.success,
        warning=base.warning,
        danger=base.danger,
    )


def preferred_font_family() -> str:
    """Devuelve Segoe y usa una fuente disponible como fallback."""
    available = set(QFontDatabase.families())
    for family in ("Segoe UI Variable", "Segoe UI", "Arial"):
        if family in available:
            return family
    return QApplication.font().family() or "Sans Serif"


def apply_fluent_theme(config: AppConfig) -> FluentTokens:
    """Aplica tema, acento y tipografía una sola vez a la aplicación."""
    mode = config.get_theme_mode()
    accent = config.get_accent_color()
    setTheme(_to_theme(mode))
    app = QApplication.instance()
    if app is not None:
        # FileOrganizerGUI aplica un QSS global heredado durante su arranque.
        # La V2 debe usar la paleta Fluent y estilos locales, no ese QSS.
        app.setStyleSheet("")
    if QColor(accent).isValid():
        setThemeColor(accent)

    if app is not None:
        font = QFont(preferred_font_family(), max(9, config.get_font_size()))
        app.setFont(font)
    return current_tokens(accent)


def legacy_surface_stylesheet(config: AppConfig) -> str:
    """QSS acotado para controles Qt heredados dentro de páginas V2."""
    tokens = current_tokens(config.get_accent_color())
    compact = config.get_interface_density() == "compact"
    control_height = 28 if compact else 34
    row_height = 30 if compact else 38
    return f"""
        QWidget#legacySurface {{
            background: transparent;
            color: {tokens.text_primary};
        }}
        QWidget#legacySurface QGroupBox {{
            background: {tokens.surface};
            border: 1px solid {tokens.stroke};
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 12px;
            font-weight: 600;
        }}
        QWidget#legacySurface QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 4px;
            color: {tokens.text_primary};
        }}
        QWidget#legacySurface QLineEdit,
        QWidget#legacySurface QComboBox,
        QWidget#legacySurface QSpinBox {{
            min-height: {control_height}px;
            background: {tokens.surface};
            color: {tokens.text_primary};
            border: 1px solid {tokens.stroke};
            border-radius: 5px;
            padding: 0 9px;
        }}
        QWidget#legacySurface QLineEdit:focus,
        QWidget#legacySurface QComboBox:focus,
        QWidget#legacySurface QSpinBox:focus {{
            border-bottom: 2px solid {tokens.accent};
        }}
        QWidget#legacySurface QPushButton {{
            min-height: {control_height}px;
            background: {tokens.surface_alt};
            color: {tokens.text_primary};
            border: 1px solid {tokens.stroke};
            border-radius: 5px;
            padding: 0 12px;
        }}
        QWidget#legacySurface QPushButton:hover {{
            background: {tokens.surface};
            border-color: {tokens.accent};
        }}
        QWidget#legacySurface QPushButton#organize_button,
        QWidget#legacySurface QPushButton#analyze_button {{
            color: white;
            background: {tokens.accent};
            border-color: {tokens.accent};
            font-weight: 600;
        }}
        QWidget#legacySurface QTableView,
        QWidget#legacySurface QTableWidget,
        QWidget#legacySurface QListWidget,
        QWidget#legacySurface QTextEdit {{
            background: {tokens.surface};
            alternate-background-color: {tokens.surface_alt};
            color: {tokens.text_primary};
            border: 1px solid {tokens.stroke};
            border-radius: 8px;
            gridline-color: {tokens.stroke};
            selection-background-color: {tokens.accent};
        }}
        QWidget#legacySurface QHeaderView::section {{
            min-height: {row_height}px;
            background: {tokens.surface_alt};
            color: {tokens.text_primary};
            border: none;
            border-bottom: 1px solid {tokens.stroke};
            padding: 0 8px;
            font-weight: 600;
        }}
        QWidget#legacySurface QProgressBar {{
            min-height: 5px;
            max-height: 5px;
            border: none;
            border-radius: 2px;
            background: {tokens.stroke};
        }}
        QWidget#legacySurface QProgressBar::chunk {{
            border-radius: 2px;
            background: {tokens.accent};
        }}
    """


def apply_legacy_surface_style(widget: QWidget, config: AppConfig) -> None:
    widget.setObjectName("legacySurface")
    widget.setStyleSheet(legacy_surface_stylesheet(config))
