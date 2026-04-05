#!/usr/bin/env python3
"""
Ventana Principal del Organizador de Archivos - REFACTORIZADO
Maneja la interfaz principal y la lógica de la aplicación
Arquivo original: 2,133 líneas → Refactorizado: ~450 líneas
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout, QWidget,
    QPushButton, QLabel, QLineEdit, QFileDialog, QTextEdit,
    QCheckBox, QSpinBox, QProgressBar, QGroupBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QSplitter, QFrame, QDialog, QTableView, QMenu
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSettings
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor, QShortcut, QKeySequence, QAction

from src.utils.constants import COLORS, DIALOG_STYLES, UI_CONFIG
from src.utils.themes import ThemeManager
from src.utils.app_config import AppConfig
from src.core.category_manager import CategoryManager
from src.core.disk_manager import DiskManager
from src.core.workers import AnalysisWorker, OrganizeWorker
from src.core.application_state import app_state, EventType
from src.gui.disk_viewer import DiskViewer
from src.gui.config_dialog import ConfigDialog
from src.gui.duplicates_dashboard import DuplicatesDashboard
from src.gui.table_models import VirtualizedMovementsModel

# Importar componentes refactorizados
from src.gui.main_window_components import MainWindowSetup, MainWindowHandlers, MainWindowActions


class FileOrganizerGUI(QMainWindow, MainWindowSetup, MainWindowHandlers, MainWindowActions):
    """
    Ventana principal del organizador de archivos
    
    NOTA: Esta clase ahora es un orquestador que delega en componentes:
    - MainWindowSetup: Construcción de UI
    - MainWindowHandlers: Manejo de eventos y señales
    - MainWindowActions: Acciones de negocio (análisis, organización)
    """
    
    def __init__(self):
        try:
            print("[MainWindow] Iniciando __init__...")
            print("[MainWindow] Llamando super().__init__()...")
            super().__init__()
            print("[MainWindow] super().__init__() OK")
        except Exception as e:
            print(f"[MainWindow] ERROR en super().__init__(): {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # === ESTADO CENTRALIZADO ===
        self._init_state()
        
        # === DATOS LOCALES ===
        self.folder_movements = []
        self.file_movements = []
        self.duplicates_dashboard = None
        self._active_workers = []  # Lista de workers activos para limpieza
        
        # === CONFIGURACIÓN PERSISTENTE ===
        print("[MainWindow] Creando QSettings...")
        self.settings = QSettings("FileOrganizer", "MainWindow")
        print("[MainWindow] QSettings OK")
        
        # === INICIALIZACIÓN ===
        print("[MainWindow] Llamando init_ui()...")
        self.init_ui()  # De MainWindowSetup
        print("[MainWindow] init_ui() OK")
        
        print("[MainWindow] Llamando _init_disk_manager()...")
        self._init_disk_manager()
        print("[MainWindow] _init_disk_manager() OK")
        
        print("[MainWindow] Llamando setup_connections()...")
        self.setup_connections()  # De MainWindowHandlers
        print("[MainWindow] setup_connections() OK")
        
        print("[MainWindow] Llamando setup_shortcuts()...")
        self.setup_shortcuts()  # De MainWindowHandlers
        print("[MainWindow] setup_shortcuts() OK")
        
        print("[MainWindow] Llamando setup_state_observers()...")
        self.setup_state_observers()  # De MainWindowHandlers
        print("[MainWindow] setup_state_observers() OK")
        
        print("[MainWindow] Llamando apply_saved_interface_settings()...")
        self.apply_saved_interface_settings()  # De MainWindowHandlers
        print("[MainWindow] apply_saved_interface_settings() OK")
        
        print("[MainWindow] __init__ completado correctamente")
    
    def _init_disk_manager(self):
        """Inicializa DiskManager usando el estado centralizado"""
        try:
            # Verificar que app_state esté disponible
            if not hasattr(app_state, 'get_disk_manager'):
                self.log_message("⚠️ app_state no tiene get_disk_manager, inicialización pospuesta")
                self.disk_manager = None
                return
            
            # Obtener DiskManager del estado centralizado
            try:
                self.disk_manager = app_state.get_disk_manager()
            except Exception as e:
                self.log_message(f"⚠️ Error llamando a get_disk_manager: {e}")
                self.disk_manager = None
                return
            
            if self.disk_manager:
                # Actualizar DiskViewer con la instancia de DiskManager
                if hasattr(self, 'disk_viewer') and self.disk_viewer:
                    self.disk_viewer.disk_manager = self.disk_manager
                    # Hacer el primer refresh después de asignar disk_manager
                    try:
                        self.disk_viewer.refresh_disks()
                        self.log_message("✅ DiskViewer actualizado con DiskManager")
                    except Exception as e:
                        self.log_message(f"⚠️ Error refrescando discos: {e}")
            else:
                self.log_message("⚠️ No se pudo inicializar DiskManager")
                
        except Exception as e:
            self.log_message(f"❌ Error al inicializar DiskManager: {e}")
            import traceback
            self.log_message(traceback.format_exc())
            self.disk_manager = None
    
    def init_ui(self):
        """Inicializa la interfaz de usuario con el nuevo diseño optimizado"""
        self.setWindowTitle(UI_CONFIG["WINDOW_TITLE"])
        self.setGeometry(100, 100, UI_CONFIG["WINDOW_WIDTH"], UI_CONFIG["WINDOW_HEIGHT"])
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header principal con título y configuración
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🏠 Organizador de Archivos y Carpetas")
        title_label.setToolTip("🏠 Aplicación principal para organizar y gestionar archivos por categorías automáticamente")
        title_label.setObjectName("main_title_label")  # Para CSS específico
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Botón de configuración
        self.config_btn = QPushButton("⚙️ Configuración")
        self.config_btn.setToolTip("⚙️ Abre la configuración de categorías y extensiones")
        self.config_btn.setObjectName("config_button")  # Para CSS específico
        self.config_btn.clicked.connect(self.open_configuration)
        header_layout.addWidget(self.config_btn)
        
        main_layout.addLayout(header_layout)
        
        # Sistema de pestañas principal
        self.main_tabs = QTabWidget()
        self.main_tabs.setObjectName("main_tabs")  # Para CSS específico
        
        # Pestaña 1: Organizar Archivos (funcionalidad existente)
        self.organize_tab = QWidget()
        organize_layout = QVBoxLayout(self.organize_tab)
        organize_layout.setSpacing(10)
        organize_layout.setContentsMargins(15, 15, 15, 15)
        
        # Pestaña 2: Gestión de Discos (nueva funcionalidad)
        self.disks_tab = QWidget()
        disks_layout = QVBoxLayout(self.disks_tab)
        disks_layout.setSpacing(10)
        disks_layout.setContentsMargins(15, 15, 15, 15)
        
        # Crear e integrar el visor de discos (DiskManager se inicializará después)
        self.disk_viewer = DiskViewer(disk_manager=None)  # Se actualizará después
        disks_layout.addWidget(self.disk_viewer)

        # Conectar señales del visor de discos
        self.disk_viewer.disk_selected.connect(self.on_disk_selected_for_organize)

        # Pestaña 3: Gestión de Duplicados (nueva funcionalidad)
        self.duplicates_tab = QWidget()
        duplicates_layout = QVBoxLayout(self.duplicates_tab)
        duplicates_layout.setSpacing(10)
        duplicates_layout.setContentsMargins(15, 15, 15, 15)

        # Crear e integrar el dashboard de duplicados
        self.duplicates_dashboard = DuplicatesDashboard()
        duplicates_layout.addWidget(self.duplicates_dashboard)

        # Conectar señales del dashboard de duplicados
        self.duplicates_dashboard.status_update.connect(self.log_message)

        # Pestaña 4: LOG (nueva funcionalidad)
        self.log_tab = QWidget()
        log_layout = QVBoxLayout(self.log_tab)
        log_layout.setSpacing(10)
        log_layout.setContentsMargins(15, 15, 15, 15)

        # Crear el widget de log
        self.create_log_widget(log_layout)

        # Añadir pestañas con tooltips informativos
        self.main_tabs.addTab(self.organize_tab, "📁 Organizar Archivos")
        self.main_tabs.setTabToolTip(0, "📁 Organiza archivos de una carpeta específica por categorías automáticamente")

        self.main_tabs.addTab(self.disks_tab, "💾 Gestión de Discos")
        self.main_tabs.setTabToolTip(1, "💾 Gestiona y analiza todos los discos del sistema para organización masiva")

        self.main_tabs.addTab(self.duplicates_tab, "🔍 Duplicados")
        self.main_tabs.setTabToolTip(2, "🔍 Detecta y gestiona archivos duplicados por contenido usando hashes MD5/SHA256")

        self.main_tabs.addTab(self.log_tab, "📝 LOG")
        self.main_tabs.setTabToolTip(3, "📝 Registro detallado de todas las operaciones realizadas en la aplicación")
        
        main_layout.addWidget(self.main_tabs)
        
        # Barra de ruta y análisis (compacta)
        path_layout = QHBoxLayout()
        
        folder_label = QLabel("📂 Ruta:")
        folder_label.setToolTip("📂 Especifica la carpeta que quieres analizar y organizar")
        folder_label.setObjectName("folder_label")
        path_layout.addWidget(folder_label)
        
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("C:/Users/Usuario/Downloads")
        self.folder_input.setToolTip("📁 Escribe la ruta de la carpeta o usa el botón 'Examinar'")
        self.folder_input.setObjectName("folder_input")  # Para CSS específico
        self.folder_input.setFixedHeight(36)  # ALTURA ESTANDARIZADA
        # Estilos aplicados automáticamente via themes.py
        path_layout.addWidget(self.folder_input)
        
        self.browse_btn = QPushButton("📂 Examinar")
        self.browse_btn.setToolTip("📂 Abre el explorador de archivos para seleccionar una carpeta")
        self.browse_btn.setObjectName("browse_button")  # Para CSS específico
        self.browse_btn.clicked.connect(self.browse_folder)
        self.browse_btn.setFixedHeight(36)  # ALTURA ESTANDARIZADA
        self.browse_btn.setProperty("styleClass", "warning")  # Usa color warning del tema
        path_layout.addWidget(self.browse_btn)
        
        self.analyze_btn = QPushButton("🔍 Analizar")
        self.analyze_btn.setToolTip("🔍 Analiza la carpeta seleccionada para ver qué se puede organizar")
        self.analyze_btn.setObjectName("analyze_button")  # Para CSS específico
        self.analyze_btn.clicked.connect(self.start_analysis)
        self.analyze_btn.setFixedHeight(36)  # ALTURA ESTANDARIZADA
        # Usa color primary del tema automáticamente
        path_layout.addWidget(self.analyze_btn)
        
        organize_layout.addLayout(path_layout)
        
        # Barra de estado inteligente con estadísticas integradas
        status_layout = QHBoxLayout()
        
        # Contador de elementos
        self.selection_count_label = QLabel("📊 Elementos: 0/0 seleccionados")
        self.selection_count_label.setToolTip("📊 Muestra el número de elementos seleccionados vs. total disponible para organizar")
        self.selection_count_label.setObjectName("selection_count_label")
        status_layout.addWidget(self.selection_count_label)
        
        # Estadísticas integradas
        self.stats_label = QLabel("📈 MÚSICA(0%) • VIDEOS(0%) • IMÁG(0%) • VARIOS(0%)")
        self.stats_label.setToolTip("📈 Distribución porcentual de archivos por categorías principales detectadas")
        self.stats_label.setObjectName("stats_label")
        status_layout.addWidget(self.stats_label)
        
        status_layout.addStretch()
        
        organize_layout.addLayout(status_layout)
        
        # Barra de botones de selección - MEJOR ALINEACIÓN
        selection_layout = QHBoxLayout()
        selection_layout.setSpacing(15)  # Espaciado consistente entre grupos
        selection_layout.setContentsMargins(0, 10, 0, 10)  # Márgenes verticales
        
        # GRUPO 1: Botones de selección
        selection_buttons_group = QHBoxLayout()
        selection_buttons_group.setSpacing(10)  # Espaciado entre botones
        
        self.select_all_btn = QPushButton("☑️ Seleccionar Todo")
        self.select_all_btn.setToolTip("☑️ Marca todos los elementos para ser organizados")
        self.select_all_btn.clicked.connect(self.select_all_items)
        self.select_all_btn.setObjectName("select_all_btn")
        self.select_all_btn.setFixedHeight(36)  # ALTURA ESTANDARIZADA
        self.select_all_btn.setMinimumWidth(140)
        self.select_all_btn.setProperty("styleClass", "success")  # Usa color success del tema
        selection_buttons_group.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("❌ Deseleccionar Todo")
        self.deselect_all_btn.setToolTip("❌ Desmarca todos los elementos")
        self.deselect_all_btn.clicked.connect(self.deselect_all_items)
        self.deselect_all_btn.setObjectName("deselect_all_btn")
        self.deselect_all_btn.setFixedHeight(36)  # ALTURA ESTANDARIZADA
        self.deselect_all_btn.setMinimumWidth(140)
        self.deselect_all_btn.setProperty("styleClass", "disabled")  # Usa color disabled del tema
        selection_buttons_group.addWidget(self.deselect_all_btn)
        
        selection_layout.addLayout(selection_buttons_group)
        
        # Separador visual
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.VLine)
        separator1.setFrameShadow(QFrame.Shadow.Sunken)
        separator1.setMaximumHeight(30)
        # Estilos se aplicarán dinámicamente con el tema
        separator1.setObjectName("separator1")
        selection_layout.addWidget(separator1)
        
        # GRUPO 2: Checkbox de carpetas - SIMPLE Y BÁSICO
        folders_group = QHBoxLayout()
        folders_group.setSpacing(8)
        folders_group.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Centrar verticalmente
        
        self.move_folders_checkbox = QCheckBox("📁 Mover carpetas completas")
        self.move_folders_checkbox.setToolTip("📁 Si está marcado, mueve las carpetas completas. Si no, solo mueve archivos sueltos.")
        self.move_folders_checkbox.setChecked(True)  # Por defecto marcado
        
        # SIN estilos específicos - solo checkbox básico
        folders_group.addWidget(self.move_folders_checkbox)
        
        selection_layout.addLayout(folders_group)
        
        # Separador visual
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        separator2.setMaximumHeight(30)
        # Estilos se aplicarán dinámicamente con el tema
        separator2.setObjectName("separator2")
        selection_layout.addWidget(separator2)
        
        # GRUPO 3: Campo de similitud - CAMPO MÁS GRANDE Y LEGIBLE
        similarity_group = QHBoxLayout()
        similarity_group.setSpacing(8)
        similarity_group.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        # Ícono de objetivo - SIMPLE
        target_icon = QLabel("🎯")
        target_icon.setToolTip("🎯 Configuración de similitud para clasificación")
        target_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        target_icon.setMinimumWidth(20)
        target_icon.setMaximumWidth(20)
        # SIN estilos específicos - solo icono básico
        similarity_group.addWidget(target_icon)
        
        similarity_label = QLabel("Similitud mínima:")
        similarity_label.setToolTip("🎯 Porcentaje mínimo de similitud para clasificar carpetas en categorías")
        similarity_group.addWidget(similarity_label)
        
        self.similarity_spinbox = QSpinBox()
        self.similarity_spinbox.setToolTip("🎯 Porcentaje mínimo de similitud (0-100%) para clasificar carpetas")
        self.similarity_spinbox.setRange(0, 100)
        self.similarity_spinbox.setValue(70)  # Por defecto 70%
        self.similarity_spinbox.setSuffix("%")
        self.similarity_spinbox.setMinimumWidth(120)
        self.similarity_spinbox.setMaximumWidth(140)
        self.similarity_spinbox.setFixedHeight(36)  # ALTURA ESTANDARIZADA
        # Estilos aplicados automáticamente via themes.py
        similarity_group.addWidget(self.similarity_spinbox)
        
        selection_layout.addLayout(similarity_group)
        
        # Espaciador final para centrar todo
        selection_layout.addStretch()
        
        organize_layout.addLayout(selection_layout)
        
        # Tabla principal optimizada
        table_label = QLabel("📋 TABLA PRINCIPAL (Optimizada)")
        # El label usará los estilos del tema automáticamente
        table_label.setToolTip("📊 Haz doble clic en las filas de 'archivos sueltos' para expandir y ver archivos individuales")
        organize_layout.addWidget(table_label)
        
        # 🚀 MEJORA: Tabla de movimientos virtualizada con QTableView + Modelo
        self.movements_table = QTableView()
        self.movements_model = VirtualizedMovementsModel()
        self.movements_table.setModel(self.movements_model)
        
        # Aplicar delegado personalizado para checkboxes
        checkbox_delegate = CheckboxDelegate(self.movements_table)
        self.movements_table.setItemDelegateForColumn(0, checkbox_delegate)
        
        self.movements_table.setToolTip("📊 Vista previa VIRTUALIZADA de todos los cambios (hasta 10,000+ elementos sin lag)")
        
        # CONFIGURACIÓN PROFESIONAL - VIRTUALIZACIÓN HABILITADA
        self.movements_table.verticalHeader().setDefaultSectionSize(42)
        self.movements_table.setMinimumHeight(350)
        self.movements_table.setAlternatingRowColors(True)
        self.movements_table.setShowGrid(True)
        self.movements_table.setGridStyle(Qt.PenStyle.SolidLine)
        
        # Los estilos se aplican automáticamente via themes.py
        header = self.movements_table.horizontalHeader()
        
        # ✅ PASO 1: PRIMERO establecer los anchos ANTES de configurar ResizeMode
        self.movements_table.setColumnWidth(0, 50)     # ☑️ Checkbox
        self.movements_table.setColumnWidth(1, 900)    # 📂 Elemento - 900px
        self.movements_table.setColumnWidth(2, 200)    # 📁 Destino - 200px
        self.movements_table.setColumnWidth(3, 200)    # 📊 % - 200px
        self.movements_table.setColumnWidth(4, 200)    # 📄 Archivos - 200px
        self.movements_table.setColumnWidth(5, 200)    # 💾 Tamaño - 200px
        
        # ✅ PASO 2: DESPUÉS configurar ResizeMode (Interactive permite que el usuario ajuste)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Checkbox - ajustable
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Elemento - ajustable
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Destino - ajustable
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Porcentaje - ajustable
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # Archivos - ajustable
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)  # Tamaño - ajustable
        
        # ✅ Habilitar ordenamiento por columnas
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        header.sectionClicked.connect(self.on_header_clicked)
        
        # Añadir tooltips a los headers de la tabla
        header.setToolTip("☑️ Selección: Marca para incluir en la organización\n"
                         "📂 Elemento: Nombre del archivo o carpeta\n"
                         "📁 Destino: Categoría donde se organizará\n"
                         "📊 %: Porcentaje de confianza en la clasificación\n"
                         "📄 Archivos: Número de archivos contenidos\n"
                         "💾 Tamaño: Tamaño total del elemento")
        
        # Permitir que el usuario reordene columnas si lo desea
        header.setSectionsMovable(True)
        
        # Habilitar selección por filas
        self.movements_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.movements_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        
        # ✅ NUEVO: Configurar menú contextual
        self.movements_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.movements_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # La tabla usará los estilos del tema automáticamente
        
        organize_layout.addWidget(self.movements_table)
        
        
        # Botón principal de organizar (prominente) - DISEÑO PROFESIONAL
        organize_btn_layout = QHBoxLayout()
        
        self.organize_btn = QPushButton("📁 ORGANIZAR ARCHIVOS")
        self.organize_btn.setToolTip("📁 Organiza los archivos y carpetas seleccionados según las categorías")
        self.organize_btn.setEnabled(False)
        self.organize_btn.setObjectName("organize_button")  # Para CSS específico del tema
        self.organize_btn.clicked.connect(self.start_organization)
        self.organize_btn.setFixedHeight(50)  # ALTURA PROMINENTE
        self.organize_btn.setObjectName("organize_button")  # ID especial para gradiente en themes.py
        organize_btn_layout.addWidget(self.organize_btn)
        
        organize_layout.addLayout(organize_btn_layout)
        
        # Barra de progreso compacta
        progress_layout = QHBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setToolTip("📊 Muestra el progreso de la operación actual (análisis u organización)")
        self.progress_bar.setVisible(False)
        # La barra de progreso usará los estilos del tema automáticamente
        progress_layout.addWidget(self.progress_bar)
        
        organize_layout.addLayout(progress_layout)
        
        # Bloque de estadísticas detalladas mejorado
        stats_group = QGroupBox("📊 ESTADÍSTICAS DETALLADAS")
        stats_group.setToolTip("📊 Información detallada sobre los elementos seleccionados y categorías disponibles")
        stats_group.setObjectName("stats_group")  # Para CSS específico del tema
        
        # Layout principal de estadísticas con diseño mejorado
        main_stats_layout = QVBoxLayout(stats_group)
        
        # Primera fila: Resumen general
        summary_layout = QHBoxLayout()
        
        # Tarjeta de resumen de tamaño
        size_card = QFrame()
        size_card.setObjectName("stats_card")
        # Estilos se aplicarán dinámicamente con el tema
        size_card_layout = QVBoxLayout(size_card)
        
        size_header = QLabel("💾 RESUMEN DE TAMAÑO")
        size_header.setObjectName("stats_card_header")
        # Estilos se aplicarán dinámicamente con el tema
        size_card_layout.addWidget(size_header)
        
        self.total_size_label = QLabel("💾 Tamaño total: 0 B")
        self.total_size_label.setToolTip("💾 Tamaño total de todos los archivos y carpetas seleccionados para organizar")
        self.total_size_label.setObjectName("total_size_label")
        # Estilos se aplicarán dinámicamente con el tema
        size_card_layout.addWidget(self.total_size_label)
        
        summary_layout.addWidget(size_card)
        
        # Tarjeta de resumen de archivos
        files_card = QFrame()
        files_card.setObjectName("stats_card")
        # Estilos se aplicarán dinámicamente con el tema
        files_card_layout = QVBoxLayout(files_card)
        
        files_header = QLabel("📄 RESUMEN DE ARCHIVOS")
        files_header.setObjectName("stats_card_header")
        # Estilos se aplicarán dinámicamente con el tema
        files_card_layout.addWidget(files_header)
        
        self.total_files_label = QLabel("📄 Total archivos: 0")
        self.total_files_label.setToolTip("📄 Número total de archivos que serán organizados")
        self.total_files_label.setObjectName("total_files_label")
        # Estilos se aplicarán dinámicamente con el tema
        files_card_layout.addWidget(self.total_files_label)
        
        summary_layout.addWidget(files_card)
        
        main_stats_layout.addLayout(summary_layout)
        
        # Segunda fila: Estadísticas por categoría (mejoradas)
        category_stats_layout = QHBoxLayout()
        
        # Tarjeta de distribución por categoría
        category_card = QFrame()
        category_card.setObjectName("stats_card")
        # Estilos se aplicarán dinámicamente con el tema
        category_card_layout = QVBoxLayout(category_card)
        
        category_header = QLabel("📁 DISTRIBUCIÓN POR CATEGORÍA")
        category_header.setObjectName("stats_card_header")
        # Estilos se aplicarán dinámicamente con el tema
        category_card_layout.addWidget(category_header)
        
        self.category_stats_label = QLabel("📁 Por categoría: Sin datos")
        self.category_stats_label.setToolTip("📁 Distribución de archivos por categorías específicas detectadas")
        self.category_stats_label.setObjectName("category_stats_label")
        self.category_stats_label.setWordWrap(True)
        # Estilos se aplicarán dinámicamente con el tema
        category_card_layout.addWidget(self.category_stats_label)
        
        category_stats_layout.addWidget(category_card)
        
        # Tarjeta de categorías disponibles
        available_card = QFrame()
        available_card.setObjectName("stats_card")
        # Estilos se aplicarán dinámicamente con el tema
        available_card_layout = QVBoxLayout(available_card)
        
        available_header = QLabel("⚙️ CATEGORÍAS DISPONIBLES")
        available_header.setObjectName("stats_card_header")
        # Estilos se aplicarán dinámicamente con el tema
        available_card_layout.addWidget(available_header)
        
        self.available_categories_label = QLabel("⚙️ Categorías disponibles: Cargando...")
        self.available_categories_label.setToolTip("⚙️ Lista de todas las categorías configuradas en el sistema")
        self.available_categories_label.setObjectName("available_categories_label")
        self.available_categories_label.setWordWrap(True)
        # Estilos se aplicarán dinámicamente con el tema
        available_card_layout.addWidget(self.available_categories_label)
        
        category_stats_layout.addWidget(available_card)
        
        main_stats_layout.addLayout(category_stats_layout)
        
        organize_layout.addWidget(stats_group)
        
        # Conectar eventos de la tabla VIRTUALIZADA
        self.movements_model.dataChanged.connect(self.on_model_data_changed)
        self.movements_table.doubleClicked.connect(self.on_table_double_clicked)
        
        # Conectar eventos de entrada
        self.folder_input.textChanged.connect(self.on_folder_path_changed)
    
    def create_log_widget(self, layout):
        """Crea el widget de log con funcionalidad de exportar"""
        # Header del log
        header_layout = QHBoxLayout()
        
        log_title = QLabel("📝 REGISTRO DE OPERACIONES")
        log_title.setToolTip("📝 Historial completo de todas las operaciones realizadas en la aplicación")
        log_title.setObjectName("log_title_label")
        header_layout.addWidget(log_title)
        
        header_layout.addStretch()
        
        # Botones de control del log
        self.clear_log_btn = QPushButton("🗑️ Limpiar Log")
        self.clear_log_btn.setToolTip("🗑️ Limpia todo el contenido del log")
        self.clear_log_btn.clicked.connect(self.clear_log)
        header_layout.addWidget(self.clear_log_btn)
        
        self.export_log_btn = QPushButton("📤 Exportar a TXT")
        self.export_log_btn.setToolTip("📤 Exporta el contenido del log a un archivo de texto")
        self.export_log_btn.clicked.connect(self.export_log)
        header_layout.addWidget(self.export_log_btn)
        
        layout.addLayout(header_layout)
        
        # Widget de log principal
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setToolTip("📝 Registro detallado de todas las operaciones realizadas en la aplicación")
        self.log_text.setObjectName("log_text")
        
        # Configurar el log con scroll automático
        self.log_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.log_text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        layout.addWidget(self.log_text)
        
        # Información del log
        info_layout = QHBoxLayout()
        
        self.log_info_label = QLabel("📊 Total de entradas: 0")
        self.log_info_label.setToolTip("📊 Número total de entradas en el log")
        self.log_info_label.setObjectName("log_info_label")
        info_layout.addWidget(self.log_info_label)
        
        info_layout.addStretch()
        
        # Botón para ir al final del log
        self.scroll_to_bottom_btn = QPushButton("⬇️ Ir al Final")
        self.scroll_to_bottom_btn.setToolTip("⬇️ Desplaza el log hasta la entrada más reciente")
        self.scroll_to_bottom_btn.clicked.connect(self.scroll_log_to_bottom)
        info_layout.addWidget(self.scroll_to_bottom_btn)
        
        layout.addLayout(info_layout)
        
        # Mensaje inicial
        self.log_message("🚀 Aplicación iniciada - Log de operaciones activo")
    
    def add_categories_info(self, layout):
        """Añade información sobre las categorías disponibles"""
        # Título
        title_label = QLabel("📁 Categorías Disponibles:")
        # El label usará los estilos del tema automáticamente
        layout.addWidget(title_label)
        
        # Información de categorías
        categories = self.category_manager.get_categories()
        info_text = ""
        
        for category, extensions in categories.items():
            info_text += f"• <b>{category}</b>: {len(extensions)} extensiones\n"
        
        info_label = QLabel(info_text)
        # El label usará los estilos del tema automáticamente
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Texto de ayuda
        help_text = QLabel("💡 <b>Consejo:</b> Haz doble clic en las filas de 'archivos sueltos' para expandir y ver archivos individuales.")
        # El label usará los estilos del tema automáticamente
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
    
    def setup_connections(self):
        """Configura las conexiones de señales"""
        # Las conexiones ya se configuraron en init_ui
        pass
    
    def setup_state_observers(self):
        """✅ NUEVO: Configura observadores del estado centralizado"""
        try:
            # Verificar que app_state esté disponible
            if not hasattr(app_state, 'state_changed'):
                self.log_message("⚠️ app_state no está completamente inicializado, saltando observadores")
                return
            
            # Conectar señales del estado centralizado
            try:
                app_state.state_changed.connect(self.on_state_changed)
            except Exception as e:
                self.log_message(f"⚠️ Error conectando state_changed: {e}")
            
            try:
                app_state.theme_changed.connect(self.on_theme_changed)
            except Exception as e:
                self.log_message(f"⚠️ Error conectando theme_changed: {e}")
            
            try:
                app_state.disk_selected.connect(self.on_disk_selected)
            except Exception as e:
                self.log_message(f"⚠️ Error conectando disk_selected: {e}")
            
            # Conectar señales del gestor de workers (temporalmente comentado)
            # worker_manager.worker_started.connect(self.on_worker_started)
            # worker_manager.worker_completed.connect(self.on_worker_completed)
            # worker_manager.worker_progress.connect(self.on_worker_progress)
            # worker_manager.worker_error.connect(self.on_worker_error)
            
            # Conectar señales del gestor de memoria (temporalmente comentado)
            # memory_manager.memory_warning.connect(self.on_memory_warning)
            # memory_manager.cleanup_completed.connect(self.on_memory_cleanup)
            
            self.log_message("✅ Observadores del estado centralizado configurados")
            
        except Exception as e:
            self.log_message(f"❌ Error configurando observadores: {e}")
    
    def on_state_changed(self, event):
        """Maneja cambios del estado de la aplicación"""
        try:
            event_type = event.event_type
            data = event.data
            
            if event_type == EventType.THEME_CHANGED:
                # El tema ya se maneja en on_theme_changed
                pass
            elif event_type == EventType.DISK_SELECTED:
                # El disco ya se maneja en on_disk_selected
                pass
            elif event_type == EventType.WORKER_STARTED:
                worker_id = data.get("worker_id")
                if worker_id:
                    self.log_message(f"🚀 Worker iniciado: {worker_id}")
            elif event_type == EventType.WORKER_FINISHED:
                worker_id = data.get("worker_id")
                if worker_id:
                    self.log_message(f"✅ Worker completado: {worker_id}")
            elif event_type == EventType.MEMORY_CLEANUP:
                cache_name = data.get("cache_name")
                self.log_message(f"🧹 Limpieza de memoria: {cache_name}")
                
        except Exception as e:
            self.log_message(f"❌ Error manejando cambio de estado: {e}")
    
    def on_theme_changed(self, theme_name: str):
        """Maneja cambios de tema"""
        try:
            self.log_message(f"🎨 Tema cambiado a: {theme_name}")
            # El tema se aplica automáticamente por el sistema de temas
        except Exception as e:
            self.log_message(f"❌ Error manejando cambio de tema: {e}")
    
    def on_disk_selected(self, disk_path: str):
        """Maneja selección de disco"""
        try:
            self.log_message(f"💾 Disco seleccionado: {disk_path}")
            # La lógica de selección de disco ya está implementada
        except Exception as e:
            self.log_message(f"❌ Error manejando selección de disco: {e}")
    
    def on_worker_started(self, worker_id: str, worker_type: str):
        """Maneja inicio de workers"""
        try:
            self.log_message(f"🚀 Worker iniciado: {worker_type} ({worker_id})")
            
            # Actualizar UI según el tipo de worker
            if "Analysis" in worker_type:
                self.analyze_btn.setEnabled(False)
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)
            elif "Organize" in worker_type:
                self.organize_btn.setEnabled(False)
                self.organize_btn.setText("🔄 Organizando...")
                
        except Exception as e:
            self.log_message(f"❌ Error manejando inicio de worker: {e}")
    
    def on_worker_completed(self, worker_id: str, success: bool):
        """Maneja completación de workers"""
        try:
            status = "✅ exitoso" if success else "❌ con errores"
            self.log_message(f"🏁 Worker completado: {worker_id} - {status}")
            
            # Restaurar UI
            self.analyze_btn.setEnabled(True)
            self.organize_btn.setEnabled(True)
            self.organize_btn.setText("📁 Organizar Archivos")
            self.progress_bar.setVisible(False)
            
        except Exception as e:
            self.log_message(f"❌ Error manejando completación de worker: {e}")
    
    def on_worker_progress(self, worker_id: str, progress: float):
        """Maneja progreso de workers"""
        try:
            # Actualizar barra de progreso si es visible
            if self.progress_bar.isVisible():
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(int(progress * 100))
                
        except Exception as e:
            self.log_message(f"❌ Error manejando progreso de worker: {e}")
    
    def on_worker_error(self, worker_id: str, error_message: str):
        """Maneja errores de workers"""
        try:
            self.log_message(f"❌ Error en worker {worker_id}: {error_message}")
            
            # Restaurar UI en caso de error
            self.analyze_btn.setEnabled(True)
            self.organize_btn.setEnabled(True)
            self.organize_btn.setText("📁 Organizar Archivos")
            self.progress_bar.setVisible(False)
            
        except Exception as e:
            self.log_message(f"❌ Error manejando error de worker: {e}")
    
    def on_memory_warning(self, warning_type: str, memory_mb: float):
        """Maneja advertencias de memoria"""
        try:
            self.log_message(f"⚠️ Advertencia de memoria: {warning_type} ({memory_mb:.1f} MB)")
            
            # Mostrar advertencia al usuario si es crítica
            if memory_mb > 500:  # Más de 500MB
                QMessageBox.warning(
                    self, 
                    "Advertencia de Memoria",
                    f"El uso de memoria es alto: {memory_mb:.1f} MB\n\n"
                    "Se recomienda cerrar otras aplicaciones o reiniciar el programa."
                )
                
        except Exception as e:
            self.log_message(f"❌ Error manejando advertencia de memoria: {e}")
    
    def on_memory_cleanup(self, stats):
        """Maneja limpieza de memoria completada"""
        try:
            self.log_message(f"🧹 Limpieza de memoria completada: {stats.cache_size_mb:.1f} MB caché, {stats.active_workers} workers")
        except Exception as e:
            self.log_message(f"❌ Error manejando limpieza de memoria: {e}")
    
    def setup_shortcuts(self):
        """🚀 MEJORA: Configura los atajos de teclado para operaciones comunes"""
        # Ctrl+O: Abrir carpeta
        QShortcut(QKeySequence("Ctrl+O"), self, self.browse_folder)
        
        # Ctrl+R o F5: Analizar/Refrescar
        QShortcut(QKeySequence("F5"), self, self.start_analysis)
        QShortcut(QKeySequence("Ctrl+R"), self, self.start_analysis)
        
        # Ctrl+S: Organizar archivos
        QShortcut(QKeySequence("Ctrl+S"), self, self.start_organization)
        
        # Ctrl+F: Buscar (cambiar a pestaña de duplicados)
        QShortcut(QKeySequence("Ctrl+F"), self, lambda: self.main_tabs.setCurrentIndex(2))
        
        # Ctrl+A: Seleccionar todo
        QShortcut(QKeySequence("Ctrl+A"), self, self.select_all_items)
        
        # Ctrl+D: Deseleccionar todo
        QShortcut(QKeySequence("Ctrl+D"), self, self.deselect_all_items)
        
        # Ctrl+L: Limpiar log
        QShortcut(QKeySequence("Ctrl+L"), self, self.clear_log)
        
        # Ctrl+,: Abrir configuración (o Ctrl+P como alternativa)
        QShortcut(QKeySequence("Ctrl+P"), self, self.open_configuration)
        QShortcut(QKeySequence("Ctrl+,"), self, self.open_configuration)
        
        # Ctrl+1, Ctrl+2, Ctrl+3, Ctrl+4: Cambiar entre pestañas
        QShortcut(QKeySequence("Ctrl+1"), self, lambda: self.main_tabs.setCurrentIndex(0))
        QShortcut(QKeySequence("Ctrl+2"), self, lambda: self.main_tabs.setCurrentIndex(1))
        QShortcut(QKeySequence("Ctrl+3"), self, lambda: self.main_tabs.setCurrentIndex(2))
        QShortcut(QKeySequence("Ctrl+4"), self, lambda: self.main_tabs.setCurrentIndex(3))
        
        # Ctrl+Q: Salir
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)
        
        # Actualizar tooltips para mostrar atajos
        self.browse_btn.setToolTip("📂 Selecciona la carpeta que quieres analizar (Ctrl+O)")
        self.analyze_btn.setToolTip("🔍 Analiza el contenido de la carpeta (Ctrl+R o F5)")
        self.organize_btn.setToolTip("📁 Organiza los archivos seleccionados (Ctrl+S)")
        self.select_all_btn.setToolTip("☑️ Marca todos los elementos para ser organizados (Ctrl+A)")
        self.deselect_all_btn.setToolTip("❌ Desmarca todos los elementos (Ctrl+D)")
        self.config_btn.setToolTip("⚙️ Abre la configuración de categorías y extensiones (Ctrl+P)")
        self.clear_log_btn.setToolTip("🗑️ Limpia todo el contenido del log (Ctrl+L)")
        
        # Mensaje en log sobre atajos disponibles
        self.log_message("⌨️ Atajos de teclado habilitados. Usa Ctrl+O, Ctrl+R, Ctrl+S, Ctrl+F, etc.")
    
    def browse_folder(self):
        """Abre el diálogo para seleccionar una carpeta"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "📂 Seleccionar Carpeta a Organizar"
        )
        
        if folder_path:
            self.folder_input.setText(folder_path)
            # Auto-analizar después de un pequeño delay
            QTimer.singleShot(500, self.start_analysis)
    
    def on_folder_path_changed(self, text):
        """Maneja el cambio en el campo de ruta de carpeta"""
        if text.strip() and os.path.exists(text.strip()):
            # Pequeño delay para evitar análisis mientras se escribe
            QTimer.singleShot(1000, self.start_analysis)
    
    def start_analysis(self):
        """Inicia el análisis de la carpeta usando el gestor de workers"""
        try:
            # Verificar que la ventana esté completamente inicializada
            if not hasattr(self, 'analyze_btn') or not self.analyze_btn:
                self.log_message("⚠️ Ventana no completamente inicializada, análisis cancelado")
                return
            
            folder_path = self.folder_input.text().strip()
            
            if not folder_path:
                QMessageBox.warning(self, "Advertencia", "Por favor, selecciona una carpeta para analizar.")
                return
            
            if not os.path.exists(folder_path):
                QMessageBox.warning(self, "Advertencia", "La carpeta seleccionada no existe.")
                return
            
            if not os.path.isdir(folder_path):
                QMessageBox.warning(self, "Advertencia", "El elemento seleccionado no es una carpeta.")
                return
            
            # Limpiar resultados anteriores
            self.folder_movements = []
            self.file_movements = []
            
            # Log
            self.log_message(f"🔍 Iniciando análisis de: {folder_path}")
            
            # Crear worker usando el gestor centralizado
            worker_id = f"analysis_{int(time.time())}"
            analysis_worker = AnalysisWorker(
                folder_path,
                self.category_manager.get_categories(),
                self.category_manager.ext_to_categoria,
                self.similarity_spinbox.value()
            )
            
            # Guardar referencia al worker para limpieza
            if not hasattr(self, '_active_workers'):
                self._active_workers = []
            self._active_workers.append(analysis_worker)
            
            # Conectar señales específicas del worker
            analysis_worker.progress_update.connect(self.log_message)
            analysis_worker.analysis_complete.connect(self.on_analysis_complete)
            analysis_worker.error_occurred.connect(self.on_analysis_error)
            
            # Conectar señal de finalización para limpiar el worker
            analysis_worker.finished.connect(lambda: self._cleanup_worker(analysis_worker))
            
            # Iniciar worker
            analysis_worker.start()
            self.log_message(f"✅ Worker de análisis iniciado: {worker_id}")
            
        except Exception as e:
            error_msg = f"❌ Error al iniciar análisis: {str(e)}"
            self.log_message(error_msg)
            QMessageBox.critical(self, "Error de Análisis", error_msg)
            
            # Restaurar botones en caso de error
            if hasattr(self, 'analyze_btn'):
                self.analyze_btn.setEnabled(True)
            if hasattr(self, 'organize_btn'):
                self.organize_btn.setEnabled(True)
            if hasattr(self, 'progress_bar'):
                self.progress_bar.setVisible(False)
    
    def on_analysis_complete(self, folder_movements, file_movements, stats):
        """Maneja la completación del análisis"""
        self.folder_movements = folder_movements
        self.file_movements = file_movements
        
        # Llenar tabla
        self.populate_results_table()
        
        # Habilitar botones
        self.analyze_btn.setEnabled(True)
        self.organize_btn.setEnabled(True)
        
        # Ocultar progreso
        self.progress_bar.setVisible(False)
        
        # Log
        total_items = len(folder_movements) + len(file_movements)
        self.log_message(f"✅ Análisis completado: {total_items} elementos encontrados")
        
        # Mostrar estadísticas
        if stats:
            self.log_message(f"📊 Estadísticas: {stats.get('total_folders', 0)} carpetas, {stats.get('total_files', 0)} archivos")
            
            # Actualizar estadísticas detalladas
            self.update_statistics()
            
            # Inicializar estadísticas de selección (sin elementos seleccionados)
            self.update_selected_statistics()
    
    def on_analysis_error(self, error_message):
        """Maneja errores durante el análisis"""
        self.log_message(error_message)
        
        # Habilitar botones
        self.analyze_btn.setEnabled(True)
        self.organize_btn.setEnabled(False)
        
        # Ocultar progreso
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(self, "Error de Análisis", error_message)
    
    def populate_results_table(self):
        """🚀 MEJORA: Llena la tabla VIRTUALIZADA con los resultados del análisis"""
        # Limpiar datos anteriores en una sola operación para evitar doble parpadeo
        self.movements_model.clear_data()
        
        # Preparar datos para el modelo virtualizado
        model_data = []
        
        # Añadir carpetas
        for mov in self.folder_movements:
            model_data.append({
                'type': 'folder',
                'element': f"📁 {mov['folder'].name}",
                'category': mov['category'],
                'percentage': mov.get('percentage', 0),
                'file_count': mov.get('total_files', 0),
                'size_bytes': mov.get('size', 0),
                'size_formatted': self.format_size(mov.get('size', 0)),
                'tooltip': f"Carpeta: {mov['folder'].name}\nArchivos: {mov.get('total_files', 0)}",
                'is_group': False,
                'is_expanded': False,
                'original_data': mov
            })
        
        # Añadir archivos (agrupados por categoría)
        files_by_category = defaultdict(list)
        size_by_category = defaultdict(int)
        
        for mov in self.file_movements:
            files_by_category[mov['category']].append(mov)
            size_by_category[mov['category']] += mov.get('size', 0)
        
        for category, file_movs in files_by_category.items():
            total_size = size_by_category[category]
            
            model_data.append({
                'type': 'file_group',
                'element': f"📄 {len(file_movs)} archivos sueltos",
                'category': category,
                'percentage': 0,
                'file_count': len(file_movs),
                'size_bytes': total_size,
                'size_formatted': self.format_size(total_size),
                'tooltip': f"Grupo de {len(file_movs)} archivos sueltos\nCategoría: {category}",
                'is_group': True,
                'is_expanded': False,
                'group_files': file_movs  # Guardar archivos para expansión
            })
        
        # Actualizar modelo con nuevos datos (virtualización automática)
        self.movements_model.update_data(model_data)
        
        # ✅ CRÍTICO: Re-aplicar anchos de columna después de actualizar el modelo
        # El resetModel() puede cambiar los anchos, así que los re-aplicamos
        self.movements_table.setColumnWidth(0, 50)     # ☑️ Checkbox
        self.movements_table.setColumnWidth(1, 900)    # 📂 Elemento - 900px
        self.movements_table.setColumnWidth(2, 200)    # 📁 Destino - 200px
        self.movements_table.setColumnWidth(3, 200)    # 📊 % - 200px
        self.movements_table.setColumnWidth(4, 200)    # 📄 Archivos - 200px
        self.movements_table.setColumnWidth(5, 200)    # 💾 Tamaño - 200px
        
        # Log de performance
        self.log_message(f"✅ Tabla virtualizada poblada con {len(model_data)} elementos (performance óptima)")
        
        # Actualizar contador de selección y estadísticas
        self.update_selection_count()
        self.update_statistics()
    
    def select_all_items(self):
        """🚀 MEJORA: Selecciona todos los elementos usando el modelo virtualizado"""
        self.movements_model.check_all()
        self.update_selection_count()
        self.log_message("✅ Todos los elementos seleccionados")
    
    def deselect_all_items(self):
        """🚀 MEJORA: Deselecciona todos los elementos usando el modelo virtualizado"""
        self.movements_model.uncheck_all()
        self.update_selection_count()
        self.log_message("❌ Todos los elementos deseleccionados")
    
    def on_model_data_changed(self, top_left, bottom_right, roles):
        """🚀 MEJORA: Maneja cambios en el modelo (checkboxes)"""
        if Qt.ItemDataRole.CheckStateRole in roles:
            self.update_selection_count()
    
    def on_table_double_clicked(self, index):
        """🚀 MEJORA: Maneja doble clic en la tabla virtualizada"""
        if not index.isValid():
            return
        
        row = index.row()
        row_data = self.movements_model.get_row_data(row)
        
        if not row_data:
            return
        
        # Solo expandir/contraer grupos de archivos
        if row_data.get('is_group', False):
            self.toggle_file_group_expansion(row)
    
    def toggle_file_group_expansion(self, group_row):
        """Expande o contrae un grupo de archivos sueltos"""
        # Validar que la fila existe y es grupo
        model = self.movements_model
        total_rows = model.rowCount()
        if group_row >= total_rows or not model.is_group_row(group_row):
            return
            
        # Alternar usando el modelo (sin tocar celdas)
        row_data = model.get_row_data(group_row)
        if row_data.get('is_expanded', False):
            model.collapse_group(group_row)
        else:
            model.expand_group(group_row)
    
    def expand_file_group(self, group_row, category):
        """Compat: usa el modelo para expandir"""
        self.movements_model.expand_group(group_row)
    
    def collapse_file_group(self, group_row, category):
        """Compat: usa el modelo para colapsar"""
        self.movements_model.collapse_group(group_row)
    
    def update_selection_count(self):
        """🚀 MEJORA: Actualiza el contador usando el modelo virtualizado"""
        selected_rows = self.movements_model.get_checked_rows()
        total_count = self.movements_model.rowCount()
        selected_count = len(selected_rows)
        
        self.selection_count_label.setText(f"📊 Elementos: {selected_count}/{total_count} seleccionados")
        
        # Habilitar/deshabilitar botón de organizar según selección
        self.organize_btn.setEnabled(selected_count > 0)
        
        # Actualizar estadísticas de elementos seleccionados
        self.update_selected_statistics()
    
    def update_selected_statistics(self):
        """🚀 MEJORA: Actualiza las estadísticas usando el modelo virtualizado"""
        selected_size = 0
        selected_files = 0
        
        # Obtener filas seleccionadas del modelo
        selected_rows = self.movements_model.get_checked_rows()
        
        for row in selected_rows:
            row_data = self.movements_model.get_row_data(row)
            if row_data:
                # Sumar tamaño
                selected_size += row_data.get('size_bytes', 0)
                
                # Contar archivos
                selected_files += 1
        
        # Actualizar las tarjetas de estadísticas
        self.total_size_label.setText(f"💾 {self.format_size(selected_size)}")
        self.total_files_label.setText(f"📄 {selected_files:,} archivos")
        
        # Log de la actualización (solo si hay cambios significativos)
        if selected_files > 0:
            self.log_message(f"📊 Estadísticas actualizadas: {selected_files} elementos seleccionados ({self.format_size(selected_size)})")
    
    def update_statistics(self):
        """Actualiza las estadísticas mostradas en la barra de estado y el bloque detallado"""
        if not hasattr(self, 'folder_movements') or not hasattr(self, 'file_movements'):
            return
        
        # Calcular estadísticas por categoría
        category_stats = defaultdict(lambda: {'count': 0, 'size': 0})
        
        # Contar carpetas por categoría
        for mov in self.folder_movements:
            category = mov['category']
            category_stats[category]['count'] += 1
            category_stats[category]['size'] += mov.get('size', 0)
        
        # Contar archivos por categoría
        for mov in self.file_movements:
            category = mov['category']
            category_stats[category]['count'] += 1
            category_stats[category]['size'] += mov.get('size', 0)
        
        # Formatear estadísticas para la barra de estado
        stats_text = ""
        for category in ['MUSICA', 'VIDEOS', 'IMAGENES', 'DOCUMENTOS', 'PROGRAMAS', 'CODIGO', 'VARIOS']:
            if category in category_stats:
                count = category_stats[category]['count']
                if count > 0:
                    percentage = (count / (len(self.folder_movements) + len(self.file_movements))) * 100
                    stats_text += f"{category}({percentage:.0f}%) • "
        
        # Limpiar el último "• "
        if stats_text.endswith("• "):
            stats_text = stats_text[:-2]
        
        if stats_text:
            self.stats_label.setText(f"📈 {stats_text}")
        else:
            self.stats_label.setText("📈 MÚSICA(0%) • VIDEOS(0%) • IMÁG(0%) • VARIOS(0%)")
        
        # Actualizar estadísticas detalladas
        self.update_detailed_statistics(category_stats)
    
    def update_detailed_statistics(self, category_stats):
        """Actualiza las estadísticas detalladas del bloque de estadísticas mejorado"""
        # Calcular totales
        total_size = sum(stats['size'] for stats in category_stats.values())
        total_files = sum(stats['count'] for stats in category_stats.values())
        
        # Actualizar etiquetas de tamaño y archivos con formato mejorado
        self.total_size_label.setText(f"💾 {self.format_size(total_size)}")
        self.total_files_label.setText(f"📄 {total_files:,} archivos")
        
        # Formatear estadísticas por categoría de manera más organizada
        category_text = ""
        category_count = 0
        
        # Ordenar categorías por cantidad de archivos
        sorted_categories = sorted(category_stats.items(), key=lambda x: x[1]['count'], reverse=True)
        
        for category, stats in sorted_categories:
            if stats['count'] > 0:
                count = stats['count']
                size = stats['size']
                category_text += f"<b>{category}:</b> {count:,} archivos ({self.format_size(size)})<br/>"
                category_count += 1
        
        if category_text:
            # Añadir resumen al inicio
            category_text = f"<div style='margin-bottom: 8px;'><b>📊 {category_count} categorías detectadas:</b></div>" + category_text
            self.category_stats_label.setText(category_text)
        else:
            self.category_stats_label.setText("📁 <b>Por categoría:</b> Sin datos detectados")
        
        # Actualizar información de categorías disponibles con formato mejorado
        categories = self.category_manager.get_categories()
        available_text = ""
        total_extensions = 0
        
        for category, extensions in categories.items():
            available_text += f"<b>{category}:</b> {len(extensions)} extensiones<br/>"
            total_extensions += len(extensions)
        
        if available_text:
            # Añadir resumen al inicio
            available_text = f"<div style='margin-bottom: 8px;'><b>⚙️ {len(categories)} categorías configuradas ({total_extensions} extensiones total):</b></div>" + available_text
            self.available_categories_label.setText(available_text)
        else:
            self.available_categories_label.setText("⚙️ <b>Categorías disponibles:</b> Sin datos")
    
    def start_organization(self):
        """🚀 MEJORA: Inicia la organización usando el modelo virtualizado"""
        # Obtener elementos seleccionados del modelo
        selected_folder_movements = []
        selected_file_movements = []
        
        selected_rows = self.movements_model.get_checked_rows()
        
        for row in selected_rows:
            row_data = self.movements_model.get_row_data(row)
            
            if not row_data:
                continue
            
            row_type = row_data.get('type', '')
            
            if row_type == 'folder':
                # Es una carpeta
                original_data = row_data.get('original_data')
                if original_data:
                    selected_folder_movements.append(original_data)
                    
            elif row_type == 'file_group':
                # Es un grupo de archivos sueltos
                group_files = row_data.get('group_files', [])
                selected_file_movements.extend(group_files)
        
        # Verificar si se deben mover carpetas completas según el checkbox
        move_folders = self.move_folders_checkbox.isChecked()
        
        if not move_folders:
            # Si no se deben mover carpetas, solo procesar archivos sueltos
            selected_folder_movements = []
            self.log_message("ℹ️ Modo: Solo archivos sueltos (carpetas ignoradas)")
        else:
            self.log_message("ℹ️ Modo: Carpetas completas + archivos sueltos")
        
        if not selected_folder_movements and not selected_file_movements:
            QMessageBox.warning(self, "Advertencia", "No hay elementos seleccionados para organizar.")
            return
        
        # Calcular tamaño total de elementos seleccionados
        total_selected_size = 0
        for mov in selected_folder_movements:
            total_selected_size += mov.get('size', 0)
        for mov in selected_file_movements:
            total_selected_size += mov.get('size', 0)
        
        formatted_size = self.format_size(total_selected_size)
        
        # Mensaje de confirmación según el modo
        if move_folders:
            confirm_message = f"¿Proceder a organizar {len(selected_folder_movements)} carpetas y {len(selected_file_movements)} archivos?\n\n"
        else:
            confirm_message = f"¿Proceder a organizar solo {len(selected_file_movements)} archivos sueltos?\n\n"
            confirm_message += "⚠️ Las carpetas seleccionadas serán ignoradas.\n\n"
        
        confirm_message += f"Tamaño total seleccionado: {formatted_size}\n\n"
        confirm_message += "Esta acción moverá solo los archivos y carpetas seleccionados."
        
        reply = QMessageBox.question(
            self, 
            "Confirmar Organización",
            confirm_message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        folder_path = self.folder_input.text().strip()
        
        # Crear worker usando el gestor centralizado
        worker_id = f"organize_{int(time.time())}"
        organize_worker = OrganizeWorker(folder_path, selected_folder_movements, selected_file_movements)
        
        # Guardar referencia al worker para limpieza
        if not hasattr(self, '_active_workers'):
            self._active_workers = []
        self._active_workers.append(organize_worker)
        
        # Conectar señales específicas del worker
        organize_worker.progress_update.connect(self.log_message)
        organize_worker.organize_complete.connect(self.on_organize_complete)
        
        # Conectar señal de finalización para limpiar el worker
        organize_worker.finished.connect(lambda: self._cleanup_worker(organize_worker))
        
        # Iniciar worker
        organize_worker.start()
        self.log_message(f"✅ Worker de organización iniciado: {worker_id}")
    
    def on_organize_complete(self, success, message):
        """Maneja completación de la organización"""
        # Restaurar UI
        self.organize_btn.setEnabled(True)
        self.organize_btn.setText("📁 Organizar Archivos")
        self.progress_bar.setVisible(False)
        
        if success:
            self.log_message("✅ " + message)
            QMessageBox.information(self, "Organización Completada", message)
        else:
            self.log_message("❌ " + message)
            QMessageBox.critical(self, "Error de Organización", message)
    
    def open_configuration(self):
        """Abre la ventana de configuración"""
        dialog = ConfigDialog(self, self.category_manager)
        
        # Aplicar tema actual al diálogo
        self.apply_theme_to_dialog_simple(dialog)
        
        # Conectar señal de cambios de interfaz
        dialog.interface_changes_requested.connect(self.apply_interface_changes)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Actualizar categorías
            self.category_manager = dialog.category_manager
            
            # Actualizar información de categorías
            self.update_categories_info()
            
            QMessageBox.information(self, "✅ Configuración Actualizada", 
                "✅ Configuración de categorías actualizada.\n\n"
                "🎨 Los cambios de tema y fuente se aplican INMEDIATAMENTE.\n"
                "📁 Los cambios de categorías se aplican en el próximo análisis.")
    
    def apply_saved_interface_settings(self):
        """Aplica la configuración de interfaz guardada UNA SOLA VEZ"""
        try:
            # SOLO UNA APLICACIÓN para evitar conflictos
            theme = self.app_config.get_theme()
            font_size = self.app_config.get_font_size()
            
            # Aplicar tema y fuente JUNTOS en una sola operación
            self.apply_theme_and_font_together(theme, font_size)
            
            # Checkbox usa estilos básicos del tema
            
            self.log_message(f"✅ Configuración aplicada: {theme}, {font_size}px")
            
        except Exception as e:
            self.log_message(f"⚠️ Error aplicando configuración guardada: {str(e)}")
    
    def apply_theme_and_font_together(self, theme_name: str, font_size: int):
        """Aplica tema y fuente JUNTOS de forma simple y segura"""
        try:
            from PyQt6.QtWidgets import QApplication, QDialog, QPushButton
            app = QApplication.instance()
            if not app:
                return
            
            # Obtener paleta y CSS del tema
            palette = ThemeManager.apply_theme_to_palette(theme_name)
            css_styles = ThemeManager.get_css_styles(theme_name, font_size)
            
            # PASO 0: LIMPIAR estilos anteriores de la aplicación completa
            app.setStyleSheet("")
            self.setStyleSheet("")
            for widget in self.findChildren(QWidget):
                try:
                    widget.setStyleSheet("")
                except:
                    pass
            
            # PASO 1: Aplicar a toda la aplicación
            app.setPalette(palette)
            app.setStyleSheet(css_styles)
            
            # PASO 2: Aplicar a la ventana principal
            self.setPalette(palette)
            self.setStyleSheet(css_styles)
            
            # PASO 3: Aplicar a todos los widgets hijos (optimizado - sin duplicados)
            processed_widgets = set()  # Para evitar procesar el mismo widget dos veces
            
            def apply_to_widget_safe(widget):
                """Aplica tema a un widget de forma segura"""
                if widget in processed_widgets:
                    return
                processed_widgets.add(widget)
                
                try:
                    widget.setPalette(palette)
                    # Solo aplicar CSS si no tiene estilos personalizados con !important
                    current_style = widget.styleSheet() or ""
                    if not current_style or '!important' not in current_style:
                        widget.setStyleSheet(css_styles)
                    widget.update()
                except:
                    pass
            
            # Aplicar a todos los widgets hijos de la ventana principal (sin recursión duplicada)
            for widget in self.findChildren(QWidget):
                apply_to_widget_safe(widget)
            
            # PASO 4: Aplicar estilos a tarjetas y elementos especiales
            self.apply_stats_cards_styles(theme_name)
            
            # PASO 5: Actualizar todos los diálogos abiertos (especialmente ConfigDialog)
            for widget in app.allWidgets():
                if isinstance(widget, QDialog) and widget.isVisible():
                    try:
                        if hasattr(widget, 'apply_current_theme_to_self'):
                            # Aplicar inmediatamente a todos los diálogos
                            widget.apply_current_theme_to_self()
                        else:
                            # Fallback: aplicar tema básico
                            widget.setPalette(palette)
                            widget.setStyleSheet(css_styles)
                            for child in widget.findChildren(QWidget):
                                try:
                                    child.setPalette(palette)
                                    child.setStyleSheet(css_styles)
                                except:
                                    pass
                            widget.update()
                            widget.repaint()
                    except:
                        pass
            
            # PASO 6: Refrescar DiskViewer (esto aplicará sus propios estilos)
            if hasattr(self, 'disk_viewer') and self.disk_viewer:
                try:
                    # Limpiar estilos del DiskViewer primero
                    self.disk_viewer.setStyleSheet("")
                    for child in self.disk_viewer.findChildren(QWidget):
                        try:
                            child.setStyleSheet("")
                        except:
                            pass
                    # Aplicar nuevos estilos
                    self.disk_viewer.apply_theme_styles(theme_name)
                    
                    # Refrescar la tabla de discos para aplicar nuevos colores
                    QTimer.singleShot(150, lambda: self._refresh_disk_viewer_after_theme(theme_name))
                except:
                    pass
            
            # PASO 7: Refrescar todas las tablas y widgets que puedan tener datos visuales
            QTimer.singleShot(200, lambda: self._refresh_all_tables_after_theme())
            
            # PASO 8: Re-aplicar anchos de columna de la tabla principal después del tema
            QTimer.singleShot(250, lambda: self._reapply_table_column_widths())
            
            # Actualización final - UNA SOLA VEZ
            self.update()
            self.repaint()
            app.processEvents()
                
        except Exception as e:
            self.log_message(f"⚠️ Error aplicando tema y fuente: {str(e)}")
            import traceback
            self.log_message(f"Traceback: {traceback.format_exc()}")
    
    def _cleanup_worker(self, worker):
        """Limpia un worker después de que termine"""
        try:
            if worker in self._active_workers:
                self._active_workers.remove(worker)
            # Esperar a que el thread termine antes de eliminarlo
            if worker.isRunning():
                worker.wait(1000)  # Esperar máximo 1 segundo
            worker.deleteLater()
        except Exception:
            pass
    
    def apply_theme_to_all_widgets_simple(self, palette, css_styles, update_visual: bool = True):
        """Aplica tema a todos los widgets de forma simple y eficiente"""
        try:
            # Aplicar a todos los widgets hijos
            for widget in self.findChildren(QWidget):
                try:
                    widget.setPalette(palette)
                    # Solo aplicar CSS si no tiene estilos personalizados con !important
                    current_style = widget.styleSheet() or ""
                    if not current_style or '!important' not in current_style:
                        widget.setStyleSheet(css_styles)
                    
                    # Si el widget tiene apply_theme_styles (como DiskViewer), llamarlo también
                    if hasattr(widget, 'apply_theme_styles') and widget is not self.disk_viewer:
                        try:
                            theme_name = self.app_config.get_theme()
                            widget.apply_theme_styles(theme_name)
                        except:
                            pass
                    
                    # Solo actualizar visualmente si se solicita
                    if update_visual:
                        widget.update()
                except:
                    pass
                    
        except Exception as e:
            pass
    
    def apply_theme_to_dialog_simple(self, dialog):
        """Aplica el tema actual a un diálogo usando el sistema mejorado"""
        try:
            # Si el diálogo tiene método para aplicar tema, usarlo (es el método más completo)
            if hasattr(dialog, 'apply_current_theme_to_self'):
                dialog.apply_current_theme_to_self()
            else:
                # Fallback: aplicar tema básico
                theme = self.app_config.get_theme()
                font_size = self.app_config.get_font_size()
                palette = ThemeManager.apply_theme_to_palette(theme)
                css_styles = ThemeManager.get_css_styles(theme, font_size)
                
                dialog.setPalette(palette)
                dialog.setStyleSheet(css_styles)
                
                # Aplicar a todos los widgets hijos del diálogo
                for widget in dialog.findChildren(QWidget):
                    try:
                        widget.setPalette(palette)
                        widget.setStyleSheet(css_styles)
                    except:
                        pass
                
                dialog.update()
                dialog.repaint()
            
        except Exception as e:
            self.log_message(f"⚠️ Error aplicando tema al diálogo: {str(e)}")
            # Fallback al método anterior
            try:
                theme = self.app_config.get_theme()
                font_size = self.app_config.get_font_size()
                self._apply_theme_to_dialog_fallback(dialog, theme, font_size)
            except:
                pass
    
    def _apply_theme_to_dialog_fallback(self, dialog, theme, font_size):
        """Método de respaldo para aplicar tema a diálogos"""
        try:
            # Aplicar paleta y estilos
            palette = ThemeManager.apply_theme_to_palette(theme)
            css_styles = ThemeManager.get_css_styles(theme, font_size)
            
            # Aplicar al diálogo
            dialog.setPalette(palette)
            dialog.setStyleSheet(css_styles)
            
            # Aplicar a todos los widgets hijos del diálogo de forma recursiva
            def apply_to_all_widgets(widget):
                try:
                    widget.setPalette(palette)
                    # Solo aplicar estilos si no tiene estilos personalizados ya definidos
                    if not widget.styleSheet():
                        widget.setStyleSheet(css_styles)
                    elif "QInputDialog" in str(type(widget)):
                        # Forzar estilos para QInputDialog que pueden tener estilos por defecto
                        widget.setStyleSheet(css_styles)
                    
                    # Aplicar recursivamente a todos los hijos
                    for child in widget.children():
                        if hasattr(child, 'setPalette'):
                            apply_to_all_widgets(child)
                except Exception:
                    pass
            
            # Aplicar a todos los widgets hijos del diálogo
            for child in dialog.findChildren(QWidget):
                apply_to_all_widgets(child)
            
            # Forzar actualización completa
            dialog.update()
            dialog.repaint()
            dialog.show()  # Forzar repintado
            
        except Exception as e:
            self.log_message(f"⚠️ Error en método de respaldo: {str(e)}")
    
    def apply_interface_changes(self, font_size: int, theme: str):
        """Aplica cambios de interfaz desde el diálogo de configuración"""
        try:
            # Guardar configuración PRIMERO
            self.app_config.set_font_size(font_size)
            self.app_config.set_theme(theme)
            
            # Aplicar tema y fuente JUNTOS
            self.apply_theme_and_font_together(theme, font_size)
            
            # Actualizar diálogos abiertos si existen (especialmente ConfigDialog)
            self.refresh_open_dialogs()
            
            # Asegurar que el ConfigDialog se actualice inmediatamente si está abierto
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                for widget in app.allWidgets():
                    if isinstance(widget, ConfigDialog) and widget.isVisible():
                        # Actualizar INMEDIATAMENTE sin delay
                        widget.apply_current_theme_to_self()
            
            self.log_message(f"✅ Configuración de interfaz aplicada: {font_size}px, {theme}")
            
        except Exception as e:
            self.log_message(f"❌ Error aplicando cambios de interfaz: {str(e)}")
    
    def _refresh_disk_viewer_after_theme(self, theme_name: str):
        """Refresca el DiskViewer después de aplicar el tema"""
        try:
            if hasattr(self, 'disk_viewer') and self.disk_viewer:
                # Refrescar la tabla de discos para aplicar nuevos colores
                self.disk_viewer.refresh_disks()
                
                # Actualizar información del disco seleccionado si hay uno
                selected_disk = self.disk_viewer.get_selected_disk_path()
                if selected_disk:
                    self.disk_viewer.update_selected_disk_info(selected_disk)
                
                # Forzar actualización visual
                self.disk_viewer.update()
                self.disk_viewer.repaint()
        except Exception as e:
            self.log_message(f"⚠️ Error refrescando DiskViewer después del tema: {str(e)}")
    
    def _refresh_all_tables_after_theme(self):
        """Refresca todas las tablas y widgets después de aplicar el tema"""
        try:
            from PyQt6.QtWidgets import QTableWidget, QTableView
            
            # Refrescar tabla de movimientos si existe
            if hasattr(self, 'movements_table') and self.movements_table:
                self.movements_table.update()
                self.movements_table.repaint()
            
            # Refrescar tabla de duplicados si existe
            if hasattr(self, 'duplicates_dashboard') and self.duplicates_dashboard:
                try:
                    # El tema ya se aplicó en el paso 3, solo refrescar la tabla
                    if hasattr(self.duplicates_dashboard, 'duplicates_table') and self.duplicates_dashboard.duplicates_table:
                        self.duplicates_dashboard.duplicates_table.update()
                        self.duplicates_dashboard.duplicates_table.repaint()
                    # Aplicar estilos al botón de escaneo si existe
                    if hasattr(self.duplicates_dashboard, 'apply_scan_button_style'):
                        self.duplicates_dashboard.apply_scan_button_style()
                except Exception as e:
                    self.log_message(f"⚠️ Error refrescando DuplicatesDashboard: {str(e)}")
            
            # Refrescar todas las tablas encontradas
            for widget in self.findChildren(QTableWidget):
                try:
                    widget.update()
                    widget.repaint()
                except:
                    pass
            for widget in self.findChildren(QTableView):
                try:
                    widget.update()
                    widget.repaint()
                except:
                    pass
            
            # Forzar actualización de la ventana principal
            self.update()
            self.repaint()
        except Exception as e:
            self.log_message(f"⚠️ Error refrescando tablas después del tema: {str(e)}")
    
    def _reapply_table_column_widths(self):
        """✅ Re-aplica los anchos de columna de TODAS las tablas después de cambiar el tema/fuente"""
        try:
            # 1. Tabla principal de movimientos
            if hasattr(self, 'movements_table') and self.movements_table:
                self.movements_table.setColumnWidth(0, 50)     # ☑️ Checkbox
                self.movements_table.setColumnWidth(1, 900)    # 📂 Elemento - 900px
                self.movements_table.setColumnWidth(2, 200)    # 📁 Destino - 200px
                self.movements_table.setColumnWidth(3, 200)    # 📊 % - 200px
                self.movements_table.setColumnWidth(4, 200)    # 📄 Archivos - 200px
                self.movements_table.setColumnWidth(5, 200)    # 💾 Tamaño - 200px
                self.log_message("📏 Anchos de tabla principal re-aplicados")
            
            # 2. Tabla de duplicados
            if hasattr(self, 'duplicates_dashboard') and self.duplicates_dashboard:
                if hasattr(self.duplicates_dashboard, 'apply_column_widths'):
                    self.duplicates_dashboard.apply_column_widths()
                    self.log_message("📏 Anchos de tabla de duplicados re-aplicados")
            
            # 3. Tabla de discos (en DiskViewer)
            if hasattr(self, 'disk_viewer') and self.disk_viewer:
                if hasattr(self.disk_viewer, 'disks_table'):
                    # Anchos predefinidos de la tabla de discos
                    self.disk_viewer.disks_table.setColumnWidth(0, 80)   # Unidad
                    self.disk_viewer.disks_table.setColumnWidth(5, 80)   # % Uso
                    self.disk_viewer.disks_table.setColumnWidth(6, 100)  # Sistema
                    self.disk_viewer.disks_table.setColumnWidth(7, 130)  # Botón
                    self.log_message("📏 Anchos de tabla de discos re-aplicados")
            
            self.log_message("✅ Todos los anchos de columna re-aplicados después del cambio")
        except Exception as e:
            self.log_message(f"⚠️ Error re-aplicando anchos de columna: {str(e)}")
    
    def refresh_open_dialogs(self):
        """Actualiza todos los diálogos abiertos con el tema actual"""
        try:
            # Buscar todos los diálogos hijos de la ventana principal
            from PyQt6.QtWidgets import QDialog
            for child in self.findChildren(QDialog):
                if child.isVisible() and child.parent() == self:
                    self.apply_theme_to_dialog_simple(child)
            
            self.log_message("🔄 Diálogos abiertos actualizados con nuevo tema")
        except Exception as e:
            self.log_message(f"⚠️ Error actualizando diálogos: {str(e)}")
    
    # Función eliminada - ahora se aplica junto con el tema
    
    def apply_stats_cards_styles(self, theme_name: str):
        """Aplica estilos dinámicos a las tarjetas de estadísticas y separadores"""
        try:
            colors = ThemeManager.get_theme_colors(theme_name)
            
            # Aplicar estilos a separadores
            for separator in self.findChildren(QFrame):
                if separator.objectName() in ["separator1", "separator2"]:
                    separator.setStyleSheet(f"QFrame {{ color: {colors['border']}; }}")
            
            # Aplicar estilos a tarjetas de estadísticas
            card_style = f"""
                QFrame {{
                    background-color: {colors['surface']};
                    border: 1px solid {colors['border']};
                    border-radius: 8px;
                    padding: 12px;
                    margin: 4px;
                }}
                QFrame:hover {{
                    border: 2px solid {colors['accent']};
                }}
            """
            for card in self.findChildren(QFrame):
                if card.objectName() == "stats_card":
                    card.setStyleSheet(card_style)
            
            # Aplicar estilos a headers de tarjetas
            header_style = f"""
                QLabel {{
                    color: {colors['accent']};
                    font-weight: bold;
                    font-size: 12px;
                    text-align: center;
                    margin-bottom: 8px;
                }}
            """
            for header in self.findChildren(QLabel):
                if header.objectName() == "stats_card_header":
                    header.setStyleSheet(header_style)
            
            # Aplicar estilos a labels de valores
            value_style = f"""
                QLabel {{
                    color: {colors['text_primary']};
                    font-weight: bold;
                    font-size: 14px;
                    text-align: center;
                    padding: 8px;
                    background-color: {colors['surface']};
                    border-radius: 4px;
                    border: 1px solid {colors['border']};
                }}
            """
            value_labels = ["total_size_label", "total_files_label", "category_stats_label", "available_categories_label"]
            for label in self.findChildren(QLabel):
                if label.objectName() in value_labels:
                    label.setStyleSheet(value_style)
        except Exception as e:
            self.log_message(f"⚠️ Error aplicando estilos a tarjetas: {str(e)}")
    
    def apply_theme(self, theme_name: str):
        """Aplica un tema específico (usa apply_theme_and_font_together internamente)"""
        try:
            # Obtener el tamaño de fuente actual
            current_font_size = self.app_config.get_font_size()
            
            # Usar el método unificado
            self.apply_theme_and_font_together(theme_name, current_font_size)
                
            self.log_message(f"✅ Tema aplicado: {theme_name}")
            
        except Exception as e:
            self.log_message(f"⚠️ Error aplicando tema: {str(e)}")
    
    # Función eliminada - simplificada
    
    # Función eliminada - simplificada
    
    # Funciones complejas eliminadas - simplificadas en apply_theme_to_all_widgets_simple
    
    def update_categories_info(self):
        """Actualiza la información de categorías mostrada"""
        # Buscar y actualizar el widget de información de categorías
        for child in self.findChildren(QGroupBox):
            if "Información" in child.title():
                # Limpiar layout existente
                for i in reversed(range(child.layout().count())):
                    child.layout().itemAt(i).widget().setParent(None)
                
                # Añadir nueva información
                self.add_categories_info(child.layout())
                break
    
    def log_message(self, message):
        """Añade un mensaje al log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # Auto-scroll al final
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # Actualizar contador de entradas
        self.update_log_info()
    
    def clear_log(self):
        """Limpia todo el contenido del log"""
        reply = QMessageBox.question(
            self, "Limpiar Log",
            "¿Estás seguro de que quieres limpiar todo el contenido del log?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.log_text.clear()
            self.log_message("🗑️ Log limpiado por el usuario")
    
    def export_log(self):
        """Exporta el contenido del log a un archivo de texto"""
        from datetime import datetime
        
        # Generar nombre de archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"log_organizador_{timestamp}.txt"
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "📤 Exportar Log",
            default_filename,
            "Archivos de texto (*.txt);;Todos los archivos (*)"
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write("📝 LOG DEL ORGANIZADOR DE ARCHIVOS\n")
                    f.write("=" * 50 + "\n")
                    f.write(f"Fecha de exportación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Total de entradas: {self.get_log_entry_count()}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(self.log_text.toPlainText())
                
                QMessageBox.information(
                    self, "✅ Exportación Exitosa",
                    f"Log exportado exitosamente a:\n{filepath}\n\n"
                    f"Total de entradas exportadas: {self.get_log_entry_count()}"
                )
                
                self.log_message(f"📤 Log exportado a: {filepath}")
                
            except Exception as e:
                QMessageBox.critical(
                    self, "❌ Error de Exportación",
                    f"No se pudo exportar el log:\n{str(e)}"
                )
                self.log_message(f"❌ Error al exportar log: {str(e)}")
    
    def scroll_log_to_bottom(self):
        """Desplaza el log hasta la entrada más reciente"""
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self.log_message("⬇️ Desplazado al final del log")
    
    def update_log_info(self):
        """Actualiza la información del log"""
        entry_count = self.get_log_entry_count()
        self.log_info_label.setText(f"📊 Total de entradas: {entry_count}")
    
    def get_log_entry_count(self):
        """Obtiene el número total de entradas en el log"""
        text = self.log_text.toPlainText()
        if not text.strip():
            return 0
        
        # Contar líneas que empiezan con timestamp [HH:MM:SS]
        lines = text.split('\n')
        count = 0
        for line in lines:
            if line.strip() and line.strip().startswith('[') and ']' in line:
                count += 1
        
        return count
    
    def on_disk_selected_for_organize(self, disk_path):
        """Maneja la selección de un disco para organizar archivos"""
        try:
            # Cambiar a la pestaña de organizar
            self.main_tabs.setCurrentIndex(0)
            
            # Establecer la ruta del disco seleccionado
            self.folder_input.setText(disk_path)
            
            # Log del cambio
            self.log_message(f"💾 Disco seleccionado para organización: {disk_path}")
            
            # Verificar que la ventana esté completamente inicializada antes de analizar
            if hasattr(self, 'analyze_btn') and self.analyze_btn:
                # Auto-iniciar análisis del disco con delay más largo
                QTimer.singleShot(2000, self.start_analysis)
            else:
                self.log_message("⚠️ Ventana no completamente inicializada, análisis manual requerido")
            
        except Exception as e:
            self.log_message(f"❌ Error al seleccionar disco: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error al seleccionar disco:\n{str(e)}")
    
    def format_size(self, size_bytes):
        """Formatea el tamaño en bytes a una representación legible"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    # ✅ NUEVO: Métodos para gestión de columnas y menú contextual
    
    def show_context_menu(self, position):
        """Muestra menú contextual para la tabla de movimientos"""
        try:
            # Obtener la fila donde se hizo clic
            index = self.movements_table.indexAt(position)
            if not index.isValid():
                return
                
            row = index.row()
            
            # Obtener información del elemento
            model = self.movements_table.model()
            element_data = model.data(model.index(row, 1), Qt.ItemDataRole.DisplayRole)
            destination_data = model.data(model.index(row, 2), Qt.ItemDataRole.DisplayRole)
            
            if not element_data:
                return
            
            # Crear menú contextual
            menu = QMenu(self)
            
            # Acción para abrir ubicación del archivo
            if hasattr(self, 'folder_path') and self.folder_path:
                open_location_action = QAction("📁 Abrir ubicación", self)
                open_location_action.triggered.connect(lambda: self.open_file_location(self.folder_path))
                menu.addAction(open_location_action)
            
            # Acción para expandir/contraer grupo (si es aplicable)
            row_data = model.get_row_data(row)
            if row_data and row_data.get('is_group', False):
                if row_data.get('is_expanded', False):
                    collapse_action = QAction("📁 Contraer grupo", self)
                    collapse_action.triggered.connect(lambda: model.collapse_group(row))
                else:
                    expand_action = QAction("📂 Expandir grupo", self)
                    expand_action.triggered.connect(lambda: model.expand_group(row))
                menu.addAction(expand_action if not row_data.get('is_expanded', False) else collapse_action)
            
            # Mostrar menú
            menu.exec(self.movements_table.mapToGlobal(position))
            
        except Exception as e:
            self.log_message(f"❌ Error en menú contextual: {str(e)}")
    
    def open_file_location(self, folder_path):
        """Abre la ubicación del archivo en el explorador"""
        try:
            import subprocess
            import sys
            
            if sys.platform == "win32":
                # Windows - abrir explorer
                subprocess.Popen(f'explorer "{folder_path}"')
            elif sys.platform == "darwin":
                # macOS
                subprocess.Popen(["open", str(folder_path)])
            else:
                # Linux
                subprocess.Popen(["xdg-open", str(folder_path)])
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo abrir la ubicación:\n{str(e)}")
    
    def on_header_clicked(self, logical_index):
        """Maneja el clic en el encabezado de una columna para ordenar"""
        # Solo permitir ordenamiento en columnas de tamaño y porcentaje
        if logical_index in [3, 5]:  # Porcentaje (3) y Tamaño (5)
            # Obtener información de ordenamiento actual
            sort_info = self.movements_model.get_sort_info() if hasattr(self.movements_model, 'get_sort_info') else {'column': -1, 'order': Qt.SortOrder.AscendingOrder}
            
            # Determinar nuevo orden
            if sort_info['column'] == logical_index:
                # Misma columna, cambiar orden
                new_order = Qt.SortOrder.DescendingOrder if sort_info['order'] == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
            else:
                # Nueva columna, empezar con ascendente
                new_order = Qt.SortOrder.AscendingOrder
            
            # Aplicar ordenamiento si el modelo lo soporta
            if hasattr(self.movements_model, 'sort'):
                self.movements_model.sort(logical_index, new_order)
            
            # Actualizar indicador visual
            header = self.movements_table.horizontalHeader()
            header.setSortIndicator(logical_index, new_order)
            
            self.log_message(f"📊 Ordenando por columna {logical_index} ({'descendente' if new_order == Qt.SortOrder.DescendingOrder else 'ascendente'})")
    
    
    def closeEvent(self, event):
        """Maneja el cierre de la ventana con limpieza completa"""
        try:
            self.log_message("🔄 Cerrando aplicación...")
            
            # Limpiar todos los workers activos
            if hasattr(self, '_active_workers'):
                for worker in self._active_workers[:]:  # Copia de la lista
                    try:
                        if worker.isRunning():
                            worker.quit()
                            worker.wait(2000)  # Esperar máximo 2 segundos
                        worker.deleteLater()
                    except:
                        pass
                self._active_workers.clear()
            
            # Limpiar estado centralizado (si está disponible)
            try:
                if hasattr(app_state, 'cleanup'):
                    app_state.cleanup()
            except Exception as cleanup_error:
                self.log_message(f"⚠️ Error durante cleanup de app_state: {cleanup_error}")
            
            self.log_message("✅ Aplicación cerrada correctamente")
            
        except Exception as e:
            self.log_message(f"❌ Error durante el cierre: {e}")
            import traceback
            self.log_message(traceback.format_exc())
        
        # Aceptar el evento de cierre
        event.accept()
