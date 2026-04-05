#!/usr/bin/env python3
"""
Componentes de Estilos para DiskViewer
Módulo extraído para manejar todos los estilos y temas del visor de discos
"""

from typing import Dict, Optional
from PyQt6.QtWidgets import QLabel, QPushButton, QCheckBox, QGroupBox, QFrame, QTextEdit, QProgressBar, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from src.utils.themes import ThemeManager
from src.utils.constants import COLORS


class DiskViewerStyler:
    """Clase especializada en aplicar estilos al DiskViewer"""
    
    @staticmethod
    def get_usage_color_by_percentage(usage_percent: float, theme_name: str = None) -> str:
        """Obtiene el color según el porcentaje de uso del disco"""
        if theme_name:
            try:
                colors = ThemeManager.get_theme_colors(theme_name)
                if usage_percent > 90:
                    return colors['error']
                elif usage_percent > 80:
                    return colors['warning']
                elif usage_percent > 70:
                    return colors['accent']
                else:
                    return colors['success']
            except:
                pass
        
        # Fallback a colores por defecto
        if usage_percent > 90:
            return "#e74c3c"  # Rojo crítico
        elif usage_percent > 80:
            return "#f39c12"  # Naranja alto
        elif usage_percent > 70:
            return "#3498db"  # Azul moderado
        else:
            return "#27ae60"  # Verde óptimo
    
    @staticmethod
    def apply_static_interface_styles(widget: QWidget, theme_name: str, colors: dict):
        """Aplica estilos del tema a todos los elementos estáticos de la interfaz"""
        try:
            # 0. Header del sistema (INFORMACIÓN DEL SISTEMA)
            if hasattr(widget, 'unified_header') and widget.unified_header:
                widget.unified_header.setStyleSheet(f"""
                    QFrame {{
                        background-color: {colors['surface']} !important;
                        border: 1px solid {colors['border']} !important;
                        border-radius: 6px;
                        margin-top: 0px !important;
                        margin-bottom: 0px;
                    }}
                """)
            
            # 0.1. Título del sistema
            for lbl in widget.findChildren(QLabel):
                if lbl.objectName() == "system_info_title":
                    lbl.setStyleSheet(f"""
                        QLabel {{
                            color: {colors['text_primary']} !important;
                            background-color: transparent;
                            font-size: 12px;
                            font-weight: bold;
                            padding: 0px 5px;
                        }}
                    """)
            
            # 0.2. Label de información del sistema
            if hasattr(widget, 'system_info_label') and widget.system_info_label:
                widget.system_info_label.setStyleSheet(f"""
                    QLabel {{
                        color: {colors['text_primary']} !important;
                        background-color: transparent;
                        font-size: 12px;
                        font-weight: normal;
                        padding: 0px 5px;
                    }}
                """)
            
            # 0.3. Labels de modo seguro
            for lbl in widget.findChildren(QLabel):
                if lbl.objectName() == "safe_mode_label":
                    lbl.setStyleSheet(f"""
                        QLabel {{
                            color: {colors['text_primary']} !important;
                            background-color: transparent;
                            font-size: 11px;
                            padding: 0px 3px;
                        }}
                    """)
            
            # 0.4. Checkbox de modo seguro
            if hasattr(widget, 'safe_mode_checkbox') and widget.safe_mode_checkbox:
                widget.safe_mode_checkbox.setStyleSheet(f"""
                    QCheckBox {{
                        color: {colors['text_primary']} !important;
                        background-color: transparent;
                        font-size: 11px;
                        padding: 0px 3px;
                    }}
                    QCheckBox::indicator {{
                        width: 14px;
                        height: 14px;
                        border: 1px solid {colors['border']};
                        border-radius: 3px;
                        background-color: {colors['surface']};
                    }}
                    QCheckBox::indicator:checked {{
                        background-color: {colors['primary']};
                        border-color: {colors['primary']};
                    }}
                """)
            
            # 0.5. Botón de refresh
            if hasattr(widget, 'refresh_btn') and widget.refresh_btn:
                widget.refresh_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {colors['primary']} !important;
                        color: white !important;
                        border: none !important;
                        border-radius: 4px;
                        font-size: 11px;
                        font-weight: bold;
                        padding: 4px 10px;
                    }}
                    QPushButton:hover {{
                        background-color: {colors.get('button_hover', colors['secondary'])} !important;
                    }}
                    QPushButton:pressed {{
                        background-color: {colors.get('button_pressed', colors['accent'])} !important;
                    }}
                """)
            
            # 0.5. Botones de acción (select_btn - "🔍 Analizar")
            for btn in widget.findChildren(QPushButton):
                if btn.objectName() == "select_btn":
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {colors['primary']} !important;
                            color: white !important;
                            border: none !important;
                            border-radius: 6px;
                            font-size: 11px;
                            font-weight: bold;
                            padding: 6px 12px;
                        }}
                        QPushButton:hover {{
                            background-color: {colors.get('button_hover', colors['secondary'])} !important;
                        }}
                        QPushButton:pressed {{
                            background-color: {colors.get('button_pressed', colors['accent'])} !important;
                        }}
                        QPushButton:disabled {{
                            background-color: {colors.get('text_disabled', '#bdbdbd')} !important;
                            color: {colors.get('text_secondary', '#999')} !important;
                        }}
                    """)
            
            # 1. Grupo principal de análisis
            if hasattr(widget, 'analysis_group') and widget.analysis_group:
                widget.analysis_group.setStyleSheet(f"""
                    QGroupBox {{
                        background-color: {colors['background']};
                        border: 2px solid {colors['border']};
                        border-radius: 15px;
                        margin-top: 10px;
                        padding-top: 10px;
                        font-weight: bold;
                        color: {colors['text_primary']};
                    }}
                    QGroupBox::title {{
                        subcontrol-origin: margin;
                        left: 20px;
                        padding: 0 15px 0 15px;
                        color: {colors['primary']};
                        font-size: 15px;
                        font-weight: bold;
                    }}
                """)
            
            # 2. Grupo de información detallada
            if hasattr(widget, 'info_group') and widget.info_group:
                widget.info_group.setStyleSheet(f"""
                    QGroupBox {{
                        background-color: {colors['background']};
                        border: 2px solid {colors['border']};
                        border-radius: 15px;
                        margin-top: 10px;
                        padding-top: 10px;
                        font-weight: bold;
                        color: {colors['text_primary']};
                    }}
                    QGroupBox::title {{
                        subcontrol-origin: margin;
                        left: 20px;
                        padding: 0 15px 0 15px;
                        color: {colors['primary']};
                        font-size: 15px;
                        font-weight: bold;
                    }}
                """)
            
            # 3. Área de logs
            if hasattr(widget, 'log_display') and widget.log_display:
                widget.log_display.setStyleSheet(f"""
                    QTextEdit {{
                        background-color: {colors['surface']};
                        color: {colors['text_primary']};
                        border: 1px solid {colors['border']};
                        border-radius: 8px;
                        padding: 8px;
                        font-family: 'Courier New', monospace;
                        font-size: 10px;
                        selection-background-color: {colors['primary']};
                        selection-color: white;
                    }}
                """)
            
            # 4. ScrollArea contenedor
            if hasattr(widget, 'scroll_area') and widget.scroll_area:
                widget.scroll_area.setStyleSheet(f"""
                    QScrollArea {{
                        background-color: {colors['background']};
                        border: none;
                    }}
                    QScrollArea > QWidget > QWidget {{
                        background-color: {colors['background']};
                    }}
                """)
            
            # 5. Widgets internos del scroll
            for child in widget.findChildren(QWidget):
                if hasattr(child, 'setStyleSheet'):
                    # Evitar sobreescribir estilos específicos
                    if child.objectName() not in ['select_btn', 'system_info_title', 'safe_mode_label']:
                        if isinstance(child, QFrame):
                            child.setStyleSheet(f"""
                                QFrame {{
                                    background-color: transparent;
                                    border: none;
                                }}
                            """)
            
        except Exception as e:
            if hasattr(widget, 'log_message'):
                widget.log_message(f"⚠️ Error aplicando estilos: {str(e)}")
    
    @staticmethod
    def apply_compact_disk_viewer_styles(widget: QWidget, theme_name: str, colors: dict):
        """Aplica estilos específicos para la tabla compacta del visor de discos"""
        try:
            if hasattr(widget, 'disks_table') and widget.disks_table:
                widget.disks_table.setStyleSheet(f"""
                    QTableWidget {{
                        background-color: {colors['surface']};
                        alternate-background-color: {colors['background']};
                        color: {colors['text_primary']};
                        border: 1px solid {colors['border']};
                        border-radius: 8px;
                        gridline-color: {colors['border']};
                        selection-background-color: {colors['primary']}33;
                        selection-color: {colors['text_primary']};
                    }}
                    QTableWidget::item {{
                        padding: 6px;
                        border: none;
                    }}
                    QTableWidget::item:selected {{
                        background-color: {colors['primary']}44;
                        color: {colors['text_primary']};
                    }}
                    QTableWidget::item:hover {{
                        background-color: {colors['primary']}22;
                    }}
                    QHeaderView::section {{
                        background-color: {colors['primary']};
                        color: white;
                        padding: 8px;
                        border: none;
                        border-bottom: 2px solid {colors['accent']};
                        font-weight: bold;
                        font-size: 11px;
                    }}
                    QScrollBar:vertical {{
                        background-color: {colors['surface']};
                        width: 10px;
                        border-radius: 5px;
                    }}
                    QScrollBar::handle:vertical {{
                        background-color: {colors['border']};
                        border-radius: 5px;
                        min-height: 20px;
                    }}
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                        height: 0px;
                    }}
                    QScrollBar:horizontal {{
                        background-color: {colors['surface']};
                        height: 10px;
                        border-radius: 5px;
                    }}
                    QScrollBar::handle:horizontal {{
                        background-color: {colors['border']};
                        border-radius: 5px;
                        min-width: 20px;
                    }}
                    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                        width: 0px;
                    }}
                """)
        except Exception as e:
            if hasattr(widget, 'log_message'):
                widget.log_message(f"⚠️ Error aplicando estilos de tabla: {str(e)}")
    
    @staticmethod
    def apply_progress_bar_styles(widget: QWidget, theme_name: str):
        """Aplica estilos a las barras de progreso"""
        try:
            colors = ThemeManager.get_theme_colors(theme_name)
            
            for progress in widget.findChildren(QProgressBar):
                progress.setStyleSheet(f"""
                    QProgressBar {{
                        background-color: {colors['surface']};
                        border: 1px solid {colors['border']};
                        border-radius: 5px;
                        text-align: center;
                        font-weight: bold;
                        color: {colors['text_primary']};
                        height: 18px;
                    }}
                    QProgressBar::chunk {{
                        background-color: {colors['primary']};
                        border-radius: 4px;
                    }}
                """)
        except Exception as e:
            if hasattr(widget, 'log_message'):
                widget.log_message(f"⚠️ Error aplicando estilos de progress bar: {str(e)}")
    
    @staticmethod
    def update_usage_progress_colors(widget: QWidget, theme_name: str, usage_percent: float):
        """Actualiza los colores de las barras de progreso según el porcentaje de uso"""
        try:
            colors = ThemeManager.get_theme_colors(theme_name)
            
            if usage_percent > 90:
                color = colors['error']
            elif usage_percent > 80:
                color = colors['warning']
            elif usage_percent > 70:
                color = colors['accent']
            else:
                color = colors['success']
            
            for progress in widget.findChildren(QProgressBar):
                current_style = progress.styleSheet()
                if 'QProgressBar::chunk' in current_style:
                    new_style = current_style.replace(
                        f"background-color: {colors['primary']};",
                        f"background-color: {color};"
                    )
                    progress.setStyleSheet(new_style)
        except Exception as e:
            if hasattr(widget, 'log_message'):
                widget.log_message(f"⚠️ Error actualizando colores: {str(e)}")
    
    @staticmethod
    def get_themed_html_box(theme_name: str, box_type: str, title: str, content: str, icon: str = "") -> str:
        """Genera una caja HTML con estilos del tema"""
        colors = ThemeManager.get_theme_colors(theme_name)
        
        type_colors = {
            "info": colors['primary'],
            "success": colors['success'],
            "warning": colors['warning'],
            "error": colors['error']
        }
        
        border_color = type_colors.get(box_type, colors['primary'])
        bg_color = f"{border_color}10"  # 10% opacity
        
        return f"""
        <div style="margin-bottom: 10px; padding: 10px; background-color: {bg_color}; 
                    border-radius: 6px; border-left: 4px solid {border_color};">
            <div style="color: {border_color}; font-weight: bold; margin-bottom: 5px;">
                {icon} {title}
            </div>
            <div style="color: {colors['text_primary']};">
                {content}
            </div>
        </div>
        """
    
    @staticmethod
    def get_themed_html_text(theme_name: str, content: str, bold: bool = False, color_type: str = "text_primary") -> str:
        """Obtiene texto HTML con color del tema"""
        colors = ThemeManager.get_theme_colors(theme_name)
        color = colors.get(color_type, colors['text_primary'])
        weight = "bold" if bold else "normal"
        return f'<span style="color: {color}; font-weight: {weight};">{content}</span>'
