#!/usr/bin/env python3
"""
Dashboard de Gestión de Duplicados para el Organizador de Archivos
Interfaz completa para detectar, visualizar y gestionar archivos duplicados
"""

import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QGroupBox,
    QCheckBox, QComboBox, QLineEdit, QFileDialog, QMessageBox, QSplitter,
    QTextEdit, QTabWidget, QScrollArea, QFrame, QSpinBox, QDialog, QMenu, QTableView,
    QStyledItemDelegate, QStyle, QStyleOptionButton, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSettings, QRect, QSize, QPoint
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor, QAction, QPainter

from src.utils.constants import COLORS, UI_CONFIG
from src.core.duplicate_finder import DuplicateFinder, DuplicateScanWorker
from src.core.hash_manager import HashCalculationWorker
from src.gui.table_models import VirtualizedDuplicatesModel, PaginatedDuplicatesModel


class CheckboxDelegate(QStyledItemDelegate):
    """Delegado personalizado para checkboxes centrados y funcionales con colores del tema"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_table = parent
    
    def paint(self, painter, option, index):
        """Pinta el checkbox centrado en la celda con colores del tema actual"""
        if not index.isValid():
            return
        
        # Obtener el estado del checkbox
        checked = index.data(Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Checked
        
        # Obtener colores del tema actual
        theme_colors = self.get_theme_colors()
        
        # Calcular rectángulo del checkbox
        checkbox_rect = self.get_checkbox_rect(option.rect)
        
        # Guardar el estado del painter
        painter.save()
        
        try:
            # Pintar el checkbox personalizado
            self.paint_custom_checkbox(painter, checkbox_rect, checked, theme_colors)
        finally:
            # Restaurar el estado del painter
            painter.restore()
    
    def get_theme_colors(self):
        """Obtiene los colores del tema actual"""
        try:
            from src.utils.themes import ThemeManager
            from src.utils.app_config import AppConfig
            # Obtener el tema actual desde la configuración
            app_config = AppConfig()
            current_theme = app_config.get_theme()
            return ThemeManager.get_theme_colors(current_theme)
        except:
            # Fallback a colores por defecto
            return {
                "primary": "#2563eb",
                "border": "#e2e8f0",
                "success": "#10b981",
                "text_primary": "#1e293b",
                "background": "#fefefe",
                "surface": "#f8fafc"
            }
    
    def paint_custom_checkbox(self, painter, rect, checked, colors):
        """Pinta un checkbox personalizado con colores del tema - ROBUSTO"""
        # Configurar el painter
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Limpiar el área del checkbox
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
            
            # Checkmark blanco más visible y robusto
            pen.setWidth(3)  # Más grueso para mejor visibilidad
            pen.setColor(QColor("white"))
            painter.setPen(pen)
            
            # Dibujar checkmark más grande y visible
            center_x = rect.x() + rect.width() // 2
            center_y = rect.y() + rect.height() // 2
            size = min(rect.width(), rect.height()) // 3
            
            # Puntos del checkmark (V) más robustos
            check_points = [
                QPoint(center_x - size//2, center_y),
                QPoint(center_x - size//4, center_y + size//2),
                QPoint(center_x + size//2, center_y - size//2)
            ]
            painter.drawPolyline(check_points)
            
            # Dibujar un segundo checkmark para mayor visibilidad
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
        checkbox_size = 20  # Tamaño del checkbox más grande
        x = cell_rect.x() + (cell_rect.width() - checkbox_size) // 2
        y = cell_rect.y() + (cell_rect.height() - checkbox_size) // 2
        return QRect(x, y, checkbox_size, checkbox_size)
    
    def editorEvent(self, event, model, option, index):
        """Maneja eventos del mouse para el checkbox"""
        if event.type() == event.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                checkbox_rect = self.get_checkbox_rect(option.rect)
                if checkbox_rect.contains(event.pos()):
                    # Alternar estado del checkbox
                    current_state = index.data(Qt.ItemDataRole.CheckStateRole)
                    new_state = Qt.CheckState.Unchecked if current_state == Qt.CheckState.Checked else Qt.CheckState.Checked
                    model.setData(index, new_state, Qt.ItemDataRole.CheckStateRole)
                    return True
        return False
    
    def sizeHint(self, option, index):
        """Retorna el tamaño sugerido para la celda"""
        return QSize(60, 40)


class DuplicatesDashboard(QWidget):
    """Dashboard principal para gestión de duplicados"""

    # Señales para comunicación con ventana principal
    status_update = pyqtSignal(str)
    analysis_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.duplicates_data = {}  # Datos de duplicados {hash: [paths]}
        self.duplicate_finder = None
        self.current_method = "fast"  # Por defecto método rápido
        self.current_folder = None
        
        # 🚀 MEJORA: Variables eliminadas - ya no se usa procesamiento por lotes
        # La paginación reemplaza el sistema de lotes asíncrono
        
        # 🚀 MEJORA: Debouncing para búsquedas
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._execute_search)
        self.search_delay_ms = 300  # Esperar 300ms después de la última tecla
        self.pending_search_query = ""
        
        # ✅ NUEVO: Configuración persistente de columnas
        self.settings = QSettings("FileOrganizer", "DuplicatesDashboard")

        self.init_ui()
        self.setup_connections()
        self.setup_context_menu()
        
        # Configurar tabla inicial
        self.setup_table()
        # ✅ NUEVO: Cargar estado de columnas guardado
        self.load_column_settings()

    def init_ui(self):
        """Inicializa la interfaz de usuario con diseño profesional tipo Dashboard 2025"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ===== DISEÑO COMPACTO Y EFICIENTE =====
        # SECCIÓN: Configuración compacta en una sola fila
        config_layout = QHBoxLayout()
        config_layout.setSpacing(10)
        
        # Método de búsqueda
        config_layout.addWidget(QLabel("⚡ Método:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "🚀 ULTRA-RÁPIDO",
            "⚖️ HÍBRIDO", 
            "🔍 PROFUNDO"
        ])
        self.method_combo.setCurrentIndex(0)
        self.method_combo.setFixedHeight(32)
        self.method_combo.setMinimumWidth(220)
        self.method_combo.setToolTip("Selecciona el método de detección de duplicados:\n• ULTRA-RÁPIDO: Compara tamaño + nombre + extensión\n• HÍBRIDO: Filtro rápido + confirmación MD5\n• PROFUNDO: MD5 completo de todo el archivo")
        config_layout.addWidget(self.method_combo)
        
        # Botón seleccionar carpeta
        self.select_folder_btn = QPushButton("📁 Seleccionar Carpeta")
        self.select_folder_btn.setFixedHeight(32)
        self.select_folder_btn.setMinimumWidth(200)
        self.select_folder_btn.setToolTip("Selecciona la carpeta donde buscar archivos duplicados")
        config_layout.addWidget(self.select_folder_btn)
        
        # Ruta actual (compacta)
        self.current_folder_label = QLabel("Ninguna ruta seleccionada")
        self.current_folder_label.setWordWrap(False)
        # Estilos se aplicarán dinámicamente con el tema
        self.current_folder_label.setToolTip("Muestra la ruta de la carpeta seleccionada para buscar duplicados")
        config_layout.addWidget(self.current_folder_label)
        
        config_layout.addStretch()  # Empujar el botón hacia la derecha
        
        main_layout.addLayout(config_layout)

        # SECCIÓN: Filtros compactos en una sola fila
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(10)
        
        # Filtro por tamaño mínimo
        filters_layout.addWidget(QLabel("Tamaño min:"))
        self.min_size_spin = QSpinBox()
        self.min_size_spin.setRange(0, 10000)
        self.min_size_spin.setValue(1)
        self.min_size_spin.setSuffix(" MB")
        self.min_size_spin.setFixedHeight(28)
        self.min_size_spin.setMinimumWidth(100)
        self.min_size_spin.setToolTip("Tamaño mínimo de archivos a analizar (en MB)\nArchivos más pequeños serán ignorados")
        filters_layout.addWidget(self.min_size_spin)

        # Filtro por extensión
        filters_layout.addWidget(QLabel("Extensión:"))
        self.ext_filter_combo = QComboBox()
        self.ext_filter_combo.addItem("Todas", None)
        extensions = [".jpg", ".png", ".gif", ".mp4", ".avi", ".mp3", ".pdf", ".txt", ".docx"]
        for ext in extensions:
            self.ext_filter_combo.addItem(ext, ext)
        self.ext_filter_combo.setFixedHeight(28)
        self.ext_filter_combo.setMinimumWidth(120)
        self.ext_filter_combo.setToolTip("Filtra por tipo de archivo específico\nSelecciona 'Todas' para analizar todos los tipos")
        filters_layout.addWidget(self.ext_filter_combo)
        
        # Checkbox recursivo (más importante)
        self.recursive_cb = QCheckBox("🔄 Recursivo")
        self.recursive_cb.setChecked(True)
        self.recursive_cb.setToolTip("Buscar archivos duplicados en todas las subcarpetas\nDesactivar para buscar solo en la carpeta principal")
        filters_layout.addWidget(self.recursive_cb)
        
        # Checkboxes opcionales (más compactos)
        self.show_details_cb = QCheckBox("Detalles")
        self.show_details_cb.setToolTip("Mostrar información detallada de cada archivo duplicado\nIncluye ruta completa, tamaño y fecha de modificación")
        self.group_by_hash_cb = QCheckBox("Agrupar")
        self.group_by_hash_cb.setToolTip("Agrupar archivos duplicados por su hash MD5\nFacilita la identificación de grupos de duplicados")
        filters_layout.addWidget(self.show_details_cb)
        filters_layout.addWidget(self.group_by_hash_cb)
        
        # Información del método (compacta)
        self.method_info = QLabel("⚡ ULTRA-RÁPIDO: Compara tamaño + nombre + extensión")
        # Estilos se aplicarán dinámicamente con el tema
        self.method_info.setToolTip("Descripción del método de búsqueda seleccionado\nCambia automáticamente según la opción elegida")
        filters_layout.addWidget(self.method_info)
        
        filters_layout.addStretch()
        main_layout.addLayout(filters_layout)
        
        # Botón de inicio - ANCHO COMPLETO
        self.scan_btn = QPushButton("🚀 BUSCAR DUPLICADOS")
        self.scan_btn.setFixedHeight(40)
        self.scan_btn.setEnabled(False)
        self.scan_btn.setToolTip("Inicia la búsqueda de archivos duplicados\nRequiere seleccionar una carpeta primero")
        # ✅ NUEVO: Estilo específico con mayor prioridad para evitar sobrescritura de temas
        self.scan_btn.setObjectName("scan_button")  # ID específico para CSS
        # Estilos se aplicarán dinámicamente con el tema
        main_layout.addWidget(self.scan_btn)
        
        # Inicializar el texto del botón con el método por defecto
        self.on_method_changed()

        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setToolTip("Muestra el progreso de la búsqueda de duplicados")
        main_layout.addWidget(self.progress_bar)

        # Tabla de resultados con diseño moderno
        results_group = QGroupBox("📊 Resultados de Duplicados")
        results_group.setStyleSheet("""
            QGroupBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(76, 175, 80, 0.05), stop:1 rgba(76, 175, 80, 0.02));
                border: 2px solid #4CAF50;
                border-radius: 15px;
                margin-top: 12px;
                padding-top: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 15px 0 15px;
                color: #4CAF50;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        results_layout = QVBoxLayout(results_group)

        # Botones de acción
        buttons_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("☑️ Seleccionar Duplicados")
        self.select_all_btn.setToolTip("Selecciona solo los archivos duplicados (rojos)")
        buttons_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("☐ Deseleccionar Todo")
        self.deselect_all_btn.setToolTip("Deselecciona todos los archivos de la tabla")
        buttons_layout.addWidget(self.deselect_all_btn)
        
        # Filtro de búsqueda rápida centrado
        buttons_layout.addStretch()
        
        filter_label = QLabel("🔍 Filtrar:")
        filter_label.setToolTip("Buscar por nombre de archivo o extensión (ej: verde, .rar)")
        buttons_layout.addWidget(filter_label)
        
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Buscar por nombre o extensión...")
        self.filter_input.setToolTip("Escribe para filtrar en tiempo real por nombre de archivo o extensión")
        self.filter_input.setMinimumWidth(200)
        self.filter_input.setMaximumWidth(300)
        self.filter_input.textChanged.connect(self.on_filter_changed)
        buttons_layout.addWidget(self.filter_input)
        
        self.filter_count_label = QLabel("")
        self.filter_count_label.setToolTip("Número de resultados filtrados")
        self.filter_count_label.setStyleSheet("color: #666; font-style: italic;")
        buttons_layout.addWidget(self.filter_count_label)
        
        buttons_layout.addStretch()
        
        self.delete_btn = QPushButton("🗑️ Eliminar Seleccionados")
        self.delete_btn.setStyleSheet("color: #d32f2f; font-weight: bold;")
        self.delete_btn.setToolTip("Elimina permanentemente los archivos seleccionados\n¡CUIDADO! Esta acción no se puede deshacer")
        buttons_layout.addWidget(self.delete_btn)
        
        self.move_btn = QPushButton("📁 Mover Seleccionados")
        self.move_btn.setToolTip("Mueve los archivos seleccionados a otra carpeta")
        buttons_layout.addWidget(self.move_btn)
        
        self.export_btn = QPushButton("💾 Exportar Resultados")
        self.export_btn.setToolTip("Exporta la lista de duplicados a un archivo CSV")
        buttons_layout.addWidget(self.export_btn)
        
        # ✅ NUEVO: Botón para resetear columnas
        self.reset_columns_btn = QPushButton("📏 Resetear Columnas")
        self.reset_columns_btn.setToolTip("Restaura el ancho y orden de las columnas a valores por defecto")
        buttons_layout.addWidget(self.reset_columns_btn)
        
        results_layout.addLayout(buttons_layout)
        
        # 🚀 MEJORA: Tabla virtualizada con modelo paginado
        self.duplicates_table = QTableView()
        self.duplicates_model = PaginatedDuplicatesModel(page_size=1000)  # 1000 elementos por página
        self.duplicates_table.setModel(self.duplicates_model)
        
        # Aplicar delegado personalizado para checkboxes
        checkbox_delegate = CheckboxDelegate(self.duplicates_table)
        self.duplicates_table.setItemDelegateForColumn(0, checkbox_delegate)
        
        results_layout.addWidget(self.duplicates_table)
        
        # Controles de paginación
        pagination_layout = QHBoxLayout()
        
        self.prev_page_btn = QPushButton("◀ Anterior")
        self.prev_page_btn.clicked.connect(self.go_to_previous_page)
        self.prev_page_btn.setEnabled(False)
        self.prev_page_btn.setToolTip("Ir a la página anterior de resultados")
        pagination_layout.addWidget(self.prev_page_btn)
        
        self.page_info_label = QLabel("Página 1 de 1 (0-0 de 0)")
        self.page_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_info_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        self.page_info_label.setToolTip("Información de paginación: página actual, total de páginas y rango de elementos")
        pagination_layout.addWidget(self.page_info_label)
        
        self.next_page_btn = QPushButton("Siguiente ▶")
        self.next_page_btn.clicked.connect(self.go_to_next_page)
        self.next_page_btn.setEnabled(False)
        self.next_page_btn.setToolTip("Ir a la página siguiente de resultados")
        pagination_layout.addWidget(self.next_page_btn)
        
        results_layout.addLayout(pagination_layout)
        
        main_layout.addWidget(results_group)
        
        # Estadísticas con tarjetas tipo dashboard
        stats_group = QGroupBox("📈 Estadísticas")
        stats_group.setStyleSheet("""
            QGroupBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(156, 39, 176, 0.05), stop:1 rgba(156, 39, 176, 0.02));
                border: 2px solid #9C27B0;
                border-radius: 15px;
                margin-top: 12px;
                padding-top: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 15px 0 15px;
                color: #9C27B0;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        stats_layout = QHBoxLayout(stats_group)
        
        # Crear tarjetas de estadísticas modernas
        self.stats_labels = {}
        stats_info = [
            ("grupos", "📊 Grupos", "#2196F3", "🔗"),
            ("duplicados", "📄 Duplicados", "#FF5722", "🔴"),
            ("seleccionados", "☑️ Seleccionados", "#FF9800", "✅"),
            ("espacio", "💾 Espacio", "#4CAF50", "⚡"),
            ("espacio_seleccionado", "💾 Esp. Seleccionado", "#E91E63", "🎯"),
            ("tiempo", "⏱️ Tiempo", "#9C27B0", "🚀")
        ]
        
        for key, label, color, icon in stats_info:
            # Crear tarjeta individual
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 rgba(255,255,255,0.9), stop:1 rgba(240,240,240,0.9));
                    border: 2px solid {color};
                    border-radius: 12px;
                    padding: 10px;
                    min-height: 70px;
                    min-width: 150px;
                }}
                QFrame:hover {{
                    border: 3px solid {color};
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 rgba(255,255,255,1), stop:1 rgba(250,250,250,1));
                }}
            """)
            
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(5)
            
            # Título de la tarjeta
            title_label = QLabel(f"{icon} {label}")
            title_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 13px;")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Valor de la tarjeta
            value_label = QLabel("0")
            value_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 18px;")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Tooltips para las tarjetas de estadísticas
            if key == "grupos":
                card.setToolTip("Número de grupos de archivos duplicados encontrados")
            elif key == "duplicados":
                card.setToolTip("Total de archivos duplicados (excluyendo originales)")
            elif key == "seleccionados":
                card.setToolTip("Número de archivos actualmente seleccionados en la tabla")
            elif key == "espacio":
                card.setToolTip("Espacio total que se puede liberar eliminando duplicados")
            elif key == "espacio_seleccionado":
                card.setToolTip("Espacio que ocupan los archivos seleccionados")
            elif key == "tiempo":
                card.setToolTip("Tiempo transcurrido durante la búsqueda de duplicados")
            
            self.stats_labels[key] = value_label
            
            card_layout.addWidget(title_label)
            card_layout.addWidget(value_label)
            stats_layout.addWidget(card)
        
        main_layout.addWidget(stats_group)

        # Log de operaciones (igual que disk_viewer)
        log_layout = QHBoxLayout()
        
        # Sin etiqueta de texto, solo el área de log
        
        self.log_text = QTextEdit()
        self.log_text.setToolTip("📝 Historial de operaciones, errores y mensajes informativos del sistema")
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(40)  # Restaurado a 40px como estaba
        self.log_text.setMinimumHeight(40)  # Altura mínima restaurada
        self.log_text.setObjectName("log_text")
        log_layout.addWidget(self.log_text)
        
        main_layout.addLayout(log_layout)

    def setup_table(self):
        """🚀 MEJORA: Configura la tabla VIRTUALIZADA de duplicados"""
        # El modelo ya tiene los headers configurados, solo configuramos la vista
        header = self.duplicates_table.horizontalHeader()
        
        # Permitir redimensionamiento manual de TODAS las columnas
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Checkbox
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Nombre
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Ubicación  
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Tamaño
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # Fecha
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)  # Hash
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)  # Acciones
        
        # Habilitar ordenamiento por columnas
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        header.sectionClicked.connect(self.on_header_clicked)
        
        # Establecer anchos por defecto
        self.default_column_widths = {
            0: 50,   # Checkbox
            1: 250,  # Nombre
            2: 300,  # Ubicación
            3: 100,  # Tamaño
            4: 140,  # Fecha
            5: 160,  # Hash
            6: 90    # Acciones
        }
        
        # Aplicar anchos por defecto
        for column, width in self.default_column_widths.items():
            self.duplicates_table.setColumnWidth(column, width)
        
        # Conectar señales
        header.sectionResized.connect(self.on_column_resized)
        header.setSectionsMovable(True)
        header.sectionMoved.connect(self.on_column_moved)
        
        # Habilitar selección por filas y checkboxes
        self.duplicates_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.duplicates_table.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)  # Permitir selección múltiple
        
        # Configuración para checkboxes - permitir clic simple
        self.duplicates_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)  # Sin edit triggers automáticos
        self.duplicates_table.setDragDropMode(QTableView.DragDropMode.NoDragDrop)  # Sin drag & drop
        
        # Habilitar clics en checkboxes
        self.duplicates_table.setMouseTracking(True)
        
        # Configuración específica para checkboxes
        self.duplicates_table.setWordWrap(False)  # Evitar wrap de texto
        self.duplicates_table.setVerticalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        self.duplicates_table.setHorizontalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        
        # Configuración visual
        self.duplicates_table.setAlternatingRowColors(True)
        self.duplicates_table.setShowGrid(True)
        
        # Conectar doble clic en la tabla para manejar botón de eliminar
        self.duplicates_table.doubleClicked.connect(self.on_table_double_clicked)

    def setup_connections(self):
        """Configura las conexiones de señales"""
        self.select_folder_btn.clicked.connect(self.select_folder)
        self.scan_btn.clicked.connect(self.start_scan)
        self.select_all_btn.clicked.connect(self.select_all_duplicates)
        self.deselect_all_btn.clicked.connect(self.deselect_all_duplicates)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.move_btn.clicked.connect(self.move_selected)
        self.export_btn.clicked.connect(self.export_results)
        self.reset_columns_btn.clicked.connect(self.reset_column_settings)  # ✅ NUEVO

        # Conectar filtros
        # 🚀 MEJORA: Usar debouncing en filtros de texto para evitar búsquedas innecesarias
        self.min_size_spin.valueChanged.connect(self._debounced_filter)
        self.ext_filter_combo.currentTextChanged.connect(self._debounced_filter)
        self.recursive_cb.stateChanged.connect(self.on_recursive_changed)  # ✅ NUEVO
        
        # Conectar selector de método
        self.method_combo.currentIndexChanged.connect(self.on_method_changed)
        
        # Conectar cambios de selección para actualizar estadísticas
        self.duplicates_model.dataChanged.connect(self.on_selection_changed)
    
    def on_selection_changed(self, top_left, bottom_right, roles):
        """Maneja cambios en la selección de checkboxes"""
        # Solo actualizar si cambió el estado de checkboxes
        if Qt.ItemDataRole.CheckStateRole in roles:
            self.update_statistics_from_selection()
    
    def setup_context_menu(self):
        """Configura menú contextual para previsualización de imágenes"""
        self.duplicates_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.duplicates_table.customContextMenuRequested.connect(self.show_context_menu)

    def on_method_changed(self):
        """Maneja el cambio de método de detección"""
        from src.utils.themes import ThemeManager
        from src.utils.app_config import AppConfig
        
        app_config = AppConfig()
        theme = app_config.get_theme()
        colors = ThemeManager.get_theme_colors(theme)
        
        method_index = self.method_combo.currentIndex()
        
        if method_index == 0:  # Ultra-rápido
            self.current_method = "fast"
            self.method_info.setText("⚡ ULTRA-RÁPIDO: Compara tamaño + nombre + extensión (hasta 100x más rápido que MD5)")
            self.method_info.setStyleSheet(f"color: {colors['success']}; font-style: italic; padding: 5px;")
            self.scan_btn.setText("🚀 BUSCAR DUPLICADOS (ULTRA-RÁPIDO)")
            
        elif method_index == 1:  # Híbrido
            self.current_method = "hybrid"
            self.method_info.setText("⚖️ HÍBRIDO: Filtro rápido + confirmación MD5 (balance perfecto velocidad/precisión)")
            self.method_info.setStyleSheet(f"color: {colors['warning']}; font-style: italic; padding: 5px;")
            self.scan_btn.setText("⚖️ BUSCAR DUPLICADOS (HÍBRIDO)")
            
        else:  # Profundo
            self.current_method = "deep"
            self.method_info.setText("🔍 PROFUNDO: MD5 completo de todo el archivo (100% preciso pero muy lento)")
            self.method_info.setStyleSheet(f"color: {colors['error']}; font-style: italic; padding: 5px;")
            self.scan_btn.setText("🔍 BUSCAR DUPLICADOS (PROFUNDO)")

    def on_recursive_changed(self):
        """Maneja el cambio en la opción de búsqueda recursiva"""
        recursive_enabled = self.recursive_cb.isChecked()
        if recursive_enabled:
            self.log_message("🔄 Búsqueda recursiva ACTIVADA - Incluirá subcarpetas")
        else:
            self.log_message("📁 Búsqueda recursiva DESACTIVADA - Solo carpeta actual")

    def select_folder(self):
        """Selecciona carpeta o disco para analizar"""
        # Crear diálogo personalizado con botones descriptivos
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("🎯 Seleccionar Ámbito de Búsqueda")
        msg_box.setText("¿Qué quieres analizar?")
        msg_box.setInformativeText(
            "📂 CARPETA: Analiza solo una carpeta específica (recomendado)\n"
            "💿 DISCO: Analiza todo un disco/unidad (puede ser muy lento)"
        )
        msg_box.setIcon(QMessageBox.Icon.Question)
        
        # Botones personalizados con texto descriptivo
        carpeta_btn = msg_box.addButton("📂 Carpeta", QMessageBox.ButtonRole.YesRole)
        disco_btn = msg_box.addButton("💿 Disco Completo", QMessageBox.ButtonRole.NoRole)
        msg_box.addButton("❌ Cancelar", QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(carpeta_btn)
        
        msg_box.exec()
        clicked_button = msg_box.clickedButton()
        
        # Si canceló, salir
        if clicked_button.text() == "❌ Cancelar":
            return
        
        if clicked_button == carpeta_btn:
            # Seleccionar carpeta específica
            folder = QFileDialog.getExistingDirectory(
                self,
                "📂 Seleccionar carpeta específica para analizar",
                str(Path.home()),
                QFileDialog.Option.ShowDirsOnly
            )
            scope_type = "CARPETA"
        else:
            # Seleccionar disco completo
            folder = QFileDialog.getExistingDirectory(
                self,
                "💿 Seleccionar disco completo (ej: C:) - ADVERTENCIA: Puede ser muy lento",
                "",
                QFileDialog.Option.ShowDirsOnly
            )
            scope_type = "DISCO"

        if folder:
            self.current_folder = folder
            folder_display = f"{scope_type}: {folder}"
            self.current_folder_label.setText(folder_display)
            self.current_folder_label.setStyleSheet("color: #1976d2; font-weight: bold; padding: 5px;")
            self.scan_btn.setEnabled(True)
            self.apply_scan_button_style()  # ✅ NUEVO: Reaplicar estilo azul
            self.log_message(f"✅ {scope_type} seleccionada: {folder}")
            
            # Advertencia para discos completos
            if scope_type == "DISCO":
                QMessageBox.warning(
                    self, "⚠️ Advertencia - Análisis de Disco Completo",
                    f"Has seleccionado analizar TODO el disco: {folder}\n\n"
                    f"⚠️ ADVERTENCIAS:\n"
                    f"• Puede tardar horas dependiendo del tamaño\n"
                    f"• Usa mucha CPU y disco durante el proceso\n"
                    f"• Se recomienda usar método ULTRA-RÁPIDO\n\n"
                    f"💡 CONSEJO: Considera analizar carpetas específicas en lugar de discos completos"
                )

    def start_scan(self):
        """Inicia el escaneo de duplicados"""
        if not self.current_folder:
            QMessageBox.warning(self, "Error", "Primero selecciona una carpeta o disco")
            return

        # Limpiar resultados anteriores
        self.duplicates_data = {}
        # NO limpiar la tabla aquí - se limpiará en load_duplicates_data para evitar doble parpadeo
        self.clear_statistics()
        
        # Configurar interfaz para escaneo
        self.scan_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminado

        method_name = {
            "fast": "ULTRA-RÁPIDO",
            "hybrid": "HÍBRIDO",
            "deep": "PROFUNDO"
        }.get(self.current_method, "DESCONOCIDO")
        
        self.log_message(f"🚀 Iniciando escaneo {method_name} en: {self.current_folder}")
        
        # Crear worker con método y configuración recursiva seleccionados
        recursive_enabled = self.recursive_cb.isChecked()
        self.scan_worker = DuplicateScanWorker(
            str(self.current_folder), 
            method=self.current_method,
            recursive=recursive_enabled  # ✅ NUEVO: Pasar opción recursiva
        )
        self.scan_worker.finished.connect(self.on_scan_finished)
        self.scan_worker.error_occurred.connect(self.on_scan_error)  # ✅ Nombre correcto
        self.scan_worker.scan_progress.connect(self.log_message)     # ✅ Añadir progreso
        self.scan_worker.duplicates_found.connect(self.on_duplicates_found)
        
        # Log información de configuración
        recursive_text = "RECURSIVA (incluye subcarpetas)" if recursive_enabled else "NO RECURSIVA (solo carpeta actual)"
        self.log_message(f"🔄 Búsqueda {recursive_text}")

        self.scan_worker.start()

    def on_duplicates_found(self, duplicates_data, statistics):
        """Maneja duplicados encontrados en tiempo real - FIRMA CORRECTA"""
        self.duplicates_data = duplicates_data
        self.log_message(f"🔍 Encontrados {len(duplicates_data)} grupos de duplicados")
        
        # Actualizar estadísticas usando las CLAVES CORRECTAS del worker
        if statistics:
            # ✅ CLAVES CORRECTAS del get_statistics_fast()
            self.stats_labels["grupos"].setText(str(statistics.get("total_duplicate_groups", 0)))
            self.stats_labels["duplicados"].setText(str(statistics.get("total_duplicate_files", 0)))
            
            # Formatear espacio guardado
            space_mb = statistics.get("space_saved_mb", 0)
            if space_mb >= 1024:
                space_str = f"{space_mb/1024:.1f} GB"
            else:
                space_str = f"{space_mb:.1f} MB"
            self.stats_labels["espacio"].setText(space_str)
            
            # Tiempo (por ahora placeholder)
            self.stats_labels["tiempo"].setText("< 1s")
        else:
            # Fallback si no hay estadísticas
            total_groups = len([group for group in duplicates_data.values() if len(group) > 1])
            total_duplicates = sum(len(paths) - 1 for paths in duplicates_data.values() if len(paths) > 1)
            self.stats_labels["grupos"].setText(str(total_groups))
            self.stats_labels["duplicados"].setText(str(total_duplicates))
            self.stats_labels["espacio"].setText("0 MB")
            self.stats_labels["tiempo"].setText("< 1s")
        
        # Poblar tabla
        self.populate_table()

    def on_scan_finished(self):
        """Maneja finalización del escaneo"""
        self.scan_btn.setEnabled(True)
        self.apply_scan_button_style()  # ✅ NUEVO: Reaplicar estilo azul
        self.progress_bar.setVisible(False)
        self.log_message("✅ Escaneo completado")

    def on_scan_error(self, error_message):
        """Maneja errores del escaneo"""
        self.scan_btn.setEnabled(True)
        self.apply_scan_button_style()  # ✅ NUEVO: Reaplicar estilo azul
        self.progress_bar.setVisible(False)
        self.log_message(f"❌ Error en escaneo: {error_message}")
        QMessageBox.critical(self, "Error", f"Error durante el escaneo:\n{error_message}")

    def clear_statistics(self):
        """Limpia las estadísticas"""
        for label in self.stats_labels.values():
            label.setText("0")
    
    def update_statistics_from_table(self):
        """Actualiza las estadísticas basándose en los datos actuales de la tabla"""
        try:
            if not hasattr(self, 'duplicates_model') or not self.duplicates_model:
                return
            
            # Obtener datos del modelo actual (puede estar filtrado)
            model_data = self.duplicates_model._data if hasattr(self.duplicates_model, '_data') else []
            
            # Calcular estadísticas de la tabla actual
            total_groups = 0
            total_duplicates = 0
            total_selected = 0
            total_space = 0
            selected_space = 0
            
            # Procesar datos del modelo
            for row_data in model_data:
                if row_data:
                    # Contar grupos (cada fila es un archivo, agrupamos por hash)
                    hash_value = row_data.get('hash', '')
                    if hash_value:
                        # Solo contar una vez por grupo
                        if not hasattr(self, '_processed_hashes'):
                            self._processed_hashes = set()
                        if hash_value not in self._processed_hashes:
                            self._processed_hashes.add(hash_value)
                            total_groups += 1
                    
                    # Contar duplicados (archivos que no son originales)
                    if not row_data.get('is_original', False):
                        total_duplicates += 1
                    
                    # Contar seleccionados
                    if row_data.get('is_checked', False):
                        total_selected += 1
                        # Sumar espacio de seleccionados
                        file_size = row_data.get('size', 0)
                        selected_space += file_size
                    
                    # Sumar espacio total
                    file_size = row_data.get('size', 0)
                    total_space += file_size
            
            # Limpiar hashes procesados para la próxima actualización
            if hasattr(self, '_processed_hashes'):
                delattr(self, '_processed_hashes')
            
            # Actualizar labels
            self.stats_labels["grupos"].setText(str(total_groups))
            self.stats_labels["duplicados"].setText(str(total_duplicates))
            self.stats_labels["seleccionados"].setText(str(total_selected))
            
            # Formatear espacio total
            if total_space >= 1024**3:
                space_str = f"{total_space/(1024**3):.1f} GB"
            elif total_space >= 1024**2:
                space_str = f"{total_space/(1024**2):.1f} MB"
            else:
                space_str = f"{total_space/1024:.1f} KB"
            self.stats_labels["espacio"].setText(space_str)
            
            # Formatear espacio seleccionado
            if selected_space >= 1024**3:
                selected_space_str = f"{selected_space/(1024**3):.1f} GB"
            elif selected_space >= 1024**2:
                selected_space_str = f"{selected_space/(1024**2):.1f} MB"
            else:
                selected_space_str = f"{selected_space/1024:.1f} KB"
            self.stats_labels["espacio_seleccionado"].setText(selected_space_str)
            
        except Exception as e:
            self.log_message(f"❌ Error actualizando estadísticas: {str(e)}")
    
    def update_statistics_from_selection(self):
        """Actualiza solo las estadísticas de selección cuando cambia la selección"""
        try:
            if not hasattr(self, 'duplicates_model') or not self.duplicates_model:
                return
            
            # Obtener filas seleccionadas
            selected_rows = self.duplicates_model.get_checked_rows()
            total_selected = len(selected_rows)
            selected_space = 0
            
            # Calcular espacio de seleccionados
            for row in selected_rows:
                row_data = self.duplicates_model.get_row_data(row)
                if row_data:
                    file_size = row_data.get('size', 0)
                    selected_space += file_size
            
            # Actualizar solo las estadísticas de selección
            self.stats_labels["seleccionados"].setText(str(total_selected))
            
            # Formatear espacio seleccionado
            if selected_space >= 1024**3:
                selected_space_str = f"{selected_space/(1024**3):.1f} GB"
            elif selected_space >= 1024**2:
                selected_space_str = f"{selected_space/(1024**2):.1f} MB"
            else:
                selected_space_str = f"{selected_space/1024:.1f} KB"
            self.stats_labels["espacio_seleccionado"].setText(selected_space_str)
            
        except Exception as e:
            self.log_message(f"❌ Error actualizando estadísticas de selección: {str(e)}")

    def populate_table(self):
        """🚀 MEJORA: Llena la tabla VIRTUALIZADA Y PAGINADA con los resultados"""
        self.populate_table_with_filtered_data(self.duplicates_data)
    
    def populate_table_with_filtered_data(self, data_to_use):
        """🚀 MEJORA: Llena la tabla VIRTUALIZADA Y PAGINADA con datos específicos"""
        self.log_message("📊 Iniciando población con virtualización + paginación...")
        
        try:
            if not data_to_use:
                self.log_message("⚠️ No hay datos de duplicados para mostrar")
                # Limpiar tabla completamente
                self.duplicates_model.clear_data()
                self.update_pagination_controls()
                return
            
            # Limpiar datos anteriores en una sola operación para evitar doble parpadeo
            self.duplicates_model.clear_data()

            # Obtener configuración de filtros
            min_size_mb = self.min_size_spin.value()
            min_size_bytes = min_size_mb * 1024 * 1024
            selected_ext = self.ext_filter_combo.currentData()
            
            self.log_message(f"🎛️ Aplicando filtros: Mín {min_size_mb}MB, Ext: {selected_ext or 'Todas'}")

            # Preparar datos para el modelo
            model_data = []
            filtered_out_files = 0
            
            for hash_value, file_paths in data_to_use.items():
                if len(file_paths) > 1:
                    files_info = []
                    
                    for file_path in file_paths:
                        try:
                            if not file_path.exists():
                                continue
                                
                            stat_info = file_path.stat()
                            
                            # Aplicar filtros
                            if stat_info.st_size < min_size_bytes:
                                filtered_out_files += 1
                                continue
                            
                            if selected_ext and not file_path.suffix.lower() == selected_ext:
                                filtered_out_files += 1
                                continue
                            
                            files_info.append({
                                'path': str(file_path),
                                'name': file_path.name,
                                'location': str(file_path.parent),
                                'size': stat_info.st_size,
                                'date': stat_info.st_mtime,
                                'hash': hash_value,
                                'is_original': False  # Se marcará después
                            })
                        except (OSError, AttributeError):
                            continue
                    
                    # Solo procesar grupos con duplicados
                    if len(files_info) <= 1:
                        continue
                    
                    # Ordenar por fecha (más reciente = original)
                    files_info.sort(key=lambda x: x['date'], reverse=True)
                    files_info[0]['is_original'] = True
                    
                    # Agregar todos los archivos del grupo
                    model_data.extend(files_info)

            total_files = len(model_data)
            self.log_message(f"✅ Preparados {total_files} archivos para visualización PAGINADA")
            self.log_message(f"🎯 Archivos filtrados: {filtered_out_files}")
            
            if total_files == 0:
                self.log_message("⚠️ No se encontraron archivos que pasen los filtros")
                # Limpiar tabla completamente
                self.duplicates_model.clear_data()
                self.update_pagination_controls()
                return
            
            # Cargar datos en el modelo PAGINADO (solo muestra 1000 a la vez)
            self.duplicates_model.load_full_data(model_data)
            self.update_pagination_controls()
            
            self.log_message(f"🚀 Tabla virtualizada lista - Mostrando página 1 de {self.duplicates_model.get_page_info()['total_pages']}")
            
        except Exception as e:
            self.log_message(f"❌ Error en populate_table: {str(e)}")
            import traceback
            self.log_message(f"🔍 Traceback: {traceback.format_exc()}")

    def go_to_next_page(self):
        """🚀 MEJORA: Avanza a la siguiente página"""
        if self.duplicates_model.next_page():
            self.update_pagination_controls()
            self.log_message(f"📄 Página {self.duplicates_model.get_page_info()['current_page']} cargada")
    
    def go_to_previous_page(self):
        """🚀 MEJORA: Retrocede a la página anterior"""
        if self.duplicates_model.previous_page():
            self.update_pagination_controls()
            self.log_message(f"📄 Página {self.duplicates_model.get_page_info()['current_page']} cargada")
    
    def update_pagination_controls(self):
        """🚀 MEJORA: Actualiza los controles de paginación"""
        page_info = self.duplicates_model.get_page_info()
        
        # Actualizar label
        self.page_info_label.setText(
            f"Página {page_info['current_page']} de {page_info['total_pages']} "
            f"({page_info['showing_from']}-{page_info['showing_to']} de {page_info['total_items']})"
        )
        
        # Habilitar/deshabilitar botones
        self.prev_page_btn.setEnabled(page_info['current_page'] > 1)
        self.next_page_btn.setEnabled(page_info['current_page'] < page_info['total_pages'])

    def _debounced_filter(self):
        """🚀 MEJORA: Inicia un temporizador para debouncing de búsquedas"""
        # Reiniciar el timer cada vez que cambia algo
        self.search_timer.start(self.search_delay_ms)
    
    def _execute_search(self):
        """🚀 MEJORA: Ejecuta la búsqueda real después del debouncing"""
        self.apply_filters()
    
    def on_filter_changed(self):
        """Maneja el cambio en el filtro de búsqueda rápida"""
        filter_text = self.filter_input.text().strip()
        
        if not self.duplicates_data:
            return
            
        # Aplicar filtro en tiempo real
        self.apply_quick_filter(filter_text)
    
    def apply_quick_filter(self, filter_text):
        """Aplica filtro rápido por nombre o extensión - VERSIÓN SIMPLE Y RÁPIDA"""
        if not filter_text:
            # Sin filtro, mostrar todos
            filtered_data = self.duplicates_data
        else:
            # Filtrar por nombre o extensión - SIMPLE Y RÁPIDO
            filtered_data = {}
            filter_lower = filter_text.lower()
            
            for hash_value, file_paths in self.duplicates_data.items():
                if len(file_paths) > 1:  # Solo grupos de duplicados
                    filtered_paths = []
                    for file_path in file_paths:
                        # Verificar que el archivo existe
                        if not file_path.exists():
                            continue
                            
                        # Extraer nombre del archivo de la ruta
                        filename = os.path.basename(file_path).lower()
                        
                        # Filtro simple: contiene el texto (coincidencia parcial)
                        if filter_lower in filename:
                            filtered_paths.append(file_path)
                    
                    # Solo incluir grupos que tengan al menos un archivo
                    if filtered_paths:
                        filtered_data[hash_value] = filtered_paths
        
        # Actualizar contador
        total_files = sum(len(paths) for paths in filtered_data.values())
        self.filter_count_label.setText(f"({total_files} archivos)")
        
        # Actualizar tabla con datos filtrados
        self.populate_table_with_filtered_data(filtered_data)
        
        # Actualizar estadísticas basándose en los datos filtrados
        self.update_statistics_from_table()
        
        # Forzar actualización de la vista
        self.duplicates_table.viewport().update()
    
    def apply_filters(self):
        """Aplica filtros a la vista de duplicados - AHORA INTEGRADO EN populate_table"""
        if not self.duplicates_data:
            self.log_message("⚠️ No hay datos para filtrar")
            return

        self.log_message("🎛️ Reaplicando filtros...")
        
        # Los filtros ahora se aplican DENTRO de populate_table
        # antes de crear las filas, no después
        self.populate_table()

    def refresh_view(self):
        """Actualiza la vista con filtros aplicados"""
        self.apply_filters()

    def select_all_duplicates(self):
        """🚀 MEJORA: Selecciona SOLO los duplicados usando el modelo"""
        self.duplicates_model.check_all_duplicates()
        self.log_message("✅ Duplicados seleccionados (originales sin marcar)")
        # Actualizar estadísticas de selección
        self.update_statistics_from_selection()

    def deselect_all_duplicates(self):
        """🚀 MEJORA: Deselecciona TODOS los archivos usando el modelo"""
        self.duplicates_model.uncheck_all()
        self.log_message("❌ Todos los archivos deseleccionados")
        # Actualizar estadísticas de selección
        self.update_statistics_from_selection()

    def delete_selected(self):
        """🚀 MEJORA: Elimina los archivos seleccionados usando el modelo"""
        selected_files = []
        selected_info = []

        self.log_message("🔍 Verificando archivos seleccionados...")

        # Obtener filas seleccionadas del modelo
        selected_rows = self.duplicates_model.get_checked_rows()
        
        for row in selected_rows:
            row_data = self.duplicates_model.get_row_data(row)
            
            if not row_data:
                continue
            
            try:
                file_path = Path(row_data.get('path', ''))
                
                # Verificar que el archivo existe
                if file_path.exists() and file_path.is_file():
                    selected_files.append(file_path)
                    
                    size_mb = row_data.get('size', 0) / (1024 * 1024)
                    selected_info.append({
                        'name': file_path.name,
                        'path': file_path,
                        'size': f"{size_mb:.2f} MB",
                        'location': row_data.get('location', '')
                    })
                else:
                    self.log_message(f"⚠️ Archivo no encontrado: {file_path}")
                    
            except Exception as e:
                self.log_message(f"❌ Error procesando fila {row}: {str(e)}")
                continue

        self.log_message(f"✅ Encontrados {len(selected_files)} archivos seleccionados")

        if not selected_files:
            QMessageBox.information(self, "Sin Selección", 
                f"❌ No hay archivos seleccionados para eliminar.\n\n"
                f"💡 Marca los checkboxes de los archivos que quieres eliminar:\n"
                f"   🟢 VERDES = Originales (más recientes)\n"
                f"   🔴 ROJOS = Duplicados (más antiguos)\n\n"
                f"Puedes eliminar cualquiera de los dos tipos.")
            return

        # Mostrar lista detallada de archivos a eliminar
        file_list = "\n".join([f"• {info['name']} ({info['size']}) - {info['location']}" 
                              for info in selected_info[:10]])  # Máximo 10 para no saturar
        if len(selected_info) > 10:
            file_list += f"\n... y {len(selected_info) - 10} archivos más"

        # Confirmar eliminación con detalles
        reply = QMessageBox.question(
            self, "🗑️ Confirmar Eliminación",
            f"¿Estás seguro de que quieres ELIMINAR PERMANENTEMENTE estos {len(selected_files)} archivos duplicados?\n\n"
            f"📂 Archivos a eliminar:\n{file_list}\n\n"
            f"⚠️ ESTA ACCIÓN NO SE PUEDE DESHACER\n"
            f"Los archivos se eliminarán permanentemente.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.log_message(f"🗑️ Iniciando eliminación de {len(selected_files)} archivos duplicados...")
            
            # IMPLEMENTAR ELIMINACIÓN REAL
            deleted_count = 0
            error_count = 0
            
            for file_path in selected_files:
                try:
                    # Eliminar archivo permanentemente
                    file_path.unlink()  # Eliminar archivo
                    deleted_count += 1
                    self.log_message(f"✅ Eliminado: {file_path.name}")
                    
                except PermissionError:
                    error_count += 1
                    self.log_message(f"❌ Sin permisos para eliminar: {file_path.name}")
                except FileNotFoundError:
                    error_count += 1
                    self.log_message(f"❌ Archivo ya no existe: {file_path.name}")
                except Exception as e:
                    error_count += 1
                    self.log_message(f"❌ Error eliminando {file_path.name}: {str(e)}")
            
            # Mostrar resultado
            if deleted_count > 0:
                QMessageBox.information(self, "✅ Eliminación Completada",
                    f"✅ Eliminados correctamente: {deleted_count} archivos\n"
                    f"❌ Errores: {error_count} archivos\n\n"
                    f"💡 Actualiza la vista para ver los cambios.")
                
                # Refrescar vista automáticamente
                self.log_message("🔄 Refrescando vista...")
                self.populate_table()
                
                # Actualizar filtro si está activo
                if hasattr(self, 'filter_input') and self.filter_input.text().strip():
                    self.log_message("🔄 Actualizando filtro después de eliminación...")
                    self.apply_quick_filter(self.filter_input.text().strip())
            else:
                QMessageBox.warning(self, "⚠️ Error en Eliminación",
                    f"❌ No se pudo eliminar ningún archivo\n"
                    f"Errores: {error_count}\n\n"
                    f"Verifica los permisos de los archivos.")

    def move_selected(self):
        """Mueve los archivos duplicados seleccionados"""
        QMessageBox.information(self, "Información", "Función de mover implementada en próximas versiones")

    def show_context_menu(self, position):
        """Muestra menú contextual para previsualizar imágenes"""
        try:
            # Obtener la fila donde se hizo clic (QTableView)
            index = self.duplicates_table.indexAt(position)
            if not index.isValid():
                return
                
            row = index.row()
            
            # Obtener información del archivo usando el modelo
            model = self.duplicates_table.model()
            name_data = model.data(model.index(row, 1), Qt.ItemDataRole.DisplayRole)
            location_data = model.data(model.index(row, 2), Qt.ItemDataRole.DisplayRole)
            
            if not name_data or not location_data:
                return
            
            # Extraer nombre sin emojis
            file_name_raw = str(name_data)
            if file_name_raw.startswith("🟢 ") or file_name_raw.startswith("🔴 "):
                file_name = file_name_raw[2:]
            else:
                file_name = file_name_raw
            
            # Construir ruta completa
            location_path = str(location_data)
            file_path = Path(location_path) / file_name
            
            # Crear menú contextual
            menu = QMenu(self)
            
            # Verificar tipo de archivo y agregar acciones apropiadas
            file_ext = file_path.suffix.lower()
            
            # Acciones para imágenes
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.ico'}
            if file_ext in image_extensions:
                preview_action = QAction("🖼️ Previsualizar imagen", self)
                preview_action.triggered.connect(lambda: self.preview_image(file_path))
                menu.addAction(preview_action)
            
            # Acciones para audio
            audio_extensions = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'}
            if file_ext in audio_extensions:
                play_action = QAction("🎵 Reproducir audio", self)
                play_action.triggered.connect(lambda: self.play_audio(file_path))
                menu.addAction(play_action)
            
            # Acciones para video
            video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
            if file_ext in video_extensions:
                play_video_action = QAction("🎬 Reproducir video", self)
                play_video_action.triggered.connect(lambda: self.play_video(file_path))
                menu.addAction(play_video_action)
            
            # Acción para abrir archivo (siempre disponible)
            open_file_action = QAction("📄 Abrir archivo", self)
            open_file_action.triggered.connect(lambda: self.open_file(file_path))
            menu.addAction(open_file_action)
            
            # Acción para abrir ubicación (siempre disponible)
            open_folder_action = QAction("📁 Abrir ubicación", self)
            open_folder_action.triggered.connect(lambda: self.open_file_location(file_path))
            menu.addAction(open_folder_action)
            
            # Mostrar menú
            menu.exec(self.duplicates_table.mapToGlobal(position))
            
        except Exception as e:
            self.log_message(f"❌ Error en menú contextual: {str(e)}")

    def preview_image(self, file_path):
        """Muestra previsualización de imagen en ventana emergente"""
        try:
            if not file_path.exists():
                QMessageBox.warning(self, "Error", f"El archivo no existe:\n{file_path}")
                return
            
            # Crear ventana de previsualización
            preview_window = QDialog(self)
            preview_window.setWindowTitle(f"🖼️ Previsualización: {file_path.name}")
            preview_window.setModal(True)
            preview_window.resize(800, 600)
            
            layout = QVBoxLayout(preview_window)
            
            # Información del archivo
            info_label = QLabel(f"📂 {file_path.parent}\n📄 {file_path.name}\n💾 {self.format_file_size(file_path.stat().st_size)}")
            info_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
            layout.addWidget(info_label)
            
            # ScrollArea para la imagen
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Label para mostrar la imagen
            image_label = QLabel()
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image_label.setStyleSheet("border: 2px solid #ccc; background-color: white;")
            
            # Cargar y mostrar imagen
            pixmap = QPixmap(str(file_path))
            if pixmap.isNull():
                image_label.setText("❌ No se pudo cargar la imagen")
            else:
                # Escalar imagen si es muy grande
                max_size = 700
                if pixmap.width() > max_size or pixmap.height() > max_size:
                    pixmap = pixmap.scaled(max_size, max_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                
                image_label.setPixmap(pixmap)
            
            scroll_area.setWidget(image_label)
            layout.addWidget(scroll_area)
            
            # Botón cerrar
            close_btn = QPushButton("✖️ Cerrar")
            close_btn.clicked.connect(preview_window.close)
            layout.addWidget(close_btn)
            
            # Mostrar ventana
            preview_window.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error mostrando previsualización:\n{str(e)}")
            self.log_message(f"❌ Error en preview_image: {str(e)}")

    def play_audio(self, file_path):
        """Reproduce archivo de audio"""
        try:
            import subprocess
            import sys
            
            if not file_path.exists():
                QMessageBox.warning(self, "Error", f"El archivo no existe:\n{file_path}")
                return
            
            # Abrir con reproductor por defecto
            if sys.platform == "win32":
                os.startfile(str(file_path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(file_path)])
            else:
                subprocess.Popen(["xdg-open", str(file_path)])
                
            self.log_message(f"🎵 Reproduciendo audio: {file_path.name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error reproduciendo audio:\n{str(e)}")
            self.log_message(f"❌ Error en play_audio: {str(e)}")

    def play_video(self, file_path):
        """Reproduce archivo de video"""
        try:
            import subprocess
            import sys
            
            if not file_path.exists():
                QMessageBox.warning(self, "Error", f"El archivo no existe:\n{file_path}")
                return
            
            # Abrir con reproductor por defecto
            if sys.platform == "win32":
                os.startfile(str(file_path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(file_path)])
            else:
                subprocess.Popen(["xdg-open", str(file_path)])
                
            self.log_message(f"🎬 Reproduciendo video: {file_path.name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error reproduciendo video:\n{str(e)}")
            self.log_message(f"❌ Error en play_video: {str(e)}")

    def open_file(self, file_path):
        """Abre archivo con aplicación por defecto"""
        try:
            import subprocess
            import sys
            
            if not file_path.exists():
                QMessageBox.warning(self, "Error", f"El archivo no existe:\n{file_path}")
                return
            
            # Abrir con aplicación por defecto
            if sys.platform == "win32":
                os.startfile(str(file_path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(file_path)])
            else:
                subprocess.Popen(["xdg-open", str(file_path)])
                
            self.log_message(f"📄 Abriendo archivo: {file_path.name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error abriendo archivo:\n{str(e)}")
            self.log_message(f"❌ Error en open_file: {str(e)}")

    def open_file_location(self, file_path):
        """Abre la ubicación del archivo en el explorador"""
        try:
            import subprocess
            import sys
            
            if sys.platform == "win32":
                # Windows - abrir explorer y seleccionar archivo
                subprocess.Popen(f'explorer /select,"{file_path}"')
            elif sys.platform == "darwin":
                # macOS
                subprocess.Popen(["open", "-R", str(file_path)])
            else:
                # Linux
                subprocess.Popen(["xdg-open", str(file_path.parent)])
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo abrir la ubicación:\n{str(e)}")

    def on_table_double_clicked(self, index):
        """Maneja doble clic en la tabla, especialmente en la columna de acciones"""
        try:
            row = index.row()
            col = index.column()
            
            # Solo manejar doble clic en la columna de acciones (columna 6)
            if col == 6:
                self.delete_single_file(row)
                
        except Exception as e:
            self.log_message(f"❌ Error en on_table_double_clicked: {str(e)}")

    def delete_single_file(self, row):
        """Elimina un archivo individual"""
        try:
            # Obtener información del archivo
            model = self.duplicates_table.model()
            name_data = model.data(model.index(row, 1), Qt.ItemDataRole.DisplayRole)
            location_data = model.data(model.index(row, 2), Qt.ItemDataRole.DisplayRole)
            
            if not name_data or not location_data:
                return
            
            # Extraer nombre sin emojis
            file_name_raw = str(name_data)
            if file_name_raw.startswith("🟢 ") or file_name_raw.startswith("🔴 "):
                file_name = file_name_raw[2:]
            else:
                file_name = file_name_raw
            
            # Construir ruta completa
            location_path = str(location_data)
            file_path = Path(location_path) / file_name
            
            # Confirmar eliminación
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Confirmar Eliminación")
            msg_box.setText(f"¿Estás seguro de que quieres eliminar este archivo?")
            msg_box.setInformativeText(f"📄 {file_name}\n📂 {location_path}")
            msg_box.setIcon(QMessageBox.Icon.Question)
            
            # Botones personalizados
            delete_btn = msg_box.addButton("🗑️ Eliminar", QMessageBox.ButtonRole.AcceptRole)
            cancel_btn = msg_box.addButton("❌ Cancelar", QMessageBox.ButtonRole.RejectRole)
            
            msg_box.exec()
            clicked_button = msg_box.clickedButton()
            
            if clicked_button == cancel_btn:
                return
            
            if clicked_button == delete_btn:
                # Eliminar archivo
                if file_path.exists():
                    file_path.unlink()
                    self.log_message(f"🗑️ Archivo eliminado: {file_name}")
                    
                    # Refrescar la tabla
                    self.log_message("🔄 Refrescando vista...")
                    self.populate_table()
                    
                    # Actualizar filtro si está activo
                    if hasattr(self, 'filter_input') and self.filter_input.text().strip():
                        self.log_message("🔄 Actualizando filtro después de eliminación...")
                        self.apply_quick_filter(self.filter_input.text().strip())
                else:
                    QMessageBox.warning(self, "Error", f"El archivo no existe:\n{file_path}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error eliminando archivo:\n{str(e)}")
            self.log_message(f"❌ Error en delete_single_file: {str(e)}")

    def format_file_size(self, size_bytes):
        """Formatea el tamaño del archivo de manera legible"""
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/(1024**2):.1f} MB"
        else:
            return f"{size_bytes/(1024**3):.1f} GB"

    def export_results(self):
        """Exporta los resultados a un archivo"""
        if not self.duplicates_data:
            QMessageBox.information(self, "Información", "No hay resultados para exportar")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Resultados",
            f"duplicados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Archivos de texto (*.txt)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("REPORTE DE ARCHIVOS DUPLICADOS\n")
                    f.write("="*50 + "\n\n")
                    
                    for i, (hash_val, paths) in enumerate(self.duplicates_data.items(), 1):
                        if len(paths) > 1:
                            f.write(f"GRUPO {i} ({len(paths)} archivos):\n")
                            f.write(f"Hash/ID: {hash_val}\n")
                            for path in paths:
                                f.write(f"  • {path}\n")
                            f.write("\n")
                
                self.log_message(f"📄 Resultados exportados a: {file_path}")
                QMessageBox.information(self, "Éxito", f"Resultados exportados correctamente a:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al exportar: {str(e)}")

    def log_message(self, message: str):
        """Añade un mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

        # Hacer scroll automático al final
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

        # Emitir señal de estado
        self.status_update.emit(message)
    
    def on_column_resized(self, logical_index, old_size, new_size):
        """Se ejecuta cuando el usuario redimensiona una columna"""
        self.log_message(f"📏 Columna {logical_index} redimensionada: {old_size}px → {new_size}px")
        self.save_column_settings()
    
    def on_column_moved(self, logical_index, old_visual_index, new_visual_index):
        """Se ejecuta cuando el usuario reordena columnas"""
        self.log_message(f"🔄 Columna movida desde posición {old_visual_index} → {new_visual_index}")
        self.save_column_settings()
    
    def on_header_clicked(self, logical_index):
        """Maneja el clic en el encabezado de una columna para ordenar"""
        # Solo permitir ordenamiento en columnas de tamaño y fecha
        if logical_index in [3, 4]:  # Tamaño (3) y Fecha (4)
            # Obtener información de ordenamiento actual
            sort_info = self.duplicates_model.get_sort_info()
            
            # Determinar nuevo orden
            if sort_info['column'] == logical_index:
                # Misma columna, cambiar orden
                new_order = Qt.SortOrder.DescendingOrder if sort_info['order'] == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
            else:
                # Nueva columna, empezar con ascendente
                new_order = Qt.SortOrder.AscendingOrder
            
            # Aplicar ordenamiento
            self.duplicates_model.sort(logical_index, new_order)
            
            # Actualizar indicador visual
            header = self.duplicates_table.horizontalHeader()
            header.setSortIndicator(logical_index, new_order)
            
            # Actualizar paginación
            self.update_pagination_controls()
            
            self.log_message(f"📊 Ordenando por columna {logical_index} ({'descendente' if new_order == Qt.SortOrder.DescendingOrder else 'ascendente'})")
    
    def save_column_settings(self):
        """Guarda el estado actual de las columnas"""
        try:
            header = self.duplicates_table.horizontalHeader()
            
            # Guardar anchos de columnas
            column_widths = {}
            for i in range(self.duplicates_table.model().columnCount()):
                column_widths[str(i)] = header.sectionSize(i)
            
            # Guardar orden visual de columnas
            column_order = []
            for i in range(self.duplicates_table.model().columnCount()):
                column_order.append(header.visualIndex(i))
            
            # Guardar en configuración persistente
            self.settings.setValue("column_widths", column_widths)
            self.settings.setValue("column_order", column_order)
            self.settings.sync()  # Forzar guardado inmediato
            
            self.log_message("💾 Estado de columnas guardado automáticamente")
            
        except Exception as e:
            self.log_message(f"❌ Error guardando estado de columnas: {str(e)}")
    
    def load_column_settings(self):
        """Carga el estado guardado de las columnas"""
        try:
            header = self.duplicates_table.horizontalHeader()
            
            # Cargar anchos de columnas
            saved_widths = self.settings.value("column_widths", {})
            if saved_widths:
                for column_str, width in saved_widths.items():
                    try:
                        column_index = int(column_str)
                        if 0 <= column_index < self.duplicates_table.model().columnCount():
                            self.duplicates_table.setColumnWidth(column_index, int(width))
                    except (ValueError, TypeError):
                        continue
            
            # Cargar orden de columnas
            saved_order = self.settings.value("column_order", [])
            if saved_order and len(saved_order) == self.duplicates_table.model().columnCount():
                try:
                    for logical_index, visual_index in enumerate(saved_order):
                        header.moveSection(header.visualIndex(logical_index), int(visual_index))
                except (ValueError, TypeError):
                    pass
            
            if saved_widths or saved_order:
                self.log_message("📋 Estado de columnas restaurado desde configuración anterior")
            else:
                self.log_message("📋 Usando configuración de columnas por defecto")
                
        except Exception as e:
            self.log_message(f"⚠️ Error cargando estado de columnas: {str(e)} - Usando valores por defecto")
    
    def reset_column_settings(self):
        """Restaura las columnas a su configuración por defecto"""
        try:
            # Aplicar anchos por defecto
            for column, width in self.default_column_widths.items():
                self.duplicates_table.setColumnWidth(column, width)
            
            # Restaurar orden original
            header = self.duplicates_table.horizontalHeader()
            for i in range(self.duplicates_table.model().columnCount()):
                header.moveSection(header.visualIndex(i), i)
            
            # Limpiar configuración guardada
            self.settings.remove("column_widths")
            self.settings.remove("column_order")
            self.settings.sync()
            
            self.log_message("🔄 Columnas restauradas a configuración por defecto")
            
        except Exception as e:
            self.log_message(f"❌ Error restaurando columnas: {str(e)}")
    
    def apply_scan_button_style(self):
        """✅ NUEVO: Reaplica el estilo al botón de escaneo usando colores del tema"""
        try:
            from src.utils.themes import ThemeManager
            from src.utils.app_config import AppConfig
            
            app_config = AppConfig()
            theme = app_config.get_theme()
            colors = ThemeManager.get_theme_colors(theme)
            
            if self.scan_btn.isEnabled():
                # Aplicar estilo usando colores del tema
                self.scan_btn.setStyleSheet(f"""
                    QPushButton#scan_button {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 {colors['primary']}, stop:1 {colors.get('button_pressed', colors['primary'])}) !important;
                        color: white !important;
                        border: none !important;
                        border-radius: 8px !important;
                        font-weight: bold !important;
                        font-size: 14px !important;
                        padding: 8px !important;
                        text-transform: uppercase !important;
                    }}
                    QPushButton#scan_button:hover {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 {colors.get('button_hover', colors['secondary'])}, stop:1 {colors['primary']}) !important;
                    }}
                    QPushButton#scan_button:pressed {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 {colors.get('button_pressed', colors['primary'])}, stop:1 {colors.get('button_hover', colors['secondary'])}) !important;
                    }}
                """)
                self.log_message("🔵 Estilo aplicado al botón de escaneo con colores del tema")
            else:
                # Aplicar estilo deshabilitado usando colores del tema
                self.scan_btn.setStyleSheet(f"""
                    QPushButton#scan_button {{
                        background: {colors.get('text_disabled', '#666')} !important;
                        color: {colors.get('text_secondary', '#999')} !important;
                        border: none !important;
                        border-radius: 8px !important;
                        font-weight: bold !important;
                        font-size: 14px !important;
                        padding: 8px !important;
                        text-transform: uppercase !important;
                    }}
                """)
        except Exception as e:
            self.log_message(f"❌ Error aplicando estilo al botón: {str(e)}")