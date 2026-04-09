#!/usr/bin/env python3
"""
Dialogo de Preview para el Organizador de Archivos
Muestra una vista previa de los cambios antes de organizar
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class PreviewDialog(QDialog):
    """Dialogo que muestra vista previa de cambios antes de organizar"""
    
    def __init__(self, folder_movements, file_movements, folder_path, parent=None):
        super().__init__(parent)
        self.folder_movements = folder_movements
        self.file_movements = file_movements
        self.folder_path = folder_path
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
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)
        
        # Resumen
        total_folders = len(self.folder_movements)
        total_files = len(self.file_movements)
        total_items = total_folders + total_files
        
        summary = QLabel(
            f"Se organizaran {total_items} elementos:\n"
            f"  - {total_folders} carpetas\n"
            f"  - {total_files} archivos sueltos\n"
            f"  Carpeta origen: {self.folder_path}"
        )
        summary.setStyleSheet("font-size: 13px; color: #555; padding: 10px; background: #f8f9fa; border-radius: 8px;")
        summary.setWordWrap(True)
        layout.addWidget(summary)
        
        # Tabla de preview
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(4)
        self.preview_table.setHorizontalHeaderLabels(["Tipo", "Nombre", "Destino", "Tamano"])
        self.preview_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.preview_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.preview_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.preview_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Llenar tabla
        self._populate_preview()
        layout.addWidget(self.preview_table)
        
        # Checkbox de confirmacion
        self.confirm_checkbox = QCheckBox("Confirmo que quiero proceder con la organizacion")
        self.confirm_checkbox.setStyleSheet("font-size: 13px; font-weight: bold; padding: 8px;")
        layout.addWidget(self.confirm_checkbox)
        
        # Botones
        btn_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setStyleSheet("""
            QPushButton { padding: 10px 20px; font-size: 13px; background: #95a5a6; color: white; border: none; border-radius: 6px; }
            QPushButton:hover { background: #7f8c8d; }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        btn_layout.addStretch()
        
        self.confirm_btn = QPushButton("Organizar Ahora")
        self.confirm_btn.setStyleSheet("""
            QPushButton { padding: 10px 20px; font-size: 13px; background: #27ae60; color: white; border: none; border-radius: 6px; }
            QPushButton:hover { background: #2ecc71; }
            QPushButton:disabled { background: #bdc3c7; }
        """)
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.confirm_btn)
        
        layout.addLayout(btn_layout)
        
        # Conectar checkbox
        self.confirm_checkbox.stateChanged.connect(self._on_confirm_changed)
    
    def _populate_preview(self):
        """Llena la tabla con la vista previa"""
        row = 0
        
        # Carpetas
        for mov in self.folder_movements:
            self.preview_table.insertRow(row)
            self.preview_table.setItem(row, 0, QTableWidgetItem("Carpeta"))
            self.preview_table.setItem(row, 1, QTableWidgetItem(mov['folder'].name))
            self.preview_table.setItem(row, 2, QTableWidgetItem(mov['category']))
            self.preview_table.setItem(row, 3, QTableWidgetItem(self._format_size(mov.get('size', 0))))
            row += 1
        
        # Archivos
        for mov in self.file_movements:
            self.preview_table.insertRow(row)
            self.preview_table.setItem(row, 0, QTableWidgetItem("Archivo"))
            self.preview_table.setItem(row, 1, QTableWidgetItem(mov['file'].name))
            self.preview_table.setItem(row, 2, QTableWidgetItem(mov['category']))
            self.preview_table.setItem(row, 3, QTableWidgetItem(self._format_size(mov.get('size', 0))))
            row += 1
    
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