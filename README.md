# 📁 Organizador de Archivos y Carpetas — Documentación Completa

> **Versión:** v3.0.2 | **Framework:** PyQt6 | **Python:** 3.10+  
> **Última actualización:** 2026-04-06

---

## 📋 Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Características Principales](#características-principales)
3. [Estructura Completa del Proyecto](#estructura-completa-del-proyecto)
4. [Archivos Críticos — Qué Tocar y Dónde](#archivos-críticos--qué-tocar-y-dónde)
5. [Sistema de Temas](#sistema-de-temas)
6. [Flujo de Datos](#flujo-de-datos)
7. [Cambio de Interfaz (v3.0.2)](#cambio-de-interfaz-v302)
8. [Atajos de Teclado](#atajos-de-teclado)
9. [Compilación a EXE](#compilación-a-exe)
10. [Solución de Problemas](#solución-de-problemas)
11. [Guía para Agentes IA](#guía-para-agentes-ia)

---

## Descripción General

Aplicación de escritorio en Python/PyQt6 que **analiza carpetas**, identifica archivos organizables por categoría (música, vídeos, imágenes, documentos, etc.), muestra una **vista previa con checkboxes** para selección selectiva, y ejecuta la organización moviendo archivos/carpetas a destinos categorizados.

**Funcionalidades clave:**
- Análisis inteligente de carpetas con categorización por extensión
- Vista previa antes de ejecutar (tabla virtualizada con checkboxes)
- Detección de archivos duplicados
- Visor de discos con datos SMART reales (temperatura, horas, TBW)
- 12 temas de color profesionales con cambio en tiempo real
- Tamaños de fuente configurables (10px–16px)
- Drag & Drop de carpetas
- Filtros de búsqueda y por categoría
- Procesamiento en segundo plano (QThread workers)
- Log de operaciones con exportación a TXT
- Configuración persistente en JSON

---

## Características Principales

| Función | Descripción |
|---------|-------------|
| 🔍 **Análisis** | Escanea carpetas, clasifica por extensión, calcula similitud |
| ☑️ **Selección selectiva** | Checkboxes para elegir qué organizar |
| 📂 **Expansión de grupos** | Doble clic en "archivos sueltos" para ver individuales |
| 🔍 **Duplicados** | Dashboard de archivos duplicados con hash SHA-256 |
| 💾 **Discos SMART** | Visor de discos con datos reales de salud (smartctl) |
| 🎨 **12 Temas** | Claro, Oscuro, Corporativo, Naturaleza, Morado, etc. |
| 📝 **Log dedicado** | Pestaña completa con limpiar, exportar, scroll |
| 🖱️ **Drag & Drop** | Arrastra carpetas directamente a la app |
| ⌨️ **Atajos** | Ctrl+O, Ctrl+R, Ctrl+S, Ctrl+F, Ctrl+1-4, etc. |
| 💾 **Persistencia** | Configuración en `app_config.json` |

---

## Estructura Completa del Proyecto

```
Ordenasion_alpha-3.0.2_Exe/
├── main.py                          # Entry point básico (legacy)
├── main_optimized.py                # Entry point principal (splash + optimizaciones)
├── app_config.json                  # Preferencias usuario (tema, fuente)
├── categories_config.json           # Categorías y extensiones personalizadas
├── hash_cache.db                    # Caché de hashes SHA-256 (SQLite)
├── startup_log.txt                  # Log de arranque (debug)
├── requirements.txt                 # Dependencias Python
├── README.md                        # Este archivo
├── CHANGELOG_v3.0.2.md              # Historial de cambios
├── PLAN_MEJORAS_diff.md             # Plan de mejoras implementadas
├── GUIA_COMPILACION_EXE.md          # Guía para compilar a .exe
├── INSTRUCCIONES_SMARTCTL.md        # Docs de smartctl para discos
│
├── bin/
│   └── smartctl.exe                 # Binario SMART para datos de discos
│
├── src/
│   ├── __init__.py
│   │
│   ├── core/                        # LÓGICA DE NEGOCIO
│   │   ├── __init__.py
│   │   ├── application_state.py     # Singleton global (AppState)
│   │   ├── category_manager.py      # Categorías + extensiones + persistencia
│   │   ├── disk_manager.py          # Gestión de discos + smartctl
│   │   ├── duplicate_finder.py      # Detección de duplicados (hash)
│   │   ├── hash_cache.py            # Caché SQLite de hashes
│   │   ├── hash_manager.py          # Gestión de hashes
│   │   ├── health_service.py        # Evaluación de salud de discos
│   │   ├── memory_manager.py        # Gestión de memoria
│   │   ├── organization_profiles.py # Perfiles de organización
│   │   ├── rule_engine.py           # Motor de reglas
│   │   ├── transaction_manager.py   # Transacciones (rollback)
│   │   ├── worker_manager.py        # Gestor de workers
│   │   └── workers.py               # AnalysisWorker, OrganizeWorker (QThread)
│   │
│   ├── gui/                         # INTERFAZ DE USUARIO
│   │   ├── __init__.py
│   │   ├── main_window.py           # ⭐ VENTANA PRINCIPAL (2000+ líneas)
│   │   ├── config_dialog.py         # Diálogo de configuración (temas, categorías)
│   │   ├── disk_viewer.py           # Visor de discos SMART (2400+ líneas)
│   │   ├── duplicates_dashboard.py  # Dashboard de duplicados
│   │   ├── filter_bar.py            # Barra de búsqueda y filtro
│   │   ├── modern_components.py     # Componentes UI reutilizables
│   │   ├── notification_manager.py  # Sistema de notificaciones
│   │   ├── preview_dialog.py        # Diálogo de preview
│   │   ├── splash_screen.py         # Pantalla de carga
│   │   ├── drop_zone.py             # Zona de Drag & Drop
│   │   └── table_models.py          # Modelos Qt (VirtualizedMovementsModel)
│   │
│   └── utils/                       # UTILIDADES
│       ├── __init__.py
│       ├── app_config.py            # Clase AppConfig (lectura/escritura JSON)
│       ├── constants.py             # COLORS, UI_CONFIG, DIALOG_STYLES (legacy)
│       ├── themes.py                # ⭐ ThemeManager (12 temas definidos)
│       ├── modern_styles.py         # ⭐ get_modern_css_styles() (generador CSS)
│       ├── theme_applier.py         # ThemeApplier (sistema legacy, 590 líneas)
│       ├── fast_theme_applier.py    # ⭐ FastThemeApplier (sistema actual, 129 líneas)
│       ├── theme_cache.py           # ThemeCache (caché LRU de CSS/paletas)
│       ├── logger.py                # Sistema de logging
│       └── smartctl_wrapper.py      # Wrapper para smartctl.exe
│
└── tests/
    ├── test_smart_parsing.py
    └── fixtures/
        ├── hdd_smart.json
        ├── nvme_smart.json
        └── sata_smart.json
```

---

## Archivos Críticos — Qué Tocar y Dónde

### 🔴 ARCHIVOS CRÍTICOS (no modificar sin testing completo)

| Archivo | Líneas | Qué hace | Cuándo tocar |
|---------|--------|----------|--------------|
| `src/gui/main_window.py` | ~2000 | **VENTANA PRINCIPAL** — toda la UI, lógica de análisis, organización, tabs, log | Para cambiar layout, agregar funcionalidades UI, modificar flujo de organización |
| `src/utils/themes.py` | ~578 | **12 TEMAS** — definición de colores, paletas Qt, CSS | Para agregar/modificar temas o colores |
| `src/utils/modern_styles.py` | ~124 | **GENERADOR CSS** — convierte dict de colores a CSS Qt | Para cambiar estilos CSS globales |
| `src/core/workers.py` | ~400 | **WORKERS** — AnalysisWorker, OrganizeWorker (QThread) | Para modificar lógica de análisis u organización |
| `src/core/category_manager.py` | ~300 | **CATEGORÍAS** — gestión de categorías y extensiones | Para cambiar categorías por defecto o lógica de clasificación |

### 🟡 ARCHIVOS IMPORTANTES

| Archivo | Qué hace | Cuándo tocar |
|---------|----------|--------------|
| `src/gui/config_dialog.py` | Diálogo de configuración (temas, categorías, extensiones) | Para cambiar UI de configuración |
| `src/gui/disk_viewer.py` | Visor de discos con SMART | Para modificar visualización de discos |
| `src/gui/duplicates_dashboard.py` | Dashboard de duplicados | Para cambiar UI de duplicados |
| `src/utils/fast_theme_applier.py` | Aplicador rápido de temas | Para optimizar aplicación de temas |
| `src/utils/theme_cache.py` | Caché de temas | Para modificar comportamiento de caché |
| `src/utils/app_config.py` | Persistencia de configuración | Para agregar nuevas opciones de config |
| `main_optimized.py` | Entry point con splash screen | Para cambiar inicio de la app |

### 🟢 ARCHIVOS SECUNDARIOS

| Archivo | Qué hace |
|---------|----------|
| `src/gui/filter_bar.py` | Barra de búsqueda/filtro |
| `src/gui/drop_zone.py` | Zona de Drag & Drop |
| `src/gui/table_models.py` | Modelo virtualizado de tabla |
| `src/gui/modern_components.py` | Componentes UI reutilizables |
| `src/gui/splash_screen.py` | Pantalla de carga |
| `src/core/disk_manager.py` | Gestión de discos |
| `src/core/duplicate_finder.py` | Lógica de detección de duplicados |
| `src/core/hash_cache.py` | Caché SQLite de hashes |
| `src/utils/constants.py` | Constantes legacy (COLORS, UI_CONFIG) |

---

## Sistema de Temas

### Cómo funciona

1. **Definición:** `src/utils/themes.py` → `ThemeManager.THEMES` (dict con 12 temas)
2. **Generación CSS:** `src/utils/modern_styles.py` → `get_modern_css_styles(colors, font_size)`
3. **Aplicación:** `src/utils/fast_theme_applier.py` → `FastThemeApplier.apply_theme_fast()`
4. **Caché:** `src/utils/theme_cache.py` → cachea CSS, paletas y colores

### Cada tema tiene estas claves de color

```python
{
    "primary": "#...",          # Color principal
    "secondary": "#...",        # Color secundario
    "accent": "#...",           # Color de acento
    "background": "#...",       # Fondo de ventana
    "surface": "#...",          # Superficie (cards, inputs)
    "surface_variant": "#...",  # Superficie alternativa
    "text_primary": "#...",     # Texto principal
    "text_secondary": "#...",   # Texto secundario
    "text_disabled": "#...",    # Texto deshabilitado
    "border": "#...",           # Bordes
    "border_focus": "#...",     # Borde en foco
    "success": "#...",          # Color de éxito
    "warning": "#...",          # Color de advertencia
    "error": "#...",            # Color de error
    "info": "#...",             # Color de información
    "button_primary": "#...",   # Botón principal
    "button_hover": "#...",     # Hover de botón
    "button_pressed": "#...",   # Pressed de botón
    "primary_hover": "#...",    # Hover primario (alias de button_hover)
    "table_header": "#...",     # Header de tabla
    "table_row_even": "#...",   # Fila par
    "table_row_odd": "#...",    # Fila impar
    "table_selected": "#...",   # Fila seleccionada
    "shadow_light": "...",      # Sombra ligera
    "shadow_medium": "...",     # Sombra media
    "shadow_strong": "..."      # Sombra fuerte
}
```

### Los 12 temas disponibles

| # | Tema | Estilo |
|---|------|--------|
| 1 | 🌞 Claro Elegante | Light, azul Material Design |
| 2 | 🌙 Oscuro Profesional | Dark, azul Material Dark |
| 3 | 💼 Corporativo Azul | Light, azul corporativo |
| 4 | 🌿 Naturaleza Profesional | Light, verde naturaleza |
| 5 | 🟣 Morado Innovador | Light, morado tech |
| 6 | 🟠 Energía Profesional | Light, naranja dinámico |
| 7 | ⚫ Lujo Minimalista | Light, gris elegante |
| 8 | 🌊 Océano Tranquilo | Light, azul oceánico |
| 9 | 🌸 Pastel Sofisticado | Light, rosa pastel |
| 10 | 🎯 Ultra Moderno | Light, índigo eléctrico |
| 11 | 🎨 Diseño Creativo | Light, morado creativo |
| 12 | ⛅ Modo Productivo | Light, verde productivo |

### Para agregar un nuevo tema

1. Abrir `src/utils/themes.py`
2. Agregar entrada en `THEMES` con todas las claves de color
3. **IMPORTANTE:** Incluir `"primary_hover"` con el mismo valor que `"button_hover"`
4. El tema aparecerá automáticamente en el combo de ConfigDialog

---

## Flujo de Datos

```
main_optimized.py
    ↓
QApplication creada
    ↓
SplashScreen mostrada
    ↓
ThemeCache.preload_theme() → precarga CSS en caché
    ↓
FileOrganizerGUI (main_window.py) instanciada
    ↓
init_ui() → construye toda la interfaz
    ↓
apply_saved_interface_settings() → aplica tema/fuente guardados
    ↓
[Usuario selecciona carpeta]
    ↓
start_analysis() → crea AnalysisWorker (QThread)
    ↓
worker analiza → emite señales progress_update, analysis_complete
    ↓
on_analysis_complete() → pobla tabla virtualizada
    ↓
[Usuario selecciona elementos con checkboxes]
    ↓
start_organization() → crea OrganizeWorker (QThread)
    ↓
worker mueve archivos → emite señales progress_update, organize_complete
    ↓
on_organize_complete() → restaura UI, muestra resultado
```

---

## Cambio de Interfaz (v3.0.2)

### Antes vs Después

**ANTES:** Log como QGroupBox colapsable en el layout principal, botones desorganizados, colores hardcodeados.

**DESPUÉS:**
- **4 pestañas:** 📁 Organizar | 💾 Discos | 🔍 Duplicados | 📝 Log
- **Log movido** a pestaña dedicada con botones Limpiar, Exportar, Ir al Final
- **GroupBox organizados:** Carpeta de Origen → Opciones de Análisis → Filtros → Tabla → Resumen
- **Botones proporcionales:** todos 36px height, sin colores hardcodeados
- **Stats compactas** en una sola línea dentro del GroupBox de Resumen

### Estructura de la pestaña ORGANIZAR (actual)

```
┌─ Header ─────────────────────────────────────────┐
│  Organizador de Archivos    [⚙️ Config]       │
├─ 📂 Carpeta de Origen ───────────────────────────┤
│ [Input ruta................] [📂 Examinar]       │
├─ ⚙️ Opciones de Análisis ────────────────────────┤
│ ☑ Mover carpetas  🎯 Similitud: [70%]           │
│ ☑ Buscar duplicados  ☐ Organizar por fecha      │
│                                  [🔍 Analizar]   │
├─ 🔍 Filtros ─────────────────────────────────────┤
│ [🔍 Buscar...] [Categorías ▼] [✖ Limpiar]       │
├─ Tabla de resultados ────────────────────────────┤
│  | Elemento | Destino | % | Archivos | Tamaño  │
│ ...                                              │
├─ 📊 Resumen de Selección ────────────────────────┤
│ ☑️ Todo  ❌ Nada │ 📊 0/0  💾 0B  📄 0          │
│                          [📁 Organizar Archivos] │
└─ [████████░░░░] 75%  ⏱️ ETA: 2m 30s ────────────┘
```

---

## Atajos de Teclado

| Atajo | Acción |
|-------|--------|
| `Ctrl+O` | Abrir carpeta |
| `Ctrl+R` / `F5` | Analizar/Refrescar |
| `Ctrl+S` | Organizar archivos |
| `Ctrl+F` | Ir a pestaña Duplicados |
| `Ctrl+A` | Seleccionar todo |
| `Ctrl+D` | Deseleccionar todo |
| `Ctrl+L` | Limpiar log |
| `Ctrl+P` / `Ctrl+,` | Abrir configuración |
| `Ctrl+1` | Ir a Organizar |
| `Ctrl+2` | Ir a Discos |
| `Ctrl+3` | Ir a Duplicados |
| `Ctrl+4` | Ir a Log |
| `Ctrl+Q` | Salir |

---

## Compilación a EXE

Ver `GUIA_COMPILACION_EXE.md` para instrucciones detalladas.

**Resumen rápido:**
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name="Organizador" --icon=icon.ico main_optimized.py
```

**Archivos a incluir en el bundle:**
- `bin/smartctl.exe`
- `categories_config.json` (si existe)
- Toda la carpeta `src/`

---

## Solución de Problemas

### Errores comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `KeyError: 'primary_hover'` | Tema sin clave primary_hover | Agregar `primary_hover` al tema en `themes.py` |
| Disco no detectado | smartctl no tiene permisos | Ejecutar como administrador |
| Tabla vacía tras análisis | Categoría no coincide | Revisar `categories_config.json` |
| Tema no se aplica | Caché stale | Borrar `hash_cache.db` y reiniciar |
| Log no muestra mensajes | `log_text` no inicializado | Verificar que `init_ui()` se ejecutó |

### Debugging

1. Revisar `startup_log.txt` para errores de inicio
2. Pestaña 📝 Log para errores en runtime
3. Agregar `self.log_message("debug info")` en cualquier método
4. Verificar `app_config.json` para configuración actual

---

## Guía para Agentes IA

### Si necesitas modificar la UI

1. **Layout principal:** `src/gui/main_window.py` → método `init_ui()` (línea ~125)
2. **Estilos de un widget:** Buscar `setStyleSheet()` en el archivo correspondiente
3. **Agregar un botón:** Crear QPushButton, setFixedHeight(36), conectar signal
4. **Agregar una pestaña:** Crear QWidget, agregar con `self.main_tabs.addTab(widget, "🏷️ Nombre")`
5. **Colores:** NO usar colores hardcodeados. Usar `ThemeManager.get_theme_colors()` o CSS del tema

### Si necesitas modificar los temas

1. **Agregar tema:** `src/utils/themes.py` → agregar entrada en `THEMES`
2. **Cambiar color:** Modificar el valor hex en el tema correspondiente
3. **Cambiar CSS global:** `src/utils/modern_styles.py` → función `get_modern_css_styles()`
4. **Agregar clave de color:** Agregar en TODOS los temas + fallback en `modern_styles.py`

### Si necesitas modificar la lógica de organización

1. **Análisis:** `src/core/workers.py` → clase `AnalysisWorker` → método `run()`
2. **Organización:** `src/core/workers.py` → clase `OrganizeWorker` → método `run()`
3. **Categorías:** `src/core/category_manager.py` → método `categorize_file()`
4. **Reglas:** `src/core/rule_engine.py` → motor de reglas personalizadas

### Si necesitas modificar los discos

1. **Visor:** `src/gui/disk_viewer.py` → clase `DiskViewer`
2. **Datos SMART:** `src/core/disk_manager.py` → método `get_disk_info()`
3. **Parsing SMART:** `src/utils/smartctl_wrapper.py` → métodos de parseo
4. **Salud:** `src/core/health_service.py` → evaluación de salud

### Reglas importantes

1. **NO** usar `print()` — usar `self.log_message()` o el logger
2. **NO** hardcodear colores — usar el sistema de temas
3. **NO** bloquear el hilo principal — usar QThread workers
4. **SIEMPRE** probar en al menos 2 temas (claro + oscuro)
5. **SIEMPRE** mantener compatibilidad con `app_config.json`
6. **SIEMPRE** agregar `try/except` en operaciones de I/O

### Patrones comunes

```python
# Obtener colores del tema actual
from src.utils.themes import ThemeManager
from src.utils.app_config import AppConfig
app_config = AppConfig()
colors = ThemeManager.get_theme_colors(app_config.get_theme())

# Aplicar tema a un widget
from src.utils.fast_theme_applier import FastThemeApplier
FastThemeApplier.apply_theme_to_widget_only(widget, theme_name, font_size)

# Crear un worker
from src.core.workers import AnalysisWorker
worker = AnalysisWorker(folder_path, categories, ext_to_cat, similarity)
worker.progress_update.connect(self.log_message)
worker.analysis_complete.connect(self.on_analysis_complete)
worker.start()

# Log de mensaje
self.log_message("✅ Operación completada")
```

---

**Última actualización:** 2026-04-06  
**Mantenedor:** Senior Python Developer  
**Licencia:** MIT
