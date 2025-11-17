#!/usr/bin/env python3
"""
Componentes UI Estandarizados para el Organizador de Archivos
Componentes reutilizables con diseño consistente y temático
"""

from typing import Dict, Any, Optional, List, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QSpinBox, QCheckBox, QProgressBar,
    QGroupBox, QFrame, QScrollArea, QSplitter, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog, QSlider
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor

# Import opcional de theme_manager (módulo puede no existir)
try:
    from ..utils.theme_manager_optimized import theme_manager
except ImportError:
    theme_manager = None

from ..utils.constants import UI_CONFIG


class ModernButton(QPushButton):
    """
    Botón moderno con estilos consistentes y efectos hover
    """
    
    # Señales personalizadas
    clicked_with_data = pyqtSignal(object)  # Para pasar datos adicionales
    
    def __init__(self, text: str = "", icon: str = "", button_type: str = "primary", 
                 data: Any = None, parent=None):
        super().__init__(text, parent)
        
        self.button_type = button_type
        self.data = data
        self.icon_text = icon
        
        self.setup_ui()
        self.setup_styles()
        self.setup_connections()
    
    def setup_ui(self):
        """Configura la UI del botón"""
        # Configuración básica
        self.setMinimumHeight(UI_CONFIG["BUTTON_HEIGHT"])
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Icono si se proporciona
        if self.icon_text:
            self.setText(f"{self.icon_text} {self.text()}")
    
    def setup_styles(self):
        """Aplica estilos según el tipo de botón"""
        styles = {
            "primary": """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #1976d2, stop:1 #1565c0);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 14px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #42a5f5, stop:1 #1976d2);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #1565c0, stop:1 #0d47a1);
                }
                QPushButton:disabled {
                    background: #666;
                    color: #999;
                }
            """,
            "secondary": """
                QPushButton {
                    background: transparent;
                    color: #1976d2;
                    border: 2px solid #1976d2;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 14px;
                    padding: 6px 16px;
                }
                QPushButton:hover {
                    background: #e3f2fd;
                    border-color: #1565c0;
                }
                QPushButton:pressed {
                    background: #bbdefb;
                }
                QPushButton:disabled {
                    background: transparent;
                    color: #999;
                    border-color: #999;
                }
            """,
            "success": """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #4caf50, stop:1 #388e3c);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 14px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #66bb6a, stop:1 #4caf50);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #388e3c, stop:1 #2e7d32);
                }
            """,
            "warning": """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #ff9800, stop:1 #f57c00);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 14px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #ffb74d, stop:1 #ff9800);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #f57c00, stop:1 #ef6c00);
                }
            """,
            "danger": """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #f44336, stop:1 #d32f2f);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 14px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #ef5350, stop:1 #f44336);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #d32f2f, stop:1 #c62828);
                }
            """,
            "ghost": """
                QPushButton {
                    background: transparent;
                    color: #666;
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background: #f5f5f5;
                    color: #333;
                }
                QPushButton:pressed {
                    background: #e0e0e0;
                }
            """
        }
        
        self.setStyleSheet(styles.get(self.button_type, styles["primary"]))
    
    def setup_connections(self):
        """Configura las conexiones de señales"""
        self.clicked.connect(self._on_clicked)
    
    def _on_clicked(self):
        """Maneja el clic del botón"""
        self.clicked_with_data.emit(self.data)
    
    def set_button_type(self, button_type: str):
        """Cambia el tipo de botón"""
        self.button_type = button_type
        self.setup_styles()
    
    def set_data(self, data: Any):
        """Establece datos adicionales"""
        self.data = data


class ModernInput(QLineEdit):
    """
    Campo de entrada moderno con validación y estilos consistentes
    """
    
    # Señales personalizadas
    validation_changed = pyqtSignal(bool)  # valid/invalid
    value_changed = pyqtSignal(str)  # nuevo valor
    
    def __init__(self, placeholder: str = "", input_type: str = "text", 
                 required: bool = False, validator: Callable = None, parent=None):
        super().__init__(parent)
        
        self.placeholder = placeholder
        self.input_type = input_type
        self.required = required
        self.validator = validator
        self.is_valid = True
        
        self.setup_ui()
        self.setup_styles()
        self.setup_connections()
    
    def setup_ui(self):
        """Configura la UI del campo de entrada"""
        if hasattr(self, 'placeholder') and self.placeholder:
            self.setPlaceholderText(self.placeholder)
        self.setMinimumHeight(UI_CONFIG["INPUT_HEIGHT"])
        
        # Configuración según el tipo
        if self.input_type == "password":
            self.setEchoMode(QLineEdit.EchoMode.Password)
        elif self.input_type == "number":
            self.setInputMethodHints(Qt.InputMethodHint.ImhDigitsOnly)
    
    def setup_styles(self):
        """Aplica estilos al campo de entrada"""
        self.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #1976d2;
                background-color: #fafafa;
            }
            QLineEdit:invalid {
                border-color: #f44336;
                background-color: #ffebee;
            }
            QLineEdit:disabled {
                background-color: #f5f5f5;
                color: #999;
                border-color: #ccc;
            }
        """)
    
    def setup_connections(self):
        """Configura las conexiones de señales"""
        self.textChanged.connect(self._on_text_changed)
        self.editingFinished.connect(self._validate)
    
    def _on_text_changed(self, text: str):
        """Maneja el cambio de texto"""
        self.value_changed.emit(text)
        
        # Validación en tiempo real para campos requeridos
        if self.required and not text.strip():
            self._set_validity(False)
        elif self.validator:
            self._validate()
    
    def _validate(self):
        """Valida el contenido del campo"""
        text = self.text().strip()
        
        # Validación requerida
        if self.required and not text:
            self._set_validity(False)
            return False
        
        # Validación personalizada
        if self.validator and text:
            is_valid = self.validator(text)
            self._set_validity(is_valid)
            return is_valid
        
        # Si llega aquí, es válido
        self._set_validity(True)
        return True
    
    def _set_validity(self, is_valid: bool):
        """Establece el estado de validez"""
        if self.is_valid != is_valid:
            self.is_valid = is_valid
            self.validation_changed.emit(is_valid)
            
            # Actualizar estilo visual
            if is_valid:
                self.setStyleSheet(self.styleSheet().replace("border-color: #f44336", "border-color: #e0e0e0"))
            else:
                self.setStyleSheet(self.styleSheet().replace("border-color: #e0e0e0", "border-color: #f44336"))
    
    def get_value(self) -> str:
        """Obtiene el valor del campo"""
        return self.text().strip()
    
    def set_value(self, value: str):
        """Establece el valor del campo"""
        self.setText(value)
        self._validate()


class ModernCard(QFrame):
    """
    Tarjeta moderna con sombra y efectos hover
    """
    
    def __init__(self, title: str = "", content_widget: QWidget = None, 
                 card_type: str = "default", parent=None):
        super().__init__(parent)
        
        self.title = title
        self.content_widget = content_widget
        self.card_type = card_type
        
        self.setup_ui()
        self.setup_styles()
    
    def setup_ui(self):
        """Configura la UI de la tarjeta"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setMinimumHeight(100)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título si se proporciona
        if self.title:
            title_label = QLabel(self.title)
            title_label.setObjectName("card_title")
            title_label.setStyleSheet("""
                QLabel#card_title {
                    font-size: 18px;
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 10px;
                }
            """)
            layout.addWidget(title_label)
        
        # Widget de contenido si se proporciona
        if self.content_widget:
            layout.addWidget(self.content_widget)
    
    def setup_styles(self):
        """Aplica estilos a la tarjeta"""
        styles = {
            "default": """
                QFrame {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                }
                QFrame:hover {
                    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
                    border-color: #1976d2;
                }
            """,
            "elevated": """
                QFrame {
                    background-color: white;
                    border: none;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                }
                QFrame:hover {
                    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
                }
            """,
            "outlined": """
                QFrame {
                    background-color: transparent;
                    border: 2px solid #e0e0e0;
                    border-radius: 12px;
                }
                QFrame:hover {
                    border-color: #1976d2;
                    background-color: #fafafa;
                }
            """
        }
        
        self.setStyleSheet(styles.get(self.card_type, styles["default"]))


class ModernProgressBar(QProgressBar):
    """
    Barra de progreso moderna con estilos mejorados
    """
    
    def __init__(self, progress_type: str = "default", show_text: bool = True, parent=None):
        super().__init__(parent)
        
        self.progress_type = progress_type
        self.show_text = show_text
        
        self.setup_ui()
        self.setup_styles()
    
    def setup_ui(self):
        """Configura la UI de la barra de progreso"""
        self.setMinimumHeight(8)
        self.setMaximumHeight(12)
        
        if self.show_text:
            self.setTextVisible(True)
        else:
            self.setTextVisible(False)
    
    def setup_styles(self):
        """Aplica estilos a la barra de progreso"""
        styles = {
            "default": """
                QProgressBar {
                    border: none;
                    border-radius: 6px;
                    background-color: #e0e0e0;
                    text-align: center;
                    color: #333;
                    font-weight: bold;
                }
                QProgressBar::chunk {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #1976d2, stop:1 #42a5f5);
                    border-radius: 6px;
                }
            """,
            "success": """
                QProgressBar {
                    border: none;
                    border-radius: 6px;
                    background-color: #e0e0e0;
                    text-align: center;
                    color: #333;
                    font-weight: bold;
                }
                QProgressBar::chunk {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #4caf50, stop:1 #66bb6a);
                    border-radius: 6px;
                }
            """,
            "warning": """
                QProgressBar {
                    border: none;
                    border-radius: 6px;
                    background-color: #e0e0e0;
                    text-align: center;
                    color: #333;
                    font-weight: bold;
                }
                QProgressBar::chunk {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #ff9800, stop:1 #ffb74d);
                    border-radius: 6px;
                }
            """,
            "danger": """
                QProgressBar {
                    border: none;
                    border-radius: 6px;
                    background-color: #e0e0e0;
                    text-align: center;
                    color: #333;
                    font-weight: bold;
                }
                QProgressBar::chunk {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #f44336, stop:1 #ef5350);
                    border-radius: 6px;
                }
            """
        }
        
        self.setStyleSheet(styles.get(self.progress_type, styles["default"]))
    
    def set_progress_type(self, progress_type: str):
        """Cambia el tipo de barra de progreso"""
        self.progress_type = progress_type
        self.setup_styles()


class ModernCheckbox(QCheckBox):
    """
    Checkbox moderno con estilos mejorados
    """
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        
        self.setup_styles()
    
    def setup_styles(self):
        """Aplica estilos al checkbox"""
        self.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                color: #333;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #1976d2;
                border-color: #1976d2;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }
            QCheckBox::indicator:hover {
                border-color: #1976d2;
            }
            QCheckBox::indicator:disabled {
                background-color: #f5f5f5;
                border-color: #ccc;
            }
        """)


class ModernComboBox(QComboBox):
    """
    ComboBox moderno con estilos mejorados
    """
    
    def __init__(self, items: List[str] = None, parent=None):
        super().__init__(parent)
        
        if items:
            self.addItems(items)
        
        self.setup_styles()
    
    def setup_styles(self):
        """Aplica estilos al ComboBox"""
        self.setStyleSheet("""
            QComboBox {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: white;
                min-width: 100px;
            }
            QComboBox:focus {
                border-color: #1976d2;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTMgNEw2IDdMOSA0IiBzdHJva2U9IiM2NjYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }
            QComboBox QAbstractItemView {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                selection-background-color: #e3f2fd;
            }
        """)


class ModernSpinBox(QSpinBox):
    """
    SpinBox moderno con estilos mejorados
    """
    
    def __init__(self, minimum: int = 0, maximum: int = 100, value: int = 0, parent=None):
        super().__init__(parent)
        
        self.setRange(minimum, maximum)
        self.setValue(value)
        
        self.setup_styles()
    
    def setup_styles(self):
        """Aplica estilos al SpinBox"""
        self.setStyleSheet("""
            QSpinBox {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: white;
                min-width: 80px;
            }
            QSpinBox:focus {
                border-color: #1976d2;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                border: none;
                background-color: #f5f5f5;
                width: 20px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #e0e0e0;
            }
            QSpinBox::up-arrow, QSpinBox::down-arrow {
                width: 8px;
                height: 8px;
            }
        """)


# Funciones de utilidad para crear componentes rápidamente
def create_button(text: str, button_type: str = "primary", icon: str = "", 
                 data: Any = None, parent=None) -> ModernButton:
    """Crea un botón moderno rápidamente"""
    return ModernButton(text, icon, button_type, data, parent)


def create_input(placeholder: str = "", input_type: str = "text", 
                required: bool = False, validator: Callable = None, parent=None) -> ModernInput:
    """Crea un campo de entrada moderno rápidamente"""
    return ModernInput(placeholder, input_type, required, validator, parent)


def create_card(title: str = "", content_widget: QWidget = None, 
               card_type: str = "default", parent=None) -> ModernCard:
    """Crea una tarjeta moderna rápidamente"""
    return ModernCard(title, content_widget, card_type, parent)


def create_progress_bar(progress_type: str = "default", show_text: bool = True, 
                      parent=None) -> ModernProgressBar:
    """Crea una barra de progreso moderna rápidamente"""
    return ModernProgressBar(progress_type, show_text, parent)


def create_checkbox(text: str = "", parent=None) -> ModernCheckbox:
    """Crea un checkbox moderno rápidamente"""
    return ModernCheckbox(text, parent)


def create_combo_box(items: List[str] = None, parent=None) -> ModernComboBox:
    """Crea un ComboBox moderno rápidamente"""
    return ModernComboBox(items, parent)


def create_spin_box(minimum: int = 0, maximum: int = 100, value: int = 0, 
                  parent=None) -> ModernSpinBox:
    """Crea un SpinBox moderno rápidamente"""
    return ModernSpinBox(minimum, maximum, value, parent)
