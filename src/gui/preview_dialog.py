#!/usr/bin/env python3
"""
Dialogo de Preview para el Organizador de Archivos
Muestra una vista previa de los cambios antes de organizar
"""

from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from src.utils.app_config import AppConfig
from src.utils.themes import ThemeManager


class PreviewDialog(QDialog):
    """Dialogo que muestra vista previa de cambios antes de organizar"""
    
    def __init__(self, folder_movements, file_movements, folder_path, parent=None, organize_by_date=False):
        super().__init__(parent)
        self.folder_movements = folder_movements
        self.file_movements = file_movements
        self.folder_path = folder_path
        self.organize_by_date = organize_by_date
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Vista Previa de Organizacion")
        self.setMinimumSize(900, 600)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header informativo
        header = QLabel("Vista Previa de Cambios")
        header.setObjectName("preview_header")
        layout.addWidget(header)
        
        # Resumen
        total_folders = len(self.folder_movements)
        total_files = len(self.file_movements)
        total_items = total_folders + total_files
        
        self.preview_rows = self._build_preview_rows()
        conflict_count = sum(1 for row in self.preview_rows if row["status"] != "Sin conflicto")
        categories = {}
        for row in self.preview_rows:
            categories[row["destination_label"]] = categories.get(row["destination_label"], 0) + 1

        summary = QLabel(
            f"Se organizarán {total_items} elementos · {total_folders} carpetas · {total_files} archivos\n"
            f"Destino(s): {len(categories)} · Conflictos detectados: {conflict_count}\n"
            f"Carpeta origen: {self.folder_path or 'No especificada'}"
        )
        summary.setObjectName("preview_summary")
        summary.setWordWrap(True)
        layout.addWidget(summary)
        
        # Tabla de preview
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(5)
        self.preview_table.setHorizontalHeaderLabels(["Tipo", "Nombre", "Destino", "Ruta final", "Estado"])
        self.preview_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.preview_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.preview_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.preview_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.preview_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Llenar tabla
        self._populate_preview()
        layout.addWidget(self.preview_table)
        
        # Checkbox de confirmacion
        self.confirm_checkbox = QCheckBox("Confirmo que quiero proceder con la organizacion")
        layout.addWidget(self.confirm_checkbox)
        
        # Botones
        btn_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        btn_layout.addStretch()
        
        self.confirm_btn = QPushButton("Organizar Ahora")
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.confirm_btn)
        
        layout.addLayout(btn_layout)
        
        # Conectar checkbox
        self.confirm_checkbox.stateChanged.connect(self._on_confirm_changed)
        self._apply_theme()
    
    def _populate_preview(self):
        """Llena la tabla con la vista previa"""
        self.preview_table.setRowCount(0)
        for row_index, row_data in enumerate(self.preview_rows):
            self.preview_table.insertRow(row_index)
            self.preview_table.setItem(row_index, 0, QTableWidgetItem(row_data["type"]))
            self.preview_table.setItem(row_index, 1, QTableWidgetItem(row_data["name"]))
            self.preview_table.setItem(row_index, 2, QTableWidgetItem(row_data["destination_label"]))
            self.preview_table.setItem(row_index, 3, QTableWidgetItem(row_data["destination_path"]))
            status_item = QTableWidgetItem(row_data["status"])
            if row_data["status"] != "Sin conflicto":
                status_item.setForeground(QColor("#c62828"))
            self.preview_table.setItem(row_index, 4, status_item)
    
    def _format_size(self, size_bytes):
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def _on_confirm_changed(self, state):
        self.confirm_btn.setEnabled(state == Qt.CheckState.Checked)

    def _build_preview_rows(self):
        rows = []
        for mov in self.folder_movements:
            destination = self._get_destination_path(
                mov["folder"],
                mov["category"],
                is_folder=True,
            )
            rows.append(
                {
                    "type": "Carpeta",
                    "name": f"{mov['folder'].name} ({self._format_size(mov.get('size', 0))})",
                    "destination_label": mov["category"],
                    "destination_path": str(destination),
                    "status": self._detect_conflict(destination),
                }
            )
        for mov in self.file_movements:
            destination = self._get_destination_path(
                mov["file"],
                mov["category"],
                is_folder=False,
                organize_by_date=self.organize_by_date,
            )
            rows.append(
                {
                    "type": "Archivo",
                    "name": f"{mov['file'].name} ({self._format_size(mov.get('size', 0))})",
                    "destination_label": mov["category"],
                    "destination_path": str(destination),
                    "status": self._detect_conflict(destination),
                }
            )
        return rows

    def _get_destination_path(self, path_obj, category, is_folder=False, organize_by_date=False):
        base_folder = "VARIOS" if category == "VARIOS" else category
        base_path = Path(self.folder_path) / base_folder
        if organize_by_date and not is_folder:
            date_info = datetime.fromtimestamp(path_obj.stat().st_mtime)
            base_path = base_path / str(date_info.year) / f"{date_info.month:02d}"
        return base_path / path_obj.name

    def _detect_conflict(self, destination: Path) -> str:
        if not destination.exists():
            return "Sin conflicto"
        return "Ya existe en destino"

    def _apply_theme(self):
        app_config = AppConfig()
        theme = app_config.get_theme()
        font_size = app_config.get_font_size()
        self.setPalette(ThemeManager.apply_theme_to_palette(theme))
        self.setStyleSheet(ThemeManager.get_css_styles(theme, font_size))
