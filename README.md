# 📁 Organizador de Archivos y Carpetas

## 🚀 Descripción

Aplicación de escritorio desarrollada en Python con PyQt6 para organizar automáticamente archivos y carpetas según categorías predefinidas. Permite gestionar extensiones de archivos, crear categorías personalizadas y organizar contenido de forma selectiva.

## ✨ Características Principales

- **🔍 Análisis Automático**: Analiza carpetas para identificar contenido organizable
- **📊 Vista Previa**: Muestra todos los cambios antes de ejecutarlos
- **☑️ Selección Selectiva**: Checkboxes para elegir qué elementos organizar
- **📂 Expansión de Grupos**: Doble clic para expandir/contraer grupos de archivos
- **⚙️ Configuración Personalizable**: Gestión de categorías y extensiones
- **🎨 Interfaz Moderna**: Diseño limpio y responsive con colores distintivos
- **📝 Registro de Actividades**: Log detallado de todas las operaciones
- **🔄 Procesamiento en Segundo Plano**: No bloquea la interfaz durante operaciones

## 🏗️ Estructura del Proyecto

```
📁 Organizador de Archivos/
├── 📄 main.py                    # Punto de entrada principal
├── 📁 src/                       # Código fuente
│   ├── 📁 gui/                   # Interfaz de usuario
│   │   ├── 📄 main_window.py     # Ventana principal
│   │   └── 📄 config_dialog.py   # Diálogo de configuración
│   ├── 📁 core/                  # Lógica de negocio
│   │   ├── 📄 category_manager.py # Gestor de categorías
│   │   └── 📄 workers.py         # Workers para operaciones
│   └── 📁 utils/                 # Utilidades y constantes
│       └── 📄 constants.py       # Configuraciones y estilos
└── 📄 README.md                  # Este archivo
```

## 🎯 Funcionalidades Detalladas

### 📂 Organización Inteligente
- **Categorización Automática**: Clasifica archivos por extensión
- **Gestión de Carpetas**: Analiza contenido de subcarpetas
- **Prevención de Conflictos**: Maneja nombres duplicados automáticamente

### 🎨 Interfaz Visual
- **Colores Distintivos**: 
  - Grupos normales: Fondo gris sutil (`#f5f5f5`)
  - Grupos expandidos: Fondo azul (`#bbdefb`)
  - Archivos individuales: Fondo gris oscuro (`#e8e8e8`)
- **Iconos Semánticos**: 📁 carpetas, 📄 archivos, 📂 expandido
- **Estilos CSS**: Aplicación consistente de colores y estilos

### ⚙️ Configuración Avanzada
- **Categorías del Sistema**: MUSICA, VIDEOS, IMAGENES, DOCUMENTOS, PROGRAMAS, CODIGO
- **Categorías Personalizadas**: Crear y gestionar nuevas categorías
- **Gestión de Extensiones**: Añadir/eliminar extensiones por categoría
- **Persistencia**: Guardado automático de configuraciones personalizadas

## 🚀 Instalación y Uso

### 📋 Requisitos
```bash
pip install PyQt6
```

### 🏃‍♂️ Ejecución
```bash
python main.py
```

### 📖 Uso Básico
1. **Seleccionar Carpeta**: Usar botón "📂 Examinar" o escribir ruta
2. **Analizar Contenido**: Hacer clic en "🔍 Analizar" (se ejecuta automáticamente)
3. **Revisar Cambios**: Ver vista previa en la tabla
4. **Seleccionar Elementos**: Usar checkboxes para elegir qué organizar
5. **Expandir Grupos**: Doble clic en filas de "archivos sueltos"
6. **Organizar**: Hacer clic en "📁 Organizar Archivos"

## 🔧 Configuración

### ⚙️ Abrir Configuración
- Hacer clic en "⚙️ Configuración" en la barra superior
- Gestionar categorías y extensiones
- Exportar configuración a archivo de texto
- Restaurar valores por defecto

### 📁 Categorías por Defecto
- **MUSICA**: .mp3, .flac, .wav, .m4a, .aac, .ogg, .wma
- **VIDEOS**: .mp4, .mkv, .avi, .mov, .wmv, .flv, .webm, .m4v
- **IMAGENES**: .jpg, .jpeg, .png, .gif, .bmp, .tiff, .webp, .svg
- **DOCUMENTOS**: .pdf, .doc, .docx, .txt, .rtf, .odt, .xls, .xlsx, .ppt, .pptx
- **PROGRAMAS**: .exe, .msi, .deb, .rpm, .dmg, .pkg, .zip, .rar, .7z
- **CODIGO**: .py, .js, .html, .css, .cpp, .c, .java, .php, .rb, .go

## 🎨 Personalización

### 🌈 Colores de la Interfaz
```python
COLORS = {
    "GROUP_NORMAL": "#f5f5f5",      # Grupos normales
    "GROUP_EXPANDED": "#bbdefb",    # Grupos expandidos
    "FILE_EXPANDED": "#e8e8e8",     # Archivos individuales
    "HEADER_BG": "#f0f0f0",         # Headers de tabla
    "GRID_LINE": "#d0d0d0",         # Líneas de grid
    "SELECTION": "#0078d4",         # Color de selección
}
```

### 📱 Configuración de UI
```python
UI_CONFIG = {
    "WINDOW_TITLE": "📁 Organizador de Archivos y Carpetas",
    "WINDOW_WIDTH": 1200,
    "WINDOW_HEIGHT": 800,
    "TABLE_ROW_HEIGHT": 25,
    "BUTTON_HEIGHT": 40,
    "INPUT_HEIGHT": 30,
}
```

## 🔍 Características Técnicas

### 🧵 Procesamiento en Segundo Plano
- **AnalysisWorker**: Analiza carpetas sin bloquear UI
- **OrganizeWorker**: Organiza archivos con progreso en tiempo real
- **Señales Qt**: Comunicación asíncrona entre workers y UI

### 💾 Gestión de Datos
- **CategoryManager**: Lógica central de categorías y extensiones
- **Índice Inverso**: Mapeo eficiente de extensiones a categorías
- **Persistencia JSON**: Guardado automático de configuraciones

### 🎯 Arquitectura Modular
- **Separación de Responsabilidades**: UI, lógica de negocio y utilidades separadas
- **Inyección de Dependencias**: Gestor de categorías inyectado en componentes
- **Patrón Observer**: Workers notifican cambios a la UI

## 🐛 Solución de Problemas

### ❌ Errores Comunes
1. **"No se puede acceder a la carpeta"**: Verificar permisos de escritura
2. **"Categoría no encontrada"**: Revisar configuración de extensiones
3. **"Archivo ya existe"**: La aplicación maneja duplicados automáticamente

### 🔧 Debugging
- Revisar pestaña "📝 Registro" para mensajes de error
- Verificar permisos de la carpeta de destino
- Comprobar que las extensiones estén correctamente configuradas

## 📈 Futuras Mejoras

- [ ] **Filtros Avanzados**: Por fecha, tamaño o tipo de archivo
- [ ] **Reglas Personalizadas**: Condiciones complejas para categorización
- [ ] **Backup Automático**: Respaldo antes de organizar
- [ ] **Estadísticas Visuales**: Gráficos de distribución de archivos
- [ ] **Plugins**: Sistema de extensiones para categorías personalizadas
- [ ] **Multiidioma**: Soporte para diferentes idiomas

## 🤝 Contribuciones

1. Fork del proyecto
2. Crear rama para nueva funcionalidad
3. Commit de cambios
4. Push a la rama
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo LICENSE para más detalles.

## 👨‍💻 Autor

Desarrollado con ❤️ para facilitar la organización de archivos digitales.

---

**💡 Consejo**: Haz doble clic en las filas de "archivos sueltos" para expandir y ver archivos individuales antes de organizar.
