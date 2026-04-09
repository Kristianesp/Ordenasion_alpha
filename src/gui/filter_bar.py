#!/usr/bin/env python3
"""
Barra de busqueda y filtro para tablas del Organizador de Archivos
"""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
    QLabel,
    QPushButton,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer


class FilterBar(QWidget):
    """Barra de busqueda y filtro para tablas"""

    filter_changed = pyqtSignal(str, str)  # (texto_busqueda, categoria)
    select_all_requested = pyqtSignal()
    deselect_all_requested = pyqtSignal()

    def __init__(self, categories=None, parent=None):
        super().__init__(parent)
        self.categories = categories or []
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        self._layout = layout

        self.select_all_btn = QPushButton("Todo")
        self.select_all_btn.setFixedHeight(36)
        self.select_all_btn.setVisible(False)
        self.select_all_btn.clicked.connect(self.select_all_requested.emit)
        layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("Nada")
        self.deselect_all_btn.setFixedHeight(36)
        self.deselect_all_btn.setVisible(False)
        self.deselect_all_btn.clicked.connect(self.deselect_all_requested.emit)
        layout.addWidget(self.deselect_all_btn)

        self.selection_separator = QLabel("│")
        self.selection_separator.setVisible(False)
        layout.addWidget(self.selection_separator)

        self.selection_count_label = QLabel("📊 Elementos: 0/0 seleccionados")
        self.selection_count_label.setObjectName("selection_count_label")
        self.selection_count_label.setVisible(False)
        layout.addWidget(self.selection_count_label)

        self.total_size_label = QLabel("💾 0 B")
        self.total_size_label.setObjectName("total_size_label")
        self.total_size_label.setVisible(False)
        layout.addWidget(self.total_size_label)

        self.total_files_label = QLabel("📄 0 elementos")
        self.total_files_label.setObjectName("total_files_label")
        self.total_files_label.setVisible(False)
        layout.addWidget(self.total_files_label)

        self.controls_separator = QLabel("│")
        self.controls_separator.setVisible(False)
        layout.addWidget(self.controls_separator)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre...")
        self.search_input.setToolTip("Escribe para filtrar elementos por nombre")
        self.search_input.setFixedHeight(36)
        self.search_input.setMinimumWidth(180)
        self.search_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_input, 1)

        # Filtro por categoria con ancho minimo
        self.category_filter = QComboBox()
        self.category_filter.setToolTip("Filtrar por categoria")
        self.category_filter.setFixedHeight(36)
        self.category_filter.setMinimumWidth(150)
        self.category_filter.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.category_filter.addItem("Todas las categorias")
        for cat in self.categories:
            self.category_filter.addItem(cat)
        self.category_filter.currentTextChanged.connect(self._on_category_changed)
        layout.addWidget(self.category_filter)

        # Boton limpiar compacto
        self.clear_btn = QPushButton("✖")
        self.clear_btn.setToolTip("Limpiar todos los filtros")
        self.clear_btn.setFixedHeight(36)
        self.clear_btn.setFixedWidth(36)
        self.clear_btn.clicked.connect(self.clear_filters)
        layout.addWidget(self.clear_btn)

        self.count_label = QLabel("0 resultados")
        self.count_label.setToolTip("Numero de elementos visibles")
        self.count_label.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        layout.addWidget(self.count_label)
        self.update_selection_summary(0, 0, "💾 0 B", "📄 0 elementos")

    def _on_search_changed(self):
        """Debounce en busqueda"""
        if not hasattr(self, "_search_timer"):
            self._search_timer = QTimer()
            self._search_timer.setSingleShot(True)
            self._search_timer.timeout.connect(self._emit_filter)
        self._search_timer.start(300)  # 300ms debounce

    def _on_category_changed(self, text):
        self._emit_filter()

    def _emit_filter(self):
        search = self.search_input.text().strip()
        category = self.category_filter.currentText()
        cat_filter = "" if category == "Todas las categorias" else category
        self.filter_changed.emit(search, cat_filter)

    def clear_filters(self):
        self.search_input.clear()
        self.category_filter.setCurrentIndex(0)

    def update_count(self, count):
        self.count_label.setText(f"{count} resultados")

    def embed_selection_bar(self):
        """Activa los controles compactos de selección dentro de la barra."""
        for widget in (
            self.select_all_btn,
            self.deselect_all_btn,
            self.selection_separator,
            self.selection_count_label,
            self.total_size_label,
            self.total_files_label,
            self.controls_separator,
        ):
            widget.setVisible(True)

    def update_selection_summary(
        self,
        selected_count: int,
        total_count: int,
        size_text: str,
        files_text: str,
    ):
        """Actualiza el resumen compacto de selección."""
        self.selection_count_label.setText(
            f"📊 Elementos: {selected_count}/{total_count} seleccionados"
        )
        self.total_size_label.setText(size_text)
        self.total_files_label.setText(files_text)

    def update_categories(self, categories):
        """Actualiza las categorias en el filtro"""
        current = self.category_filter.currentText()
        self.category_filter.clear()
        self.category_filter.addItem("Todas las categorias")
        for cat in categories:
            self.category_filter.addItem(cat)
        # Restaurar seleccion si existe
        idx = self.category_filter.findText(current)
        if idx >= 0:
            self.category_filter.setCurrentIndex(idx)
