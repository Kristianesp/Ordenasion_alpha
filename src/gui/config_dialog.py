#!/usr/bin/env python3
"""
Diálogo de Configuración para el Organizador de Archivos
Maneja la gestión de categorías y extensiones
"""

import os
from typing import Dict, List, Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QInputDialog, QMessageBox, QDialogButtonBox, QFileDialog,
    QTextEdit, QSpinBox, QCheckBox, QComboBox, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor

from src.utils.constants import COLORS, DIALOG_STYLES
from src.core.category_manager import CategoryManager


class ConfigDialog(QDialog):
    """Ventana de configuración para gestionar categorías y extensiones"""
    
    # Señales para notificar cambios
    categories_updated = pyqtSignal()
    interface_changes_requested = pyqtSignal(int, str)  # font_size, theme
    
    def __init__(self, parent=None, category_manager: CategoryManager = None):
        super().__init__(parent)
        self.category_manager = category_manager or CategoryManager()
        self.init_ui()
        # Cargar tema actual en el combo box
        self._load_current_theme()
        self.refresh_categories_list()
        self.update_stats()
        # Aplicar tema inicial
        self.apply_current_theme_to_self()
    
    def _load_current_theme(self):
        """Carga el tema actual en el combo box"""
        try:
            from src.utils.app_config import AppConfig
            app_config = AppConfig()
            current_theme = app_config.get_theme()
            if hasattr(self, 'theme_combo') and self.theme_combo:
                # Buscar el índice del tema actual
                for i in range(self.theme_combo.count()):
                    if self.theme_combo.itemText(i) == current_theme:
                        self.theme_combo.setCurrentIndex(i)
                        break
        except:
            pass
    
    def init_ui(self):
        """Inicializa la interfaz del diálogo"""
        self.setWindowTitle("⚙️ Configuración de Categorías")
        self.setGeometry(300, 200, 700, 600)
        self.setModal(True)
        # Los estilos se aplican automáticamente via themes.py
        
        layout = QVBoxLayout(self)
        
        # Título
        self.title_label = QLabel("⚙️ Configuración de Categorías y Extensiones")
        self.title_label.setToolTip("⚙️ Panel principal para configurar categorías, extensiones y personalizar la interfaz")
        self.title_label.setObjectName("config_title_label")
        # Estilos se aplicarán dinámicamente con el tema
        layout.addWidget(self.title_label)
        
        # Estadísticas
        self.stats_label = QLabel()
        self.stats_label.setToolTip("📊 Resumen de categorías y extensiones configuradas en el sistema")
        self.stats_label.setObjectName("config_stats_label")
        # Estilos se aplicarán dinámicamente con el tema
        layout.addWidget(self.stats_label)
        
        # Área principal con dos columnas
        main_layout = QHBoxLayout()
        
        # Columna izquierda - Categorías
        left_column = QVBoxLayout()
        
        # Grupo de configuración de interfaz
        interface_group = QGroupBox("🎨 Configuración de Interfaz")
        interface_group.setToolTip("🎨 Personaliza la apariencia visual de la aplicación: temas y tamaños de fuente")
        interface_layout = QGridLayout(interface_group)
        
        # Selector de tamaño de fuente
        font_size_label = QLabel("📝 Tamaño de fuente:")
        font_size_label.setToolTip("📝 Cambia el tamaño de la fuente en toda la aplicación")
        interface_layout.addWidget(font_size_label, 0, 0)
        
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems([
            "Pequeño (10px)",
            "Normal (12px) - Por defecto",
            "Grande (14px)",
            "Muy Grande (16px)"
        ])
        self.font_size_combo.setCurrentIndex(1)  # Normal por defecto
        self.font_size_combo.setToolTip("📝 Selecciona el tamaño de fuente para toda la aplicación")
        self.font_size_combo.currentTextChanged.connect(self.on_font_size_changed)
        interface_layout.addWidget(self.font_size_combo, 0, 1)
        
        # Selector de tema
        theme_label = QLabel("🌈 Tema de color:")
        theme_label.setToolTip("🌈 Cambia el esquema de colores de la aplicación")
        interface_layout.addWidget(theme_label, 1, 0)
        
        self.theme_combo = QComboBox()
        # Importar ThemeManager para obtener la lista dinámica de temas
        from src.utils.themes import ThemeManager
        theme_names = ThemeManager.get_theme_names()
        self.theme_combo.addItems(theme_names)
        self.theme_combo.setToolTip("🌈 Selecciona un tema de color para la aplicación")
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        interface_layout.addWidget(self.theme_combo, 1, 1)
        
        # Botón para aplicar cambios
        self.apply_interface_btn = QPushButton("🎨 Aplicar Cambios")
        self.apply_interface_btn.setToolTip("🎨 Aplica los cambios de interfaz inmediatamente")
        self.apply_interface_btn.clicked.connect(self.apply_interface_changes)
        self.apply_interface_btn.setFixedHeight(36)  # ALTURA ESTANDARIZADA
        # Usa color primary del tema automáticamente
        interface_layout.addWidget(self.apply_interface_btn, 2, 0, 1, 2)
        
        left_column.addWidget(interface_group)
        
        # Grupo de categorías
        categories_group = QGroupBox("📁 Categorías Existentes")
        categories_group.setToolTip("📁 Gestiona las categorías del sistema y crea nuevas personalizadas")
        categories_layout = QVBoxLayout(categories_group)
        
        # Lista de categorías - USA TEMAS AUTOMÁTICAMENTE  
        self.categories_list = QListWidget()
        self.categories_list.setToolTip("📁 Selecciona una categoría de la lista para ver y gestionar sus extensiones")
        self.categories_list.itemClicked.connect(self.on_category_selected)
        self.categories_list.setMinimumHeight(200)
        # Los estilos se aplican automáticamente via themes.py
        categories_layout.addWidget(self.categories_list)
        
        # Botones de categorías
        cat_buttons_layout = QHBoxLayout()
        
        self.add_cat_btn = QPushButton("➕ Añadir Categoría")
        self.add_cat_btn.setToolTip("➕ Crea una nueva categoría personalizada")
        self.add_cat_btn.clicked.connect(self.add_category)
        self.add_cat_btn.setFixedHeight(36)  # ALTURA ESTANDARIZADA
        self.add_cat_btn.setProperty("styleClass", "success")  # Usa color success del tema
        cat_buttons_layout.addWidget(self.add_cat_btn)
        
        self.remove_cat_btn = QPushButton("🗑️ Eliminar Categoría")
        self.remove_cat_btn.setToolTip("🗑️ Elimina la categoría seleccionada (solo personalizadas)")
        self.remove_cat_btn.clicked.connect(self.remove_category)
        self.remove_cat_btn.setFixedHeight(36)  # ALTURA ESTANDARIZADA
        self.remove_cat_btn.setProperty("styleClass", "error")  # Usa color error del tema
        cat_buttons_layout.addWidget(self.remove_cat_btn)
        
        categories_layout.addLayout(cat_buttons_layout)
        left_column.addWidget(categories_group)
        
        # Columna derecha - Extensiones
        right_column = QVBoxLayout()
        
        # Grupo de extensiones
        extensions_group = QGroupBox("📄 Extensiones de la Categoría")
        extensions_group.setToolTip("📄 Gestiona las extensiones de archivo de la categoría seleccionada")
        extensions_layout = QVBoxLayout(extensions_group)
        
        # Lista de extensiones - USA TEMAS AUTOMÁTICAMENTE
        self.extensions_list = QListWidget()
        self.extensions_list.setToolTip("📄 Lista de extensiones de la categoría seleccionada")
        self.extensions_list.setMinimumHeight(200)
        # Los estilos se aplican automáticamente via themes.py
        extensions_layout.addWidget(self.extensions_list)
        
        # Botones de extensiones
        ext_buttons_layout = QHBoxLayout()
        
        self.add_ext_btn = QPushButton("➕ Añadir Extensión")
        self.add_ext_btn.setToolTip("➕ Añade una nueva extensión a la categoría")
        self.add_ext_btn.clicked.connect(self.add_extension)
        ext_buttons_layout.addWidget(self.add_ext_btn)
        
        self.remove_ext_btn = QPushButton("🗑️ Eliminar Extensión")
        self.remove_ext_btn.setToolTip("🗑️ Elimina la extensión seleccionada")
        self.remove_ext_btn.clicked.connect(self.remove_extension)
        ext_buttons_layout.addWidget(self.remove_ext_btn)
        
        extensions_layout.addLayout(ext_buttons_layout)
        right_column.addWidget(extensions_group)
        
        # Botones de acción
        action_buttons_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("📤 Exportar a TXT")
        self.export_btn.setToolTip("📤 Exporta todas las categorías y extensiones a un archivo de texto para respaldo")
        self.export_btn.clicked.connect(self.export_to_txt)
        action_buttons_layout.addWidget(self.export_btn)
        
        self.reset_btn = QPushButton("🔄 Restaurar Por Defecto")
        self.reset_btn.setToolTip("🔄 Restaura las categorías del sistema por defecto (elimina todas las personalizadas)")
        self.reset_btn.clicked.connect(self.reset_to_default)
        action_buttons_layout.addWidget(self.reset_btn)
        
        right_column.addLayout(action_buttons_layout)
        
        # Añadir columnas al layout principal
        main_layout.addLayout(left_column, 1)
        main_layout.addLayout(right_column, 1)
        layout.addLayout(main_layout)
        
        # Botones de diálogo
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Personalizar botones
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("💾 Guardar y Cerrar")
        ok_button.setToolTip("💾 Guarda los cambios y cierra la ventana")
        
        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setText("❌ Cancelar")
        cancel_button.setToolTip("❌ Cancela los cambios y cierra la ventana")
        
        layout.addWidget(button_box)
        
        # Estado inicial
        self.remove_cat_btn.setEnabled(False)
        self.add_ext_btn.setEnabled(False)
        self.remove_ext_btn.setEnabled(False)
    
    def refresh_categories_list(self):
        """Actualiza la lista de categorías"""
        self.categories_list.clear()
        
        # Obtener colores del tema actual (no hardcodeados)
        from src.utils.themes import ThemeManager
        from src.utils.app_config import AppConfig
        app_config = AppConfig()
        theme = app_config.get_theme()
        colors = ThemeManager.get_theme_colors(theme)
        
        # Obtener categorías del gestor
        categories = self.category_manager.get_categories()
        
        for category_name in sorted(categories.keys()):
            item = QListWidgetItem(category_name)
            
            # Marcar categorías del sistema con color del tema
            if self.category_manager.is_system_category(category_name):
                # Usar color del tema en lugar de hardcodeado
                item.setBackground(QColor(colors.get('accent', colors['primary'])))
                item.setForeground(QColor(colors['text_primary']))
                item.setToolTip("📁 Categoría del sistema (no se puede eliminar)")
            else:
                item.setForeground(QColor(colors['text_primary']))
                item.setToolTip("📁 Categoría personalizada (se puede eliminar)")
            
            self.categories_list.addItem(item)
    
    def on_category_selected(self, item):
        """Maneja la selección de una categoría"""
        if not item:
            return
        
        category_name = item.text()
        self.refresh_extensions_list(category_name)
        
        # Habilitar/deshabilitar botones según el tipo de categoría
        is_system = self.category_manager.is_system_category(category_name)
        self.remove_cat_btn.setEnabled(not is_system)
        self.add_ext_btn.setEnabled(True)
        self.remove_ext_btn.setEnabled(True)
    
    def refresh_extensions_list(self, category_name: str):
        """Actualiza la lista de extensiones de una categoría"""
        self.extensions_list.clear()
        
        # Obtener colores del tema actual
        from src.utils.themes import ThemeManager
        from src.utils.app_config import AppConfig
        app_config = AppConfig()
        theme = app_config.get_theme()
        colors = ThemeManager.get_theme_colors(theme)
        
        extensions = self.category_manager.get_extensions_for_category(category_name)
        
        for extension in sorted(extensions):
            item = QListWidgetItem(extension)
            item.setForeground(QColor(colors['text_primary']))
            self.extensions_list.addItem(item)
    
    def add_category(self):
        """Añade una nueva categoría"""
        name, ok = QInputDialog.getText(
            self, "➕ Nueva Categoría", 
            "Nombre de la nueva categoría:"
        )
        
        if ok and name.strip():
            name = name.strip().upper()
            
            if name in self.category_manager.get_categories():
                QMessageBox.warning(self, "Advertencia", f"La categoría '{name}' ya existe.")
                return
            
            # Añadir categoría vacía
            if self.category_manager.add_category(name, []):
                self.refresh_categories_list()
                self.update_stats()
                QMessageBox.information(self, "Éxito", f"Categoría '{name}' creada exitosamente.")
            else:
                QMessageBox.critical(self, "Error", "No se pudo crear la categoría.")
    
    def remove_category(self):
        """Elimina la categoría seleccionada"""
        current_item = self.categories_list.currentItem()
        if not current_item:
            return
        
        category_name = current_item.text()
        
        if self.category_manager.is_system_category(category_name):
            QMessageBox.warning(self, "Advertencia", "No se pueden eliminar categorías del sistema.")
            return
        
        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Estás seguro de que quieres eliminar la categoría '{category_name}'?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.category_manager.remove_category(category_name):
                self.refresh_categories_list()
                self.extensions_list.clear()
                self.update_stats()
                QMessageBox.information(self, "Éxito", f"Categoría '{category_name}' eliminada exitosamente.")
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar la categoría.")
    
    def add_extension(self):
        """Añade una extensión a la categoría seleccionada"""
        current_item = self.categories_list.currentItem()
        if not current_item:
            return
        
        category_name = current_item.text()
        extension, ok = QInputDialog.getText(
            self, "➕ Nueva Extensión", 
            f"Extensión para la categoría '{category_name}':\n\n"
            "Formato: .ext (ejemplo: .pdf)"
        )
        
        if ok and extension.strip():
            extension = extension.strip()
            
            # Validar formato
            if not self.category_manager.validate_extension(extension):
                QMessageBox.warning(self, "Formato Inválido", 
                    "La extensión debe comenzar con '.' y tener al menos 2 caracteres.\n\n"
                    "Ejemplo: .pdf, .mp3, .jpg")
                return
            
            # Verificar si ya existe
            if extension in self.category_manager.get_extensions_for_category(category_name):
                QMessageBox.warning(self, "Advertencia", f"La extensión '{extension}' ya existe en esta categoría.")
                return
            
            # Añadir extensión
            if self.category_manager.add_extension_to_category(category_name, extension):
                self.refresh_extensions_list(category_name)
                self.update_stats()
                QMessageBox.information(self, "Éxito", f"Extensión '{extension}' añadida exitosamente.")
            else:
                QMessageBox.critical(self, "Error", "No se pudo añadir la extensión.")
    
    def remove_extension(self):
        """Elimina la extensión seleccionada"""
        current_cat_item = self.categories_list.currentItem()
        current_ext_item = self.extensions_list.currentItem()
        
        if not current_cat_item or not current_ext_item:
            return
        
        category_name = current_cat_item.text()
        extension = current_ext_item.text()
        
        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Estás seguro de que quieres eliminar la extensión '{extension}' "
            f"de la categoría '{category_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.category_manager.remove_extension_from_category(category_name, extension):
                self.refresh_extensions_list(category_name)
                self.update_stats()
                QMessageBox.information(self, "Éxito", f"Extensión '{extension}' eliminada exitosamente.")
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar la extensión.")
    
    def export_to_txt(self):
        """Exporta las categorías a un archivo de texto"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "📤 Exportar Categorías",
            "categorias_organizador.txt",
            "Archivos de texto (*.txt)"
        )
        
        if filepath:
            if self.category_manager.export_to_txt(filepath):
                QMessageBox.information(self, "Éxito", 
                    f"Categorías exportadas exitosamente a:\n{filepath}")
            else:
                QMessageBox.critical(self, "Error", "No se pudo exportar las categorías.")
    
    def reset_to_default(self):
        """Restaura las categorías por defecto"""
        reply = QMessageBox.question(
            self, "Confirmar Restauración",
            "¿Estás seguro de que quieres restaurar las categorías por defecto?\n\n"
            "Esta acción eliminará todas las categorías personalizadas y no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.category_manager.reset_to_default()
            self.refresh_categories_list()
            self.extensions_list.clear()
            self.update_stats()
            QMessageBox.information(self, "Éxito", "Categorías restauradas por defecto exitosamente.")
    
    def update_stats(self):
        """Actualiza las estadísticas mostradas"""
        stats = self.category_manager.get_stats()
        total_categories = len(stats)
        total_extensions = sum(stats.values())
        
        stats_text = f"📊 {total_categories} categorías • 📄 {total_extensions} extensiones"
        self.stats_label.setText(stats_text)
    
    def accept(self):
        """Maneja la aceptación del diálogo"""
        # Guardar configuración
        if self.category_manager.save_configuration():
            self.categories_updated.emit()
            super().accept()
        else:
            QMessageBox.critical(self, "Error", "No se pudo guardar la configuración.")
    
    def get_updated_categories(self) -> Dict[str, List[str]]:
        """Retorna las categorías actualizadas"""
        return self.category_manager.get_categories()
    
    def update_global_index(self):
        """Actualiza el índice inverso global"""
        # Este método se puede usar para sincronizar con otros componentes
        pass
    
    def on_font_size_changed(self, value):
        """Maneja el cambio en el tamaño de fuente"""
        # El cambio se aplicará cuando se presione "Aplicar Cambios"
        pass
    
    def on_theme_changed(self, theme_text):
        """Maneja el cambio de tema"""
        # El cambio se aplicará cuando se presione "Aplicar Cambios"
        pass
    
    def apply_interface_changes(self):
        """Aplica los cambios de interfaz INMEDIATAMENTE"""
        try:
            # Obtener valores actuales
            font_size = self.get_font_size_from_combo()
            theme_text = self.theme_combo.currentText()
            
            # Guardar configuración PRIMERO
            from src.utils.app_config import AppConfig
            app_config = AppConfig()
            app_config.set_font_size(font_size)
            app_config.set_theme(theme_text)
            
            # Emitir señal para aplicar cambios INMEDIATAMENTE
            self.interface_changes_requested.emit(font_size, theme_text)
            
            # Aplicar el tema a este mismo diálogo inmediatamente (después de guardar)
            # Usar QTimer para asegurar que se aplica después de que se procesen los eventos
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(50, self.apply_current_theme_to_self)
            
            # Crear el mensaje con el tema aplicado
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("✅ Cambios Aplicados INMEDIATAMENTE")
            msg_box.setText(
                f"🎨 Tema: {theme_text}\n"
                f"📝 Tamaño: {self.get_font_size_description(font_size)}\n\n"
                f"Los cambios se han aplicado INMEDIATAMENTE a toda la aplicación."
            )
            msg_box.setIcon(QMessageBox.Icon.Information)
            
            # Aplicar el tema actual al QMessageBox
            from src.utils.themes import ThemeManager
            theme_palette = ThemeManager.apply_theme_to_palette(theme_text)
            theme_css = ThemeManager.get_css_styles(theme_text, font_size)
            msg_box.setPalette(theme_palette)
            msg_box.setStyleSheet(theme_css)
            
            msg_box.exec()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"❌ Error al aplicar cambios de interfaz:\n{str(e)}"
            )
    
    def get_font_size_from_combo(self) -> int:
        """Obtiene el tamaño de fuente en píxeles desde el combo"""
        current_text = self.font_size_combo.currentText()
        if "Pequeño" in current_text:
            return 10
        elif "Normal" in current_text:
            return 12
        elif "Grande" in current_text:
            return 14
        elif "Muy Grande" in current_text:
            return 16
        else:
            return 12  # Por defecto
    
    def get_font_size_description(self, size: int) -> str:
        """Convierte el tamaño de fuente a descripción legible"""
        if size <= 10:
            return "Pequeño"
        elif size <= 12:
            return "Normal (Por defecto)"
        elif size <= 14:
            return "Grande"
        else:
            return "Muy Grande"
    
    def apply_current_theme_to_self(self):
        """Aplica el tema actual a este mismo diálogo usando el sistema mejorado"""
        try:
            from src.utils.app_config import AppConfig
            from src.utils.themes import ThemeManager
            from PyQt6.QtWidgets import QWidget, QGroupBox, QComboBox, QPushButton, QLabel
            
            app_config = AppConfig()
            theme = app_config.get_theme()
            font_size = app_config.get_font_size()
            
            # Obtener colores del tema
            colors = ThemeManager.get_theme_colors(theme)
            palette = ThemeManager.apply_theme_to_palette(theme)
            css_styles = ThemeManager.get_css_styles(theme, font_size)
            
            # Aplicar paleta y CSS al diálogo PRIMERO
            self.setPalette(palette)
            self.setStyleSheet(css_styles)
            
            # Aplicar estilos a título y stats con colores del tema
            if hasattr(self, 'title_label') and self.title_label:
                self.title_label.setStyleSheet(f"""
                    QLabel {{
                        font-size: 18px;
                        font-weight: bold;
                        color: {colors['text_primary']} !important;
                        padding: 15px;
                        text-align: center;
                        background-color: {colors['surface']} !important;
                        border-radius: 8px;
                        margin-bottom: 10px;
                    }}
                """)
            
            if hasattr(self, 'stats_label') and self.stats_label:
                self.stats_label.setStyleSheet(f"""
                    QLabel {{
                        color: {colors['text_secondary']} !important;
                        font-size: 12px;
                        padding: 8px;
                        text-align: center;
                        background-color: {colors['surface']} !important;
                        border-radius: 6px;
                        border: 1px solid {colors['border']} !important;
                    }}
                """)
            
            # Aplicar estilos específicos a QListWidget (listas de categorías y extensiones)
            if hasattr(self, 'categories_list') and self.categories_list:
                self.categories_list.setStyleSheet(f"""
                    QListWidget {{
                        background-color: {colors['surface']} !important;
                        color: {colors['text_primary']} !important;
                        border: 1px solid {colors['border']} !important;
                        border-radius: 8px;
                        padding: 4px;
                    }}
                    QListWidget::item {{
                        background-color: {colors['surface']} !important;
                        color: {colors['text_primary']} !important;
                        padding: 6px;
                        border-radius: 4px;
                    }}
                    QListWidget::item:selected {{
                        background-color: {colors['primary']} !important;
                        color: white !important;
                    }}
                    QListWidget::item:hover {{
                        background-color: {colors.get('button_hover', colors['secondary'])} !important;
                        color: white !important;
                    }}
                """)
            
            if hasattr(self, 'extensions_list') and self.extensions_list:
                self.extensions_list.setStyleSheet(f"""
                    QListWidget {{
                        background-color: {colors['surface']} !important;
                        color: {colors['text_primary']} !important;
                        border: 1px solid {colors['border']} !important;
                        border-radius: 8px;
                        padding: 4px;
                    }}
                    QListWidget::item {{
                        background-color: {colors['surface']} !important;
                        color: {colors['text_primary']} !important;
                        padding: 6px;
                        border-radius: 4px;
                    }}
                    QListWidget::item:selected {{
                        background-color: {colors['primary']} !important;
                        color: white !important;
                    }}
                    QListWidget::item:hover {{
                        background-color: {colors.get('button_hover', colors['secondary'])} !important;
                        color: white !important;
                    }}
                """)
            
            # Aplicar a todos los widgets hijos de forma más completa
            for widget in self.findChildren(QWidget):
                try:
                    widget.setPalette(palette)
                    # Para GroupBox, Labels, ComboBox, etc., aplicar estilos del tema
                    if isinstance(widget, (QGroupBox, QLabel, QComboBox)):
                        # Aplicar estilos del tema pero mantener funcionalidad
                        widget.setStyleSheet(css_styles)
                    elif isinstance(widget, QPushButton):
                        # Los botones ya tienen estilos en el CSS global, solo aplicar paleta
                        widget.setPalette(palette)
                    elif isinstance(widget, QListWidget):
                        # QListWidget ya tiene estilos específicos arriba, solo aplicar paleta
                        widget.setPalette(palette)
                    else:
                        # Otros widgets: aplicar CSS si no tiene estilos personalizados
                        current_style = widget.styleSheet() or ""
                        if not current_style or '!important' not in current_style:
                            widget.setStyleSheet(css_styles)
                except:
                    pass
            
            # Refrescar las listas para aplicar nuevos colores a los items
            # Guardar categoría seleccionada antes de refrescar
            current_category = None
            if hasattr(self, 'categories_list') and self.categories_list.currentItem():
                current_category = self.categories_list.currentItem().text()
            
            # Refrescar lista de categorías
            self.refresh_categories_list()
            
            # Restaurar selección si había una
            if current_category:
                for i in range(self.categories_list.count()):
                    item = self.categories_list.item(i)
                    if item and item.text() == current_category:
                        self.categories_list.setCurrentItem(item)
                        self.refresh_extensions_list(current_category)
                        break
            
            # Forzar actualización completa
            self.update()
            self.repaint()
            
            # Procesar eventos para asegurar que se apliquen los cambios
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.processEvents()
            
        except Exception as e:
            from src.utils.logger import error
            error(f"Error aplicando tema al diálogo de configuración: {e}")
            # Fallback al método anterior
            self._apply_theme_fallback()
    
    def _apply_theme_fallback(self):
        """Método de respaldo para aplicar tema"""
        try:
            from src.utils.themes import ThemeManager
            from src.utils.app_config import AppConfig
            
            app_config = AppConfig()
            theme = app_config.get_theme()
            font_size = app_config.get_font_size()
            
            # Aplicar paleta y estilos
            palette = ThemeManager.apply_theme_to_palette(theme)
            css_styles = ThemeManager.get_css_styles(theme, font_size)
            
            # Aplicar al diálogo
            self.setPalette(palette)
            self.setStyleSheet(css_styles)
            
            # Aplicar a todos los widgets hijos (respetando estilos personalizados)
            for widget in self.findChildren(QWidget):
                try:
                    widget.setPalette(palette)
                    # Solo aplicar CSS si no tiene estilos personalizados con !important
                    current_style = widget.styleSheet() or ""
                    if not current_style or '!important' not in current_style:
                        widget.setStyleSheet(css_styles)
                except:
                    pass
            
            # Forzar actualización visual
            self.update()
            self.repaint()
            
        except Exception as e:
            from src.utils.logger import error
            error(f"Error en método de respaldo: {e}")
