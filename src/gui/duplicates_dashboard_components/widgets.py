#!/usr/bin/env python3
"""
DuplicateWidgets - Widgets y componentes UI del Dashboard de Duplicados
Extraído de duplicates_dashboard.py para mejorar mantenibilidad
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QGroupBox,
    QCheckBox, QComboBox, QLineEdit, QFileDialog, QMessageBox, QSplitter,
    QTextEdit, QTabWidget, QScrollArea, QFrame, QSpinBox, QDialog, QMenu, QTableView,
    QStyledItemDelegate, QStyle, QStyleOptionButton, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSettings, QRect, QSize, QPoint
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor, QAction, QPainter


class CheckboxDelegate(QStyledItemDelegate):
    """Delegado personalizado para checkboxes centrados con colores del tema"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_table = parent
    
    def paint(self, painter, option, index):
        """Pinta el checkbox centrado en la celda con colores del tema actual"""
        if not index.isValid():
            return
        
        checked = index.data(Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Checked
        theme_colors = self.get_theme_colors()
        checkbox_rect = self.get_checkbox_rect(option.rect)
        
        painter.save()
        try:
            self.paint_custom_checkbox(painter, checkbox_rect, checked, theme_colors)
        finally:
            painter.restore()
    
    def get_theme_colors(self):
        """Obtiene los colores del tema actual"""
        try:
            from src.utils.themes import ThemeManager
            from src.utils.app_config import AppConfig
            app_config = AppConfig()
            current_theme = app_config.get_theme()
            return ThemeManager.get_theme_colors(current_theme)
        except:
            return {
                "primary": "#2563eb",
                "border": "#e2e8f0",
                "success": "#10b981",
                "text_primary": "#1e293b",
                "background": "#fefefe",
                "surface": "#f8fafc"
            }
    
    def paint_custom_checkbox(self, painter, rect, checked, colors):
        """Pinta un checkbox personalizado con colores del tema"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(rect, QColor(colors["background"]))
        
        if checked:
            # Checkbox marcado - FONDO VERDE SÓLIDO
            painter.fillRect(rect, QColor(colors["success"]))
            
            # Borde verde
            pen = painter.pen()
            pen.setWidth(2)
            pen.setColor(QColor(colors["success"]))
            painter.setPen(pen)
            painter.drawRect(rect.adjusted(0, 0, -1, -1))
            
            # Checkmark blanco más visible
            pen.setWidth(3)
            pen.setColor(QColor("white"))
            painter.setPen(pen)
            
            center_x = rect.x() + rect.width() // 2
            center_y = rect.y() + rect.height() // 2
            size = min(rect.width(), rect.height()) // 3
            
            check_points = [
                QPoint(center_x - size//2, center_y),
                QPoint(center_x - size//4, center_y + size//2),
                QPoint(center_x + size//2, center_y - size//2)
            ]
            painter.drawPolyline(check_points)
            
            # Segundo checkmark para mayor visibilidad
            check_points2 = [
                QPoint(center_x - size//2 + 1, center_y + 1),
                QPoint(center_x - size//4 + 1, center_y + size//2 + 1),
                QPoint(center_x + size//2 + 1, center_y - size//2 + 1)
            ]
            painter.drawPolyline(check_points2)
        else:
            # Checkbox desmarcado - FONDO BLANCO CON BORDE VISIBLE
            painter.fillRect(rect, QColor(colors["background"]))
            
            # Borde más grueso y visible
            pen = painter.pen()
            pen.setWidth(2)
            pen.setColor(QColor(colors["primary"]))
            painter.setPen(pen)
            painter.drawRect(rect.adjusted(0, 0, -1, -1))
    
    def get_checkbox_rect(self, cell_rect):
        """Calcula el rectángulo centrado para el checkbox"""
        checkbox_size = 20
        x = cell_rect.x() + (cell_rect.width() - checkbox_size) // 2
        y = cell_rect.y() + (cell_rect.height() - checkbox_size) // 2
        return QRect(x, y, checkbox_size, checkbox_size)
    
    def editorEvent(self, event, model, option, index):
        """Maneja eventos del mouse para el checkbox"""
        if event.type() == event.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                checkbox_rect = self.get_checkbox_rect(option.rect)
                if checkbox_rect.contains(event.pos()):
                    current_state = index.data(Qt.ItemDataRole.CheckStateRole)
                    new_state = Qt.CheckState.Unchecked if current_state == Qt.CheckState.Checked else Qt.CheckState.Checked
                    model.setData(index, new_state, Qt.ItemDataRole.CheckStateRole)
                    return True
        return False
    
    def sizeHint(self, option, index):
        """Retorna el tamaño sugerido para la celda"""
        return QSize(60, 40)


class DuplicateWidgets:
    """Mixin para widgets del Dashboard de Duplicados"""
    
    def create_control_panel(self, layout):
        """Crea el panel de controles principal"""
        control_group = QGroupBox("🎛️ CONTROLES DE BÚSQUEDA")
        control_group.setObjectName("control_group")
        control_layout = QGridLayout(control_group)
        control_layout.setSpacing(12)
        control_layout.setContentsMargins(15, 15, 15, 15)
        
        # Fila 1: Método y recursividad
        row = 0
        control_layout.addWidget(self._create_method_selector(), row, 0)
        control_layout.addWidget(self._create_recursive_checkbox(), row, 1)
        
        # Fila 2: Selector de carpeta
        row = 1
        control_layout.addWidget(self._create_folder_selector(), row, 0, 1, 2)
        
        # Fila 3: Botones de acción
        row = 2
        control_layout.addWidget(self._create_action_buttons(), row, 0, 1, 2)
        
        layout.addWidget(control_group)
    
    def _create_method_selector(self):
        """Crea el selector de método de búsqueda"""
        method_widget = QWidget()
        method_layout = QHBoxLayout(method_widget)
        method_layout.setContentsMargins(0, 0, 0, 0)
        
        method_label = QLabel("🔍 Método:")
        method_label.setToolTip("Selecciona el método de detección de duplicados")
        method_layout.addWidget(method_label)
        
        self.method_combo = QComboBox()
        self.method_combo.addItem("⚡ Rápido (por tamaño)", "fast")
        self.method_combo.addItem("📋 Estándar (por hash MD5)", "md5")
        self.method_combo.addItem("🔐 Seguro (por hash SHA256)", "sha256")
        self.method_combo.setCurrentIndex(0)
        self.method_combo.setMinimumWidth(200)
        self.method_combo.currentIndexChanged.connect(self.on_method_changed)
        method_layout.addWidget(self.method_combo)
        
        method_layout.addStretch()
        return method_widget
    
    def _create_recursive_checkbox(self):
        """Crea el checkbox de búsqueda recursiva"""
        recursive_widget = QWidget()
        recursive_layout = QHBoxLayout(recursive_widget)
        recursive_layout.setContentsMargins(0, 0, 0, 0)
        
        self.recursive_checkbox = QCheckBox("🔄 Búsqueda recursiva")
        self.recursive_checkbox.setChecked(True)
        self.recursive_checkbox.setToolTip("Buscar en subcarpetas")
        self.recursive_checkbox.stateChanged.connect(self.on_recursive_changed)
        recursive_layout.addWidget(self.recursive_checkbox)
        
        recursive_layout.addStretch()
        return recursive_widget
    
    def _create_folder_selector(self):
        """Crea el selector de carpeta"""
        folder_widget = QWidget()
        folder_layout = QHBoxLayout(folder_widget)
        folder_layout.setContentsMargins(0, 0, 0, 0)
        folder_layout.setSpacing(10)
        
        folder_label = QLabel("📁 Carpeta:")
        folder_layout.addWidget(folder_label)
        
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Selecciona una carpeta para buscar duplicados...")
        self.folder_input.setReadOnly(True)
        folder_layout.addWidget(self.folder_input)
        
        self.browse_btn = QPushButton("📂 Examinar")
        self.browse_btn.clicked.connect(self.select_folder)
        self.browse_btn.setObjectName("browse_button")
        folder_layout.addWidget(self.browse_btn)
        
        return folder_widget
    
    def _create_action_buttons(self):
        """Crea los botones de acción principales"""
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(15)
        
        self.scan_btn = QPushButton("🔍 INICIAR BÚSQUEDA")
        self.scan_btn.setEnabled(False)
        self.scan_btn.clicked.connect(self.start_scan)
        self.scan_btn.setObjectName("scan_button")
        self.scan_btn.setFixedHeight(45)
        buttons_layout.addWidget(self.scan_btn)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(45)
        buttons_layout.addWidget(self.progress_bar)
        
        return buttons_widget
    
    def create_filter_panel(self, layout):
        """Crea el panel de filtros y búsqueda"""
        filter_group = QGroupBox("🔎 FILTROS Y BÚSQUEDA")
        filter_group.setObjectName("filter_group")
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setSpacing(12)
        filter_layout.setContentsMargins(15, 15, 15, 15)
        
        # Campo de búsqueda
        search_label = QLabel("🔎 Buscar:")
        filter_layout.addWidget(search_label)
        
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filtrar por nombre de archivo...")
        self.filter_input.textChanged.connect(self._debounced_filter)
        self.filter_input.setMinimumWidth(300)
        filter_layout.addWidget(self.filter_input)
        
        # Botones de filtro rápido
        filter_layout.addWidget(QLabel("|"))
        
        self.show_all_btn = QPushButton("📋 Todos")
        self.show_all_btn.clicked.connect(lambda: self.apply_quick_filter(""))
        filter_layout.addWidget(self.show_all_btn)
        
        self.large_files_btn = QPushButton("💾 Grandes (>1MB)")
        self.large_files_btn.clicked.connect(lambda: self.apply_quick_filter("size:>1MB"))
        filter_layout.addWidget(self.large_files_btn)
        
        self.recent_btn = QPushButton("📅 Recientes")
        self.recent_btn.clicked.connect(lambda: self.apply_quick_filter("recent:7days"))
        filter_layout.addWidget(self.recent_btn)
        
        filter_layout.addStretch()
        
        # Contador de resultados
        self.results_count_label = QLabel("📊 0 duplicados encontrados")
        self.results_count_label.setObjectName("results_count_label")
        filter_layout.addWidget(self.results_count_label)
        
        layout.addWidget(filter_group)
    
    def create_results_table(self, layout):
        """Crea la tabla de resultados virtualizada"""
        table_group = QGroupBox("📊 RESULTADOS")
        table_group.setObjectName("table_group")
        table_layout = QVBoxLayout(table_group)
        
        # Tabla virtualizada
        self.duplicates_table = QTableView()
        from src.gui.table_models import VirtualizedDuplicatesModel
        self.duplicates_model = VirtualizedDuplicatesModel()
        self.duplicates_table.setModel(self.duplicates_model)
        
        # Delegado para checkboxes
        checkbox_delegate = CheckboxDelegate(self.duplicates_table)
        self.duplicates_table.setItemDelegateForColumn(0, checkbox_delegate)
        
        # Configuración
        self.duplicates_table.verticalHeader().setDefaultSectionSize(42)
        self.duplicates_table.setAlternatingRowColors(True)
        self.duplicates_table.setShowGrid(True)
        self.duplicates_table.setGridStyle(Qt.PenStyle.SolidLine)
        self.duplicates_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.duplicates_table.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        
        # Menú contextual
        self.duplicates_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.duplicates_table.customContextMenuRequested.connect(self.show_context_menu)
        
        table_layout.addWidget(self.duplicates_table)
        
        # Paginación
        pagination_layout = self._create_pagination_controls()
        table_layout.addLayout(pagination_layout)
        
        layout.addWidget(table_group)
    
    def _create_pagination_controls(self):
        """Crea los controles de paginación"""
        pagination_layout = QHBoxLayout()
        pagination_layout.addStretch()
        
        self.prev_page_btn = QPushButton("◀️ Anterior")
        self.prev_page_btn.setEnabled(False)
        self.prev_page_btn.clicked.connect(self.go_to_previous_page)
        pagination_layout.addWidget(self.prev_page_btn)
        
        self.page_info_label = QLabel("Página 1 de 1")
        pagination_layout.addWidget(self.page_info_label)
        
        self.next_page_btn = QPushButton("Siguiente ▶️")
        self.next_page_btn.setEnabled(False)
        self.next_page_btn.clicked.connect(self.go_to_next_page)
        pagination_layout.addWidget(self.next_page_btn)
        
        page_size_label = QLabel("Elementos por página:")
        pagination_layout.addWidget(page_size_label)
        
        self.page_size_spinbox = QSpinBox()
        self.page_size_spinbox.setRange(10, 200)
        self.page_size_spinbox.setValue(50)
        self.page_size_spinbox.valueChanged.connect(self.update_pagination_controls)
        pagination_layout.addWidget(self.page_size_spinbox)
        
        pagination_layout.addStretch()
        return pagination_layout
    
    def create_statistics_panel(self, layout):
        """Crea el panel de estadísticas"""
        stats_group = QGroupBox("📈 ESTADÍSTICAS")
        stats_group.setObjectName("stats_group")
        stats_layout = QGridLayout(stats_group)
        stats_layout.setSpacing(12)
        stats_layout.setContentsMargins(15, 15, 15, 15)
        
        # Estadísticas principales
        row = 0
        stats_layout.addWidget(self._create_stat_card("💾 Espacio Total Duplicado", "0 MB"), row, 0)
        stats_layout.addWidget(self._create_stat_card("📄 Archivos Duplicados", "0"), row, 1)
        stats_layout.addWidget(self._create_stat_card("📁 Grupos de Duplicados", "0"), row, 2)
        
        row = 1
        stats_layout.addWidget(self._create_stat_card("⏱️ Tiempo de Escaneo", "0s"), row, 0)
        stats_layout.addWidget(self._create_stat_card("📊 Archivos Analizados", "0"), row, 1)
        stats_layout.addWidget(self._create_stat_card("✅ Espacio Recuperable", "0 MB"), row, 2)
        
        # Acciones masivas
        row = 2
        action_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("☑️ Seleccionar Todo")
        self.select_all_btn.clicked.connect(self.select_all_duplicates)
        action_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("❌ Deseleccionar Todo")
        self.deselect_all_btn.clicked.connect(self.deselect_all_duplicates)
        action_layout.addWidget(self.deselect_all_btn)
        
        action_layout.addStretch()
        
        self.delete_selected_btn = QPushButton("🗑️ Eliminar Seleccionados")
        self.delete_selected_btn.clicked.connect(self.delete_selected)
        self.delete_selected_btn.setProperty("styleClass", "danger")
        action_layout.addWidget(self.delete_selected_btn)
        
        self.move_selected_btn = QPushButton("📁 Mover Seleccionados")
        self.move_selected_btn.clicked.connect(self.move_selected)
        action_layout.addWidget(self.move_selected_btn)
        
        stats_layout.addLayout(action_layout, row, 0, 1, 3)
        
        layout.addWidget(stats_group)
    
    def _create_stat_card(self, title, value):
        """Crea una tarjeta de estadística"""
        card = QFrame()
        card.setObjectName("stats_card")
        card_layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setObjectName("stats_card_title")
        card_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("stats_card_value")
        card_layout.addWidget(value_label)
        
        return card
