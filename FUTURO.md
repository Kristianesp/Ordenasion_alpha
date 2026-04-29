# FUTURO_APP

## Estado real a dia de hoy

- La app ya tiene una pestaña musical integrada en `src/gui/main_window.py` con una vista propia `src/gui/music_duplicates_view.py`.
- La pestaña musical ya cubre dos bloques funcionales claros:
  - `Duplicados`: grupos musicales, comparacion por tabla, preview de detalle, reproducir, detener, abrir carpeta y enviar a papelera.
  - `Metadatos`: biblioteca indexada, faltantes, relleno basico, busqueda online, selector de variantes, edicion manual y revision manual por estado.
- La biblioteca musical ya no depende del flujo viejo de botones encadenados. El flujo principal es:
  1. indexar carpeta,
  2. buscar online,
  3. autoaplicar solo coincidencias muy fiables,
  4. abrir selector si hay variantes multiples,
  5. revisar, marcar como no coincide, elegir variante o dejarla aplicada.

## Lo que ya esta hecho de verdad

### Metadatos e indexado

- `src/core/audio_index.py` ya:
  - indexa audio en `media_index.db`,
  - extrae metadatos tecnicos y tags,
  - escribe tags reales con `mutagen`,
  - reindexa tras guardar para que la tabla refleje lo escrito,
  - mantiene un estado persistente de revision manual por pista en `audio_track_review_state`,
  - mantiene cache persistente de lookup online por pista en `audio_lookup_cache`,
  - guarda portada embebida por formato cuando se aplica una coincidencia o se guarda desde el editor.
- Ya hay fixtures reales pequeños para probar portada por formato en `tests/fixtures/audio/`.
- Ya hay pruebas reales de portada por formato en `tests/test_audio_index_real_fixtures.py`.
- `find_missing_metadata()` ya excluye pistas marcadas como `complete` y `no_match`.
- `find_missing_metadata()` ya excluye tambien pistas marcadas como `applied`, para poder procesar bibliotecas grandes por tandas.
- `remove_track()` y `rename_track_file()` ya sincronizan tambien el estado de revision.

### Lookup online

- `src/core/audio_fingerprint.py` ya usa este orden:
  1. `AcoustID` + `fpcalc` si hay client key valida y binario.
  2. `MusicBrainz` como fuente principal gratuita.
  3. `Discogs` como fallback opcional.
- El lookup ya combina candidatos, los deduplica, los ordena y deja diagnostico por fuente.
- Ya existe criterio de autoaplicacion conservador:
  - solo si hay un unico candidato,
  - y ademas la coincidencia es practicamente exacta o de confianza muy alta.
- Si la coincidencia unica no supera el umbral, ya no se autoaplica.
- El lookup ya usa cache persistente real:
  - conserva candidatos y sugerencias entre sesiones,
  - cachea portada descargada,
  - y recuerda variante elegida y variante aplicada cuando siguen coincidiendo con la pista.
- La UI ya muestra si el resultado viene de cache fresca o reutilizada, junto con fecha de ultima actualizacion.
- Discogs ya no usa `master_id` como album por defecto; ahora prioriza mejor release title, año y genero utiles.

### UX de la tab musical

- `Buscar online` ya no bloquea la UI: usa `AudioLookupWorker(QThread)`.
- `scan()` y `refresh_from_folder()` ya no bloquean la UI: usan `AudioLibraryWorker(QThread)`.
- La orquestacion del scan ya esta extraida en `src/gui/music_duplicates_scan_controller.py`, dejando `src/gui/music_duplicates_view.py` un poco mas cerca de coordinador.
- Mientras busca, la vista muestra progreso y deshabilita acciones conflictivas.
- La seleccion de filas se conserva al refrescar la biblioteca.
- La vista ya restaura `last_folder` y `recursive` al abrir.
- Si hay varias variantes, se abre el selector pista por pista.
- En la tabla de variantes:
  - se muestran `Fuente`, `Confianza`, `Titulo`, `Artista`, `Album`, `Año`, `MBID`,
  - hay panel de detalle,
  - doble clic acepta y guarda directamente.
- La biblioteca musical ya tiene menu contextual con:
  - `Marcar como datos completos` / quitar marca,
  - `Marcar como no coincide` / quitar marca,
  - `Limpiar titulos`,
  - `Editar metadatos`.
- La biblioteca ya distingue visualmente por fila:
  - `completa` en verde suave,
  - `aplicada` tambien en verde suave,
  - `no coincide` en rojo suave,
  - `variante elegida` en azul suave.
- Si hay varias variantes y la mejor supera el umbral conservador, ya se aplica automaticamente sin abrir el selector.
- La pestaña musical ya muestra un toast visual temporal para avisar de la auto-seleccion automatica.
- La biblioteca ya permite elegir portada alternativa si el lookup devuelve varias opciones.
- La portada elegida manualmente ya se conserva al refrescar el lookup si esa opcion sigue existiendo en `cover_choices`.
- La biblioteca ya permite abrir el payload/diagnostico completo del lookup desde la UI.
- La tabla principal ya refleja cuando una variante solo esta elegida en cache y cuando ya fue escrita al archivo.
- Los estados `complete` y `applied` quedan persistidos para siguientes iteraciones sobre bibliotecas grandes.
- El editor ya resalta campos cargados desde variante y la tabla principal mantiene ese estado al volver.
- El orden y tamaño de columnas de la tabla musical ya se guardan si el usuario los cambia.
- La tabla musical ya permite marcar pistas con checkbox para procesarlas visualmente por lotes.
- La tabla musical ya mantiene barra horizontal inferior y editor de columnas visibles/ocultas.
- Tambien queda guardado el tamaño del splitter entre la tabla y el panel derecho.
- La vista ya permite restaurar rapidamente el layout por defecto de la biblioteca.
- El panel de detalle de la derecha ya incluye reproductor sencillo de preescucha para la pista seleccionada.
- Ese panel ya permite tambien:
  - ver duracion total antes de dar play,
  - ajustar volumen,
  - ajustar `Pitch DJ` de la preescucha,
  - forzar refresh de cache online,
  - limpiar cache por pista.
- El panel de detalle ya muestra badge de cache y fecha de ultima actualizacion del lookup.
- `Limpiar titulos` ya limpia el tag `title` y tambien puede renombrar el archivo al nombre limpio manteniendo la extension.
- La portada elegida manualmente ya se intenta escribir tambien en los metadatos reales del archivo, ademas de conservarse en cache.
- El reproductor ya reengancha salida de audio, volumen, seek y `Pitch DJ` al reproducir para evitar estados mudos o controles bloqueados.
- Ya se quitaron de la UI los botones redundantes de:
  - `Cargar biblioteca`,
  - `Aplicar sugerencias`,
  - `Elegir variante`,
  - `Renombrar archivo`.

### Duplicados musicales

- `src/core/audio_duplicates.py` ya agrupa pistas por identidad local y estima calidad tecnica.
- La pestaña `Duplicados` ya muestra:
  - grupos,
  - tabla por grupo,
  - detalle de seleccion,
  - reproducir,
  - detener,
  - abrir carpeta,
  - enviar a papelera.
- La UX de duplicados ya incluye:
  - columna de decision (`⭐ Conservar` / `Revisar`),
  - boton `Ir a mejor`,
  - boton `Conservar`,
  - menu contextual en la tabla,
  - ahorro potencial visible si se elimina el resto del grupo.
- Ya hay pruebas GUI basicas de biblioteca y duplicados en `tests/test_music_duplicates_view_gui.py`.
- Esas pruebas GUI ya cubren tambien:
  - reset de layout,
  - seleccion de mejor copia,
  - auto-seleccion de variantes fuertes,
  - estados finos de biblioteca,
  - acciones de portada/diagnostico,
  - y persistencia de portada elegida tras refresh.
- El borrado ya usa `TransactionManager` y elimina la pista del indice local.

### Configuracion

- `src/utils/app_config.py` ya guarda:
  - `audio.acoustid_api_key`,
  - `audio.discogs_enabled`,
  - `audio.discogs_token`,
  - `audio.allow_online_metadata`,
  - `audio.library_roots`,
  - `audio.last_folder`,
  - `audio.recursive`,
  - `audio.library_column_widths`,
  - `audio.library_column_order`,
  - `audio.library_visible_columns`,
  - `audio.library_splitter_sizes`,
  - `audio.preview_playback_rate`,
  - `audio.duplicate_policy`,
  - `audio.organization_template`.
- `src/gui/config_dialog.py` ya expone las claves y flags musicales.
- La persistencia de configuracion ya recarga el JSON antes de cada `set()` para no perder claves cuando varias instancias de `AppConfig` escriben cambios distintos seguidos.

## Lo que ya no describe bien el FUTURO viejo

- Ya no es correcto decir que falta "escribir tags reales con mutagen": eso ya esta hecho.
- Ya no es correcto decir que la UI sigue basada en lista pobre o en aplicar sugerencias aparte: el flujo ya esta simplificado.
- Ya no es correcto listar `renombrado de archivo` como accion principal de la tab musical: se retiro del flujo UI.
- Ya no es correcto pensar la seleccion de variantes como un popup pobre: ahora es tabla con detalle y doble clic.

## Pendientes reales ahora mismo

### Criticos

- Extender los fixtures reales de portada con mas muestras y casos menos triviales.

### Importantes

- Mejorar el fallback de Discogs.
  - Todavia puede devolver albumes poco utiles o resultados demasiado genericos.
- Seguir troceando `src/gui/music_duplicates_view.py` en modulos pequeños.

### Muy recomendables

- Añadir invalidez inteligente de cache cuando cambian tags manuales en formas que ya no parecen compatibles con la coincidencia elegida.
- Añadir acciones mas visibles sobre la cache en el panel detalle.
- Añadir tooltips consistentes en toda la tab de musica; ahora mismo faltan muchos y eso hace que varios botones no se entiendan a primera vista.
- Revisar a fondo la persistencia del editor de columnas y del layout para asegurar que la configuracion elegida por el usuario siempre prevalezca sobre cualquier default al reabrir la app.

### Arquitectura / deuda tecnica

- `src/gui/music_duplicates_view.py` sigue siendo un archivo grande, aunque ya se extrajeron:
  - `src/gui/music_duplicates_constants.py`,
  - `src/gui/music_duplicates_formatters.py`,
  - `src/gui/music_duplicates_presenters.py`,
  - `src/gui/music_duplicates_duplicate_logic.py`,
  - `src/gui/music_duplicates_library_logic.py`,
  - `src/gui/music_duplicates_library_panel_logic.py`,
  - `src/gui/music_duplicates_lookup_logic.py`,
  - `src/gui/music_duplicates_lookup_controller.py`,
  - `src/gui/music_duplicates_scan_controller.py`,
  - `src/gui/music_duplicates_lookup_presenters.py`,
  - `src/gui/music_duplicates_lookup_dialogs.py`,
  - `src/gui/music_duplicates_library_actions.py`,
  - `src/gui/music_duplicates_metadata_editor.py`,
  - `src/gui/music_duplicates_variant_dialog.py`,
  - `src/gui/music_duplicates_workers.py`,
  - `src/gui/music_duplicates_ui.py`,
  - `src/gui/music_duplicates_table_builders.py`.
- Conviene separarlo en piezas:
  - coordinador final de acciones musicales.
- `src/gui/duplicates_dashboard.py` debe mantenerse independiente de la tab musical; si reaparece logica musical ahi, conviene eliminarla en vez de reutilizar componentes de `music_duplicates_view.py`.

## Analisis de la tab actual: que mejoraria yo ademas del plan

### Mejoras que si haria

- Seguir refinando el bloque de detalle de biblioteca para que diagnostico y sugerencia queden aun mas escaneables.
- Añadir filtro para ver solo:
  - incompletas,
  - con sugerencias,
  - completas,
  - con multiples variantes.

### Mejoras que no meteria aun

- Comparacion perceptual compleja de versiones/remixes/directos.
- Reorganizacion fisica avanzada de la biblioteca.

Primero cerraria rendimiento, claridad de estado y persistencia del flujo actual.

## ¿Con seguir este plan es suficiente?

- Para la siguiente iteracion practica: si.
- Para considerar la tab musical "seria" de verdad: aun no.

Con el estado actual, el plan correcto es:

1. consolidar pruebas y controles manuales sobre cache/portada,
2. refinar aun mas la legibilidad del estado por pista,
3. mejorar UX de duplicados musicales,
4. recortar deuda tecnica del archivo gigante de la vista.

## Siguiente roadmap recomendado

### Fase 1 inmediata

- Revisar la semantica exacta entre `aplicada` y cambios manuales posteriores.
- Afinar Discogs para casos ambiguos de recopilatorios y releases genéricas.
- Extender pruebas GUI a editor de metadatos, selector de variantes y cache visual mas profunda.

### Fase 2 de UX

- Añadir feedback mas explicito de cache usada vs lookup fresco.
- Añadir comparativa mas clara entre mejor copia y copias peores dentro del grupo.
- Añadir tooltips y microcopys explicativos en acciones de biblioteca, lookup, duplicados y reproductor.

### Fase 3 de valor alto

- Pruebas mas completas con casos reales.
- Refactor de `music_duplicates_view.py` en subcomponentes.
- Afinar calidad de resultados Discogs/MusicBrainz para casos ambiguos.

## Riesgos a no romper

- No volver a autoaplicar coincidencias medias o ambiguas.
- No renombrar archivos desde `Limpiar titulos` de forma agresiva o sorprendente; si se mantiene, debe seguir siendo conservador y coherente con el titulo limpio.
- No perder el estado `complete` al reindexar, renombrar o borrar.
- No perder la distincion entre `variante elegida` y `aplicada` al refrescar o reiniciar.
- No bloquear la UI en operaciones largas.
- No duplicar aun mas la logica musical entre `music_duplicates_view.py` y `duplicates_dashboard.py`.
- No romper el layout personalizado de columnas al refrescar la biblioteca.
- No sobrescribir preferencias guardadas del usuario con defaults al abrir/cerrar la tab o al escribir varias claves de configuracion seguidas.

## Resumen corto

- La base musical ya no esta en fase embrionaria; ya es una funcionalidad real de trabajo.
- Lo mas flojo ahora ya no es el flujo basico, sino rendimiento, claridad de estado y profundidad del editor.
- La suite esta en `54 passed` tras cubrir persistencia de portada elegida y el refactor del scan.
- El siguiente salto bueno no es meter mas botones, sino refinar el pipeline actual, mejorar claridad/tooltips y blindar persistencia de layout/configuracion.
