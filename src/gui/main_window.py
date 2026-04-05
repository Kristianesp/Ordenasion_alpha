#!/usr/bin/env python3
"""
Ventana Principal del Organizador de Archivos - REFACTORIZADO
Maneja la interfaz principal y la lógica de la aplicación
Archivo original: 2,133 líneas → Refactorizado: ~150 líneas
"""

import os
import sys
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtCore import QSettings

from src.utils.constants import UI_CONFIG
from src.core.application_state import app_state
from src.gui.disk_viewer import DiskViewer
from src.gui.config_dialog import ConfigDialog
from src.gui.duplicates_dashboard import DuplicatesDashboard

# Importar componentes refactorizados
from src.gui.main_window_components import MainWindowSetup, MainWindowHandlers, MainWindowActions


class FileOrganizerGUI(QMainWindow, MainWindowSetup, MainWindowHandlers, MainWindowActions):
    """
    Ventana principal del organizador de archivos
    
    NOTA: Esta clase ahora es un orquestador que delega en componentes:
    - MainWindowSetup: Construcción de UI (~500 líneas)
    - MainWindowHandlers: Manejo de eventos y señales (~270 líneas)
    - MainWindowActions: Acciones de negocio (análisis, organización) (~420 líneas)
    
    Total código movido a componentes: ~1,200 líneas
    """
    
    def __init__(self):
        super().__init__()
        
        # === ESTADO CENTRALIZADO ===
        self._init_state()
        
        # === CONFIGURACIÓN PERSISTENTE ===
        self.settings = QSettings("FileOrganizer", "MainWindow")
        
        # === INICIALIZACIÓN ===
        self.init_ui()  # De MainWindowSetup
        self._init_disk_manager()
        self.setup_connections()  # De MainWindowHandlers
        self.setup_shortcuts()  # De MainWindowHandlers
        self.setup_state_observers()  # De MainWindowHandlers
        self.apply_saved_interface_settings()  # De MainWindowHandlers
        
        print("[MainWindow] ✅ Inicialización completada")
    
    def _init_disk_manager(self):
        """Inicializa DiskManager usando el estado centralizado"""
        try:
            if not hasattr(app_state, 'get_disk_manager'):
                self.log_message("⚠️ app_state no tiene get_disk_manager")
                self.disk_manager = None
                return
            
            self.disk_manager = app_state.get_disk_manager()
            
            if self.disk_manager and hasattr(self, 'disk_viewer') and self.disk_viewer:
                self.disk_viewer.disk_manager = self.disk_manager
                self.disk_viewer.refresh_disks()
                self.log_message("✅ DiskViewer actualizado con DiskManager")
        except Exception as e:
            self.log_message(f"❌ Error al inicializar DiskManager: {e}")
            self.disk_manager = None
