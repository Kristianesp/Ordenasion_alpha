# 📋 ANÁLISIS Y MEJORAS PARA ORDENASION

## 📊 Resumen Ejecutivo

Este documento contiene un análisis exhaustivo del proyecto **Ordenasion**, identificando mejoras, bugs potenciales y funcionalidades que faltan o sobran.

---

## 🎯 1. SISTEMA DE CATEGORIZACIÓN

### Mejoras Detectadas

#### 1.1. Panel de Gestión de Reglas Personalizadas

**Problema:** Las reglas personalizadas existen pero no hay interfaz para gestionarlas.

**Solución Propuesta:**

```python
# Nuevo archivo: gui/rule_panel.py
from PyQt6.QtWidgets import QDialog, QTableWidget, QVBoxLayout, QPushButton, QMessageBox
from src.core.category_manager import CategoryManager, CategoryRule
from src.gui.config_dialog import ConfigDialog

class RulePanel(QDialog):
    """Panel para gestionar reglas personalizadas de categorización"""
    
    def __init__(self, parent=None, category_manager: CategoryManager = None):
        super().__init__(parent)
        self.category_manager = category_manager
        self.init_ui()
        self.load_rules()
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        self.setWindowTitle("📋 Reglas de Categorización Personalizada")
        self.setMinimumSize(800, 600)
        
        # Layout principal
        layout = QVBoxLayout()
        
        # Tabla de reglas
        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(6)
        self.rules_table.setHorizontalHeaderLabels([
            "Nombre", "Patrón", "Categoría", "Prioridad", "Estado", "Archivos Afectados"
        ])
        
        # Agregar botones de acción
        self.btn_add = QPushButton("➕ Agregar Regla")
        self.btn_edit = QPushButton("✏️ Editar")
        self.btn_delete = QPushButton("🗑️ Eliminar")
        self.btn_apply = QPushButton("🎯 Aplicar a Archivos")
        
        # Botones de control
        self.btn_close = QPushButton("❌ Cerrar")
        
        # Configurar botones
        self.btn_add.clicked.connect(self.add_rule)
        self.btn_edit.clicked.connect(self.edit_selected_rule)
        self.btn_delete.clicked.connect(self.delete_selected_rule)
        self.btn_apply.clicked.connect(self.apply_selected_rules)
        self.btn_close.clicked.connect(self.close)
        
        layout.addWidget(self.rules_table)
        layout.addSpacing(10)
        
        # Botones de acción
        action_layout = QHBoxLayout()
        action_layout.addWidget(self.btn_add)
        action_layout.addWidget(self.btn_edit)
        action_layout.addWidget(self.btn_delete)
        action_layout.addWidget(self.btn_apply)
        action_layout.addStretch()
        action_layout.addWidget(self.btn_close)
        
        layout.addLayout(action_layout)
        self.setLayout(layout)
    
    def load_rules(self):
        """Carga las reglas desde la configuración"""
        self.rules_table.setRowCount(0)
        
        if not self.category_manager:
            return
        
        # Aquí cargaríamos las reglas desde category_manager.custom_rules
        # y las mostraríamos en la tabla
        pass
    
    def add_rule(self):
        """Abre diálogo para agregar regla"""
        # Crear diálogo de configuración de regla
        dialog = RuleConfigDialog(self, self.category_manager)
        if dialog.exec() == QDialog.Accepted:
            rule = dialog.get_rule_data()
            # Guardar regla usando category_manager.add_custom_rule()
            pass
    
    def apply_selected_rules(self):
        """Aplica las reglas seleccionadas a archivos seleccionados"""
        # Implementación completa para aplicar reglas en tiempo real
        pass

class RuleConfigDialog(QDialog):
    """Diálogo para configurar una regla personalizada"""
    
    def __init__(self, parent=None, category_manager: CategoryManager = None):
        super().__init__(parent)
        self.category_manager = category_manager
        self.init_ui()
    
    def init_ui(self):
        """Inicializa la interfaz"""
        self.setWindowTitle("📝 Configurar Regla")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout()
        
        # Campo de nombre
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Nombre:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Archivos PDF grandes")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Campo de patrón
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("Patrón (Regex):"))
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("Ej: regex:.*\\.pdf.* tamaño:.*100M")
        self.pattern_input.setPlaceholderText("Ej: Archivos PDF grandes")
        pattern_layout.addWidget(self.pattern_input)
        layout.addLayout(pattern_layout)
        
        # Categoría
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Categoría:"))
        self.category_combo = QComboBox()
        # Llenar con categorías disponibles
        layout.addLayout(category_layout)
        
        # Prioridad
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(QLabel("Prioridad:"))
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(0, 100)
        self.priority_spin.setValue(50)
        priority_layout.addWidget(self.priority_spin)
        layout.addLayout(priority_layout)
        
        # Preview de archivos afectados
        preview_btn = QPushButton("🔍 Preview de Archivos Afectados")
        preview_btn.clicked.connect(self.preview_affected_files)
        layout.addWidget(preview_btn)
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(QPushButton("Cancelar"))
        btn_layout.addWidget(QPushButton("Guardar"))
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
    def get_rule_data(self):
        """Devuelve los datos de la regla configurada"""
        return {
            "name": self.name_input.text(),
            "pattern": self.pattern_input.text(),
            "category": self.category_combo.currentText(),
            "priority": self.priority_spin.value()
        }
    
    def preview_affected_files(self):
        """Muestra preview de archivos que coincidirían con esta regla"""
        # Implementar búsqueda de archivos coincidentes
        pass
```

---

#### 1.2. Mejorar la Lógica de Categorización

```python
# Mejora en category_manager.py

def categorize_file(self, file_path: Path, options: CategorizeOptions = None) -> str:
    """
    Categoriza un archivo con múltiples criterios y opciones de control
    
    Args:
        file_path: Ruta del archivo a categorizar
        options: Opciones de categorización (por defecto: usar prioridad de prioridad
    """
    options = options or CategorizeOptions()
    
    # 1. Reglas de RuleEngine (más específicas)
    rule_category = self.rule_engine.categorize_file(file_path)
    if rule_category:
        self.log(f"⚡ Categorización RuleEngine: {file_path.name} → {rule_category}")
        return rule_category
    
    # 2. Reglas personalizadas ordenadas por prioridad
    for rule in sorted(self.custom_rules, key=lambda r: r.priority, reverse=True):
        if rule.matches(file_path):
            self.log(f"📋 Regla personalizada: {file_path.name} → {rule.category}")
            return rule.category
    
    # 3. Categorización por extensión (método principal)
    extension = file_path.suffix.lower()
    category = self.ext_to_categoria.get(extension, "VARIOS")
    
    # 4. Categorización por tipo de archivo (si está habilitado)
    if options.auto_detect_type and extension not in self.ext_to_categoria:
        file_type = self.detect_file_type(file_path)
        if file_type:
            # Crear categorías basadas en tipos detectados
            type_to_category = {
                "audio": "MUSICA",
                "video": "VIDEOS",
                "image": "IMAGENES",
                "pdf": "DOCUMENTOS",
                "archive": "PROGRAMAS",
                "code": "CODIGO",
            }
            if file_type in type_to_category:
                return type_to_category[file_type]
    
    # 5. Categorización por nombre del archivo
    if options.use_name_patterns:
        name_category = self.categorize_by_name(file_path.name)
        if name_category and options.name_priority > 0:
            return name_category
    
    # 6. Categorización por tamaño
    if options.use_size_patterns:
        if file_path.stat().st_size > 100_000_000:  # > 100MB
            return "ARCHIVOS GRANDES"
        elif file_path.stat().st_size > 10_000_000:  # > 10MB
            return "ARCHIVOS MEDIANOS"
    
    return category

class CategorizeOptions:
    """Opciones para la categorización"""
    def __init__(self):
        self.auto_detect_type = True  # Detectar tipo por header
        self.use_name_patterns = True  # Usar patrones por nombre
        self.use_size_patterns = True  # Usar tamaño como factor
        self.name_priority = 0  # Prioridad para nombre (0 = desactivado)
        self.log = False  # Habilitar logging de decisiones
```

---

#### 1.3. Sistema de Priorización Flexible

```python
class CategorizationPriority:
    """Sistema de pesos para priorizar métodos de categorización"""
    
    DEFAULT_WEIGHTS = {
        "rule_engine": 30,      # 30% - Reglas específicas
        "custom_rules": 20,     # 20% - Reglas personalizadas
        "extension": 25,        # 25% - Por extensión
        "type_detection": 15,   # 15% - Det