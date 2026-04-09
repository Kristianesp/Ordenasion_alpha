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

    def __init__(self, categories=None, parent=None):
        super().__init__(parent)
        self.categories = categories or []
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Campo de busqueda con ancho minimo y stretch
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

        # Contador de resultados compacto
        self.count_label = QLabel("0 resultados")
        self.count_label.setToolTip("Numero de elementos visibles")
        self.count_label.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        layout.addWidget(self.count_label)

        layout.addStretch()

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
