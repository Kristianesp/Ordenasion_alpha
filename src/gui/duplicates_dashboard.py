#!/usr/bin/env python3
"""
Dashboard de Gestión de Duplicados - REFACTORIZADO
Interfaz completa para detectar, visualizar y gestionar archivos duplicados
Archivo original: 1,772 líneas → Refactorizado: ~120 líneas
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import pyqtSignal

from src.utils.constants import UI_CONFIG

# Importar componentes refactorizados
from src.gui.duplicates_dashboard_components import DuplicateWidgets, DuplicateHandlers, ScanLogic
from src.gui.table_models import VirtualizedDuplicatesModel


class DuplicatesDashboard(QWidget, DuplicateWidgets, DuplicateHandlers, ScanLogic):
    """
    Dashboard de gestión de duplicados
    
    NOTA: Esta clase ahora es un orquestador que delega en componentes:
    - DuplicateWidgets: Construcción de UI (~400 líneas)
    - DuplicateHandlers: Manejo de eventos y señales (~330 líneas)
    - ScanLogic: Lógica de escaneo y gestión (~270 líneas)
    
    Total código movido a componentes: ~1,000 líneas
    """
    
    # Señales
    status_update = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # === ESTADO ===
        self.duplicates_data = []
        self.filtered_data = []
        self.scan_worker = None
        self.current_page = 0
        self.rows_per_page = 100
        
        # === INICIALIZACIÓN ===
        self.init_ui()
        self.setup_connections()
        
        print("[DuplicatesDashboard] ✅ Inicialización completada")
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        self.setWindowTitle("Gestión de Duplicados")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Título
        title = QLabel("🔍 Detector y Gestor de Archivos Duplicados")
        title.setObjectName("duplicates_title")
        layout.addWidget(title)
        
        # Paneles
        self.create_control_panel(layout)
        self.create_filter_panel(layout)
        self.create_results_table(layout)
        self.create_statistics_panel(layout)
        
        # Modelo de tabla virtualizada
        self.model = VirtualizedDuplicatesModel([], parent=self)
        self.duplicates_table.setModel(self.model)
        
        print("[DuplicatesDashboard] UI inicializada")
