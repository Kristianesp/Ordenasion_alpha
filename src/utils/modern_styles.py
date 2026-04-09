#!/usr/bin/env python3
"""
Sistema de Estilos Modernos UI/UX 2026 - PyQt6 Compatible
Diseño profesional con colores modernos y controles elegantes.
"""

COLORS_2026 = {
    "primary": "#6366F1",
    "primary_hover": "#4F46E5",
    "secondary": "#8B5CF6",
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "background": "#F8FAFC",
    "surface": "#FFFFFF",
    "surface_variant": "#F1F5F9",
    "text_primary": "#1E293B",
    "text_secondary": "#64748B",
    "text_disabled": "#CBD5E1",
    "border": "#E2E8F0",
    "accent": "#6366F1",
    "table_header": "#F8FAFC",
    "input_background": "#FFFFFF",
    "disabled": "#CBD5E1",
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
    
    QGroupBox {{ background-color: {c["surface"]} !important; border: 1px solid {c["border"]} !important; border-radius: 12px !important; margin-top: 12px !important; padding: 24px 16px 12px 16px !important; font-weight: 600 !important; }}
    QGroupBox::title {{ subcontrol-origin: margin !important; subcontrol-position: top left !important; left: 12px !important; top: -2px !important; padding: 2px 14px !important; border-radius: 8px !important; color: {c["primary"]} !important; background-color: {c["surface_variant"]} !important; max-width: 80% !important; }}
    
    QPushButton {{ background-color: {c["primary"]} !important; color: white !important; border: none !important; border-radius: 8px !important; padding: 10px 20px !important; font-weight: 600 !important; min-height: 36px !important; }}
    QPushButton:hover {{ background-color: {c["primary_hover"]} !important; }}
    QPushButton:pressed {{ background-color: {c["secondary"]} !important; }}
    QPushButton:disabled {{ background-color: {c["border"]} !important; color: {c["text_disabled"]} !important; }}
    
    #organize_button {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c["primary"]}, stop:1 {c["secondary"]}) !important; color: white !important; border: none !important; border-radius: 12px !important; padding: 14px 32px !important; font-weight: 700 !important; font-size: {font_size + 1}px !important; min-height: 48px !important; }}
    #organize_button:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c["primary_hover"]}, stop:1 #7C3AED) !important; }}
    #organize_button:pressed {{ background: qlineargradient(x1:0, y1:0, x2:1, y2=0, stop:0 #4338CA, stop:1 #6D28D9) !important; }}
    
    QLineEdit {{ background-color: {c["input_background"]} !important; color: {c["text_primary"]} !important; border: 2px solid {c["border"]} !important; border-radius: 10px !important; padding: 10px 16px !important; min-height: 40px !important; selection-background-color: {c["primary"]} !important; selection-color: white !important; }}
    QLineEdit:focus {{ border-color: {c["primary"]} !important; }}
    QLineEdit:hover:!focus {{ border-color: {c["text_secondary"]} !important; }}
    
    QTextEdit {{ background-color: {c["input_background"]} !important; color: {c["text_primary"]} !important; border: 1px solid {c["border"]} !important; border-radius: 10px !important; padding: 8px !important; }}
    #log_text {{ background-color: {c["surface"]} !important; color: {c["text_secondary"]} !important; border: 1px solid {c["border"]} !important; border-radius: 8px !important; padding: 6px !important; font-family: 'Consolas', monospace !important; font-size: {font_size - 1}px !important; }}
    
    QTableView {{ background-color: {c["surface"]} !important; color: {c["text_primary"]} !important; border: 1px solid {c["border"]} !important; border-radius: 12px !important; gridline-color: {c["border"]} !important; selection-background-color: {c["primary"]}20 !important; selection-color: {c["text_primary"]} !important; alternate-background-color: {c["surface_variant"]} !important; margin-top: 4px !important; }}
    QTableView::item {{ padding: 8px !important; border-bottom: 1px solid {c["border"]}40 !important; }}
    QTableView::item:hover {{ background-color: {c["primary"]}10 !important; }}
    QTableView::item:selected {{ background-color: {c["primary"]} !important; color: white !important; font-weight: 600 !important; }}
    
    QHeaderView::section {{ background-color: {c["surface_variant"]} !important; color: {c["text_secondary"]} !important; padding: 10px 16px !important; border: none !important; border-bottom: 2px solid {c["border"]} !important; font-weight: 600 !important; font-size: {font_size - 1}px !important; }}
    
    QTabWidget::pane {{ background-color: {c["surface"]} !important; border: 1px solid {c["border"]} !important; border-radius: 12px !important; }}
    QTabBar::tab {{ background-color: {c["surface"]} !important; color: {c["text_secondary"]} !important; padding: 12px 24px !important; border-radius: 8px 8px 0 0 !important; font-weight: 500 !important; }}
    QTabBar::tab:selected {{ background-color: {c["primary"]} !important; color: white !important; font-weight: 600 !important; }}
    QTabBar::tab:hover:!selected {{ background-color: {c["secondary"]} !important; color: white !important; }}
    
    QCheckBox {{ color: {c["text_primary"]} !important; spacing: 8px !important; }}
    QCheckBox::indicator {{ width: 20px !important; height: 20px !important; border: 2px solid {c["border"]} !important; border-radius: 6px !important; background-color: {c["surface"]} !important; }}
    QCheckBox::indicator:checked {{ background-color: {c["success"]} !important; border-color: {c["success"]} !important; }}
    QCheckBox::indicator:hover {{ border-color: {c["primary"]} !important; }}
    
    QSpinBox {{ background-color: {c["surface"]} !important; color: {c["text_primary"]} !important; border: 2px solid {c["border"]} !important; border-radius: 8px !important; padding: 2px 16px 2px 4px !important; }}
    QSpinBox:focus {{ border-color: {c["primary"]} !important; }}
    QSpinBox::up-button {{ subcontrol-origin: border !important; subcontrol-position: top right !important; width: 14px !important; height: 10px !important; border: none !important; border-radius: 2px !important; background-color: transparent !important; }}
    QSpinBox::down-button {{ subcontrol-origin: border !important; subcontrol-position: bottom right !important; width: 14px !important; height: 10px !important; border: none !important; border-radius: 2px !important; background-color: transparent !important; }}
    
    QProgressBar {{ background-color: {c["surface"]} !important; border: 1px solid {c["border"]} !important; border-radius: 8px !important; text-align: center !important; color: {c["text_primary"]} !important; font-weight: 600 !important; height: 24px !important; }}
    QProgressBar::chunk {{ background-color: {c["primary"]} !important; border-radius: 6px !important; margin: 2px !important; }}
    
    QComboBox {{ background-color: {c["surface"]} !important; color: {c["text_primary"]} !important; border: 2px solid {c["border"]} !important; border-radius: 10px !important; padding: 8px 16px !important; min-height: 36px !important; min-width: 140px !important; }}
    QComboBox:hover {{ border-color: {c["primary"]} !important; }}
    QComboBox::drop-down {{ border: none !important; width: 30px !important; }}
    QComboBox QAbstractItemView {{ background-color: {c["surface"]} !important; color: {c["text_primary"]} !important; border: 1px solid {c["border"]} !important; border-radius: 8px !important; selection-background-color: {c["primary"]} !important; selection-color: white !important; outline: none !important; }}
    
    #main_title_label {{ color: {c["primary"]} !important; font-size: {font_size + 2}px !important; font-weight: 700 !important; padding: 4px 0 !important; }}
    
    QLabel {{ color: {c["text_primary"]} !important; background-color: transparent !important; }}
    
    QScrollBar:vertical {{ background-color: {c["surface"]} !important; width: 10px !important; border-radius: 5px !important; }}
    QScrollBar::handle:vertical {{ background-color: {c["border"]} !important; border-radius: 5px !important; margin: 2px !important; min-height: 30px !important; }}
    QScrollBar::handle:vertical:hover {{ background-color: {c["primary"]} !important; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px !important; }}
    """
