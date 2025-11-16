#!/usr/bin/env python3
"""
Visor de Discos y Particiones para el Organizador de Archivos
Interfaz visual consistente con el diseño principal de la aplicación
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


class DiskViewer(QWidget):
    """Widget principal para visualizar y gestionar discos del sistema"""
    
    # Señales para comunicación con la ventana principal
    disk_selected = pyqtSignal(str)  # Emite la ruta del disco seleccionado
    analysis_requested = pyqtSignal(str)  # Emite solicitud de análisis
    
    def __init__(self, parent=None, disk_manager=None):
        super().__init__(parent)
        # Usar la instancia compartida si se proporciona, sino None (se asignará después)
        self.disk_manager = disk_manager
        self.current_selection = None
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_disks)
        
        # Debounce timer para operaciones pesadas (solo análisis de archivos)
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self._on_debounce_timeout)
        self.pending_analysis = None
        
        # Cache local para datos SMART ya obtenidos
        self._smart_cache = {}
        self._cache_priority = {}  # Prioridad de cache por disco
        
        self.init_ui()
        self.setup_connections()
        # No hacer refresh_disks aquí si no hay disk_manager
        if self.disk_manager:
            self.refresh_disks()
        
        # Aplicar tema inicial
        try:
            initial_theme = self.get_current_theme_name()
            self.apply_theme_styles(initial_theme)
        except Exception as e:
            self.log_message(f"⚠️ Error aplicando tema inicial: {str(e)}")
        
        # Auto-refresh desactivado para mantener la selección del usuario
        # self.refresh_timer.start(30000)
    
    def init_ui(self):
        """Inicializa la interfaz de usuario con diseño ultra compacto y eficiente"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)  # SIN espaciado - log completamente pegado abajo
        main_layout.setContentsMargins(4, 4, 4, 0)  # SIN margen inferior - log pegado abajo
        
        # Establecer política de tamaño para evitar redimensionamiento automático
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setMinimumSize(930, 500)  # Reducido de 600 a 500 para más compacto
        
        # Header unificado con título y controles en la misma fila - ULTRA COMPACTO
        unified_header = QGroupBox("🖥️ INFORMACIÓN DEL SISTEMA")
        unified_header.setToolTip("🖥️ Muestra información en tiempo real del sistema: CPU, RAM, estado de seguridad y discos monitoreados")
        unified_header.setObjectName("system_info_group")
        unified_header.setMaximumHeight(35)  # Ultra compacto - reducido de 50 a 35
        unified_header.setMinimumHeight(30)  # Altura mínima ultra compacta - reducido de 40 a 30
        
        # Layout horizontal para título y controles en la misma fila
        unified_layout = QHBoxLayout(unified_header)
        unified_layout.setContentsMargins(2, 0, 2, 0)  # Márgenes ultra reducidos - SIN padding vertical
        unified_layout.setSpacing(4)  # Espaciado mínimo
        
        # Información del sistema a la izquierda
        self.system_info_label = QLabel("Cargando información del sistema...")
        self.system_info_label.setObjectName("system_info_label")
        self.system_info_label.setWordWrap(True)
        self.system_info_label.setMaximumHeight(25)  # Altura ultra compacta - reducido de 30 a 25
        unified_layout.addWidget(self.system_info_label)
        
        # Espacio para empujar controles a la derecha
        unified_layout.addStretch()
        
        # Controles de modo seguro compactos
        safe_mode_label = QLabel("🛡️ Modo Seguro:")
        safe_mode_label.setToolTip("🛡️ Configuración de seguridad para proteger los datos del sistema")
        safe_mode_label.setObjectName("safe_mode_label")
        safe_mode_label.setMaximumHeight(18)  # Ultra compacto - reducido de 20 a 18
        unified_layout.addWidget(safe_mode_label)
        
        self.safe_mode_checkbox = QCheckBox("Solo Lectura")
        self.safe_mode_checkbox.setToolTip("🛡️ Cuando está activado, solo permite análisis y visualización sin modificar archivos")
        self.safe_mode_checkbox.setChecked(True)
        self.safe_mode_checkbox.setObjectName("safe_mode_checkbox")
        self.safe_mode_checkbox.setMaximumHeight(18)  # Ultra compacto - reducido de 20 a 18
        self.safe_mode_checkbox.toggled.connect(self.on_safe_mode_changed)
        unified_layout.addWidget(self.safe_mode_checkbox)
        
        # Botón de refresh compacto
        self.refresh_btn = QPushButton("🔄 Actualizar")
        self.refresh_btn.setToolTip("🔄 Actualiza la información de discos")
        self.refresh_btn.setObjectName("refresh_btn")
        self.refresh_btn.clicked.connect(self.refresh_disks)
        self.refresh_btn.setFixedHeight(20)  # Ultra compacto - reducido de 24 a 20
        self.refresh_btn.setFixedWidth(90)  # Ancho fijo compacto
        unified_layout.addWidget(self.refresh_btn)
        
        main_layout.addWidget(unified_header)
        
        # ===== TABLA DE DISCOS DIRECTAMENTE =====
        # Tabla de discos - DISEÑO PROFESIONAL MEJORADO
        self.disks_table = QTableWidget()
        self.disks_table.setColumnCount(8)
        self.disks_table.setHorizontalHeaderLabels([
            "💿 Unidad", "📁 Punto de Montaje", "💾 Total", "📊 Usado", 
            "🆓 Libre", "📈 % Uso", "🛡️ Sistema", "🔍"
        ])
        
        # 🚀 OPTIMIZACIÓN: Tabla compacta y ajustable automáticamente
        self.disks_table.verticalHeader().setDefaultSectionSize(45)  # Reducido para filas más compactas
        self.disks_table.setMinimumHeight(120)  # Mínimo para header + 1 fila
        self.disks_table.setMaximumHeight(600)  # Máximo más alto para más discos
        self.disks_table.setRowCount(0)  # Sin filas fijas - se ajustará dinámicamente
        self.disks_table.setAlternatingRowColors(True)
        self.disks_table.setShowGrid(True)
        self.disks_table.setGridStyle(Qt.PenStyle.SolidLine)
        # Los estilos se aplican automáticamente via themes.py
        
        # Configurar tabla
        header = self.disks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)      # Unidad
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)    # Punto de Montaje
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Total
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Usado
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Libre
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)      # % Uso
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)      # Sistema
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)      # Botón independiente
        
        # Establecer anchos fijos para columnas críticas
        self.disks_table.setColumnWidth(0, 80)   # Unidad
        self.disks_table.setColumnWidth(5, 80)   # % Uso
        self.disks_table.setColumnWidth(6, 100)  # Sistema - Solo texto
        self.disks_table.setColumnWidth(7, 130)  # Botón independiente - Ancho suficiente para "Analizar"
        
        # Añadir tooltips a los headers de la tabla
        header.setToolTip("💿 Unidad: Letra de la unidad del disco\n"
                         "📁 Punto de Montaje: Ruta donde está montado el disco\n"
                         "💾 Total: Espacio total del disco\n"
                         "📊 Usado: Espacio utilizado actualmente\n"
                         "🆓 Libre: Espacio disponible\n"
                         "📈 % Uso: Porcentaje de espacio utilizado\n"
                         "🛡️ Sistema: Indica si es unidad del sistema\n"
                         "🔍 Botón para analizar y organizar el disco")
        
        # La tabla usará los estilos del tema automáticamente
        self.disks_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        main_layout.addWidget(self.disks_table)
        
        # ===== PANEL DE ANÁLISIS DEL DISCO SELECCIONADO CON LAZY LOADING =====
        self.analysis_group = QGroupBox("🔍 ANÁLISIS DEL DISCO SELECCIONADO")
        self.analysis_group.setToolTip("🔍 Panel de análisis detallado que se muestra cuando seleccionas un disco específico")
        self.analysis_group.setObjectName("analysis_group")
        
        # Configurar política de tamaño para evitar redimensionamiento
        self.analysis_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.analysis_group.setMinimumHeight(400)
        # Remover altura máxima para permitir scroll
        
        # Cargar panel de análisis inmediatamente (sin lazy loading)
        analysis_layout = QVBoxLayout(self.analysis_group)
        analysis_layout.setSpacing(12)
        
        # ===== DISEÑO CON TÍTULOS FIJOS Y ALINEADOS =====
        # Fila de títulos fijos - todos a la misma altura
        headers_row = QHBoxLayout()
        headers_row.setSpacing(20)
        headers_row.setContentsMargins(0, 0, 0, 0)
        
        # Títulos fijos para cada columna
        self.basic_header = QLabel("💾 INFORMACIÓN BÁSICA")
        self.basic_header.setObjectName("card_header")
        self.basic_header.setFixedHeight(50)  # Altura aumentada para mejor legibilidad
        self.basic_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        headers_row.addWidget(self.basic_header)
        
        self.health_header = QLabel("🩺 ESTADO Y SALUD")
        self.health_header.setObjectName("card_header")
        self.health_header.setFixedHeight(50)  # Altura aumentada para mejor legibilidad
        self.health_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        headers_row.addWidget(self.health_header)
        
        self.content_header = QLabel("📁 CONTENIDO")
        self.content_header.setObjectName("card_header")
        self.content_header.setFixedHeight(50)  # Altura aumentada para mejor legibilidad
        self.content_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        headers_row.addWidget(self.content_header)
        
        analysis_layout.addLayout(headers_row)
        
        # Fila de contenido - 3 tarjetas en la misma fila
        content_row = QHBoxLayout()
        content_row.setSpacing(20)
        content_row.setContentsMargins(0, 0, 0, 0)
        
        # 1. TARJETA DE INFORMACIÓN BÁSICA (COLUMNA 1) - EXPANDIDA
        self.basic_card = QFrame()
        self.basic_card.setObjectName("analysis_card_large")
        self.basic_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.basic_card.setMinimumHeight(250)  # Reducido para pantallas 1080p
        basic_card_layout = QVBoxLayout(self.basic_card)
        basic_card_layout.setSpacing(8)
        basic_card_layout.setContentsMargins(0, 0, 0, 0)  # Sin márgenes, el título está fuera
        
        # Contenido de información básica envuelto en un único bloque consistente
        self.basic_content_frame = QFrame()
        self.basic_content_frame.setObjectName("analysis_inner_frame")
        basic_inner_layout = QVBoxLayout(self.basic_content_frame)
        basic_inner_layout.setSpacing(4)
        basic_inner_layout.setContentsMargins(12, 8, 12, 8)
        
        self.basic_info_label = QLabel("Selecciona un disco para ver su información")
        self.basic_info_label.setToolTip("💾 Información fundamental del disco: sistema de archivos, tipo y estado")
        self.basic_info_label.setObjectName("analysis_content_label")
        self.basic_info_label.setWordWrap(True)
        self.basic_info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        basic_inner_layout.addWidget(self.basic_info_label)
        
        basic_card_layout.addWidget(self.basic_content_frame)
        content_row.addWidget(self.basic_card)
        
        # 2. TARJETA DE ESTADO Y SALUD (COLUMNA 2) - EXPANDIDA
        self.health_card = QFrame()
        self.health_card.setObjectName("analysis_card_large")
        self.health_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.health_card.setMinimumHeight(250)  # Reducido para pantallas 1080p
        health_card_layout = QVBoxLayout(self.health_card)
        health_card_layout.setSpacing(8)
        health_card_layout.setContentsMargins(0, 0, 0, 0)  # Sin márgenes, el título está fuera
        
        # Contenido de estado envuelto en un único bloque consistente
        self.health_content_frame = QFrame()
        self.health_content_frame.setObjectName("analysis_inner_frame")
        health_inner_layout = QVBoxLayout(self.health_content_frame)
        health_inner_layout.setSpacing(4)
        health_inner_layout.setContentsMargins(12, 8, 12, 8)
        
        self.health_status_label = QLabel("Estado: No seleccionado")
        self.health_status_label.setToolTip("🩺 Estado actual del disco y recomendaciones de mantenimiento")
        self.health_status_label.setObjectName("analysis_content_label")
        self.health_status_label.setWordWrap(True)
        self.health_status_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        health_inner_layout.addWidget(self.health_status_label)
        
        health_card_layout.addWidget(self.health_content_frame)
        content_row.addWidget(self.health_card)
        
        # 3. TARJETA DE CONTENIDO Y ARCHIVOS (COLUMNA 3) - EXPANDIDA
        self.content_card = QFrame()
        self.content_card.setObjectName("analysis_card_large")
        self.content_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.content_card.setMinimumHeight(250)  # Reducido para pantallas 1080p
        content_card_layout = QVBoxLayout(self.content_card)
        content_card_layout.setSpacing(8)
        content_card_layout.setContentsMargins(0, 0, 0, 0)  # Sin márgenes, el título está fuera
        
        # Contenido del análisis envuelto en un único bloque consistente
        self.content_content_frame = QFrame()
        self.content_content_frame.setObjectName("analysis_inner_frame")
        content_inner_layout = QVBoxLayout(self.content_content_frame)
        content_inner_layout.setSpacing(4)
        content_inner_layout.setContentsMargins(12, 8, 12, 8)

        self.content_info_label = QLabel("Contenido: No seleccionado")
        self.content_info_label.setToolTip("📁 Análisis del contenido del disco: archivos, carpetas y tipos")
        self.content_info_label.setObjectName("analysis_content_label")
        self.content_info_label.setWordWrap(True)
        self.content_info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        content_inner_layout.addWidget(self.content_info_label)

        content_card_layout.addWidget(self.content_content_frame)
        content_row.addWidget(self.content_card)
        
        # Añadir la fila de contenido
        analysis_layout.addLayout(content_row)
        
        # Segunda fila: Barra de progreso para análisis
        self.analysis_progress = QProgressBar()
        self.analysis_progress.setObjectName("analysis_progress")
        self.analysis_progress.setToolTip("📊 Muestra el progreso del análisis del disco seleccionado")
        self.analysis_progress.setVisible(False)
        analysis_layout.addWidget(self.analysis_progress)
        
        # ===== CREAR SCROLL AREA PARA EL PANEL DE ANÁLISIS =====
        # Crear QScrollArea para el panel de análisis (solución para pantallas 1080p)
        self.analysis_scroll_area = QScrollArea()
        self.analysis_scroll_area.setWidget(self.analysis_group)
        self.analysis_scroll_area.setWidgetResizable(True)
        self.analysis_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.analysis_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.analysis_scroll_area.setMinimumHeight(400)  # Altura mínima visible
        self.analysis_scroll_area.setMaximumHeight(500)  # Altura máxima para pantallas 1080p
        self.analysis_scroll_area.setObjectName("analysis_scroll_area")
        
        # Aplicar estilos al scroll area para que se vea bien con el tema
        self.analysis_scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid var(--border-color);
                border-radius: 8px;
                background-color: var(--background);
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: var(--surface);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: var(--primary);
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: var(--accent);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        main_layout.addWidget(self.analysis_scroll_area)
        
        # ===== TARJETA DE ESTADÍSTICAS I/O (MOVIDA A LA SECCIÓN DE ESPACIO) =====
        # Las métricas SMART se moverán junto a TOTAL USADO LIBRE
        
        # ===== TARJETA DE ESPACIO DE ANCHO COMPLETO =====
        space_card_full = QFrame()
        space_card_full.setObjectName("space_card_full")
        space_card_full.setMaximumHeight(75)  # Reducido de 90 a 75px
        space_card_full.setMinimumHeight(65)  # Reducido de 80 a 65px
        space_card_full.setStyleSheet("""
            QFrame {
                background-color: var(--card-bg);
                border: 1px solid var(--border-color);
                border-radius: 8px;  /* Reducido de 12px a 8px */
                padding: 4px;  /* Reducido de 8px a 4px */
                margin: 2px 0 0 0;  /* SIN margen inferior - log pegado abajo */
            }
            QFrame:hover {
                border: 2px solid var(--accent-color);
            }
        """)
        
        space_card_layout = QHBoxLayout(space_card_full)
        space_card_layout.setSpacing(8)  # Espaciado ultra reducido de 20 a 8
        space_card_layout.setContentsMargins(2, 0, 2, 0)  # SIN padding vertical, solo lateral mínimo
        
        # Barra de progreso de uso
        progress_section = QVBoxLayout()
        progress_section.setSpacing(2)  # Espaciado ultra reducido de 6 a 2
        progress_section.setContentsMargins(0, 0, 0, 0)  # SIN paddings
        
        progress_label = QLabel("📊 Porcentaje de Uso:")
        progress_label.setObjectName("space_section_label")
        progress_label.setStyleSheet("""
            QLabel {
                color: var(--accent-color);
                font-weight: bold;
                font-size: 12px;
                text-align: center;
            }
        """)
        progress_section.addWidget(progress_label)
        
        # Barra de progreso mejorada
        self.usage_progress_bar = QProgressBar()
        self.usage_progress_bar.setObjectName("usage_progress_bar")
        self.usage_progress_bar.setRange(0, 100)
        self.usage_progress_bar.setValue(0)
        self.usage_progress_bar.setToolTip("📊 Barra visual del porcentaje de uso del disco")
        self.usage_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid var(--border-color);
                border-radius: 10px;
                text-align: center;
                font-weight: bold;
                font-size: 12px;
                min-height: 16px;
                max-height: 16px;
                background-color: var(--bg-color);
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 var(--accent-color), 
                    stop:1 var(--accent-color));
                border-radius: 8px;
            }
        """)
        progress_section.addWidget(self.usage_progress_bar)
        
        # Porcentaje de uso eliminado - la barra de progreso es suficiente
        
        space_card_layout.addLayout(progress_section)
        
        # Información de tamaños y métricas SMART en HORIZONTAL (más compacto)
        sizes_section = QHBoxLayout()
        sizes_section.setSpacing(6)  # Espaciado ultra reducido de 15 a 6
        sizes_section.setContentsMargins(0, 0, 0, 0)  # SIN paddings
        
        # TOTAL
        total_layout = QVBoxLayout()
        total_layout.setSpacing(1)  # Espaciado ultra reducido de 4 a 1
        total_layout.setContentsMargins(0, 0, 0, 0)  # SIN paddings
        total_label = QLabel("💾 TOTAL")
        total_label.setObjectName("space_section_label")
        total_label.setStyleSheet("""
            QLabel {
                color: var(--accent-color);
                font-weight: bold;
                font-size: 11px;
                text-align: center;
            }
        """)
        total_layout.addWidget(total_label)
        
        self.total_size_label = QLabel("0 GB")
        self.total_size_label.setObjectName("space_value_label")
        self.total_size_label.setStyleSheet("""
            QLabel {
                color: var(--text-color);
                font-weight: bold;
                font-size: 12px;
                text-align: center;
                padding: 4px 8px;
                background-color: var(--bg-color);
                border-radius: 4px;
                border: 1px solid var(--border-color);
            }
        """)
        total_layout.addWidget(self.total_size_label)
        sizes_section.addLayout(total_layout)
        
        # USADO
        used_layout = QVBoxLayout()
        used_layout.setSpacing(1)  # Espaciado ultra reducido de 4 a 1
        used_layout.setContentsMargins(0, 0, 0, 0)  # SIN paddings
        used_label = QLabel("📊 USADO")
        used_label.setObjectName("space_section_label")
        used_label.setStyleSheet("""
            QLabel {
                color: var(--error-color, #e74c3c);
                font-weight: bold;
                font-size: 11px;
                text-align: center;
            }
        """)
        used_layout.addWidget(used_label)
        
        self.used_size_label = QLabel("0 GB")
        self.used_size_label.setObjectName("space_value_label")
        self.used_size_label.setStyleSheet("""
            QLabel {
                color: var(--text-color);
                font-weight: bold;
                font-size: 12px;
                text-align: center;
                padding: 4px 8px;
                background-color: var(--bg-color);
                border-radius: 4px;
                border: 1px solid var(--border-color);
            }
        """)
        used_layout.addWidget(self.used_size_label)
        sizes_section.addLayout(used_layout)
        
        # LIBRE
        free_layout = QVBoxLayout()
        free_layout.setSpacing(1)  # Espaciado ultra reducido de 4 a 1
        free_layout.setContentsMargins(0, 0, 0, 0)  # SIN paddings
        free_label = QLabel("💚 LIBRE")
        free_label.setObjectName("space_section_label")
        free_label.setStyleSheet("""
            QLabel {
                color: var(--success-color, #27ae60);
                font-weight: bold;
                font-size: 11px;
                text-align: center;
            }
        """)
        free_layout.addWidget(free_label)
        
        self.free_size_label = QLabel("0 GB")
        self.free_size_label.setObjectName("space_value_label")
        self.free_size_label.setStyleSheet("""
            QLabel {
                color: var(--text-color);
                font-weight: bold;
                font-size: 12px;
                text-align: center;
                padding: 4px 8px;
                background-color: var(--bg-color);
                border-radius: 4px;
                border: 1px solid var(--border-color);
            }
        """)
        free_layout.addWidget(self.free_size_label)
        sizes_section.addLayout(free_layout)
        
        # ===== MÉTRICAS SMART INTEGRADAS =====
        # LECTURAS
        reads_layout = QVBoxLayout()
        reads_layout.setSpacing(1)  # Espaciado ultra reducido de 4 a 1
        reads_layout.setContentsMargins(0, 0, 0, 0)  # SIN paddings
        self.reads_label = QLabel("📖 LECTURAS")
        self.reads_label.setObjectName("io_section_label")
        reads_layout.addWidget(self.reads_label)
        
        self.read_count_label = QLabel("0")
        self.read_count_label.setObjectName("io_value_label")
        reads_layout.addWidget(self.read_count_label)
        sizes_section.addLayout(reads_layout)
        
        # ESCRITURAS
        writes_layout = QVBoxLayout()
        writes_layout.setSpacing(1)  # Espaciado ultra reducido de 4 a 1
        writes_layout.setContentsMargins(0, 0, 0, 0)  # SIN paddings
        self.writes_label = QLabel("✍️ ESCRITURAS")
        self.writes_label.setObjectName("io_section_label")
        writes_layout.addWidget(self.writes_label)
        
        self.write_count_label = QLabel("0")
        self.write_count_label.setObjectName("io_value_label")
        writes_layout.addWidget(self.write_count_label)
        sizes_section.addLayout(writes_layout)
        
        # DATOS LEÍDOS
        read_data_layout = QVBoxLayout()
        read_data_layout.setSpacing(1)  # Espaciado ultra reducido de 4 a 1
        read_data_layout.setContentsMargins(0, 0, 0, 0)  # SIN paddings
        self.read_data_header_label = QLabel("📥 DATOS LEÍDOS")
        self.read_data_header_label.setObjectName("io_section_label")
        read_data_layout.addWidget(self.read_data_header_label)
        
        self.read_data_label = QLabel("0 GB")
        self.read_data_label.setObjectName("io_value_label")
        read_data_layout.addWidget(self.read_data_label)
        sizes_section.addLayout(read_data_layout)
        
        # DATOS ESCRITOS
        write_data_layout = QVBoxLayout()
        write_data_layout.setSpacing(1)  # Espaciado ultra reducido de 4 a 1
        write_data_layout.setContentsMargins(0, 0, 0, 0)  # SIN paddings
        self.write_data_header_label = QLabel("📤 DATOS ESCRITOS")
        self.write_data_header_label.setObjectName("io_section_label")
        write_data_layout.addWidget(self.write_data_header_label)
        
        self.write_data_label = QLabel("0 GB")
        self.write_data_label.setObjectName("io_value_label")
        write_data_layout.addWidget(self.write_data_label)
        sizes_section.addLayout(write_data_layout)
        
        # TEMPERATURA
        temp_layout = QVBoxLayout()
        temp_layout.setSpacing(1)  # Espaciado ultra reducido de 4 a 1
        temp_layout.setContentsMargins(0, 0, 0, 0)  # SIN paddings
        temp_label_header = QLabel("🌡️ TEMPERATURA")
        temp_label_header.setObjectName("io_section_label")
        temp_layout.addWidget(temp_label_header)
        
        self.temperature_label = QLabel("--")
        self.temperature_label.setObjectName("io_value_label")
        temp_layout.addWidget(self.temperature_label)
        sizes_section.addLayout(temp_layout)
        
        # HORAS DE ENCENDIDO
        hours_layout = QVBoxLayout()
        hours_layout.setSpacing(1)  # Espaciado ultra reducido de 4 a 1
        hours_layout.setContentsMargins(0, 0, 0, 0)  # SIN paddings
        hours_label_header = QLabel("⏰ HORAS ENCENDIDO")
        hours_label_header.setObjectName("io_section_label")
        hours_layout.addWidget(hours_label_header)
        
        self.power_hours_label = QLabel("--")
        self.power_hours_label.setObjectName("io_value_label")
        hours_layout.addWidget(self.power_hours_label)
        sizes_section.addLayout(hours_layout)
        
        # CICLOS DE ENCENDIDO
        cycles_layout = QVBoxLayout()
        cycles_layout.setSpacing(1)  # Espaciado ultra reducido de 4 a 1
        cycles_layout.setContentsMargins(0, 0, 0, 0)  # SIN paddings
        cycles_label_header = QLabel("🔄 CICLOS")
        cycles_label_header.setObjectName("io_section_label")
        cycles_layout.addWidget(cycles_label_header)
        
        self.power_cycles_label = QLabel("--")
        self.power_cycles_label.setObjectName("io_value_label")
        cycles_layout.addWidget(self.power_cycles_label)
        sizes_section.addLayout(cycles_layout)
        
        space_card_layout.addLayout(sizes_section)
        
        # Añadir stretch para centrar el contenido
        space_card_layout.addStretch()
        
        main_layout.addWidget(space_card_full)
        
        # Log de operaciones - PEGADO ABAJO DEL TODO SIN MÁRGENES
        log_layout = QHBoxLayout()
        log_layout.setContentsMargins(0, 0, 0, 0)  # SIN márgenes
        log_layout.setSpacing(0)  # SIN espaciado
        
        self.log_text = QTextEdit()
        self.log_text.setToolTip("📝 Historial de operaciones, errores y mensajes informativos del sistema")
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(40)  # Altura fija
        self.log_text.setMinimumHeight(40)  # Altura mínima fija
        self.log_text.setObjectName("log_text")
        log_layout.addWidget(self.log_text)
        
        main_layout.addLayout(log_layout)
        
        # Inicialmente ocultar el scroll area del análisis
        self.analysis_scroll_area.setVisible(False)
        
        # Configurar el widget principal para pantallas 1080p
        self.setMinimumHeight(400)  # Reducido de 600 a 400 para más compacto
        self.setMaximumHeight(16777215)  # Valor máximo de Qt
        
        # Tabla dinámica: solo mostrar discos reales
        self.disks_table.setRowCount(0)
    
    def setup_connections(self):
        """Configura las conexiones de señales"""
        self.disks_table.itemSelectionChanged.connect(self.on_disk_selection_changed)
    
    def refresh_disks(self):
        """Actualiza la información de todos los discos"""
        try:
            self.log_message("🔄 Actualizando información de discos...")
            
            # Obtener discos
            disks = self.disk_manager.get_all_disks()
            
            if not disks:
                self.log_message("⚠️ No se encontraron discos disponibles")
                # Tabla dinámica: no crear filas vacías
                self.disks_table.setRowCount(0)
                return
            
            # Limpiar tabla
            self.disks_table.setRowCount(0)
            
            # Llenar tabla con discos reales
            for i, disk in enumerate(disks):
                try:
                    # Verificar que el disco esté disponible
                    if not os.path.exists(disk.mountpoint):
                        continue  # Saltar discos no disponibles
                    
                    self.disks_table.insertRow(i)
                    
                    # Unidad
                    unit_item = QTableWidgetItem(f"{disk.drive_letter}:" if disk.drive_letter else "N/A")
                    unit_item.setData(Qt.ItemDataRole.UserRole, disk.mountpoint)
                    unit_item.setToolTip(f"💿 Unidad del disco: {disk.drive_letter or 'No disponible'}")
                    self.disks_table.setItem(i, 0, unit_item)
                    
                    # Punto de montaje
                    mount_item = QTableWidgetItem(disk.mountpoint)
                    mount_item.setToolTip(f"📁 Punto de montaje: {disk.mountpoint}")
                    self.disks_table.setItem(i, 1, mount_item)
                    
                    # Tamaño total
                    total_item = QTableWidgetItem(self.disk_manager.format_size(disk.total_size))
                    total_item.setToolTip(f"💾 Espacio total del disco: {self.disk_manager.format_size(disk.total_size)}")
                    self.disks_table.setItem(i, 2, total_item)
                    
                    # Tamaño usado
                    used_item = QTableWidgetItem(self.disk_manager.format_size(disk.used_size))
                    used_item.setToolTip(f"📊 Espacio utilizado: {self.disk_manager.format_size(disk.used_size)}")
                    self.disks_table.setItem(i, 3, used_item)
                    
                    # Tamaño libre
                    free_item = QTableWidgetItem(self.disk_manager.format_size(disk.free_size))
                    free_item.setToolTip(f"🆓 Espacio libre disponible: {self.disk_manager.format_size(disk.free_size)}")
                    self.disks_table.setItem(i, 4, free_item)
                    
                    # Porcentaje de uso
                    usage_item = QTableWidgetItem(f"{disk.usage_percent:.1f}%")
                    # Color según el porcentaje usando SOLO colores del tema
                    color = self.get_usage_color_by_percentage(disk.usage_percent)
                    usage_item.setBackground(QColor(color))
                    
                    if disk.usage_percent > 90:
                        usage_item.setToolTip(f"📈 CRÍTICO: {disk.usage_percent:.1f}% del disco está lleno. ¡Libera espacio urgentemente!")
                    elif disk.usage_percent > 80:
                        usage_item.setToolTip(f"📈 ALTO: {disk.usage_percent:.1f}% del disco está lleno. Considera liberar espacio.")
                    elif disk.usage_percent > 70:
                        usage_item.setToolTip(f"📈 MODERADO: {disk.usage_percent:.1f}% del disco está lleno.")
                    else:
                        usage_item.setToolTip(f"📈 ÓPTIMO: {disk.usage_percent:.1f}% del disco está lleno. Espacio suficiente disponible.")
                    self.disks_table.setItem(i, 5, usage_item)
                    
                    # Es unidad del sistema - Solo texto
                    system_item = QTableWidgetItem("🛡️ Sí" if disk.is_system_drive else "✅ No")
                    # Usar colores del tema para unidad del sistema
                    try:
                        colors = ThemeManager.get_theme_colors(self.get_current_theme_name())
                        system_color = colors['error'] if disk.is_system_drive else colors['success']
                        system_item.setBackground(QColor(system_color))
                    except:
                        # Fallback básico si hay error
                        system_item.setBackground(QColor("#e74c3c" if disk.is_system_drive else "#27ae60"))
                    
                    if disk.is_system_drive:
                        system_item.setToolTip("🛡️ UNIDAD DEL SISTEMA: Contiene archivos críticos del sistema. ¡Manipular con precaución!")
                    else:
                        system_item.setToolTip("✅ DISCO DE DATOS: Disco seguro para organizar y gestionar archivos")
                    self.disks_table.setItem(i, 6, system_item)
                    
                    # Botón de acción independiente - Optimizado para filas compactas
                    action_widget = QWidget()
                    action_layout = QHBoxLayout(action_widget)
                    action_layout.setContentsMargins(2, 8, 2, 8)  # Padding vertical reducido para filas compactas
                    action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centrar el botón
                    
                    select_btn = QPushButton("🔍 Analizar")
                    select_btn.setToolTip(f"🔍 Analiza el disco {disk.mountpoint} y permite organizar archivos por categorías")
                    select_btn.setObjectName("select_btn")
                    select_btn.setFixedHeight(28)  # Altura reducida para filas compactas
                    select_btn.setFixedWidth(120)  # Ancho fijo para ajuste perfecto
                    select_btn.clicked.connect(self.create_analyze_handler(i))
                    action_layout.addWidget(select_btn)
                    
                    self.disks_table.setCellWidget(i, 7, action_widget)
                    
                except Exception as disk_error:
                    self.log_message(f"⚠️ Error al procesar disco {i}: {str(disk_error)}")
                    continue
            
            # 🚀 OPTIMIZACIÓN: Ajustar altura de tabla automáticamente
            self.adjust_table_height()
            
            # Actualizar información del sistema
            self.update_system_info()
        except Exception as e:
            error_msg = f"❌ Error al actualizar discos: {str(e)}"
            self.log_message(error_msg)
            QMessageBox.critical(
                self,
                "Error",
                f"Error al actualizar la información de discos:\n{str(e)}\n\n"
                "La aplicación continuará funcionando con la información anterior."
            )
            return

        # Prefetch asíncrono de SMART para discos visibles (calienta la caché)
        try:
            visible_paths = []
            for row in range(self.disks_table.rowCount()):
                item = self.disks_table.item(row, 1)
                if item:
                    path = item.text()
                    if path and os.path.exists(path) and path not in self._smart_cache:
                        visible_paths.append(path)
            if visible_paths:
                self.disk_manager.prefetch_smart_for_disks(visible_paths)
                # Marcar como prioridad media para prefetch
                for path in visible_paths:
                    if path not in self._cache_priority:
                        self._cache_priority[path] = 50
                self.log_message(f"🔄 Prefetch SMART iniciado para {len(visible_paths)} discos")
        except Exception as e:
            # No crítico, continuar
            self.log_message(f"ℹ️ Prefetch SMART no realizado: {e}")

        available_disks = self.disks_table.rowCount()
        self.log_message(f"✅ Información actualizada. {available_disks} discos reales en la tabla.")
        
        # Seleccionar automáticamente el primer disco si hay discos disponibles
        if available_disks > 0:
            self.disks_table.selectRow(0)
            # Obtener el mountpoint del primer disco y actualizar la información
            first_disk_item = self.disks_table.item(0, 1)  # Columna de mountpoint
            if first_disk_item:
                first_mountpoint = first_disk_item.text()
                self.update_selected_disk_info(first_mountpoint)
                self.log_message(f"🔍 Disco seleccionado automáticamente: {first_mountpoint}")
    
    def _fill_empty_row(self, row_index: int):
        """Llena una fila vacía con información de placeholder para mantener el layout"""
        try:
            # Unidad
            unit_item = QTableWidgetItem("---")
            unit_item.setToolTip("💿 Fila reservada para futuros discos")
            self.disks_table.setItem(row_index, 0, unit_item)
            
            # Punto de montaje
            mount_item = QTableWidgetItem("Disponible")
            mount_item.setToolTip("📁 Espacio reservado para nuevos discos")
            self.disks_table.setItem(row_index, 1, mount_item)
            
            # Tamaño total
            total_item = QTableWidgetItem("---")
            total_item.setToolTip("💾 Tamaño no disponible")
            self.disks_table.setItem(row_index, 2, total_item)
            
            # Tamaño usado
            used_item = QTableWidgetItem("---")
            used_item.setToolTip("📊 Uso no disponible")
            self.disks_table.setItem(row_index, 3, used_item)
            
            # Tamaño libre
            free_item = QTableWidgetItem("---")
            free_item.setToolTip("🆓 Espacio libre no disponible")
            self.disks_table.setItem(row_index, 4, free_item)
            
            # Porcentaje de uso
            usage_item = QTableWidgetItem("---")
            try:
                colors = ThemeManager.get_theme_colors(self.get_current_theme_name())
                usage_item.setBackground(QColor(colors['border']))
            except:
                usage_item.setBackground(QColor("#bdc3c7"))
            usage_item.setToolTip("📈 Porcentaje no disponible")
            self.disks_table.setItem(row_index, 5, usage_item)
            
            # Es unidad del sistema - Solo texto (deshabilitado)
            system_item = QTableWidgetItem("---")
            try:
                colors = ThemeManager.get_theme_colors(self.get_current_theme_name())
                system_item.setBackground(QColor(colors['border']))
            except:
                system_item.setBackground(QColor("#bdc3c7"))
            system_item.setToolTip("🛡️ Estado no disponible")
            self.disks_table.setItem(row_index, 6, system_item)
            
            # Botón de acción independiente (deshabilitado)
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 14, 2, 14)  # Padding vertical aumentado para centrado perfecto
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centrar el botón
            
            select_btn = QPushButton("⏳ N/A")
            select_btn.setToolTip("⏳ Esta fila está reservada para futuros discos")
            select_btn.setObjectName("select_btn")
            select_btn.setEnabled(False)
            select_btn.setFixedHeight(32)  # Altura ajustada para celda
            select_btn.setFixedWidth(120)  # Ancho fijo para consistencia
            select_btn.setProperty("styleClass", "disabled")  # Usa color disabled del tema
            action_layout.addWidget(select_btn)
            
            self.disks_table.setCellWidget(row_index, 7, action_widget)
            
        except Exception as e:
            self.log_message(f"⚠️ Error al crear fila vacía {row_index}: {str(e)}")
    
    def _fill_empty_rows(self, count: int):
        """Llena múltiples filas vacías"""
        for i in range(count):
            self._fill_empty_row(i)
    
    def adjust_table_height(self):
        """🚀 OPTIMIZACIÓN: Ajusta automáticamente la altura de la tabla según el contenido"""
        try:
            row_count = self.disks_table.rowCount()
            if row_count == 0:
                # Sin datos, altura mínima
                self.disks_table.setFixedHeight(120)
                return
            
            # Calcular altura óptima
            header_height = self.disks_table.horizontalHeader().height()
            row_height = self.disks_table.verticalHeader().defaultSectionSize()
            
            # Altura total = header + (filas * altura_fila) + margen
            optimal_height = header_height + (row_count * row_height) + 10
            
            # Aplicar límites
            min_height = 120
            max_height = 600
            
            final_height = max(min_height, min(optimal_height, max_height))
            
            # Aplicar altura calculada
            self.disks_table.setFixedHeight(final_height)
            
            self.log_message(f"📏 Tabla ajustada: {row_count} filas, altura {final_height}px")
            
        except Exception as e:
            self.log_message(f"⚠️ Error ajustando altura de tabla: {e}")
            # Fallback a altura fija
            self.disks_table.setFixedHeight(300)
    
    def update_system_info(self):
        """Actualiza la información del sistema"""
        try:
            import psutil
            
            # Información del sistema - COMPACTA
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Texto compacto en una sola línea
            system_text = f"""🖥️ <b>Sistema:</b> CPU: {cpu_percent:.1f}% | RAM: {memory.percent:.1f}% ({psutil._common.bytes2human(memory.used)}/{psutil._common.bytes2human(memory.total)}) | Modo Seguro: {'🛡️ ON' if self.disk_manager.get_safe_mode_status() else '⚠️ OFF'} | Discos: {self.disks_table.rowCount()}"""
            
            self.system_info_label.setText(system_text)
            
        except Exception as e:
            self.system_info_label.setText(f"❌ Error al obtener información del sistema: {str(e)}")
    
    def create_analyze_handler(self, row):
        """Crea un handler para el botón de análisis de una fila específica"""
        def handler():
            self.on_analyze_and_organize(row)
        return handler
    
    def on_disk_selection_changed(self):
        """Maneja el cambio de selección en la tabla de discos"""
        current_row = self.disks_table.currentRow()
        if current_row >= 0:
            mountpoint = self.disks_table.item(current_row, 1).text()
            self.current_selection = mountpoint
            
            # Actualización inmediata de la UI básica
            self.update_selected_disk_info(mountpoint)
            
            # Mostrar el panel de análisis sin redimensionar la ventana
            if not self.analysis_scroll_area.isVisible():
                self.analysis_scroll_area.setVisible(True)
                # Forzar actualización del layout sin cambiar el tamaño de la ventana
                self.updateGeometry()
        else:
            self.current_selection = None
            if self.analysis_scroll_area.isVisible():
                self.analysis_scroll_area.setVisible(False)
                # Forzar actualización del layout sin cambiar el tamaño de la ventana
                self.updateGeometry()
    
    def _on_debounce_timeout(self):
        """Ejecuta análisis pesado después del debounce (solo para operaciones costosas)"""
        if self.pending_analysis:
            # Aquí irían operaciones pesadas como análisis de archivos
            # Por ahora solo limpiamos
            self.pending_analysis = None
    
    def _schedule_heavy_analysis(self, mountpoint: str):
        """Programa análisis pesado con debounce de 100ms"""
        self.pending_analysis = mountpoint
        self.debounce_timer.stop()
        self.debounce_timer.start(100)  # 100ms para operaciones pesadas
    
    def _cleanup_cache(self):
        """Limpia cache cuando se llena demasiado, manteniendo prioridades altas"""
        if len(self._smart_cache) > 10:  # Límite de 10 discos en cache
            # Ordenar por prioridad y eliminar los de menor prioridad
            sorted_items = sorted(self._cache_priority.items(), key=lambda x: x[1], reverse=True)
            # Mantener solo los 8 de mayor prioridad
            keep_paths = set([path for path, _ in sorted_items[:8]])
            
            # Limpiar cache
            paths_to_remove = []
            for path in self._smart_cache:
                if path not in keep_paths:
                    paths_to_remove.append(path)
            
            for path in paths_to_remove:
                del self._smart_cache[path]
                del self._cache_priority[path]
            
            self.log_message(f"🧹 Cache SMART limpiado: {len(paths_to_remove)} entradas eliminadas")
    
    def on_analyze_and_organize(self, row):
        """Maneja la selección, análisis y cambio a organización del disco"""
        try:
            if row < 0 or row >= self.disks_table.rowCount():
                self.log_message("⚠️ Fila de disco inválida")
                return
            
            mountpoint_item = self.disks_table.item(row, 1)
            if not mountpoint_item:
                self.log_message("⚠️ No se pudo obtener información de la fila")
                return
            
            mountpoint = mountpoint_item.text()
            if not mountpoint:
                self.log_message("⚠️ Ruta de montaje vacía")
                return
            
            # Verificar que la ruta existe
            if not os.path.exists(mountpoint):
                self.log_message(f"⚠️ La unidad {mountpoint} no está disponible")
                QMessageBox.warning(
                    self,
                    "Unidad No Disponible",
                    f"La unidad {mountpoint} no está disponible o no es accesible.\n\n"
                    "Verifica que la unidad esté conectada."
                )
                return
            
            # Seleccionar el disco y mostrar información
            self.disks_table.selectRow(row)
            self.current_selection = mountpoint
            self.update_selected_disk_info(mountpoint)
            
            # Mostrar el panel de análisis sin redimensionar la ventana
            if not self.analysis_scroll_area.isVisible():
                self.analysis_scroll_area.setVisible(True)
                # Forzar actualización del layout sin cambiar el tamaño de la ventana
                self.updateGeometry()
            
            self.log_message(f"✅ Disco seleccionado: {mountpoint}")
            
            # Emitir señal para cambiar a la pestaña de organización
            try:
                self.disk_selected.emit(mountpoint)
                self.log_message("✅ Cambiando a pestaña de organización...")
            except Exception as signal_error:
                self.log_message(f"⚠️ Error al cambiar de pestaña: {str(signal_error)}")
            
        except Exception as e:
            self.log_message(f"❌ Error al procesar disco: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al procesar el disco:\n{str(e)}"
            )
    
    def update_selected_disk_info(self, mountpoint):
        """Actualiza la información del disco seleccionado con información detallada y organizada"""
        try:
            # Verificar que los widgets existen antes de usarlos
            if not hasattr(self, 'basic_info_label') or not self.basic_info_label:
                self.log_message("❌ Error: Widgets de información no disponibles")
                return
                
            # Verificar que la ruta existe antes de procesar
            if not os.path.exists(mountpoint):
                try:
                    self.basic_info_label.setText(f"❌ La unidad {mountpoint} no está disponible")
                    self.health_status_label.setText("Estado: No disponible")
                    self.content_info_label.setText("Contenido: No disponible")
                except Exception as widget_error:
                    self.log_message(f"❌ Error al actualizar widgets: {str(widget_error)}")
                return
            
            disk_info = self.disk_manager.get_disk_info(mountpoint)
            if not disk_info:
                try:
                    self.basic_info_label.setText("❌ No se pudo obtener información del disco")
                    self.health_status_label.setText("Estado: Error")
                    self.content_info_label.setText("Contenido: Error")
                except Exception as widget_error:
                    self.log_message(f"❌ Error al actualizar widgets: {str(widget_error)}")
                return
            
            # 1. INFORMACIÓN BÁSICA ORGANIZADA
            # Obtener el tema actual para aplicar colores dinámicos
            current_theme = self.get_current_theme_name()
            
            # Generar información básica con colores del tema
            system_drive_color = "error" if disk_info.is_system_drive else "success"
            system_drive_text = "🛡️ SÍ - CRÍTICA" if disk_info.is_system_drive else "✅ NO - SEGURA"
            
            basic_text = f"""
            <div style="margin-bottom: 10px;">
                {self.get_themed_html_text(current_theme, "💾 Disco:", bold=True, color_type="primary")} 
                {self.get_themed_html_text(current_theme, disk_info.mountpoint)}
            </div>
            
            <div style="margin-bottom: 10px;">
                {self.get_themed_html_text(current_theme, "💿 Sistema de Archivos:", bold=True, color_type="primary")} 
                {self.get_themed_html_text(current_theme, disk_info.filesystem)}
            </div>
            
            <div style="margin-bottom: 10px;">
                {self.get_themed_html_text(current_theme, "📁 Unidad del Sistema:", bold=True, color_type="primary")} 
                {self.get_themed_html_text(current_theme, system_drive_text, bold=True, color_type=system_drive_color)}
            </div>
            
            <div style="margin-bottom: 10px;">
                {self.get_themed_html_text(current_theme, "🔌 Removible:", bold=True, color_type="primary")} 
                {self.get_themed_html_text(current_theme, "✅ Sí" if disk_info.is_removable else "❌ No")}
            </div>
            
            <div style="margin-bottom: 10px;">
                {self.get_themed_html_text(current_theme, "🖥️ Dispositivo:", bold=True, color_type="primary")} 
                {self.get_themed_html_text(current_theme, disk_info.device)}
            </div>
            """
            
            # Añadir información adicional del sistema
            io_stats = None  # Inicializar variable
            try:
                # Verificar cache local primero
                if mountpoint in self._smart_cache:
                    io_stats = self._smart_cache[mountpoint]
                    self.log_message(f"📊 Usando datos SMART de cache para {mountpoint}")
                else:
                    # Mostrar indicador de carga
                    self.basic_info_label.setText("🔄 Cargando datos SMART...")
                    self.health_status_label.setText("🔄 Analizando salud del disco...")
                    
                    # Obtener estadísticas I/O específicas del disco (SOLO SMART reales)
                    # Usar cache si está disponible (prefetch ya lo habrá cargado)
                    io_stats = self.disk_manager.get_disk_io_stats(mountpoint)
                    # Guardar en cache local para futuras consultas
                    if io_stats:
                        self._smart_cache[mountpoint] = io_stats
                        # Marcar como alta prioridad (disco seleccionado)
                        self._cache_priority[mountpoint] = 100
                        # Limpiar cache si es necesario
                        self._cleanup_cache()
                if io_stats and io_stats.get('read_bytes', 0) > 0:
                    # Actualizar la tarjeta de estadísticas I/O
                    io_text = f"""
                    <div style="margin-bottom: 10px;">
                        {self.get_themed_html_text(current_theme, "📊 Estadísticas I/O del Disco:", bold=True, color_type="primary")}
                    </div>
                    
                    <div style="margin-bottom: 8px;">
                        {self.get_themed_html_text(current_theme, f"• Lecturas: {io_stats.get('read_count', 0) or 0:,}", bold=True)}
                    </div>
                    
                    <div style="margin-bottom: 8px;">
                        {self.get_themed_html_text(current_theme, f"• Escrituras: {io_stats.get('write_count', 0) or 0:,}", bold=True)}
                    </div>
                    
                    <div style="margin-bottom: 8px;">
                        {self.get_themed_html_text(current_theme, f"• Datos leídos: {self.disk_manager.format_size(io_stats.get('read_bytes', 0) or 0)}", bold=True)}
                    </div>
                    
                    <div style="margin-bottom: 8px;">
                        {self.get_themed_html_text(current_theme, f"• Datos escritos: {self.disk_manager.format_size(io_stats.get('write_bytes', 0) or 0)}", bold=True)}
                    </div>
                    """
                    
                                         # La información I/O se muestra en las etiquetas individuales
                    
                    # Verificar que los widgets I/O existen antes de usarlos
                    if (hasattr(self, 'read_count_label') and self.read_count_label and
                        hasattr(self, 'write_count_label') and self.write_count_label and
                        hasattr(self, 'read_data_label') and self.read_data_label and
                        hasattr(self, 'write_data_label') and self.write_data_label):
                        
                        try:
                            # Actualizar los indicadores visuales con protección contra None
                            read_count = io_stats.get('read_count', 0) or 0
                            write_count = io_stats.get('write_count', 0) or 0
                            read_bytes = io_stats.get('read_bytes', 0) or 0
                            write_bytes = io_stats.get('write_bytes', 0) or 0
                            
                            self.read_count_label.setText(f"{read_count:,}")
                            self.write_count_label.setText(f"{write_count:,}")
                            self.read_data_label.setText(self.disk_manager.format_size(read_bytes))
                            self.write_data_label.setText(self.disk_manager.format_size(write_bytes))
                        except Exception as io_widget_error:
                            self.log_message(f"❌ Error al actualizar widgets I/O: {str(io_widget_error)}")
                    else:
                        self.log_message("⚠️ Widgets I/O no disponibles")
                    
                    # Actualizar campos SMART (normalizando tipos y permitiendo 0)
                    try:
                        temp_raw = io_stats.get('temperature', None)
                        temp_val = None
                        if temp_raw is not None:
                            temp_str = str(temp_raw).strip().replace('°C', '').replace('C', '')
                            temp_val = int(float(temp_str))
                        if temp_val is not None and -50 <= temp_val < 200:
                            if hasattr(self, 'temperature_label') and self.temperature_label:
                                self.temperature_label.setText(f"{temp_val}°C")
                    except Exception:
                        pass

                    try:
                        hours_raw = io_stats.get('power_on_hours', None)
                        hours_val = None
                        if hours_raw is not None:
                            hours_val = int(float(str(hours_raw)))
                        if hours_val is not None and hasattr(self, 'power_hours_label') and self.power_hours_label:
                            days = hours_val // 24
                            remaining_hours = hours_val % 24
                            self.power_hours_label.setText(f"{hours_val:,}h ({days:,}d {remaining_hours}h)")
                    except Exception:
                        pass

                    try:
                        cycles_raw = io_stats.get('power_cycles', None)
                        cycles_val = None
                        if cycles_raw is not None:
                            cycles_val = int(float(str(cycles_raw)))
                        if cycles_val is not None and hasattr(self, 'power_cycles_label') and self.power_cycles_label:
                            self.power_cycles_label.setText(f"{cycles_val:,}")
                    except Exception:
                        pass

                    # Añadir información I/O a la tarjeta básica (versión resumida)
                    colors = ThemeManager.get_theme_colors(current_theme)
                    read_count_safe = io_stats.get('read_count', 0) or 0
                    write_count_safe = io_stats.get('write_count', 0) or 0
                    basic_text += f"""
                    <div style="margin-top: 10px; padding: 8px; background-color: {colors['surface']}; border-radius: 6px; border-left: 4px solid {colors['primary']};">
                        <div style="color: {colors['primary']}; font-weight: bold; margin-bottom: 5px;">📊 I/O: {read_count_safe:,} lecturas, {write_count_safe:,} escrituras</div>
                    </div>
                    """
                
                # Información de temperatura (si está disponible)
                try:
                    import psutil
                    if hasattr(psutil, 'sensors_temperatures'):
                        temps = psutil.sensors_temperatures()
                        if temps:
                            colors = ThemeManager.get_theme_colors(current_theme)
                            basic_text += f"""
                            <div style="margin-top: 10px; padding: 8px; background-color: {colors['surface']}; border-radius: 6px; border-left: 4px solid {colors['warning']};">
                                <span style="color: {colors['warning']}; font-weight: bold;">🌡️ Temperatura:</span> 
                                <span style="color: {colors['text_primary']};">Monitoreo disponible</span>
                            </div>
                            """
                except:
                    pass
                    
            except ImportError:
                pass
                
            # Si no hay estadísticas I/O, mostrar mensaje en las etiquetas individuales
            if not io_stats:
                try:
                    if (hasattr(self, 'read_count_label') and self.read_count_label):
                        self.read_count_label.setText("0")
                    if (hasattr(self, 'write_count_label') and self.write_count_label):
                        self.write_count_label.setText("0")
                    if (hasattr(self, 'read_data_label') and self.read_data_label):
                        self.read_data_label.setText("0 GB")
                    if (hasattr(self, 'write_data_label') and self.write_data_label):
                        self.write_data_label.setText("0 GB")
                except Exception as reset_error:
                    self.log_message(f"❌ Error al resetear widgets I/O: {str(reset_error)}")
                
            self.basic_info_label.setText(basic_text)
            
            # 2. ESTADO Y SALUD ORGANIZADO CON SISTEMA DE PUNTUACIÓN
            health_data = self.disk_manager.get_disk_health_status(mountpoint)
            
            # Determinar color y estado visual basado en la puntuación usando colores del tema
            colors = ThemeManager.get_theme_colors(current_theme)
            
            score = health_data.get('score', 0)
            if score >= 90:
                status_color = colors['success']
                status_icon = "🟢"
                status_text = "EXCELENTE"
            elif score >= 75:
                status_color = colors['success']
                status_icon = "🟢"
                status_text = "SALUDABLE"
            elif score >= 60:
                status_color = colors['warning']
                status_icon = "🟡"
                status_text = "ATENCIÓN"
            elif score >= 40:
                status_color = colors['warning']
                status_icon = "🟠"
                status_text = "ADVERTENCIA"
            else:
                status_color = colors['error']
                status_icon = "🔴"
                status_text = "CRÍTICO"
            
            # Crear el texto del estado de salud
            text_color = colors['text_primary']
            
            health_text = self._render_health_html(current_theme, disk_info, health_data)
            
            self.health_status_label.setText(health_text)
            
            # 3. ESTADÍSTICAS DE ESPACIO CON BARRAS VISUALES
            try:
                # Verificar que los widgets de espacio existen antes de usarlos
                if (hasattr(self, 'usage_progress_bar') and self.usage_progress_bar and
                    hasattr(self, 'total_size_label') and self.total_size_label and
                    hasattr(self, 'used_size_label') and self.used_size_label and
                    hasattr(self, 'free_size_label') and self.free_size_label):
                    
                    # Actualizar la barra de progreso de uso
                    self.usage_progress_bar.setValue(int(disk_info.usage_percent))
                    
                    # Actualizar colores de la barra según el porcentaje y tema
                    self.update_usage_progress_colors(current_theme, disk_info.usage_percent)
                    
                    # Actualizar los tamaños en las etiquetas
                    self.total_size_label.setText(self.disk_manager.format_size(disk_info.total_size))
                    self.used_size_label.setText(self.disk_manager.format_size(disk_info.used_size))
                    self.free_size_label.setText(self.disk_manager.format_size(disk_info.free_size))
                else:
                    self.log_message("⚠️ Widgets de espacio no disponibles")
            except Exception as space_error:
                self.log_message(f"❌ Error al actualizar widgets de espacio: {str(space_error)}")
            
            # 4. CONTENIDO Y ARCHIVOS ORGANIZADO
            try:
                # Obtener análisis del contenido
                content_analysis = self.disk_manager._analyze_folder_contents(mountpoint)
                
                if content_analysis:
                    total_files = content_analysis.get('total_files', 0)
                    total_dirs = content_analysis.get('total_dirs', 0)
                    total_size = content_analysis.get('total_size', 0)
                    file_types = content_analysis.get('file_types', {})
                    large_files = content_analysis.get('large_files', [])
                    recent_count = content_analysis.get('recent_files_count', 0)
                    old_count = content_analysis.get('old_files_count', 0)
                    limit_reached = content_analysis.get('analysis_limit_reached', False)
                    
                    # Resumen principal con colores del tema
                    content_text = self.get_themed_html_box(
                        current_theme, "info", "RESUMEN DEL CONTENIDO",
                        f"""📁 <b>Carpetas:</b> {total_dirs:,}<br>
                        📄 <b>Archivos:</b> {total_files:,}<br>
                        💾 <b>Tamaño Total:</b> {self.disk_manager.format_size(total_size)}""", "📊"
                    )
                    
                    # Información temporal
                    if recent_count > 0 or old_count > 0:
                        temporal_info = ""
                        if recent_count > 0:
                            temporal_info += f"🆕 <b>Recientes (<7 días):</b> {recent_count:,}<br>"
                        if old_count > 0:
                            temporal_info += f"📅 <b>Antiguos (>30 días):</b> {old_count:,}"
                            
                        content_text += self.get_themed_html_box(
                            current_theme, "warning", "ANÁLISIS TEMPORAL", temporal_info, "⏰"
                        )
                    
                    # Archivos grandes
                    if large_files:
                        large_files_info = ""
                        for i, large_file in enumerate(large_files[:5]):  # Top 5
                            size_str = self.disk_manager.format_size(large_file['size'])
                            large_files_info += f"📄 <b>{large_file['name']}</b> - {size_str}<br>"
                            
                        content_text += self.get_themed_html_box(
                            current_theme, "warning", "ARCHIVOS GRANDES (>100MB)", large_files_info.rstrip('<br>'), "🔍"
                        )
                    
                    # Tipos de archivo más comunes
                    if file_types:
                        file_types_info = ""
                        # Ordenar por cantidad y mostrar los top 5
                        sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:5]
                        for ext, count in sorted_types:
                            if ext == "sin_extension":
                                file_types_info += f"📄 <b>Sin extensión:</b> {count:,}<br>"
                            else:
                                file_types_info += f"📄 <b>{ext}:</b> {count:,}<br>"
                        
                        content_text += self.get_themed_html_box(
                            current_theme, "info", "TIPOS DE ARCHIVO MÁS COMUNES", file_types_info.rstrip('<br>'), "📋"
                        )
                    
                    # Aviso si se alcanzó el límite
                    if limit_reached:
                        colors = ThemeManager.get_theme_colors(current_theme)
                        content_text += f"""
                        <div style="padding: 8px; background-color: {colors['surface']}; border-radius: 6px; border-left: 4px solid {colors['primary']};">
                            <span style="color: {colors['primary']}; font-weight: bold;">⚠️ Nota:</span> 
                            <span style="color: {colors['text_primary']};">Análisis limitado a 10,000 elementos para mejor rendimiento</span>
                        </div>
                        """
                    
                    self.content_info_label.setText(content_text)
                else:
                    self.content_info_label.setText("📁 <b>Contenido:</b> No se pudo analizar")
                    
            except Exception as content_error:
                self.content_info_label.setText(f"📁 <b>Contenido:</b> Error al analizar: {str(content_error)}")
            
        except Exception as e:
            error_msg = f"❌ Error al obtener información: {str(e)}"
            self.basic_info_label.setText(f"❌ Error: {str(e)}")
            self.health_status_label.setText("Estado: Error")
                         # La información de espacio se muestra en la barra de progreso y etiquetas
            self.content_info_label.setText("Contenido: Error")
            self.log_message(error_msg)
        
        finally:
            # No aplicar estilos aquí para evitar bucles y parpadeos
            # Los estilos se aplican automáticamente cuando se cambia el tema
            pass
    
    def update_selected_disk_info_with_theme(self, mountpoint, theme_name):
        """Actualiza la información del disco seleccionado usando un tema específico (para evitar problemas de timing)"""
        try:
            self.log_message(f"🔄 Iniciando actualización con tema {theme_name} para {mountpoint}")
            
            # Verificar que los widgets existen antes de usarlos
            if not hasattr(self, 'basic_info_label') or not self.basic_info_label:
                self.log_message("❌ Error: Widgets de información no disponibles")
                return
                
            # Verificar que la ruta existe antes de procesar
            if not os.path.exists(mountpoint):
                self.log_message(f"❌ La ruta {mountpoint} no existe")
                try:
                    self.basic_info_label.setText(f"❌ La unidad {mountpoint} no está disponible")
                    self.health_status_label.setText("Estado: No disponible")
                    self.content_info_label.setText("Contenido: No disponible")
                except Exception as widget_error:
                    self.log_message(f"❌ Error al actualizar widgets: {str(widget_error)}")
                return
            
            # Obtener información del disco con logging detallado
            self.log_message(f"🔍 Obteniendo información del disco {mountpoint}")
            disk_info = self.disk_manager.get_disk_info(mountpoint)
            
            if not disk_info:
                self.log_message(f"❌ No se pudo obtener información del disco {mountpoint}")
                try:
                    self.basic_info_label.setText("❌ No se pudo obtener información del disco")
                    self.health_status_label.setText("Estado: Error")
                    self.content_info_label.setText("Contenido: Error")
                except Exception as widget_error:
                    self.log_message(f"❌ Error al actualizar widgets: {str(widget_error)}")
                return
            
            self.log_message(f"✅ Información del disco obtenida correctamente")
            
            # 1. INFORMACIÓN BÁSICA ORGANIZADA
            # USAR EL TEMA PASADO COMO PARÁMETRO (no get_current_theme_name())
            current_theme = theme_name
            
            # Generar información básica con colores del tema
            system_drive_color = "error" if disk_info.is_system_drive else "success"
            system_drive_text = "🛡️ SÍ - CRÍTICA" if disk_info.is_system_drive else "✅ NO - SEGURA"
            
            basic_text = f"""
            <div style="margin-bottom: 10px;">
                {self.get_themed_html_text(current_theme, "💾 Disco:", bold=True, color_type="primary")} 
                {self.get_themed_html_text(current_theme, disk_info.mountpoint)}
            </div>
            
            <div style="margin-bottom: 10px;">
                {self.get_themed_html_text(current_theme, "💿 Sistema de Archivos:", bold=True, color_type="primary")} 
                {self.get_themed_html_text(current_theme, disk_info.filesystem)}
            </div>
            
            <div style="margin-bottom: 10px;">
                {self.get_themed_html_text(current_theme, "📁 Unidad del Sistema:", bold=True, color_type="primary")} 
                {self.get_themed_html_text(current_theme, system_drive_text, bold=True, color_type=system_drive_color)}
            </div>
            
            <div style="margin-bottom: 10px;">
                {self.get_themed_html_text(current_theme, "🔌 Removible:", bold=True, color_type="primary")} 
                {self.get_themed_html_text(current_theme, "✅ Sí" if disk_info.is_removable else "❌ No")}
            </div>
            
            <div style="margin-bottom: 10px;">
                {self.get_themed_html_text(current_theme, "🖥️ Dispositivo:", bold=True, color_type="primary")} 
                {self.get_themed_html_text(current_theme, disk_info.device)}
            </div>
            """
            
            # Continuar con el resto de la lógica pero usando current_theme = theme_name
            self.basic_info_label.setText(basic_text)
            
            # 2. ESTADO Y SALUD con tema específico
            health_data = self.disk_manager.get_disk_health_status(mountpoint)
            health_text = self._render_health_html(current_theme, disk_info, health_data)
            self.health_status_label.setText(health_text)
            
            # 3. CONTENIDO con tema específico  
            content_analysis = self.disk_manager.analyze_disk_content(mountpoint)
            if content_analysis:
                total_dirs = content_analysis.get('total_dirs', 0)
                total_files = content_analysis.get('total_files', 0)
                total_size = content_analysis.get('total_size', 0)
                large_files = content_analysis.get('large_files', [])
                recent_count = content_analysis.get('recent_files_count', 0)
                old_count = content_analysis.get('old_files_count', 0)
                limit_reached = content_analysis.get('analysis_limit_reached', False)
                
                # Resumen principal con colores del tema
                content_text = self.get_themed_html_box(
                    current_theme, "info", "RESUMEN DEL CONTENIDO",
                    f"""📁 <b>Carpetas:</b> {total_dirs:,}<br>
                    📄 <b>Archivos:</b> {total_files:,}<br>
                    💾 <b>Tamaño Total:</b> {self.disk_manager.format_size(total_size)}""", "📊"
                )
                
                # Análisis temporal
                if recent_count > 0 or old_count > 0:
                    temporal_info = f"Recientes (3 días): {recent_count} | Antiguos (>30 días): {old_count}"
                    content_text += self.get_themed_html_box(
                        current_theme, "warning", "ANÁLISIS TEMPORAL", temporal_info, "⏰"
                    )
                
                # Archivos grandes
                if large_files:
                    large_files_info = ""
                    for file_info in large_files[:5]:  # Mostrar solo los 5 primeros
                        large_files_info += f"{file_info['name']} - {self.disk_manager.format_size(file_info['size'])}<br>"
                    
                    content_text += self.get_themed_html_box(
                        current_theme, "warning", "ARCHIVOS GRANDES (>100MB)", large_files_info.rstrip('<br>'), "🔍"
                    )
                
                # Tipos de archivo más comunes
                file_types = content_analysis.get('file_types', {})
                if file_types:
                    file_types_info = ""
                    sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
                    for ext, count in sorted_types[:5]:  # Top 5
                        ext_display = ext if ext else "Sin extensión"
                        file_types_info += f"{ext_display}: {count}<br>"
                    
                    content_text += self.get_themed_html_box(
                        current_theme, "info", "TIPOS DE ARCHIVO MÁS COMUNES", file_types_info.rstrip('<br>'), "📋"
                    )
                
                # Aviso si se alcanzó el límite
                if limit_reached:
                    colors = ThemeManager.get_theme_colors(current_theme)
                    content_text += f"""
                    <div style="padding: 8px; background-color: {colors['surface']}; border-radius: 6px; border-left: 4px solid {colors['primary']};">
                        <span style="color: {colors['primary']}; font-weight: bold;">⚠️ Nota:</span> 
                        <span style="color: {colors['text_primary']};">Análisis limitado a 10,000 elementos para mejor rendimiento</span>
                    </div>
                    """
                
                self.content_info_label.setText(content_text)
            else:
                self.content_info_label.setText("📁 <b>Contenido:</b> No se pudo analizar")
            
            # 4. ACTUALIZAR WIDGETS I/O Y BARRAS DE PROGRESO
            try:
                # Obtener estadísticas I/O
                io_stats = self.disk_manager.get_disk_io_stats(mountpoint)
                if io_stats:
                    # Actualizar widgets I/O básicos
                    if (hasattr(self, 'read_count_label') and self.read_count_label and
                        hasattr(self, 'write_count_label') and self.write_count_label and
                        hasattr(self, 'read_data_label') and self.read_data_label and
                        hasattr(self, 'write_data_label') and self.write_data_label):
                        
                        read_count = io_stats.get('read_count', 0) or 0
                        write_count = io_stats.get('write_count', 0) or 0
                        read_bytes = io_stats.get('read_bytes', 0) or 0
                        write_bytes = io_stats.get('write_bytes', 0) or 0
                        
                        self.read_count_label.setText(f"{read_count:,}")
                        self.write_count_label.setText(f"{write_count:,}")
                        self.read_data_label.setText(self.disk_manager.format_size(read_bytes))
                        self.write_data_label.setText(self.disk_manager.format_size(write_bytes))
                    
                    # Actualizar campos SMART (normalizando tipos y permitiendo 0)
                    try:
                        temp_raw = io_stats.get('temperature', None)
                        temp_val = None
                        if temp_raw is not None:
                            # Aceptar int/float/string ("44", "44 C", etc.)
                            temp_str = str(temp_raw).strip().replace('°C', '').replace('C', '')
                            temp_val = int(float(temp_str))
                        if temp_val is not None and -50 <= temp_val < 200:
                            if hasattr(self, 'temperature_label') and self.temperature_label:
                                self.temperature_label.setText(f"{temp_val}°C")
                    except Exception:
                        pass

                    try:
                        hours_raw = io_stats.get('power_on_hours', None)
                        hours_val = None
                        if hours_raw is not None:
                            hours_val = int(float(str(hours_raw)))
                        if hours_val is not None and hasattr(self, 'power_hours_label') and self.power_hours_label:
                            days = hours_val // 24
                            remaining_hours = hours_val % 24
                            self.power_hours_label.setText(f"{hours_val:,}h ({days:,}d {remaining_hours}h)")
                    except Exception:
                        pass

                    try:
                        cycles_raw = io_stats.get('power_cycles', None)
                        cycles_val = None
                        if cycles_raw is not None:
                            cycles_val = int(float(str(cycles_raw)))
                        if cycles_val is not None and hasattr(self, 'power_cycles_label') and self.power_cycles_label:
                            self.power_cycles_label.setText(f"{cycles_val:,}")
                    except Exception:
                        pass
                else:
                    # Si no hay datos SMART, mostrar "No disponible"
                    if (hasattr(self, 'read_count_label') and self.read_count_label and
                        hasattr(self, 'write_count_label') and self.write_count_label and
                        hasattr(self, 'read_data_label') and self.read_data_label and
                        hasattr(self, 'write_data_label') and self.write_data_label):
                        self.read_count_label.setText("N/A")
                        self.write_count_label.setText("N/A")
                        self.read_data_label.setText("Datos SMART no disponibles")
                        self.write_data_label.setText("Datos SMART no disponibles")
                    
                    # También resetear los campos SMART adicionales
                    if hasattr(self, 'temperature_label') and self.temperature_label:
                        self.temperature_label.setText("N/A")
                    if hasattr(self, 'power_hours_label') and self.power_hours_label:
                        self.power_hours_label.setText("N/A")
                    if hasattr(self, 'power_cycles_label') and self.power_cycles_label:
                        self.power_cycles_label.setText("N/A")
                
                # Actualizar barra de progreso y etiquetas de espacio
                if (hasattr(self, 'usage_progress_bar') and self.usage_progress_bar and
                    hasattr(self, 'total_size_label') and self.total_size_label and
                    hasattr(self, 'used_size_label') and self.used_size_label and
                    hasattr(self, 'free_size_label') and self.free_size_label):
                    
                    # Actualizar la barra de progreso de uso
                    self.usage_progress_bar.setValue(int(disk_info.usage_percent))
                    
                    # Actualizar colores de la barra según el porcentaje y tema
                    self.update_usage_progress_colors(current_theme, disk_info.usage_percent)
                    
                    # Actualizar los tamaños en las etiquetas
                    self.total_size_label.setText(self.disk_manager.format_size(disk_info.total_size))
                    self.used_size_label.setText(self.disk_manager.format_size(disk_info.used_size))
                    self.free_size_label.setText(self.disk_manager.format_size(disk_info.free_size))
                    
            except Exception as widget_error:
                self.log_message(f"⚠️ Error actualizando widgets I/O: {str(widget_error)}")
            
            self.log_message(f"✅ Información regenerada con tema: {theme_name}")
            
        except Exception as e:
            error_msg = f"❌ Error al actualizar información del disco con tema {theme_name}: {str(e)}"
            self.basic_info_label.setText("❌ No se pudo obtener información del disco")
            self.health_status_label.setText("Estado: Error")
            self.content_info_label.setText("Contenido: Error")
            self.log_message(error_msg)

    def on_safe_mode_changed(self, enabled):
        """Maneja el cambio del modo seguro"""
        try:
            self.disk_manager.set_safe_mode(enabled)
            self.log_message(f"🛡️ Modo seguro {'activado' if enabled else 'desactivado'}")
            self.update_system_info()
        except Exception as e:
            self.log_message(f"❌ Error al cambiar modo seguro: {str(e)}")
    
    def apply_static_interface_styles(self, theme_name: str, colors: dict):
        """Aplica estilos del tema a todos los elementos estáticos de la interfaz"""
        try:
            # 1. Grupo principal de análisis
            if hasattr(self, 'analysis_group') and self.analysis_group:
                self.analysis_group.setStyleSheet(f"""
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
            
            # 2. Tarjetas principales (marcos)
            card_style = f"""
                QFrame {{
                    background-color: {colors['surface']};
                    border: 1px solid {colors['border']};
                    border-radius: 12px;
                    padding: 16px;
                    margin: 5px;
                }}
                QFrame:hover {{
                    border: 2px solid {colors['primary']};
                }}
            """
            
            # Aplicar a todas las tarjetas
            cards = ['basic_card', 'health_card', 'content_card', 'io_card_full', 'space_card_full']
            for card_name in cards:
                if hasattr(self, card_name):
                    card = getattr(self, card_name)
                    if card:
                        card.setStyleSheet(card_style)
            
            # 3. Barra de progreso de análisis
            if hasattr(self, 'analysis_progress') and self.analysis_progress:
                self.analysis_progress.setStyleSheet(f"""
                    QProgressBar {{
                        border: 2px solid {colors['border']};
                        border-radius: 10px;
                        text-align: center;
                        font-weight: bold;
                        font-size: 12px;
                        min-height: 20px;
                        margin: 8px 0;
                        background-color: {colors['surface']};
                        color: {colors['text_primary']};
                    }}
                    QProgressBar::chunk {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 {colors['primary']},
                            stop:0.5 {colors['secondary']},
                            stop:1 {colors['accent']});
                        border-radius: 8px;
                    }}
                """)
            
            # 4. Labels de secciones I/O con estilos completos
            section_labels = [
                ('reads_label', colors['primary']),
                ('writes_label', colors['warning']),
                ('read_data_label', colors['success']),
                ('write_data_label', colors['error']),
                ('progress_label', colors['primary']),
                ('total_label', colors['primary']),
                ('used_label', colors['error']),
                ('free_label', colors['success'])
            ]
            
            for label_name, label_color in section_labels:
                if hasattr(self, label_name):
                    label = getattr(self, label_name)
                    if label:
                        label.setStyleSheet(f"""
                            QLabel {{
                                color: {label_color} !important;
                                font-weight: bold;
                                font-size: 11px;
                                text-align: center;
                                padding: 3px;
                            }}
                        """)
            
            # 5. Labels de valores I/O
            value_labels = [
                ('read_count_label', colors['text_primary']),
                ('write_count_label', colors['text_primary']),
                ('read_data_label', colors['text_primary']),
                ('write_data_label', colors['text_primary']),
                ('total_size_label', colors['text_primary']),
                ('used_size_label', colors['text_primary']),
                ('free_size_label', colors['text_primary'])
            ]
            
            for label_name, text_color in value_labels:
                if hasattr(self, label_name):
                    label = getattr(self, label_name)
                    if label:
                        label.setStyleSheet(f"""
                            QLabel {{
                                color: {text_color} !important;
                                font-weight: bold;
                                font-size: 12px;
                                text-align: center;
                                padding: 4px 8px;
                                background-color: {colors['background']};
                                border-radius: 4px;
                                border: 1px solid {colors['border']};
                            }}
                        """)
            
        except Exception as e:
            self.log_message(f"❌ Error aplicando estilos estáticos: {str(e)}")
    
    def apply_compact_disk_viewer_styles(self, theme_name: str, colors: dict):
        """🚀 OPTIMIZACIÓN: Aplica estilos compactos específicos para Disk Viewer"""
        try:
            from src.utils.compact_styles import get_compact_disk_viewer_styles
            
            # Obtener estilos compactos
            compact_styles = get_compact_disk_viewer_styles(colors, 12)
            
            # Aplicar estilos compactos a toda la ventana
            self.setStyleSheet(compact_styles)
            
            # Aplicar estilos específicos a elementos clave
            if hasattr(self, 'disks_table') and self.disks_table:
                self.disks_table.setStyleSheet(compact_styles)
            
            if hasattr(self, 'system_info_label') and self.system_info_label:
                self.system_info_label.setStyleSheet(compact_styles)
            
            if hasattr(self, 'refresh_btn') and self.refresh_btn:
                self.refresh_btn.setStyleSheet(compact_styles)
            
            self.log_message("✅ Estilos compactos aplicados al Disk Viewer")
            
        except Exception as e:
            self.log_message(f"⚠️ Error aplicando estilos compactos: {str(e)}")
    
    def apply_theme_styles(self, theme_name: str):
        """Aplica los estilos del tema a todos los elementos del análisis de disco"""
        try:
            # Marcar que estamos aplicando estilos para evitar recursión infinita
            self._applying_theme_styles = True
            
            # Obtener colores del tema
            colors = ThemeManager.get_theme_colors(theme_name)
            
            # PASO 0: Aplicar estilos compactos específicos para Disk Viewer
            self.apply_compact_disk_viewer_styles(theme_name, colors)
            
            # PASO 1: Aplicar estilos a elementos estáticos de la interfaz
            self.apply_static_interface_styles(theme_name, colors)
            
            # Aplicar estilos a los labels de información básica
            if hasattr(self, 'basic_info_label') and self.basic_info_label:
                self.basic_info_label.setStyleSheet(f"""
                    QLabel {{
                        color: {colors['text_primary']} !important;
                        background-color: transparent;
                        font-size: 13px;
                        line-height: 1.5;
                        padding: 0;
                    }}
                """)
            
            # Aplicar estilos a los labels de estado de salud
            if hasattr(self, 'health_status_label') and self.health_status_label:
                self.health_status_label.setStyleSheet(f"""
                    QLabel {{
                        color: {colors['text_primary']} !important;
                        background-color: transparent;
                        font-size: 13px;
                        line-height: 1.5;
                        padding: 0;
                    }}
                """)
            
            # Aplicar estilos a los labels de contenido
            if hasattr(self, 'content_info_label') and self.content_info_label:
                self.content_info_label.setStyleSheet(f"""
                    QLabel {{
                        color: {colors['text_primary']} !important;
                        background-color: transparent;
                        font-size: 13px;
                        line-height: 1.4;
                        padding: 0;
                    }}
                """)
            
            # Aplicar estilos a los headers de las tarjetas (estos son FIJOS y no cambian con cada disco)
            headers = [
                ('basic_header', self.basic_header),
                ('health_header', self.health_header), 
                ('content_header', self.content_header)
            ]
            
            for header_name, header_widget in headers:
                if header_widget:
                    header_widget.setStyleSheet(f"""
                        QLabel {{
                            color: {colors['primary']} !important;
                            font-weight: bold;
                            font-size: 15px;
                            padding: 8px 12px;
                            border-bottom: 3px solid {colors['primary']};
                            margin-bottom: 10px;
                            background-color: {colors['surface']};
                            border-radius: 8px 8px 0 0;
                            text-align: center;
                        }}
                    """)
            
            # Aplicar estilos al marco interno de cada tarjeta para un único bloque consistente
            for frame_attr in ('basic_content_frame', 'health_content_frame', 'content_content_frame'):
                if hasattr(self, frame_attr):
                    frame = getattr(self, frame_attr)
                    if frame:
                        frame.setStyleSheet(f"""
                            QFrame {{
                                background-color: {colors['surface']};
                                border: 1px solid {colors['border']};
                                border-radius: 8px;
                            }}
                        """)

            # Aplicar estilos a los labels de I/O
            io_labels = [
                ('read_count_label', colors['text_primary']),
                ('write_count_label', colors['text_primary']),
                ('read_data_label', colors['text_primary']),
                ('write_data_label', colors['text_primary']),
                ('temperature_label', colors['text_primary']),
                ('power_hours_label', colors['text_primary']),
                ('power_cycles_label', colors['text_primary'])
            ]
            
            for label_name, text_color in io_labels:
                if hasattr(self, label_name):
                    label = getattr(self, label_name)
                    if label:
                        label.setStyleSheet(f"""
                            QLabel {{
                                color: {text_color} !important;
                                font-weight: bold;
                                font-size: 12px;
                                text-align: center;
                                padding: 4px 8px;
                                background-color: {colors['surface']};
                                border-radius: 4px;
                                border: 1px solid {colors['border']};
                            }}
                        """)
            
            # Aplicar estilos a las barras de progreso
            self.apply_progress_bar_styles(theme_name)
            
            # Aplicar estilos al scroll area del análisis
            if hasattr(self, 'analysis_scroll_area') and self.analysis_scroll_area:
                self.analysis_scroll_area.setStyleSheet(f"""
                    QScrollArea {{
                        border: 1px solid {colors['border']};
                        border-radius: 8px;
                        background-color: {colors['background']};
                    }}
                    QScrollArea > QWidget > QWidget {{
                        background-color: transparent;
                    }}
                    QScrollBar:vertical {{
                        background-color: {colors['surface']};
                        width: 12px;
                        border-radius: 6px;
                    }}
                    QScrollBar::handle:vertical {{
                        background-color: {colors['primary']};
                        border-radius: 6px;
                        min-height: 20px;
                    }}
                    QScrollBar::handle:vertical:hover {{
                        background-color: {colors['accent']};
                    }}
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                        border: none;
                        background: none;
                    }}
                """)
            
            # PASO ADICIONAL: Si hay un disco seleccionado, regenerar su información con los nuevos colores
            # Se ha movido a main_window.py para un mejor control del ciclo de vida de la actualización.
            
            self.log_message(f"🎨 Estilos del tema {theme_name} aplicados al análisis de disco")
            
        except Exception as e:
            self.log_message(f"❌ Error al aplicar estilos del tema: {str(e)}")
        finally:
            # Limpiar la marca de aplicación de estilos
            self._applying_theme_styles = False
    
    def apply_progress_bar_styles(self, theme_name: str):
        """Aplica estilos dinámicos y gradientes a las barras de progreso según el tema"""
        try:
            colors = ThemeManager.get_theme_colors(theme_name)
            
            # Estilos base para barra de análisis
            if hasattr(self, 'analysis_progress') and self.analysis_progress:
                self.analysis_progress.setStyleSheet(f"""
                    QProgressBar {{
                        border: 2px solid {colors['border']};
                        border-radius: 10px;
                        text-align: center;
                        font-weight: bold;
                        font-size: 12px;
                        min-height: 20px;
                        margin: 8px 0;
                        background-color: {colors['surface']};
                        color: {colors['text_primary']};
                    }}
                    QProgressBar::chunk {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 {colors['primary']},
                            stop:0.5 {colors['secondary']},
                            stop:1 {colors['accent']});
                        border-radius: 8px;
                    }}
                """)
            
            # Aplicar estilos a la barra de uso con gradientes dinámicos
            if hasattr(self, 'usage_progress_bar') and self.usage_progress_bar:
                # Obtener valor actual para determinar el color
                current_value = self.usage_progress_bar.value()
                self.update_usage_progress_colors(theme_name, current_value)
                
        except Exception as e:
            self.log_message(f"❌ Error al aplicar estilos a barras de progreso: {str(e)}")
    
    def update_usage_progress_colors(self, theme_name: str, usage_percent: float):
        """Actualiza los colores de la barra de uso según el porcentaje y tema"""
        try:
            colors = ThemeManager.get_theme_colors(theme_name)
            
            # Determinar colores según el porcentaje de uso - SOLO DEL TEMA
            if usage_percent > 90:
                # Crítico - Rojo con gradiente
                bar_color = colors['error']
                gradient_color = colors['warning']
                border_color = bar_color
            elif usage_percent > 80:
                # Alto - Naranja con gradiente
                bar_color = colors['warning']
                gradient_color = colors['accent']
                border_color = bar_color
            elif usage_percent > 70:
                # Moderado - Amarillo con gradiente
                bar_color = colors['accent']
                gradient_color = colors['secondary']
                border_color = bar_color
            else:
                # Óptimo - Verde/Azul del tema
                bar_color = colors['success']
                gradient_color = colors['primary']
                border_color = colors['primary']
            
            # Aplicar el estilo con gradiente hermoso
            if hasattr(self, 'usage_progress_bar') and self.usage_progress_bar:
                self.usage_progress_bar.setStyleSheet(f"""
                    QProgressBar {{
                        border: 2px solid {border_color};
                        border-radius: 10px;
                        text-align: center;
                        font-weight: bold;
                        font-size: 12px;
                        min-height: 16px;
                        max-height: 16px;
                        background-color: {colors['surface']};
                        color: {colors['text_primary']};
                    }}
                    QProgressBar::chunk {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 {bar_color},
                            stop:0.3 {gradient_color},
                            stop:0.7 {bar_color},
                            stop:1 {gradient_color});
                        border-radius: 8px;
                    }}
                """)
                
        except Exception as e:
            self.log_message(f"❌ Error al actualizar colores de barra de uso: {str(e)}")
    
    def get_themed_html_box(self, theme_name: str, box_type: str, title: str, content: str, icon: str = "") -> str:
        """Genera HTML con colores del tema actual para las cajas de información - SIN COLORES HARDCODEADOS"""
        try:
            colors = ThemeManager.get_theme_colors(theme_name)
            
            # USAR SOLO COLORES DEL TEMA - Sin fallbacks hardcodeados
            bg_color = colors['surface']
            text_color = colors['text_primary']
            
            # Definir colores según el tipo de caja USANDO SOLO EL TEMA
            if box_type == "success":
                border_color = colors['success']
                title_color = colors['success'] 
            elif box_type == "warning":
                border_color = colors['warning']
                title_color = colors['warning']
            elif box_type == "error":
                border_color = colors['error']
                title_color = colors['error']
            else:  # default/info
                border_color = colors['primary']  # Usar primary en lugar de info que no todos los temas tienen
                title_color = colors['primary']
            
            return f"""
            <div style="margin-bottom: 10px; padding: 10px; background-color: {bg_color}; border-radius: 6px; border-left: 4px solid {border_color};">
                <div style="color: {title_color}; font-weight: bold; margin-bottom: 5px;">{icon} {title}</div>
                <div style="color: {text_color};">{content}</div>
            </div>
            """
        except Exception as e:
            # Fallback usando colores del tema actual si hay error
            try:
                colors = ThemeManager.get_theme_colors(self.get_current_theme_name())
                return f"""
                <div style="margin-bottom: 10px; padding: 10px; background-color: {colors['surface']}; border-radius: 6px; border-left: 4px solid {colors['border']};">
                    <div style="color: {colors['text_primary']}; font-weight: bold; margin-bottom: 5px;">{icon} {title}</div>
                    <div style="color: {colors['text_primary']};">{content}</div>
                </div>
                """
            except:
                # Último fallback - tema por defecto
                return f"""
                <div style="margin-bottom: 10px; padding: 10px; background-color: #f8f9fa; border-radius: 6px; border-left: 4px solid #6c757d;">
                    <div style="color: #495057; font-weight: bold; margin-bottom: 5px;">{icon} {title}</div>
                    <div style="color: #495057;">{content}</div>
                </div>
                """
    
    def get_current_theme_name(self) -> str:
        """Obtiene el nombre del tema actual"""
        try:
            # Intentar obtener el tema desde la configuración
            from src.utils.app_config import AppConfig
            app_config = AppConfig()
            return app_config.get_theme()
        except:
            # Fallback al tema por defecto
            return "🌞 Claro Elegante"
    
    def get_themed_html_text(self, theme_name: str, content: str, bold: bool = False, color_type: str = "text_primary") -> str:
        """Genera HTML con colores del tema para texto simple"""
        try:
            colors = ThemeManager.get_theme_colors(theme_name)
            color = colors.get(color_type, colors['text_primary'])
            weight = "bold" if bold else "normal"
            return f'<span style="color: {color}; font-weight: {weight};">{content}</span>'
        except:
            return content
    
    def get_usage_color_by_percentage(self, usage_percent: float) -> str:
        """Obtiene el color del tema según el porcentaje de uso del disco"""
        try:
            colors = ThemeManager.get_theme_colors(self.get_current_theme_name())
            
            if usage_percent > 90:
                return colors['error']
            elif usage_percent > 80:
                return colors['warning']
            elif usage_percent > 70:
                return colors['accent']
            else:
                return colors['success']
        except:
            # Fallback seguro
            return "#6c757d"
    
    def on_analyze_disk(self):
        """Maneja la solicitud de análisis del disco"""
        if not self.current_selection:
            return
        
        try:
            self.log_message(f"🔍 Iniciando análisis del disco {self.current_selection}...")
            self.analysis_progress.setVisible(True)
            self.analysis_progress.setRange(0, 0)  # Indeterminado
            
            # Simular análisis (en una implementación real, esto sería asíncrono)
            QTimer.singleShot(2000, self.complete_analysis)
            
        except Exception as e:
            self.log_message(f"❌ Error al iniciar análisis: {str(e)}")
    
    def complete_analysis(self):
        """Completa el análisis del disco"""
        try:
            if not self.current_selection:
                return
            
            # Obtener análisis real
            analysis = self.disk_manager.analyze_disk_space(self.current_selection)
            
            if analysis:
                disk_info = analysis.get("disk_info")
                folder_stats = analysis.get("folder_analysis", {})
                recommendations = analysis.get("recommendations", [])
                
                # Mostrar resultados
                result_text = f"""
                🔍 <b>Análisis Completado:</b> {self.current_selection}
                
                📁 <b>Contenido de la Carpeta:</b>
                • Archivos: {folder_stats.get('total_files', 0):,}
                • Carpetas: {folder_stats.get('total_dirs', 0):,}
                • Tamaño Total: {self.disk_manager.format_size(folder_stats.get('total_size', 0))}
                
                💡 <b>Recomendaciones:</b>
                """
                
                for rec in recommendations:
                    result_text += f"• {rec}\n"
                
                self.selected_disk_info.setText(result_text)
                self.log_message(f"✅ Análisis completado para {self.current_selection}")
                
            else:
                self.log_message(f"❌ No se pudo completar el análisis de {self.current_selection}")
            
        except Exception as e:
            self.log_message(f"❌ Error al completar análisis: {str(e)}")
        finally:
            self.analysis_progress.setVisible(False)
    

    
    def log_message(self, message):
        """Añade un mensaje al log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # Auto-scroll al final
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def get_selected_disk_path(self) -> Optional[str]:
        """Retorna la ruta del disco actualmente seleccionado"""
        return self.current_selection
    
    def is_safe_mode_enabled(self) -> bool:
        """Retorna si el modo seguro está habilitado"""
        return self.disk_manager.get_safe_mode_status()

    def _render_health_html(self, current_theme, disk_info, health_data) -> str:
        """Genera el HTML del estado de salud y factores SMART con colores de tema."""
        colors = ThemeManager.get_theme_colors(current_theme)
        score = health_data.get('score', 0)
        # Determinar color/ícono/etiqueta
        if score >= 90:
            status_color = colors['success']; status_icon = "🟢"; status_text = "EXCELENTE"
        elif score >= 75:
            status_color = colors['success']; status_icon = "🟢"; status_text = "SALUDABLE"
        elif score >= 60:
            status_color = colors['warning']; status_icon = "🟡"; status_text = "ATENCIÓN"
        elif score >= 40:
            status_color = colors['warning']; status_icon = "🟠"; status_text = "ADVERTENCIA"
        else:
            status_color = colors['error']; status_icon = "🔴"; status_text = "CRÍTICO"
        text_color = colors['text_primary']

        # Bloque principal
        health_text = f"""
        <div style="margin-bottom: 15px; padding: 12px; background-color: {status_color}20; border-radius: 8px; border-left: 5px solid {status_color};">
            <div style="color: {status_color}; font-weight: bold; font-size: 14px; margin-bottom: 8px;">
                {status_icon} Estado: {status_text}
            </div>
            <div style="color: {text_color}; margin-bottom: 5px;">
                📊 Puntuación de Salud: <span style="font-weight: bold; color: {status_color};">{score}/100</span>
            </div>
            <div style="color: {text_color}; margin-bottom: 5px;">
                💾 Uso del Disco: <span style="font-weight: bold;">{disk_info.usage_percent:.1f}%</span>
            </div>
            <div style="color: {text_color}; margin-bottom: 8px;">
                💡 Acción: <span style="font-weight: bold;">{health_data.get('status', 'Desconocido')}</span>
            </div>
        </div>
        """

        # Factores
        factors = health_data.get('factors', [])
        if factors:
            surface_color = colors['surface']
            accent_color = colors['primary']
            health_text += f"""
            <div style="margin-bottom: 15px; padding: 12px; background-color: {surface_color}; border-radius: 8px; border-left: 4px solid {accent_color};">
                <div style="color: {accent_color}; font-weight: bold; margin-bottom: 8px;">🔍 FACTORES DE SALUD:</div>
            """
            for factor in factors:
                bg_color = colors['background']
                health_text += f"""
                <div style="color: {text_color}; margin-bottom: 4px; padding: 3px; background-color: {bg_color}; border-radius: 3px;">
                    • {factor}
                </div>
                """
            health_text += "</div>"

        # Resumen compacto: Temp / TBW / Horas / Ciclos
        temp = health_data.get('temperature', None)
        tbw = health_data.get('tbw', {})
        hours = health_data.get('power_on_hours', None)
        cycles = health_data.get('power_cycles', None)
        if any([temp is not None, tbw, hours is not None, cycles is not None]):
            surface = colors['surface']
            accent = colors['primary']
            tbw_read = tbw.get('read_tb', 0)
            tbw_write = tbw.get('write_tb', 0)
            tbw_rated = tbw.get('rated_tbw', 0)
            health_text += f"""
            <div style="margin-bottom: 15px; padding: 12px; background-color: {surface}; border-radius: 8px; border-left: 4px solid {accent};">
                <div style="color: {accent}; font-weight: bold; margin-bottom: 8px;">📌 RESUMEN (SMART)</div>
                <div style="display: grid; grid-template-columns: repeat(2, minmax(180px, 1fr)); gap: 6px;">
                    <div>🌡️ Temp: <b>{(str(temp) + '°C') if isinstance(temp, (int, float)) else ('N/A' if temp is None else temp)}</b></div>
                    <div>⏰ Horas: <b>{(f"{int(hours):,}h" if isinstance(hours, (int, float)) else 'N/A')}</b></div>
                    <div>🔄 Ciclos: <b>{(f"{int(cycles):,}" if isinstance(cycles, (int, float)) else 'N/A')}</b></div>
                    <div>🧮 TBW: <b>{tbw_read:.1f}T L / {tbw_write:.1f}T E</b>{(f" (de {int(tbw_rated)}T)" if tbw_rated else '')}</div>
                </div>
            </div>
            """

        # Advertencias de seguridad según tipo de unidad
        if disk_info.is_system_drive:
            health_text += self.get_themed_html_box(
                current_theme, "error", "SEGURIDAD CRÍTICA",
                "⚠️ Unidad del sistema - Manipular con precaución extrema", "🛡️"
            )
        elif disk_info.is_removable:
            health_text += self.get_themed_html_box(
                current_theme, "success", "TIPO DE DISCO",
                "✅ Disco removible - Ideal para organización de archivos", "🔌"
            )
        else:
            health_text += self.get_themed_html_box(
                current_theme, "success", "TIPO DE DISCO",
                "✅ Disco de datos - Seguro para organización", "💾"
            )

        return health_text