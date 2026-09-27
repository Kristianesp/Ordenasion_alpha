# Ordenasion Alpha

Aplicación de escritorio para Windows desarrollada en Python y PyQt6. Permite analizar, clasificar, organizar y revisar archivos desde una interfaz visual, con foco en seguridad operativa, vista previa antes de mover datos y herramientas adicionales para discos, duplicados y biblioteca musical.

Versión: **3.5.0**

## Novedades de 3.5.0

1. Inicio compacto con métricas reales, donut de ocupación y distribución del
   último análisis de espacio; sin series ni cifras de demostración.
2. Interfaz Fluent Ocean Frost, tema global animado y configuración compacta con
   selector de color, validación y guardado fiable.
3. Organización guiada con revisión y confirmación única, conflictos explícitos,
   selección conservada y Deshacer según el estado real.
4. Discos con estados de salud honestos y nuevo Uso del espacio: análisis manual,
   mapa/tabla, navegación, top20 y cancelación cooperativa.
5. Música centrada en biblioteca/reproducción, herramientas avanzadas bajo
   demanda y ventanas de metadatos/portadas con tema coherente.
6. Duplicados con candidatos, copia conservada y destino de retirada explícitos;
   Actividad prioriza progreso y resultados sobre el log técnico.
7. Splash e icono propios, fuentes incluidas y lanzador BAT con `--comprobar`.
8. EXE Windows Fluent 3.5.0 con assets/licencias y smoke aislado; no lleva la
   configuración ni los perfiles personales del workspace.

Consulta [CHANGELOG.md](CHANGELOG.md) para el detalle y
[la guía de compilación](releases_tags_creacion_exes.md) para generar el EXE.

## Funcionalidades Principales

- Organización automática de archivos y carpetas por categorías configurables.
- Vista previa antes de ejecutar movimientos, con resolución explícita de conflictos.
- Opción de mantener archivos duplicados renombrando el nuevo, sobrescribir archivos existentes u omitir conflictos.
- Selección granular de elementos mediante checkboxes y grupos expandibles.
- Refresco automático de la tabla tras finalizar una organización.
- Rollback de operaciones recientes mediante registro transaccional.
- Modo avanzado con perfiles, exclusiones, tamaño mínimo, similitud y búsqueda de duplicados.
- Pestaña de discos con información de unidades, uso, estado SMART y análisis del sistema.
- Pestaña de música para indexar biblioteca, revisar duplicados, reproducir audio y editar metadatos.
- Pestaña de duplicados generales con modos rápido, híbrido y profundo.
- Configuración persistente en JSON para categorías, preferencias, interfaz, audio y rutas recientes.
- Interfaz con temas, pestañas principales y procesamiento en segundo plano para no bloquear la aplicación.

## Descarga

La versión compilada se publica como ejecutable de Windows en GitHub Releases:

[Release 3.5.0](https://github.com/Kristianesp/Ordenasion_alpha/releases/tag/v3.5.0)

Asset principal:

[Descargar Ordenasion_v3.5.0.exe](https://github.com/Kristianesp/Ordenasion_alpha/releases/download/v3.5.0/Ordenasion_v3.5.0.exe)

## Pestañas de la Aplicación

### Organizar

Es el flujo principal de trabajo. Permite seleccionar una carpeta, analizar su contenido y decidir qué elementos mover.

Incluye:

- análisis de carpetas y archivos sueltos,
- organización por categorías,
- organización opcional por fecha,
- umbral de similitud para carpetas mixtas,
- tamaño mínimo de archivo,
- selección total/parcial,
- expansión de grupos de archivos,
- preview final antes de mover,
- actualización automática tras organizar,
- botón de deshacer cuando hay una transacción reciente.

### Discos

Vista dedicada al estado de unidades y particiones del sistema.

Incluye:

- listado de discos/unidades,
- espacio total, usado y libre,
- porcentaje de uso,
- identificación de unidad del sistema,
- modo seguro de solo lectura,
- análisis de disco seleccionado,
- integración con `smartctl` cuando está disponible,
- información de salud, temperatura y métricas SMART.

### Música

Pestaña especializada para biblioteca musical y duplicados de audio.

Incluye:

- escaneo de carpetas de música con opción recursiva,
- indexación local de metadatos en SQLite (`media_index.db`),
- soporte de formatos comunes como MP3, FLAC, WAV, M4A, AAC, OGG, WMA, ALAC, AIFF,
- extracción de codec, duración, bitrate, sample rate, canales, bit depth y tags,
- detección de duplicados musicales por identidad técnica y metadatos,
- puntuación de calidad para sugerir la mejor copia,
- reproducción integrada con `QMediaPlayer`,
- panel de detalle con portada cuando está disponible,
- edición manual de metadatos,
- búsqueda de metadatos online si se configura y habilita,
- cache de resultados de lookup,
- filtros por estado: pendientes, variantes, aplicadas, completas, sin coincidencia, etc.,
- personalización de columnas y persistencia de la vista.

### Duplicados

Herramienta para buscar duplicados generales en carpetas o discos.

Modos disponibles:

- rápido: agrupa por tamaño, nombre normalizado y extensión,
- híbrido: usa filtro rápido y confirma sospechosos con hash,
- profundo: compara por hash; los archivos muy grandes pueden usar muestreo y
  siguen requiriendo revisión antes de retirarlos.

También incluye acciones sobre resultados, vista de grupos, apertura de ubicación y gestión segura según el flujo disponible en la interfaz.

### Actividad

Progreso y resultados de la sesión, con el registro técnico desplegable.

Permite:

- revisar mensajes de análisis, organización, errores y advertencias,
- limpiar el panel,
- exportar el log a TXT,
- saltar al final del registro.

## Organización de Archivos

La aplicación clasifica archivos por extensión, MIME básico y heurísticas de nombre. Las categorías por defecto incluyen:

- `MUSICA`
- `VIDEOS`
- `IMAGENES`
- `DOCUMENTOS`
- `PROGRAMAS`
- `CODIGO`
- `VARIOS`

Las categorías y extensiones se gestionan desde configuración y se guardan en `categories_config.json`.

## Vista Previa y Conflictos

Antes de organizar, la aplicación muestra una ventana de vista previa con:

- tipo de elemento,
- nombre,
- destino,
- ruta final,
- estado de conflicto.

Si existen conflictos en destino, el usuario puede elegir una política para esa ejecución:

- mantener ambos renombrando el nuevo archivo,
- sobrescribir archivo existente,
- omitir elementos en conflicto.

Para carpetas, el comportamiento seguro es renombrar para evitar sobrescritura recursiva accidental.

Los nombres alternativos usan el formato habitual de Windows:

`archivo (1).ext`, `archivo (2).ext`, etc.

## Seguridad Operativa

La aplicación evita mover archivos sin confirmación final. Las operaciones se ejecutan mediante `TransactionManager`, que registra movimientos, renombres, creación de carpetas y permite revertir la última organización cuando hay una transacción disponible.

El borrado seguro usa papelera mediante `send2trash` cuando está instalado. Si no está disponible, usa cuarentena local en lugar de eliminación directa.

## Configuración

Los valores iniciales de configuración, perfiles y categorías proceden del código.
Los archivos locales se crean al guardar y no se incluyen en Git ni en el EXE.
La configuración se guarda principalmente en:

- `app_config.json`
- `categories_config.json`
- `operations_log.json`
- `audio_duplicate_operations_log.json`
- `media_index.db`

Opciones destacadas:

- tema visual y tamaño de fuente,
- modo avanzado de interfaz,
- autoanálisis,
- rutas favoritas y recientes,
- extensiones y rutas ignoradas,
- rutas protegidas,
- política de conflictos por defecto,
- biblioteca musical,
- Discogs y AcoustID opcionales,
- columnas y estado visual de la tabla musical.

No se deben subir tokens reales ni claves personales dentro de `app_config.json`.

## Requisitos

Requisitos principales:

```bash
pip install -r requirements.txt
```

Dependencias principales:

- Python 3.10 o superior recomendado,
- PyQt6,
- psutil,
- WMI en Windows,
- send2trash,
- mutagen.

Dependencias opcionales comentadas en `requirements.txt` permiten ampliar detección de tipos, documentos, PDFs, Excel, compresión y gráficos.

## Ejecución Desde Código

En Windows puedes ejecutar `arrancar_ordenasion.bat`; `--comprobar` valida el
entrypoint y sus dependencias sin abrir la GUI ni escribir configuración.
Punto de entrada recomendado:

```bash
venv\Scripts\python.exe main_fluent.py
```

También puede existir compatibilidad con otros entrypoints históricos según la rama o versión del proyecto.

## Compilación del EXE

Usa Python 3.12 x64, instala `requirements.txt` y `requirements-build.txt` en el
venv y compila la spec incluida (entrada `main_fluent.py`, onefile):

```powershell
venv\Scripts\python.exe -m PyInstaller --clean --noconfirm --distpath artifacts/release-v3.5.0/dist --workpath artifacts/release-v3.5.0/build OrganizadorAlpha_OPTIMIZED.spec
```

Salida esperada:

```text
artifacts/release-v3.5.0/dist/Ordenasion_v3.5.0.exe
```

## Estructura del Proyecto

```text
.
├── main_fluent.py
├── OrganizadorAlpha_OPTIMIZED.spec
├── requirements.txt
├── README.md
├── src/
│   ├── core/
│   │   ├── workers.py
│   │   ├── category_manager.py
│   │   ├── duplicate_finder.py
│   │   ├── transaction_manager.py
│   │   ├── disk_manager.py
│   │   ├── health_service.py
│   │   ├── audio_index.py
│   │   ├── audio_duplicates.py
│   │   ├── audio_fingerprint.py
│   │   └── organization_conflicts.py
│   ├── gui/
│   │   ├── main_window.py
│   │   ├── preview_dialog.py
│   │   ├── config_dialog.py
│   │   ├── disk_viewer.py
│   │   ├── duplicates_dashboard.py
│   │   ├── music_duplicates_view.py
│   │   └── music_duplicates_*.py
│   └── utils/
│       ├── app_config.py
│       ├── themes.py
│       ├── theme_cache.py
│       ├── smartctl_wrapper.py
│       └── logger.py
└── tests/
    ├── test_organization_conflicts.py
    ├── test_preview_dialog_conflicts.py
    ├── test_main_window_refresh.py
    ├── test_audio_*.py
    └── test_music_duplicates_*.py
```

## Arquitectura

La aplicación separa responsabilidades en tres capas principales:

- `src/gui`: interfaz PyQt6, tablas, diálogos, pestañas y controles.
- `src/core`: análisis, organización, duplicados, audio, discos y transacciones.
- `src/utils`: configuración, temas, logging, constantes y wrappers del sistema.

Los procesos pesados se ejecutan mediante workers de Qt para mantener la interfaz activa. La comunicación con la UI se realiza mediante señales.

## Pruebas

Ejecutar la suite completa:

```bash
python -m pytest
```

Pruebas focalizadas útiles:

```bash
python -m pytest tests/test_organization_conflicts.py tests/test_preview_dialog_conflicts.py tests/test_main_window_refresh.py -q
python -m pytest tests/test_audio_config.py tests/test_audio_duplicates.py tests/test_audio_index.py -q
```

## Atajos

Atajos disponibles en la ventana principal:

- `Ctrl+F`: ir a duplicados,
- `Ctrl+A`: seleccionar todo,
- `Ctrl+P` o `Ctrl+,`: abrir configuración,
- `Ctrl+1` a `Ctrl+5`: cambiar entre pestañas principales,
- `Ctrl+Q`: salir.

## Solución de Problemas

### No se puede acceder a una carpeta

Revisar permisos de lectura/escritura y comprobar si la ruta está marcada como protegida o excluida.

### La vista previa muestra conflictos

Seleccionar una política de resolución antes de organizar: mantener ambos, sobrescribir u omitir.

### El análisis tarda demasiado

Reducir el alcance de la carpeta, activar tamaño mínimo, desactivar análisis recursivo en música o usar modo rápido en duplicados.

### No aparecen metadatos musicales

Comprobar que `mutagen` esté instalado y que los archivos contengan tags válidos. Para búsquedas online, habilitar la opción correspondiente y configurar las claves necesarias.

### SMART no muestra todos los datos

Algunas métricas dependen del dispositivo, del controlador y de que `smartctl` esté instalado y accesible.

## Estado del Proyecto

Ordenasion Alpha está orientado a uso local en Windows. La versión `v3.5.0` incorpora correcciones importantes en el flujo de vista previa, resolución de conflictos antes de organizar, refresco automático tras mover archivos y una pestaña musical avanzada.

## Licencia

Licencia pendiente de definir en un archivo dedicado del repositorio.
