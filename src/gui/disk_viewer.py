#!/usr/bin/env python3
"""
Visor de Discos y Particiones para el Organizador de Archivos
Versión refactorizada - Delega lógica a componentes especializados
"""

import os
from typing import Optional, List
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QProgressBar, QTextEdit, QFrame, QSplitter,
    QMessageBox, QCheckBox, QComboBox, QSizePolicy, QScrollArea,
    QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette

from src.core.disk_manager import DiskManager, DiskInfo
from src.utils.constants import COLORS
from src.utils.themes import ThemeManager
from src.gui.disk_viewer_components import (
    DiskViewerStyler,
    DiskViewerHandlers,
    CompactDiskTable,
    SystemInfoPanel,
    ActionButtonWidget,
    HealthDisplayWidget,
    LogDisplayWidget,
    DiskViewerUIBuilder,
    DiskInfoUpdater
)


class DiskViewer(QWidget):
    """Widget principal para visualizar y gestionar discos del sistema"""
    
    # Señales para comunicación con la ventana principal
    disk_selected = pyqtSignal(str)
    analysis_requested = pyqtSignal(str)
    
    def __init__(self, parent=None, disk_manager=None):
        super().__init__(parent)
        self.disk_manager = disk_manager
        self.current_selection = None
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_disks)
        
        # Debounce timer para operaciones pesadas
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self._on_debounce_timeout)
        self.pending_analysis = None
        
        # Cache local para datos SMART
        self._smart_cache = {}
        self._cache_priority = {}
        
        # Inicializar UI usando el builder
        self.styler = DiskViewerStyler()
        self.handlers = DiskViewerHandlers()
        self._init_ui()
        self.setup_connections()
        
        if self.disk_manager:
            self.refresh_disks()
        
        # Aplicar tema inicial
        try:
            initial_theme = self.get_current_theme_name()
            self.apply_theme_styles(initial_theme)
        except Exception as e:
            self.log_message(f"⚠️ Error aplicando tema inicial: {str(e)}")
    
    def _init_ui(self):
        """Inicializa la interfaz usando DiskViewerUIBuilder"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(4, 0, 4, 0)
        
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setMinimumSize(930, 500)
        
        # Header unificado
        unified_header = DiskViewerUIBuilder.create_unified_header(
            self, 
            getattr(self, 'system_info_label', QLabel()),
            getattr(self, 'safe_mode_checkbox', QCheckBox()),
            getattr(self, 'refresh_btn', QPushButton())
        )
        main_layout.addWidget(unified_header)
        
        # Tabla de discos
        self.disks_table = DiskViewerUIBuilder.create_disks_table()
        main_layout.addWidget(self.disks_table)
        
        # Panel de análisis
        self.analysis_group, self.analysis_widgets = DiskViewerUIBuilder.create_analysis_panel()
        main_layout.addWidget(self.analysis_group)
        
        # Guardar referencias a widgets creados por el builder
        self.system_info_label = QLabel()
        self.safe_mode_checkbox = QCheckBox("Solo Lectura")
        self.safe_mode_checkbox.setChecked(True)
        self.safe_mode_checkbox.toggled.connect(self.on_safe_mode_changed)
        self.refresh_btn = QPushButton("🔄 Actualizar")
        self.refresh_btn.clicked.connect(self.refresh_disks)
    
    def setup_connections(self):
        """Configura las conexiones de señales"""
        self.disks_table.cellClicked.connect(self.handlers.on_cell_clicked)
        self.safe_mode_checkbox.toggled.connect(self.on_safe_mode_changed)
    
    def refresh_disks(self):
        """Actualiza la lista de discos"""
        self.handlers.refresh_disks()
    
    def on_disk_selection_changed(self):
        """Maneja el cambio de selección de disco"""
        self.handlers.on_disk_selection_changed()
    
    def _on_debounce_timeout(self):
        """Timeout del debounce para análisis pesado"""
        if self.pending_analysis:
            mountpoint = self.pending_analysis
            self.pending_analysis = None
            self._execute_analysis(mountpoint)
    
    def _schedule_heavy_analysis(self, mountpoint: str):
        """Programa un análisis pesado con debounce"""
        self.pending_analysis = mountpoint
        self.debounce_timer.start(500)
    
    def _cleanup_cache(self):
        """Limpia la caché SMART"""
        max_cache_size = 10
        if len(self._smart_cache) > max_cache_size:
            sorted_items = sorted(self._cache_priority.items(), key=lambda x: x[1])
            for device, _ in sorted_items[:len(sorted_items) - max_cache_size]:
                if device in self._smart_cache:
                    del self._smart_cache[device]
                if device in self._cache_priority:
                    del self._cache_priority[device]
    
    def on_analyze_and_organize(self, row):
        """Analiza y organiza el disco en la fila especificada"""
        self.handlers.on_analyze_and_organize(row)
    
    def update_selected_disk_info(self, mountpoint):
        """Actualiza la información del disco seleccionado"""
        current_theme = self.get_current_theme_name()
        self.update_selected_disk_info_with_theme(mountpoint, current_theme)
    
    def update_selected_disk_info_with_theme(self, mountpoint, theme_name):
        """Actualiza la información del disco con el tema especificado"""
        if not self.disk_manager:
            return
        
        disk_info = self.disk_manager.get_disk_by_mountpoint(mountpoint)
        if not disk_info:
            return
        
        # Actualizar información básica
        basic_info_label = self.analysis_widgets.get('basic_info_label')
        if basic_info_label:
            DiskInfoUpdater.update_basic_info(basic_info_label, disk_info, theme_name)
        
        # Obtener datos de salud
        health_data = self._get_health_data(disk_info)
        
        # Actualizar salud
        health_label = self.analysis_widgets.get('health_label')
        if health_label:
            DiskInfoUpdater.update_health_html(health_label, disk_info, health_data, theme_name)
        
        # Actualizar contenido
        content_label = self.analysis_widgets.get('content_label')
        if content_label:
            DiskInfoUpdater.update_content_info(content_label, disk_info, theme_name)
    
    def _get_health_data(self, disk_info: DiskInfo) -> dict:
        """Obtiene datos de salud del disco"""
        device = disk_info.device
        
        if device in self._smart_cache:
            return self._smart_cache[device]
        
        health_data = {
            'score': 85,
            'status': 'Saludable',
            'factors': [
                {'name': 'Temperatura', 'score': 90},
                {'name': 'Espacio Disponible', 'score': int(100 - disk_info.usage_percent)},
                {'name': 'Estado General', 'score': 85}
            ]
        }
        
        self._smart_cache[device] = health_data
        self._cache_priority[device] = self._cache_priority.get(device, 0) + 1
        
        return health_data
    
    def on_safe_mode_changed(self, enabled):
        """Maneja el cambio del modo seguro"""
        if self.disk_manager:
            self.disk_manager.set_safe_mode(enabled)
        status = "activado" if enabled else "desactivado"
        self.log_message(f"🛡️ Modo Seguro {status}")
    
    def apply_static_interface_styles(self, theme_name: str, colors: dict):
        """Aplica estilos estáticos de la interfaz"""
        self.styler.apply_static_interface_styles(self, theme_name, colors)
    
    def apply_compact_disk_viewer_styles(self, theme_name: str, colors: dict):
        """Aplica estilos compactos al visor de discos"""
        self.styler.apply_compact_disk_viewer_styles(self, theme_name, colors)
    
    def apply_theme_styles(self, theme_name: str):
        """Aplica todos los estilos del tema"""
        colors = ThemeManager.get_theme_colors(theme_name)
        self.styler.apply_theme_styles(self, theme_name, colors)
        self.apply_progress_bar_styles(theme_name)
        self.update_usage_progress_colors(theme_name)
    
    def apply_progress_bar_styles(self, theme_name: str):
        """Aplica estilos a las barras de progreso"""
        self.styler.apply_progress_bar_styles(self, theme_name)
    
    def update_usage_progress_colors(self, theme_name: str, usage_percent: float = None):
        """Actualiza los colores de las barras de uso"""
        self.styler.update_usage_progress_colors(self, theme_name, usage_percent)
    
    def get_themed_html_box(self, theme_name: str, box_type: str, title: str, content: str, icon: str = "") -> str:
        """Genera una caja HTML tematizada"""
        return self.styler.get_themed_html_box(theme_name, box_type, title, content, icon)
    
    def get_current_theme_name(self) -> str:
        """Obtiene el nombre del tema actual"""
        try:
            if self.disk_manager and hasattr(self.disk_manager, 'config'):
                return self.disk_manager.config.get('theme', 'dark')
        except:
            pass
        return 'dark'
    
    def get_themed_html_text(self, theme_name: str, content: str, bold: bool = False, color_type: str = "text_primary") -> str:
        """Genera texto HTML tematizado"""
        return self.styler.get_themed_html_text(theme_name, content, bold, color_type)
    
    def get_usage_color_by_percentage(self, usage_percent: float) -> str:
        """Obtiene el color según el porcentaje de uso"""
        return self.styler.get_usage_color_by_percentage(usage_percent)
    
    def on_analyze_disk(self):
        """Maneja el botón de analizar disco"""
        selected_path = self.get_selected_disk_path()
        if selected_path:
            self.analysis_requested.emit(selected_path)
            self.log_message(f"🔍 Análisis solicitado para: {selected_path}")
        else:
            QMessageBox.information(self, "Información", "Por favor selecciona un disco primero")
    
    def complete_analysis(self):
        """Completa el análisis actual"""
        self.log_message("✅ Análisis completado exitosamente")
    
    def log_message(self, message):
        """Agrega un mensaje al log"""
        log_display = self.analysis_widgets.get('log_display')
        if log_display:
            timestamp = QTimer().currentTime().toString("HH:mm:ss")
            log_display.append(f"[{timestamp}] {message}")
    
    def get_selected_disk_path(self) -> Optional[str]:
        """Obtiene la ruta del disco seleccionado"""
        return self.current_selection
    
    def is_safe_mode_enabled(self) -> bool:
        """Retorna si el modo seguro está habilitado"""
        return self.disk_manager.get_safe_mode_status() if self.disk_manager else True
    
    def _render_health_html(self, current_theme, disk_info, health_data) -> str:
        """Genera el HTML del estado de salud (método legacy, usar DiskInfoUpdater)"""
        return self.styler._render_health_html(current_theme, disk_info, health_data)
    
    def _execute_analysis(self, mountpoint: str):
        """Ejecuta el análisis pesado del disco"""
        try:
            self.log_message(f"🔍 Iniciando análisis profundo de: {mountpoint}")
            
            if self.disk_manager:
                self.disk_manager.analyze_directory(mountpoint)
            
            self.update_selected_disk_info(mountpoint)
            self.complete_analysis()
            
        except Exception as e:
            self.log_message(f"❌ Error en análisis: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error analizando {mountpoint}:\n{str(e)}")
