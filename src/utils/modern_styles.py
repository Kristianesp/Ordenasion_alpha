#!/usr/bin/env python3
"""
Sistema de Estilos Modernos UI/UX 2026 - PyQt6 Compatible
Diseño profesional con colores modernos y controles elegantes.
"""

COLORS_2026 = {
    "primary": "#0F766E",
    "primary_hover": "#115E59",
    "secondary": "#0EA5E9",
    "success": "#16A34A",
    "warning": "#D97706",
    "error": "#DC2626",
    "background": "#F4F7F9",
    "surface": "#FFFFFF",
    "surface_variant": "#ECF3F6",
    "text_primary": "#14213D",
    "text_secondary": "#52606D",
    "text_disabled": "#9AA7B3",
    "border": "#D8E1E8",
    "accent": "#0EA5E9",
    "table_header": "#EEF4F7",
    "input_background": "#FFFFFF",
    "disabled": "#C7D2DA",
}


def get_theme_colors(theme_name: str = "modern_2026") -> dict:
    return COLORS_2026


def get_modern_css_styles(colors: dict, font_size: int = 12) -> str:
    if "primary" not in colors or colors.get("primary") == "#1976D2":
        colors = COLORS_2026.copy()

    c = colors.copy()
    c.setdefault("primary_hover", c.get("button_hover", c.get("secondary", "#4F46E5")))
    c.setdefault("button_hover", c["primary_hover"])
    c.setdefault("button_pressed", c.get("secondary", "#8B5CF6"))
    c.setdefault("surface_variant", c.get("surface_variant", "#F1F5F9"))
    c.setdefault(
        "input_background", c.get("input_background", c.get("surface", "#FFFFFF"))
    )
    c.setdefault("disabled", c.get("text_disabled", c.get("border", "#C7D2DA")))
    for key in (
        "text_primary",
        "text_secondary",
        "text_disabled",
        "background",
        "surface",
        "border",
        "secondary",
        "success",
        "warning",
        "error",
    ):
        c.setdefault(key, COLORS_2026.get(key, "#000000"))

    return f"""
    * {{ font-family: 'Segoe UI Variable', 'Segoe UI', sans-serif !important; font-size: {font_size}px !important; color: {c["text_primary"]} !important; }}
    QMainWindow {{ background-color: {c["background"]} !important; }}

    QGroupBox {{ background-color: {c["surface"]} !important; border: 1px solid {c["border"]} !important; border-radius: 10px !important; margin-top: 8px !important; padding: 12px 10px 10px 10px !important; font-weight: 600 !important; }}
    QGroupBox::title {{ subcontrol-origin: margin !important; subcontrol-position: top left !important; left: 10px !important; top: -1px !important; padding: 1px 8px !important; border-radius: 6px !important; color: {c["primary"]} !important; background-color: {c["surface_variant"]} !important; max-width: 80% !important; }}

    QPushButton {{ background-color: {c["primary"]} !important; color: white !important; border: none !important; border-radius: 7px !important; padding: 5px 12px !important; font-weight: 600 !important; min-height: 28px !important; }}
    QPushButton:hover {{ background-color: {c["primary_hover"]} !important; }}
    QPushButton:pressed {{ background-color: {c["secondary"]} !important; }}
    QPushButton:disabled {{ background-color: {c["border"]} !important; color: {c["text_disabled"]} !important; }}

    QPushButton[styleClass="ghost"] {{ background-color: {c["surface_variant"]} !important; color: {c["text_primary"]} !important; border: 1px solid {c["border"]} !important; }}
    QPushButton[styleClass="ghost"]:hover {{ background-color: {c["border"]} !important; }}
    QPushButton[styleClass="success"] {{ background-color: {c["success"]} !important; }}
    QPushButton[styleClass="danger"] {{ background-color: {c["error"]} !important; }}
    QPushButton[styleClass="icon"] {{ min-width: 28px !important; max-width: 28px !important; min-height: 28px !important; max-height: 28px !important; padding: 0 !important; border-radius: 6px !important; }}

    QToolButton {{ background-color: {c["surface_variant"]} !important; color: {c["text_primary"]} !important; border: 1px solid {c["border"]} !important; border-radius: 7px !important; padding: 4px 10px !important; min-height: 28px !important; }}
    QToolButton:hover {{ background-color: {c["border"]} !important; }}
    QToolButton::menu-indicator {{ image: none !important; width: 0px !important; }}

    #organize_button {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c["primary"]}, stop:1 {c["secondary"]}) !important; color: white !important; border: none !important; border-radius: 10px !important; padding: 8px 20px !important; font-weight: 700 !important; font-size: {font_size + 1}px !important; min-height: 34px !important; }}
    #organize_button:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c["primary_hover"]}, stop:1 #0284C7) !important; }}
    #organize_button:pressed {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0F5C55, stop:1 #0369A1) !important; }}

    QLineEdit {{ background-color: {c["input_background"]} !important; color: {c["text_primary"]} !important; border: 1px solid {c["border"]} !important; border-radius: 8px !important; padding: 5px 10px !important; min-height: 28px !important; selection-background-color: {c["primary"]} !important; selection-color: white !important; }}
    QLineEdit:focus {{ border-color: {c["primary"]} !important; }}
    QLineEdit:hover:!focus {{ border-color: {c["text_secondary"]} !important; }}

    QTextEdit {{ background-color: {c["input_background"]} !important; color: {c["text_primary"]} !important; border: 1px solid {c["border"]} !important; border-radius: 9px !important; padding: 5px !important; }}
    #log_text {{ background-color: {c["surface"]} !important; color: {c["text_secondary"]} !important; border: 1px solid {c["border"]} !important; border-radius: 8px !important; padding: 4px 6px !important; font-family: 'Consolas', monospace !important; font-size: {max(font_size - 1, 10)}px !important; }}

    QTableView {{ background-color: {c["surface"]} !important; color: {c["text_primary"]} !important; border: 1px solid {c["border"]} !important; border-radius: 10px !important; gridline-color: {c["border"]} !important; selection-background-color: {c["primary"]}20 !important; selection-color: {c["text_primary"]} !important; alternate-background-color: {c["surface_variant"]} !important; margin-top: 0 !important; }}
    QTableView::item {{ padding: 4px 6px !important; border-bottom: 1px solid {c["border"]}40 !important; }}
    QTableView::item:hover {{ background-color: {c["secondary"]}14 !important; }}
    QTableView::item:selected {{ background-color: {c["primary"]} !important; color: white !important; font-weight: 600 !important; }}

    QHeaderView::section {{ background-color: {c["table_header"]} !important; color: {c["text_secondary"]} !important; padding: 6px 8px !important; border: none !important; border-bottom: 1px solid {c["border"]} !important; font-weight: 600 !important; font-size: {max(font_size - 1, 10)}px !important; }}

    QTabWidget::pane {{ background-color: {c["surface"]} !important; border: 1px solid {c["border"]} !important; border-radius: 10px !important; }}
    QTabBar::tab {{ background-color: {c["surface_variant"]} !important; color: {c["text_secondary"]} !important; padding: 7px 14px !important; border-radius: 7px 7px 0 0 !important; font-weight: 500 !important; }}
    QTabBar::tab:selected {{ background-color: {c["primary"]} !important; color: white !important; font-weight: 600 !important; }}
    QTabBar::tab:hover:!selected {{ background-color: {c["secondary"]} !important; color: white !important; }}

    QCheckBox {{ color: {c["text_primary"]} !important; spacing: 5px !important; }}
    QCheckBox::indicator {{ width: 15px !important; height: 15px !important; border: 1px solid {c["border"]} !important; border-radius: 4px !important; background-color: {c["surface"]} !important; }}
    QCheckBox::indicator:checked {{ background-color: {c["success"]} !important; border-color: {c["success"]} !important; }}
    QCheckBox::indicator:hover {{ border-color: {c["primary"]} !important; }}

    QSpinBox {{ background-color: {c["surface"]} !important; color: {c["text_primary"]} !important; border: 1px solid {c["border"]} !important; border-radius: 8px !important; padding: 2px 12px 2px 6px !important; min-height: 28px !important; }}
    QSpinBox:focus {{ border-color: {c["primary"]} !important; }}
    QSpinBox::up-button {{ subcontrol-origin: border !important; subcontrol-position: top right !important; width: 14px !important; height: 10px !important; border: none !important; background-color: transparent !important; }}
    QSpinBox::down-button {{ subcontrol-origin: border !important; subcontrol-position: bottom right !important; width: 14px !important; height: 10px !important; border: none !important; background-color: transparent !important; }}

    QProgressBar {{ background-color: {c["surface"]} !important; border: 1px solid {c["border"]} !important; border-radius: 6px !important; text-align: center !important; color: {c["text_primary"]} !important; font-weight: 600 !important; height: 12px !important; }}
    QProgressBar::chunk {{ background-color: {c["primary"]} !important; border-radius: 4px !important; margin: 1px !important; }}

    QComboBox {{ background-color: {c["surface"]} !important; color: {c["text_primary"]} !important; border: 1px solid {c["border"]} !important; border-radius: 8px !important; padding: 4px 10px !important; min-height: 28px !important; min-width: 108px !important; }}
    QComboBox:hover {{ border-color: {c["primary"]} !important; }}
    QComboBox::drop-down {{ border: none !important; width: 24px !important; }}
    QComboBox QAbstractItemView {{ background-color: {c["surface"]} !important; color: {c["text_primary"]} !important; border: 1px solid {c["border"]} !important; border-radius: 8px !important; selection-background-color: {c["primary"]} !important; selection-color: white !important; outline: none !important; }}

    #main_title_label {{ color: {c["primary"]} !important; font-size: {font_size + 2}px !important; font-weight: 700 !important; padding: 4px 0 !important; }}
    #config_title_label {{ color: {c["text_primary"]} !important; font-size: {font_size + 5}px !important; font-weight: 700 !important; background-color: {c["surface"]} !important; border: 1px solid {c["border"]} !important; border-radius: 10px !important; padding: 10px 12px !important; }}
    #config_stats_label {{ color: {c["text_secondary"]} !important; background-color: {c["surface"]} !important; border: 1px solid {c["border"]} !important; border-radius: 8px !important; padding: 6px 10px !important; }}

    QFrame#duplicates_controls_frame, QFrame#duplicates_filters_frame, QFrame#duplicates_summary_frame, QFrame#duplicates_action_frame, QFrame#duplicates_results_frame {{ background-color: {c["surface"]} !important; border: 1px solid {c["border"]} !important; border-radius: 10px !important; }}
    QFrame#duplicates_filters_frame {{ background-color: {c["surface_variant"]} !important; }}
    QLabel#duplicates_path_label {{ background-color: {c["surface_variant"]} !important; color: {c["text_primary"]} !important; border: 1px solid {c["border"]} !important; border-radius: 8px !important; padding: 5px 10px !important; font-weight: 600 !important; }}
    QLabel#duplicates_method_info {{ background-color: transparent !important; color: {c["text_secondary"]} !important; padding: 2px 4px !important; font-size: {max(font_size - 1, 10)}px !important; }}
    QPushButton#scan_button {{ background-color: {c["secondary"]} !important; color: white !important; border: 1px solid {c["secondary"]} !important; border-radius: 8px !important; padding: 5px 14px !important; min-width: 140px !important; min-height: 30px !important; font-weight: 700 !important; }}
    QPushButton#scan_button:hover {{ background-color: #0284C7 !important; border-color: #0284C7 !important; }}
    QPushButton#scan_button:disabled {{ background-color: {c["disabled"]} !important; color: {c["text_secondary"]} !important; border-color: {c["disabled"]} !important; }}
    QPushButton#duplicates_preview_toggle {{ min-width: 132px !important; }}
    QToolButton#duplicates_more_button {{ min-width: 76px !important; }}
    QTextEdit#duplicates_preview_panel {{ background-color: {c["surface_variant"]} !important; border: 1px solid {c["border"]} !important; border-radius: 10px !important; padding: 8px !important; }}
    QFrame[styleClass="stat-chip"] {{ background-color: {c["surface_variant"]} !important; border: 1px solid {c["border"]} !important; border-radius: 8px !important; }}
    QLabel[styleClass="stat-title"] {{ color: {c["text_secondary"]} !important; font-size: {max(font_size - 1, 10)}px !important; font-weight: 600 !important; }}
    QLabel[styleClass="stat-value"] {{ font-size: {font_size + 2}px !important; font-weight: 800 !important; padding-left: 2px !important; }}
    QLabel#stat_value_grupos {{ color: #0369A1 !important; }}
    QLabel#stat_value_duplicados {{ color: #C2410C !important; }}
    QLabel#stat_value_seleccionados {{ color: #B45309 !important; }}
    QLabel#stat_value_espacio {{ color: #15803D !important; }}
    QLabel#stat_value_espacio_seleccionado {{ color: #BE123C !important; }}
    QLabel#stat_value_tiempo {{ color: #4338CA !important; }}

    QLabel {{ color: {c["text_primary"]} !important; background-color: transparent !important; }}

    QScrollBar:vertical {{ background-color: {c["surface"]} !important; width: 10px !important; border-radius: 5px !important; }}
    QScrollBar::handle:vertical {{ background-color: {c["border"]} !important; border-radius: 5px !important; margin: 2px !important; min-height: 24px !important; }}
    QScrollBar::handle:vertical:hover {{ background-color: {c["primary"]} !important; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px !important; }}
    """
