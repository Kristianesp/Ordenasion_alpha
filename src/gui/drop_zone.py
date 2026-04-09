#!/usr/bin/env python3
"""
Widget de zona de arrastrar y soltar (Drag & Drop) para el Organizador de Archivos
Permite arrastrar carpetas directamente sobre la aplicacion
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal

from src.utils.app_config import AppConfig
from src.utils.themes import ThemeManager


class DropZone(QFrame):
    """Zona donde se pueden arrastrar carpetas para abrirlas directamente"""
    
    folder_dropped = pyqtSignal(str)  # Senal emitida cuando se suelta una carpeta
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._is_dragging = False
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la apariencia visual de la zona de drop"""
        self.setMinimumHeight(80)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.icon_label = QLabel("📂")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setObjectName("drop_zone_icon")
        
        self.text_label = QLabel("Arrastra una carpeta aqui o usa Examinar")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setObjectName("drop_zone_text")
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        
        self._apply_normal_style()
    
    def _apply_normal_style(self):
        """Estilo normal (sin drag encima)"""
        colors = self._get_theme_colors()
        self.setStyleSheet(
            f"""
            DropZone {{
                border: 2px dashed {colors['border']};
                border-radius: 12px;
                background-color: {colors['surface_variant']};
            }}
            QLabel#drop_zone_icon {{
                font-size: 32px;
                color: {colors['primary']};
            }}
            QLabel#drop_zone_text {{
                color: {colors['text_secondary']};
                font-size: 14px;
            }}
        """
        )
    
    def _apply_dragover_style(self):
        """Estilo cuando se arrastra algo encima"""
        colors = self._get_theme_colors()
        self.setStyleSheet(
            f"""
            DropZone {{
                border: 3px solid {colors['primary']};
                border-radius: 12px;
                background-color: {colors['table_selected']};
            }}
            QLabel#drop_zone_icon {{
                font-size: 32px;
                color: {colors['primary']};
            }}
            QLabel#drop_zone_text {{
                color: {colors['text_primary']};
                font-size: 14px;
            }}
        """
        )

    def _get_theme_colors(self):
        app_config = AppConfig()
        return ThemeManager.get_theme_colors(app_config.get_theme())
    
    def dragEnterEvent(self, event):
        """Se llama cuando algo se arrastra sobre el widget"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                import os
                if os.path.isdir(path):
                    self._is_dragging = True
                    self._apply_dragover_style()
                    self.text_label.setText("¡Suelo la carpeta aqui!")
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def dragMoveEvent(self, event):
        """Se llama mientras se mueve el cursor con algo arrastrado"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        """Se llama cuando el cursor sale del widget"""
        self._is_dragging = False
        self._apply_normal_style()
        self.text_label.setText("Arrastra una carpeta aqui o usa Examinar")
    
    def dropEvent(self, event):
        """Se llama cuando se suelta algo sobre el widget"""
        self._is_dragging = False
        self._apply_normal_style()
        self.text_label.setText("Arrastra una carpeta aqui o usa Examinar")
        
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                import os
                if os.path.isdir(path):
                    self.folder_dropped.emit(path)
                    event.acceptProposedAction()
                    return
        event.ignore()
