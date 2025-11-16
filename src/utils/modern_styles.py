#!/usr/bin/env python3
"""
Sistema de Estilos Modernos UI/UX 2025 - PyQt6 Compatible
Diseño profesional con propiedades CSS únicamente soportadas por PyQt6
"""

def get_modern_css_styles(colors: dict, font_size: int = 12) -> str:
    """
    Genera estilos CSS modernos y profesionales compatibles con PyQt6:
    - Solo propiedades CSS soportadas
    - Contraste optimizado para accesibilidad
    - Diseño limpio y consistente
    - Sin animaciones o transformaciones complejas
    """

    return f"""
    /* ================================================================
       🎨 SISTEMA DE DISEÑO MODERNO 2025 - PYQT6 COMPATIBLE
       ================================================================ */

    /* 🔧 CONFIGURACIÓN BASE */
    * {{
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif !important;
        font-size: {font_size}px !important;
    }}

    /* 🏠 CONTENEDOR PRINCIPAL */
    QMainWindow {{
        background-color: {colors['background']} !important;
        color: {colors['text_primary']} !important;
        border: none !important;
    }}

    /* 📋 PESTAÑAS MODERNAS */
    QTabWidget::pane {{
        background-color: {colors['surface']} !important;
        border: 1px solid {colors['border']} !important;
        border-radius: 12px !important;
        margin-top: 8px !important;
    }}

    QTabBar::tab {{
        background-color: {colors['surface']} !important;
        color: {colors['text_secondary']} !important;
        padding: 12px 24px !important;
        margin-right: 4px !important;
        border-radius: 8px 8px 0 0 !important;
        font-weight: 500 !important;
        min-width: 100px !important;
    }}

    QTabBar::tab:selected {{
        background-color: {colors['primary']} !important;
        color: white !important;
        font-weight: 600 !important;
    }}

    QTabBar::tab:hover:!selected {{
        background-color: {colors['secondary']} !important;
        color: white !important;
    }}

    /* 🎯 BOTONES MODERNOS */
    QPushButton {{
        background-color: {colors['primary']} !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 8px 16px !important;
        font-weight: 600 !important;
        font-size: {font_size}px !important;
        min-height: 32px !important;
    }}

    QPushButton:hover {{
        background-color: {colors.get('button_hover', colors['secondary'])} !important;
    }}

    QPushButton:pressed {{
        background-color: {colors.get('button_pressed', colors['accent'])} !important;
    }}

    QPushButton:disabled {{
        background-color: {colors.get('text_disabled', '#bdbdbd')} !important;
        color: {colors['text_secondary']} !important;
    }}

    /* 🚀 BOTÓN PRINCIPAL (ORGANIZAR) */
    #organize_button {{
        background-color: {colors['primary']} !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: 700 !important;
        font-size: {font_size + 1}px !important;
        min-height: 40px !important;
    }}

    #organize_button:hover {{
        background-color: {colors['secondary']} !important;
    }}

    #organize_button:pressed {{
        background-color: {colors['accent']} !important;
    }}

    /* ✅ BOTÓN ÉXITO (ESCANEAR) */
    #scan_button {{
        background-color: {colors['success']} !important;
        color: white !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        min-height: 32px !important;
        padding: 8px 16px !important;
    }}

    #scan_button:hover {{
        background-color: #2e7d32 !important;
    }}

    /* ⚠️ BOTÓN ADVERTENCIA (ANALIZAR) */
    #analyze_button {{
        background-color: {colors['warning']} !important;
        color: white !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        min-height: 32px !important;
        padding: 8px 16px !important;
    }}

    #analyze_button:hover {{
        background-color: #e65100 !important;
    }}

    /* 📝 CAMPOS DE ENTRADA MODERNOS */
    QLineEdit, QTextEdit {{
        background-color: {colors['surface']} !important;
        color: {colors['text_primary']} !important;
        border: 2px solid {colors['border']} !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
        font-size: {font_size}px !important;
        min-height: 20px !important;
    }}

    QLineEdit:focus, QTextEdit:focus {{
        border-color: {colors['primary']} !important;
        background-color: {colors['background']} !important;
    }}

    QLineEdit:hover:!focus, QTextEdit:hover:!focus {{
        border-color: {colors['secondary']} !important;
        background-color: {colors.get('surface_variant', colors['surface'])} !important;
    }}

    /* 📊 TABLAS PROFESIONALES */
    QTableWidget, QTableView {{
        background-color: {colors['surface']} !important;
        color: {colors['text_primary']} !important;
        border: 1px solid {colors['border']} !important;
        border-radius: 8px !important;
        gridline-color: {colors['border']} !important;
        selection-background-color: {colors['primary']} !important;
        selection-color: white !important;
        font-size: {font_size}px !important;
        alternate-background-color: {colors.get('surface_variant', colors['surface'])} !important;
    }}

    QTableWidget::item, QTableView::item {{
        padding: 8px 12px !important;
        border-bottom: 1px solid {colors['border']}50 !important;
        background-color: transparent !important;
    }}

    QTableWidget::item:hover, QTableView::item:hover {{
        background-color: {colors['primary']}30 !important;
        color: {colors['text_primary']} !important;
    }}

    QTableWidget::item:selected, QTableView::item:selected {{
        background-color: {colors['primary']} !important;
        color: white !important;
        font-weight: 600 !important;
    }}

    QTableWidget::item:selected:hover, QTableView::item:selected:hover {{
        background-color: {colors['secondary']} !important;
        color: white !important;
    }}

    /* 🏷️ CABECERAS DE TABLA */
    QHeaderView::section {{
        background-color: {colors.get('table_header', colors['surface'])} !important;
        color: {colors['text_primary']} !important;
        padding: 12px !important;
        border: none !important;
        border-bottom: 2px solid {colors['primary']} !important;
        font-weight: 600 !important;
        font-size: {font_size}px !important;
    }}

    /* 📦 GRUPOS Y CONTENEDORES */
    QGroupBox {{
        background-color: {colors['surface']} !important;
        color: {colors['text_primary']} !important;
        border: 1px solid {colors['border']} !important;
        border-radius: 12px !important;
        margin-top: 16px !important;
        padding-top: 16px !important;
        font-weight: 600 !important;
        font-size: {font_size}px !important;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin !important;
        subcontrol-position: top left !important;
        left: 16px !important;
        padding: 4px 12px !important;
        background-color: !important;
        color: white !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }}

    /* ☑️ CHECKBOXES MODERNOS */
    QCheckBox {{
        color: {colors['text_primary']} !important;
        font-size: {font_size}px !important;
        spacing: 8px !important;
    }}

    QCheckBox::indicator {{
        width: 20px !important;
        height: 20px !important;
        border: 2px solid {colors['border']} !important;
        border-radius: 6px !important;
        background-color: {colors['surface']} !important;
    }}

    QCheckBox::indicator:checked {{
        background-color: {colors['success']} !important;
        border-color: {colors['success']} !important;
        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEzLjUgNEw2IDExLjVMMi41IDgiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=) !important;
    }}

    QCheckBox::indicator:hover {{
        border-color: {colors['primary']} !important;
    }}

    /* 📊 BARRAS DE PROGRESO */
    QProgressBar {{
        background-color: {colors['surface']} !important;
        border: 1px solid {colors['border']} !important;
        border-radius: 8px !important;
        text-align: center !important;
        color: {colors['text_primary']} !important;
        font-weight: 600 !important;
        height: 24px !important;
    }}

    QProgressBar::chunk {{
        background-color: {colors['primary']} !important;
        border-radius: 6px !important;
        margin: 2px !important;
    }}

    /* 🎛️ COMBOS Y SELECTORES */
    QComboBox {{
        background-color: {colors['surface']} !important;
        color: {colors['text_primary']} !important;
        border: 2px solid {colors['border']} !important;
        border-radius: 10px !important;
        padding: 8px 16px !important;
        min-height: 20px !important;
    }}

    QComboBox:hover {{
        border-color: {colors['primary']} !important;
    }}

    QComboBox::drop-down {{
        border: none !important;
        width: 30px !important;
    }}

    QComboBox::down-arrow {{
        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQgNkw4IDEwTDEyIDYiIHN0cm9rZT0iIzY2NiIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+Cg==) !important;
        width: 16px !important;
        height: 16px !important;
    }}

    /* 📝 ETIQUETAS */
    QLabel {{
        color: {colors['text_primary']} !important;
        font-size: {font_size}px !important;
        background-color: transparent !important;
    }}

    /* 🔢 SPINBOXES */
    QSpinBox {{
        background-color: {colors['surface']} !important;
        color: {colors['text_primary']} !important;
        border: 2px solid {colors['border']} !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        min-height: 20px !important;
    }}

    QSpinBox:focus {{
        border-color: {colors['primary']} !important;
    }}

    QSpinBox::up-button, QSpinBox::down-button {{
        background-color: {colors['primary']} !important;
        border: none !important;
        border-radius: 4px !important;
        width: 20 !important;
        margin: 2px !important;
    }}

    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
        background-color: {colors['secondary']} !important;
    }}

    /* 🎨 EFECTOS ESPECIALES SIMPLES */
    .success {{
        background-color: {colors['success']} !important;
        color: white !important;
    }}

    .warning {{
        background-color: {colors['warning']} !important;
        color: white !important;
    }}

    .error {{
        background-color: {colors['error']} !important;
        color: white !important;
    }}

    .info {{
        background-color: {colors['info']} !important;
        color: white !important;
    }}

    /* 📋 SCROLLBARS SIMPLES */
    QScrollBar:vertical {{
        background-color: {colors['surface']} !important;
        width: 12px !important;
        border-radius: 6px !important;
    }}

    QScrollBar::handle:vertical {{
        background-color: {colors['border']} !important;
        border-radius: 6px !important;
        margin: 2px !important;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {colors['primary']} !important;
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px !important;
    }}

    /* 🎯 ESTADO ESPECIAL PARA BOTÓN DE ESCANEO */
    QPushButton#scan_button {{
        background-color: #2196F3 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        font-size: 14px !important;
        padding: 8px !important;
    }}

    QPushButton#scan_button:hover {{
        background-color: #42A5F5 !important;
    }}

    QPushButton#scan_button:pressed {{
        background-color: #1976D2 !important;
    }}

    QPushButton#scan_button:disabled {{
        background-color: #666 !important;
        color: #999 !important;
    }}
    """