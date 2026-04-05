#!/usr/bin/env python3
"""
MainWindowSetup - Configuración y construcción de la UI de MainWindow
Extraído de main_window.py para mejorar mantenibilidad
"""

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
from src.gui.table_models import VirtualizedMovementsModel, CheckboxDelegate


class MainWindowSetup:
    """Mixin para configuración de UI de MainWindow"""
    
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
        
        # Header principal
        self._create_header(main_layout)
        
        # Sistema de pestañas
        self._create_main_tabs(main_layout)
        
        # Pestaña Organizar Archivos
        self._create_organize_tab()
        
        # Barra de ruta y análisis
        self._create_path_bar()
        
        # Barra de estado inteligente
        self._create_status_bar()
        
        # Barra de selección
        self._create_selection_bar()
        
        # Tabla principal
        self._create_main_table()
        
        # Botón de organizar
        self._create_organize_button()
        
        # Barra de progreso
        self._create_progress_bar()
        
        # Estadísticas detalladas
        self._create_stats_group()
        
        # Conectar eventos
        self._connect_table_events()
        self._connect_input_events()
    
    def _create_header(self, layout):
        """Crea el header con título y botón de configuración"""
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🏠 Organizador de Archivos y Carpetas")
        title_label.setToolTip("🏠 Aplicación principal para organizar y gestionar archivos por categorías automáticamente")
        title_label.setObjectName("main_title_label")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.config_btn = QPushButton("⚙️ Configuración")
        self.config_btn.setToolTip("⚙️ Abre la configuración de categorías y extensiones")
        self.config_btn.setObjectName("config_button")
        self.config_btn.clicked.connect(self.open_configuration)
        header_layout.addWidget(self.config_btn)
        
        layout.addLayout(header_layout)
    
    def _create_main_tabs(self, layout):
        """Crea el sistema de pestañas principal"""
        self.main_tabs = QTabWidget()
        self.main_tabs.setObjectName("main_tabs")
        
        # Crear pestañas vacías (se llenarán después)
        self.organize_tab = QWidget()
        self.disks_tab = QWidget()
        self.duplicates_tab = QWidget()
        self.log_tab = QWidget()
        
        # Añadir pestañas con tooltips
        self.main_tabs.addTab(self.organize_tab, "📁 Organizar Archivos")
        self.main_tabs.setTabToolTip(0, "📁 Organiza archivos de una carpeta específica por categorías automáticamente")
        
        self.main_tabs.addTab(self.disks_tab, "💾 Gestión de Discos")
        self.main_tabs.setTabToolTip(1, "💾 Gestiona y analiza todos los discos del sistema para organización masiva")
        
        self.main_tabs.addTab(self.duplicates_tab, "🔍 Duplicados")
        self.main_tabs.setTabToolTip(2, "🔍 Detecta y gestiona archivos duplicados por contenido usando hashes MD5/SHA256")
        
        self.main_tabs.addTab(self.log_tab, "📝 LOG")
        self.main_tabs.setTabToolTip(3, "📝 Registro detallado de todas las operaciones realizadas en la aplicación")
        
        layout.addWidget(self.main_tabs)
    
    def _create_organize_tab(self):
        """Configura la pestaña de organizar archivos"""
        organize_layout = QVBoxLayout(self.organize_tab)
        organize_layout.setSpacing(10)
        organize_layout.setContentsMargins(15, 15, 15, 15)
        
        # Integrar DiskViewer en la pestaña de discos
        disks_layout = QVBoxLayout(self.disks_tab)
        disks_layout.setSpacing(10)
        disks_layout.setContentsMargins(15, 15, 15, 15)
        
        from src.gui.disk_viewer import DiskViewer
        self.disk_viewer = DiskViewer(disk_manager=None)
        disks_layout.addWidget(self.disk_viewer)
        self.disk_viewer.disk_selected.connect(self.on_disk_selected_for_organize)
        
        # Integrar DuplicatesDashboard
        duplicates_layout = QVBoxLayout(self.duplicates_tab)
        duplicates_layout.setSpacing(10)
        duplicates_layout.setContentsMargins(15, 15, 15, 15)
        
        from src.gui.duplicates_dashboard import DuplicatesDashboard
        self.duplicates_dashboard = DuplicatesDashboard()
        duplicates_layout.addWidget(self.duplicates_dashboard)
        self.duplicates_dashboard.status_update.connect(self.log_message)
        
        # Configurar pestaña de log
        log_layout = QVBoxLayout(self.log_tab)
        log_layout.setSpacing(10)
        log_layout.setContentsMargins(15, 15, 15, 15)
        self.create_log_widget(log_layout)
    
    def _create_path_bar(self):
        """Crea la barra de ruta y análisis"""
        path_layout = QHBoxLayout()
        
        folder_label = QLabel("📂 Ruta:")
        folder_label.setToolTip("📂 Especifica la carpeta que quieres analizar y organizar")
        folder_label.setObjectName("folder_label")
        path_layout.addWidget(folder_label)
        
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("C:/Users/Usuario/Downloads")
        self.folder_input.setToolTip("📁 Escribe la ruta de la carpeta o usa el botón 'Examinar'")
        self.folder_input.setObjectName("folder_input")
        self.folder_input.setFixedHeight(36)
        path_layout.addWidget(self.folder_input)
        
        self.browse_btn = QPushButton("📂 Examinar")
        self.browse_btn.setToolTip("📂 Abre el explorador de archivos para seleccionar una carpeta")
        self.browse_btn.setObjectName("browse_button")
        self.browse_btn.clicked.connect(self.browse_folder)
        self.browse_btn.setFixedHeight(36)
        self.browse_btn.setProperty("styleClass", "warning")
        path_layout.addWidget(self.browse_btn)
        
        self.analyze_btn = QPushButton("🔍 Analizar")
        self.analyze_btn.setToolTip("🔍 Analiza la carpeta seleccionada para ver qué se puede organizar")
        self.analyze_btn.setObjectName("analyze_button")
        self.analyze_btn.clicked.connect(self.start_analysis)
        self.analyze_btn.setFixedHeight(36)
        path_layout.addWidget(self.analyze_btn)
        
        # Acceder al layout de la pestaña organize_tab
        organize_layout = self.organize_tab.layout()
        organize_layout.addLayout(path_layout)
    
    def _create_status_bar(self):
        """Crea la barra de estado con estadísticas integradas"""
        status_layout = QHBoxLayout()
        
        self.selection_count_label = QLabel("📊 Elementos: 0/0 seleccionados")
        self.selection_count_label.setToolTip("📊 Muestra el número de elementos seleccionados vs. total disponible")
        self.selection_count_label.setObjectName("selection_count_label")
        status_layout.addWidget(self.selection_count_label)
        
        self.stats_label = QLabel("📈 MÚSICA(0%) • VIDEOS(0%) • IMÁG(0%) • VARIOS(0%)")
        self.stats_label.setToolTip("📈 Distribución porcentual de archivos por categorías principales")
        self.stats_label.setObjectName("stats_label")
        status_layout.addWidget(self.stats_label)
        
        status_layout.addStretch()
        
        organize_layout = self.organize_tab.layout()
        organize_layout.addLayout(status_layout)
    
    def _create_selection_bar(self):
        """Crea la barra de botones de selección"""
        selection_layout = QHBoxLayout()
        selection_layout.setSpacing(15)
        selection_layout.setContentsMargins(0, 10, 0, 10)
        
        # Grupo 1: Botones de selección
        self._add_selection_buttons(selection_layout)
        
        # Separadores y checkboxes
        self._add_selection_controls(selection_layout)
        
        organize_layout = self.organize_tab.layout()
        organize_layout.addLayout(selection_layout)
    
    def _add_selection_buttons(self, layout):
        """Añade los botones de seleccionar/deseleccionar todo"""
        selection_buttons_group = QHBoxLayout()
        selection_buttons_group.setSpacing(10)
        
        self.select_all_btn = QPushButton("☑️ Seleccionar Todo")
        self.select_all_btn.setToolTip("☑️ Marca todos los elementos para ser organizados")
        self.select_all_btn.clicked.connect(self.select_all_items)
        self.select_all_btn.setObjectName("select_all_btn")
        self.select_all_btn.setFixedHeight(36)
        self.select_all_btn.setMinimumWidth(140)
        self.select_all_btn.setProperty("styleClass", "success")
        selection_buttons_group.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("❌ Deseleccionar Todo")
        self.deselect_all_btn.setToolTip("❌ Desmarca todos los elementos")
        self.deselect_all_btn.clicked.connect(self.deselect_all_items)
        self.deselect_all_btn.setObjectName("deselect_all_btn")
        self.deselect_all_btn.setFixedHeight(36)
        self.deselect_all_btn.setMinimumWidth(140)
        self.deselect_all_btn.setProperty("styleClass", "disabled")
        selection_buttons_group.addWidget(self.deselect_all_btn)
        
        layout.addLayout(selection_buttons_group)
    
    def _add_selection_controls(self, layout):
        """Añade separadores y controles de selección"""
        # Separador 1
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.VLine)
        separator1.setFrameShadow(QFrame.Shadow.Sunken)
        separator1.setMaximumHeight(30)
        separator1.setObjectName("separator1")
        layout.addWidget(separator1)
        
        # Grupo 2: Checkbox de carpetas
        folders_group = QHBoxLayout()
        folders_group.setSpacing(8)
        folders_group.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.move_folders_checkbox = QCheckBox("📁 Mover carpetas completas")
        self.move_folders_checkbox.setToolTip("📁 Si está marcado, mueve carpetas completas. Si no, solo archivos sueltos.")
        self.move_folders_checkbox.setChecked(True)
        folders_group.addWidget(self.move_folders_checkbox)
        
        layout.addLayout(folders_group)
        
        # Separador 2
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        separator2.setMaximumHeight(30)
        separator2.setObjectName("separator2")
        layout.addWidget(separator2)
        
        # Grupo 3: Campo de similitud
        self._add_similarity_control(layout)
        
        # Espaciador final
        layout.addStretch()
    
    def _add_similarity_control(self, layout):
        """Añade el control de similitud mínima"""
        similarity_group = QHBoxLayout()
        similarity_group.setSpacing(8)
        similarity_group.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        target_icon = QLabel("🎯")
        target_icon.setToolTip("🎯 Configuración de similitud para clasificación")
        target_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        target_icon.setMinimumWidth(20)
        target_icon.setMaximumWidth(20)
        similarity_group.addWidget(target_icon)
        
        similarity_label = QLabel("Similitud mínima:")
        similarity_label.setToolTip("🎯 Porcentaje mínimo de similitud para clasificar carpetas")
        similarity_group.addWidget(similarity_label)
        
        self.similarity_spinbox = QSpinBox()
        self.similarity_spinbox.setToolTip("🎯 Porcentaje mínimo de similitud (0-100%) para clasificar carpetas")
        self.similarity_spinbox.setRange(0, 100)
        self.similarity_spinbox.setValue(70)
        self.similarity_spinbox.setSuffix("%")
        self.similarity_spinbox.setMinimumWidth(120)
        self.similarity_spinbox.setMaximumWidth(140)
        self.similarity_spinbox.setFixedHeight(36)
        similarity_group.addWidget(self.similarity_spinbox)
        
        layout.addLayout(similarity_group)
    
    def _create_main_table(self):
        """Crea la tabla principal virtualizada"""
        table_label = QLabel("📋 TABLA PRINCIPAL (Optimizada)")
        table_label.setToolTip("📊 Haz doble clic en las filas de 'archivos sueltos' para expandir")
        self.organize_tab.layout().addWidget(table_label)
        
        # Tabla virtualizada
        self.movements_table = QTableView()
        self.movements_model = VirtualizedMovementsModel()
        self.movements_table.setModel(self.movements_model)
        
        # Delegado para checkboxes
        checkbox_delegate = CheckboxDelegate(self.movements_table)
        self.movements_table.setItemDelegateForColumn(0, checkbox_delegate)
        
        self.movements_table.setToolTip("📊 Vista previa VIRTUALIZADA de todos los cambios")
        
        # Configuración profesional
        self.movements_table.verticalHeader().setDefaultSectionSize(42)
        self.movements_table.setMinimumHeight(350)
        self.movements_table.setAlternatingRowColors(True)
        self.movements_table.setShowGrid(True)
        self.movements_table.setGridStyle(Qt.PenStyle.SolidLine)
        
        # Configurar headers
        self._configure_table_headers()
        
        # Menú contextual
        self.movements_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.movements_table.customContextMenuRequested.connect(self.show_context_menu)
        
        self.organize_tab.layout().addWidget(self.movements_table)
    
    def _configure_table_headers(self):
        """Configura los headers de la tabla"""
        header = self.movements_table.horizontalHeader()
        
        # Establecer anchos
        self.movements_table.setColumnWidth(0, 50)     # Checkbox
        self.movements_table.setColumnWidth(1, 900)    # Elemento
        self.movements_table.setColumnWidth(2, 200)    # Destino
        self.movements_table.setColumnWidth(3, 200)    # %
        self.movements_table.setColumnWidth(4, 200)    # Archivos
        self.movements_table.setColumnWidth(5, 200)    # Tamaño
        
        # Configurar ResizeMode
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        
        # Habilitar ordenamiento
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        header.sectionClicked.connect(self.on_header_clicked)
        
        # Tooltips
        header.setToolTip("☑️ Selección | 📂 Elemento | 📁 Destino | 📊 % | 📄 Archivos | 💾 Tamaño")
        
        # Permitir reordenar columnas
        header.setSectionsMovable(True)
        
        # Selección por filas
        self.movements_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.movements_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
    
    def _create_organize_button(self):
        """Crea el botón principal de organizar"""
        organize_btn_layout = QHBoxLayout()
        
        self.organize_btn = QPushButton("📁 ORGANIZAR ARCHIVOS")
        self.organize_btn.setToolTip("📁 Organiza los archivos y carpetas seleccionados")
        self.organize_btn.setEnabled(False)
        self.organize_btn.setObjectName("organize_button")
        self.organize_btn.clicked.connect(self.start_organization)
        self.organize_btn.setFixedHeight(50)
        
        organize_btn_layout.addWidget(self.organize_btn)
        self.organize_tab.layout().addLayout(organize_btn_layout)
    
    def _create_progress_bar(self):
        """Crea la barra de progreso compacta"""
        progress_layout = QHBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setToolTip("📊 Muestra el progreso de la operación actual")
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.organize_tab.layout().addLayout(progress_layout)
    
    def _create_stats_group(self):
        """Crea el grupo de estadísticas detalladas"""
        stats_group = QGroupBox("📊 ESTADÍSTICAS DETALLADAS")
        stats_group.setToolTip("📊 Información detallada sobre elementos seleccionados y categorías")
        stats_group.setObjectName("stats_group")
        
        main_stats_layout = QVBoxLayout(stats_group)
        
        # Primera fila: Resumen general
        self._create_summary_cards(main_stats_layout)
        
        # Segunda fila: Estadísticas por categoría
        self._create_category_stats(main_stats_layout)
        
        self.organize_tab.layout().addWidget(stats_group)
    
    def _create_summary_cards(self, layout):
        """Crea las tarjetas de resumen"""
        summary_layout = QHBoxLayout()
        
        # Tarjeta de tamaño
        size_card = QFrame()
        size_card.setObjectName("stats_card")
        size_card_layout = QVBoxLayout(size_card)
        
        size_header = QLabel("💾 RESUMEN DE TAMAÑO")
        size_header.setObjectName("stats_card_header")
        size_card_layout.addWidget(size_header)
        
        self.total_size_label = QLabel("💾 Tamaño total: 0 B")
        self.total_size_label.setToolTip("💾 Tamaño total de archivos y carpetas seleccionados")
        self.total_size_label.setObjectName("total_size_label")
        size_card_layout.addWidget(self.total_size_label)
        
        summary_layout.addWidget(size_card)
        
        # Tarjeta de archivos
        files_card = QFrame()
        files_card.setObjectName("stats_card")
        files_card_layout = QVBoxLayout(files_card)
        
        files_header = QLabel("📄 RESUMEN DE ARCHIVOS")
        files_header.setObjectName("stats_card_header")
        files_card_layout.addWidget(files_header)
        
        self.total_files_label = QLabel("📄 Total archivos: 0")
        self.total_files_label.setToolTip("📄 Número total de archivos que serán organizados")
        self.total_files_label.setObjectName("total_files_label")
        files_card_layout.addWidget(self.total_files_label)
        
        summary_layout.addWidget(files_card)
        
        layout.addLayout(summary_layout)
    
    def _create_category_stats(self, layout):
        """Crea las tarjetas de estadísticas por categoría"""
        category_stats_layout = QHBoxLayout()
        
        # Tarjeta de distribución
        category_card = QFrame()
        category_card.setObjectName("stats_card")
        category_card_layout = QVBoxLayout(category_card)
        
        category_header = QLabel("📁 DISTRIBUCIÓN POR CATEGORÍA")
        category_header.setObjectName("stats_card_header")
        category_card_layout.addWidget(category_header)
        
        self.category_stats_label = QLabel("📁 Por categoría: Sin datos")
        self.category_stats_label.setToolTip("📁 Distribución de archivos por categorías específicas")
        self.category_stats_label.setObjectName("category_stats_label")
        self.category_stats_label.setWordWrap(True)
        category_card_layout.addWidget(self.category_stats_label)
        
        category_stats_layout.addWidget(category_card)
        
        # Tarjeta de categorías disponibles
        available_card = QFrame()
        available_card.setObjectName("stats_card")
        available_card_layout = QVBoxLayout(available_card)
        
        available_header = QLabel("⚙️ CATEGORÍAS DISPONIBLES")
        available_header.setObjectName("stats_card_header")
        available_card_layout.addWidget(available_header)
        
        self.available_categories_label = QLabel("⚙️ Categorías disponibles: Cargando...")
        self.available_categories_label.setToolTip("⚙️ Lista de todas las categorías configuradas")
        self.available_categories_label.setObjectName("available_categories_label")
        self.available_categories_label.setWordWrap(True)
        available_card_layout.addWidget(self.available_categories_label)
        
        category_stats_layout.addWidget(available_card)
        
        layout.addLayout(category_stats_layout)
    
    def _connect_table_events(self):
        """Conecta eventos de la tabla virtualizada"""
        self.movements_model.dataChanged.connect(self.on_model_data_changed)
        self.movements_table.doubleClicked.connect(self.on_table_double_clicked)
    
    def _connect_input_events(self):
        """Conecta eventos de entrada"""
        self.folder_input.textChanged.connect(self.on_folder_path_changed)
