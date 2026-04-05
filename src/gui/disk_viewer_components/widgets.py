#!/usr/bin/env python3
"""
Widgets y Componentes para DiskViewer
Módulo extraído con widgets especializados y componentes reutilizables
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QProgressBar, QTextEdit, QFrame, QSplitter,
    QCheckBox, QComboBox, QSizePolicy, QScrollArea, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor


class CompactDiskTable(QTableWidget):
    """Tabla optimizada para visualización compacta de discos"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()
    
    def setup_table(self):
        """Configura la tabla con diseño compacto"""
        # Headers
        headers = [
            "Unidad", "Punto de Montaje", "Total", "Usado", 
            "Libre", "Uso %", "Sistema", "Acciones"
        ]
        self.setHorizontalHeaderLabels(headers)
        
        # Configuración de columnas
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Unidad
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Mountpoint
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Total
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Usado
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Libre
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Uso %
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # Sistema
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)  # Acciones
        
        # Anchos fijos
        self.setColumnWidth(0, 70)   # Unidad
        self.setColumnWidth(2, 90)   # Total
        self.setColumnWidth(3, 90)   # Usado
        self.setColumnWidth(4, 90)   # Libre
        self.setColumnWidth(5, 70)   # Uso %
        self.setColumnWidth(6, 80)   # Sistema
        self.setColumnWidth(7, 130)  # Acciones
        
        # Estilo compacto
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Política de tamaño
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumHeight(150)
    
    def clear_all(self):
        """Limpia toda la tabla"""
        self.setRowCount(0)
    
    def get_selected_mountpoint(self) -> Optional[str]:
        """Obtiene el punto de montaje de la fila seleccionada"""
        selected_items = self.selectedItems()
        if not selected_items:
            return None
        
        current_row = selected_items[0].row()
        mount_item = self.item(current_row, 1)  # Columna de mountpoint
        return mount_item.text() if mount_item else None


class SystemInfoPanel(QFrame):
    """Panel compacto para información del sistema"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("system_info_group")
        self.setFrameShape(QFrame.Shape.Box)
        self.setLineWidth(0)
        self.setMinimumHeight(45)
        self.setMaximumHeight(45)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz del panel"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(12)
        
        # Título
        title_label = QLabel("🖥️ INFORMACIÓN DEL SISTEMA:")
        title_label.setObjectName("system_info_title")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title_label)
        
        # Label de información
        self.info_label = QLabel("Cargando información del sistema...")
        self.info_label.setObjectName("system_info_label")
        self.info_label.setWordWrap(False)
        self.info_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.info_label)
        
        # Checkbox modo seguro
        safe_mode_label = QLabel("Modo seguro:")
        safe_mode_label.setObjectName("safe_mode_label")
        layout.addWidget(safe_mode_label)
        
        self.safe_mode_checkbox = QCheckBox("Activar")
        self.safe_mode_checkbox.setToolTip("🛡️ Activa modo seguro: Previene eliminación de archivos críticos del sistema")
        layout.addWidget(self.safe_mode_checkbox)
        
        # Botón refresh
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setToolTip("🔄 Actualiza la información de todos los discos en tiempo real")
        self.refresh_btn.setFixedHeight(28)
        layout.addWidget(self.refresh_btn)
    
    def update_info(self, cpu_percent: float, ram_percent: float, disk_count: int, safe_mode: bool):
        """Actualiza la información del sistema"""
        self.info_label.setText(
            f"CPU: {cpu_percent:.1f}% | RAM: {ram_percent:.1f}% | Discos: {disk_count} monitoreados"
        )
        self.safe_mode_checkbox.setChecked(safe_mode)


class ActionButtonWidget(QWidget):
    """Widget contenedor para botones de acción en la tabla"""
    
    clicked = pyqtSignal()
    
    def __init__(self, text: str = "🔍 Analizar", parent=None):
        super().__init__(parent)
        self.setup_ui(text)
    
    def setup_ui(self, text: str):
        """Configura el botón de acción"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 8, 2, 8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.button = QPushButton(text)
        self.button.setToolTip(f"{text} - Analiza el disco y permite organizar archivos")
        self.button.setObjectName("select_btn")
        self.button.setFixedHeight(28)
        self.button.setFixedWidth(120)
        self.button.clicked.connect(self.clicked.emit)
        
        layout.addWidget(self.button)


class HealthDisplayWidget(QWidget):
    """Widget para mostrar información de salud del disco"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Configura el widget de salud"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Grupo de análisis
        self.analysis_group = QGroupBox("📊 ANÁLISIS DE DISCO")
        self.analysis_group.setObjectName("analysis_group")
        analysis_layout = QVBoxLayout(self.analysis_group)
        
        # Área de contenido HTML para salud
        self.health_content = QTextEdit()
        self.health_content.setReadOnly(True)
        self.health_content.setHtml("<p>Seleccione un disco para ver su estado de salud</p>")
        self.health_content.setMinimumHeight(200)
        analysis_layout.addWidget(self.health_content)
        
        layout.addWidget(self.analysis_group)
    
    def update_health_info(self, html_content: str):
        """Actualiza la información de salud con HTML"""
        self.health_content.setHtml(html_content)


class LogDisplayWidget(QTextEdit):
    """Widget especializado para mostrar logs de la aplicación"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Configura el widget de logs"""
        self.setReadOnly(True)
        self.setObjectName("log_display")
        self.setMinimumHeight(100)
        self.setMaximumHeight(150)
        self.setFont(QFont('Courier New', 10))
    
    def append_log(self, message: str):
        """Agrega un mensaje al log"""
        self.append(message)
        # Auto-scroll al final
        scrollbar = self.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())
