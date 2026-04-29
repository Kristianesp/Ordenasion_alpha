# Guía para Crear Releases, Tags y Ejecutables (.exe)

Este documento describe el flujo recomendado para:
- Compilar el ejecutable (.exe)
- Etiquetar versiones (tags)
- Crear releases en GitHub
- Adjuntar archivos ejecutables para todas las futuras versiones

---

## 1. COMPILAR EL EJECUTABLE (.EXE)

### Checklist Precompilación
- [ ] Usa SIEMPRE el archivo `OrganizadorAlpha_OPTIMIZED.spec`
- [ ] Asegúrate que `main_optimized.py` es el punto de entrada
- [ ] Elimina emojis de prints/logs críticos
- [ ] Verifica que `ApplicationState` NO hereda de QObject directamente

### Limpia Compilaciones Previas
```powershell
Remove-Item -Path "dist\OrganizadorAlpha_vX.Y.Z.exe" -Force
Remove-Item -Path "build" -Recurse -Force
```

### Compila el .exe
- Usando el script recomendado:
```powershell
./compilar_exe_completo.bat
```
- O directamente con PyInstaller:
```powershell
pyinstaller --clean --noconfirm OrganizadorAlpha_OPTIMIZED.spec
```

### Verifica el ejecutable
```powershell
Test-Path "dist\OrganizadorAlpha_vX.Y.Z.exe"
(Get-Item "dist\OrganizadorAlpha_vX.Y.Z.exe").Length / 1MB   # Debe ser ~40-50 MB
```
- Ejecuta el .exe y verifica inicio correcto (sin errores ni bloqueos, abre la ventana principal)
- Revisa el log `dist/startup_log.txt` y que no haya errores críticos

### Consideraciones clave (de GUIA_COMPILACION_EXE.md)
- Solo usa dependencias MÍNIMAS en el .spec (PyQt6 básico, psutil)
- NO uses `collect_all()`
- Excluye librerías pesadas no usadas: `matplotlib`, `numpy`, `PIL`, `torch`, etc.
- NO heredes de QObject, utiliza un QObject interno para señales (revisa `application_state.py`)
- El nombre del .exe debe corresponder a la versión (ej: OrganizadorAlpha_v3.2.0.exe)

---

## 2. ETIQUETA (TAG) LA VERSIÓN EN GIT

```sh
git add .
git commit -m "Cambios para la versión vX.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

- Cambia `X.Y.Z` por la nueva versión.

---

## 3. CREA LA RELEASE EN GITHUB Y ADJUNTA EL .EXE

Desde la terminal:
```sh
gh release create vX.Y.Z "dist/OrganizadorAlpha_vX.Y.Z.exe" \
  --title "Ordenasion Alpha vX.Y.Z" \
  --notes "Release vX.Y.Z. Incluye ejecutable para Windows (.exe)."
```
- Cambia el nombre por el archivo generado real.
- El tag, nombre y ejecutable deben coincidir con la versión.
- Puedes adjuntar más archivos como txt, docs, etc.

---

## 4. VERIFICACIÓN FINAL
- Confirma en la pestaña "Releases" de GitHub que:
  - El release/tag aparece como publicado
  - El ejecutable está en "Assets"
  - El archivo corresponde a la versión y tamaño correcto

---

## 5. RESUMEN DE FLUJO (RÁPIDO)

```sh
# 1. Compila el .exe correctamente (ver arriba)
# 2. Etiqueta el repo
git add .
git commit -m "Cambios vX.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
# 3. Publica el release con el ejecutable
gh release create vX.Y.Z "dist/OrganizadorAlpha_vX.Y.Z.exe" --title "Ordenasion Alpha vX.Y.Z" --notes "Release vX.Y.Z. Incluye ejecutable."
```

---

## Notas y Mejores Prácticas
- El ejecutable .exe NO debe pesar más de 50MB. Si supera, revisa exclusión de dependencias.
- Conserva registros en `startup_log.txt` y revisa advertencias `warn-*.txt` tras cada build.
- Si gh falla, ejecuta `gh auth login`.
- Haz este procedimiento para CADA release.
- También puedes crear releases y subir el .exe manualmente desde la web de GitHub si es necesario.

---

**Este documento fusiona la guía de compilación y el flujo de releases/tags para futuras versiones y garantiza releases limpios y descargables.**
