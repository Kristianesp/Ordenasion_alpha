"""Configuración visual centralizada para la interfaz Fluent."""

from dataclasses import dataclass

from PyQt6.QtGui import QColor, QFont, QFontDatabase, QPalette
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
    canvas="#EEF5FB",
    surface="#FFFFFF",
    surface_alt="#E5F0FA",
    text_primary="#17202A",
    text_secondary="#4D6072",
    stroke="#C9D9E8",
    accent="#0F6CBD",
    success="#0F7B0F",
    warning="#9D5D00",
    danger="#C42B1C",
)

DARK_TOKENS = FluentTokens(
    canvas="#101827",
    surface="#182337",
    surface_alt="#22324A",
    text_primary="#F5F9FF",
    text_secondary="#B9C8D9",
    stroke="#3A4D66",
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


def current_tokens(
    accent: str | None = None,
    mode: str | None = None,
) -> FluentTokens:
    """Devuelve tokens resueltos para el tema efectivo."""
    normalized_mode = (mode or "").lower()
    use_dark = (
        normalized_mode == "dark"
        or (normalized_mode not in {"light", "dark"} and isDarkTheme())
    )
    base = DARK_TOKENS if use_dark else LIGHT_TOKENS
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
    return current_tokens(accent, mode)


def apply_fluent_palette(widget: QWidget, config: AppConfig) -> None:
    """Fija la paleta de superficies para evitar fondos Acrylic neutros."""
    tokens = current_tokens(
        config.get_accent_color(),
        config.get_theme_mode(),
    )
    palette = widget.palette()
    for role, color in (
        (QPalette.ColorRole.Window, tokens.canvas),
        (QPalette.ColorRole.Base, tokens.surface),
        (QPalette.ColorRole.AlternateBase, tokens.surface_alt),
        (QPalette.ColorRole.Button, tokens.surface_alt),
        (QPalette.ColorRole.ButtonText, tokens.text_primary),
        (QPalette.ColorRole.Text, tokens.text_primary),
        (QPalette.ColorRole.WindowText, tokens.text_primary),
        (QPalette.ColorRole.Highlight, tokens.accent),
        (QPalette.ColorRole.HighlightedText, "#FFFFFF"),
        (QPalette.ColorRole.PlaceholderText, tokens.text_secondary),
    ):
        palette.setColor(role, QColor(color))
    widget.setPalette(palette)
    widget.setAutoFillBackground(True)


def fluent_window_stylesheet(config: AppConfig) -> str:
    """Estilos locales del shell V2, separados del QSS heredado."""
    tokens = current_tokens(
        config.get_accent_color(),
        config.get_theme_mode(),
    )
    return f"""
        QMainWindow#fluentAppWindow {{
            background: {tokens.canvas};
            background-color: {tokens.canvas};
            color: {tokens.text_primary};
        }}
        QMainWindow#fluentAppWindow > QWidget {{
            background-color: {tokens.canvas};
        }}
        QMainWindow#fluentAppWindow QScrollArea,
        QMainWindow#fluentAppWindow StackedWidget,
        QMainWindow#fluentAppWindow PopUpAniStackedWidget,
        QMainWindow#fluentAppWindow QWidget > StackedWidget,
        QMainWindow#fluentAppWindow QWidget#homePage,
        QMainWindow#fluentAppWindow QWidget#activityPage,
        QMainWindow#fluentAppWindow QWidget#settingsPage,
        QMainWindow#fluentAppWindow QWidget#legacyContent {{
            background: {tokens.canvas};
            background-color: {tokens.canvas};
            color: {tokens.text_primary};
            border: none;
        }}
        QMainWindow#fluentAppWindow StackedWidget > QWidget,
        QMainWindow#fluentAppWindow PopUpAniStackedWidget > QWidget {{
            background: {tokens.canvas};
            background-color: {tokens.canvas};
        }}
        QMainWindow#fluentAppWindow QScrollArea#homePage > QWidget,
        QMainWindow#fluentAppWindow QScrollArea#settingsPage > QWidget,
        QMainWindow#fluentAppWindow QScrollArea#activityPage > QWidget {{
            background: {tokens.canvas};
            background-color: {tokens.canvas};
        }}
        QMainWindow#fluentAppWindow QWidget#pageHeader {{
            background: {tokens.surface_alt};
            background-color: {tokens.surface_alt};
            border: 1px solid {tokens.stroke};
            border-radius: 12px;
        }}
        QMainWindow#fluentAppWindow QLabel,
        QMainWindow#fluentAppWindow BodyLabel,
        QMainWindow#fluentAppWindow CaptionLabel,
        QMainWindow#fluentAppWindow SubtitleLabel,
        QMainWindow#fluentAppWindow TitleLabel {{
            color: {tokens.text_primary};
        }}
        QMainWindow#fluentAppWindow CardWidget,
        QMainWindow#fluentAppWindow MetricCard,
        QMainWindow#fluentAppWindow FeatureCard {{
            background: {tokens.surface};
            background-color: {tokens.surface};
            border: 1px solid {tokens.stroke};
            border-radius: 12px;
        }}
        QMainWindow#fluentAppWindow MetricCard {{
            border-top: 3px solid {tokens.accent};
        }}
        QMainWindow#fluentAppWindow FeatureCard {{
            border-left: 3px solid {tokens.accent};
        }}
        QMainWindow#fluentAppWindow CardWidget:hover,
        QMainWindow#fluentAppWindow FeatureCard:hover {{
            background: {tokens.surface_alt};
            background-color: {tokens.surface_alt};
            border-color: {tokens.accent};
        }}
        QMainWindow#fluentAppWindow LineEdit,
        QMainWindow#fluentAppWindow ComboBox,
        QMainWindow#fluentAppWindow TextEdit,
        QMainWindow#fluentAppWindow SpinBox {{
            background: {tokens.surface};
            background-color: {tokens.surface};
            color: {tokens.text_primary};
            border: 1px solid {tokens.stroke};
            border-radius: 7px;
            selection-background-color: {tokens.accent};
            selection-color: white;
        }}
        QMainWindow#fluentAppWindow LineEdit:focus,
        QMainWindow#fluentAppWindow ComboBox:focus,
        QMainWindow#fluentAppWindow TextEdit:focus,
        QMainWindow#fluentAppWindow SpinBox:focus {{
            border: 2px solid {tokens.accent};
        }}
        QMainWindow#fluentAppWindow PushButton {{
            color: {tokens.text_primary};
            background: {tokens.surface_alt};
            background-color: {tokens.surface_alt};
            border: 1px solid {tokens.stroke};
            border-radius: 7px;
            padding: 5px 12px;
        }}
        QMainWindow#fluentAppWindow PushButton:hover {{
            background: {tokens.surface};
            background-color: {tokens.surface};
            border-color: {tokens.accent};
        }}
        QMainWindow#fluentAppWindow PrimaryPushButton {{
            color: white;
            background: {tokens.accent};
            background-color: {tokens.accent};
            border-color: {tokens.accent};
        }}
        QMainWindow#fluentAppWindow PrimaryPushButton:hover {{
            background: {tokens.accent};
            background-color: {tokens.accent};
        }}
        QMainWindow#fluentAppWindow NavigationInterface,
        QMainWindow#fluentAppWindow NavigationPanel {{
            background: {tokens.surface_alt};
            background-color: {tokens.surface_alt};
            border-right: 1px solid {tokens.stroke};
        }}
        QMainWindow#fluentAppWindow NavigationToolButton {{
            color: {tokens.text_secondary};
            border-radius: 8px;
        }}
        QMainWindow#fluentAppWindow NavigationToolButton:hover {{
            color: {tokens.text_primary};
            background: {tokens.surface_alt};
            background-color: {tokens.surface_alt};
        }}
        QMainWindow#fluentAppWindow NavigationToolButton:checked {{
            color: white;
            background: {tokens.accent};
            background-color: {tokens.accent};
        }}
        QMainWindow#fluentAppWindow QTableView,
        QMainWindow#fluentAppWindow QTableWidget,
        QMainWindow#fluentAppWindow QListWidget {{
            background: {tokens.surface};
            background-color: {tokens.surface};
            color: {tokens.text_primary};
            alternate-background-color: {tokens.surface_alt};
            border: 1px solid {tokens.stroke};
            gridline-color: {tokens.stroke};
            selection-background-color: {tokens.accent};
            selection-color: white;
        }}
        QMainWindow#fluentAppWindow QHeaderView::section {{
            background: {tokens.surface_alt};
            background-color: {tokens.surface_alt};
            color: {tokens.text_primary};
            border: none;
            border-bottom: 1px solid {tokens.stroke};
            padding: 6px 8px;
        }}
        QMainWindow#fluentAppWindow QProgressBar {{
            background: {tokens.surface_alt};
            background-color: {tokens.surface_alt};
            border: none;
            border-radius: 4px;
            text-align: center;
            color: {tokens.text_primary};
        }}
        QMainWindow#fluentAppWindow QProgressBar::chunk {{
            background: {tokens.accent};
            border-radius: 4px;
        }}
    """


def legacy_surface_stylesheet(config: AppConfig) -> str:
    """QSS acotado para controles Qt heredados dentro de páginas V2."""
    tokens = current_tokens(
        config.get_accent_color(),
        config.get_theme_mode(),
    )
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
