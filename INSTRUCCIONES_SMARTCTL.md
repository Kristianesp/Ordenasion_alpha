# 📊 Integración de smartctl para Datos SMART Reales

## ✅ ¿Qué se ha implementado?

Se ha integrado **smartctl.exe** en el proyecto para obtener **datos SMART lifetime REALES** de los discos, incluyendo:

- **Total de datos leídos/escritos** desde la fabricación del disco (TB/GB lifetime)
- **Horas de encendido totales** (Power On Hours)
- **Ciclos de encendido** (Power Cycles)
- **Temperatura actual** del disco
- **Estado de salud** (Health Percentage)
- **Estado SMART** (Pass/Fail)

### Archivos creados/modificados:

1. **`src/utils/smartctl_wrapper.py`** - Wrapper para interactuar con smartctl.exe
2. **`src/core/disk_manager.py`** - Modificado para usar smartctl como prioridad
3. **`bin/README.md`** - Instrucciones de descarga
4. **`descargar_smartctl.bat`** - Script de ayuda para descargar
5. **`OrganizadorArchivos_v2.8_SMART.spec`** - Configuración PyInstaller actualizada

---

## 📥 PASO 1: Descargar smartctl.exe

### Opción A: Script automático (Recomendado)
1. Ejecuta `descargar_smartctl.bat`
2. Se abrirá la página de descarga
3. Descarga `smartmontools-7.4-1.win32-setup.exe`
4. Ejecuta el instalador
5. Ve a `C:\Program Files\smartmontools\bin\`
6. **Copia `smartctl.exe`** a la carpeta `bin\` del proyecto

### Opción B: Descarga manual
1. Ve a: https://sourceforge.net/projects/smartmontools/files/smartmontools/7.4/
2. Descarga: `smartmontools-7.4-1.win32-setup.exe`
3. Instala
4. Copia `smartctl.exe` desde `C:\Program Files\smartmontools\bin\` a `bin\`

### Opción C: Con winget
```bash
winget install smartmontools
```
Luego copia `smartctl.exe` a `bin\`

---

## 🧪 PASO 2: Probar la integración

Una vez colocado `smartctl.exe` en `bin\`:

```bash
python main.py
```

Deberías ver en la consola:
```
✅ smartctl disponible - Se usarán datos SMART reales lifetime
🔍 Obteniendo datos SMART lifetime para C: (PHYSICALDRIVE2)...
✅ SMART lifetime obtenido: 15.3 TB leídos
```

Si NO colocas `smartctl.exe`, verás:
```
⚠️ smartctl no disponible - Se usarán datos desde arranque
```
(La aplicación funcionará, pero con datos menos precisos)

---

## 🔧 PASO 3: Compilar a .exe con smartctl incluido

```bash
pyinstaller OrganizadorArchivos_v2.8_SMART.spec
```

El `.exe` resultante incluirá automáticamente `smartctl.exe` si está en `bin\`

### Verificación durante la compilación:
```
✅ smartctl.exe será incluido en el ejecutable
```

O si no está:
```
⚠️ smartctl.exe NO encontrado en bin/ - La app funcionará sin datos SMART lifetime
```

---

## 📊 Diferencias entre datos

### Con smartctl (RECOMENDADO):
- ✅ Datos **lifetime reales** desde la fabricación
- ✅ Totales acumulativos de TB/GB leídos/escritos
- ✅ Horas de encendido totales
- ✅ Salud del disco
- ✅ Funciona en **todos los discos** (HDD, SSD, NVMe)

### Sin smartctl (Fallback):
- ⚠️ Datos **desde el último arranque** del sistema
- ⚠️ Menos precisos (se resetean al reiniciar)
- ⚠️ No incluye temperatura ni estado de salud
- ⚠️ Puede mostrar valores altos si el sistema lleva mucho tiempo encendido

---

## 🎯 Ejemplo de uso

### Con smartctl:
```
Disco C: (WD_BLACK SN850X 1000GB)
- Datos leídos: 15.3 TB (lifetime total)
- Datos escritos: 24.7 TB (lifetime total)
- Horas de encendido: 8,234 horas
- Temperatura: 42°C
- Salud: 98%
- Estado SMART: ✅ PASS
```

### Sin smartctl:
```
Disco C:
- Datos leídos: 55.3 GB (desde arranque)
- Datos escritos: 82.5 GB (desde arranque)
- Nota: Datos desde el último arranque del sistema
```

---

## ⚙️ Detalles técnicos

### Prioridad de métodos:
1. **smartctl** (si está disponible) → Datos SMART lifetime reales
2. **psutil + cache** (fallback) → Datos desde arranque

### Formato de smartctl:
- Usa salida JSON (`smartctl -a -j /dev/pdX`)
- Soporta discos NVMe, SATA, SAS
- Parsea atributos SMART estándar (ID 9, 12, 194, etc.)
- Para NVMe: Lee `data_units_read/written` y los convierte a bytes

### Cache:
- Los datos se cachean para evitar llamadas repetitivas
- Refresh automático cada 30 segundos
- No bloquea la UI

---

## ❓ Preguntas frecuentes

**¿Es necesario smartctl?**
No, la aplicación funciona sin él, pero los datos serán menos precisos.

**¿Se puede distribuir smartctl.exe con la aplicación?**
Sí, smartmontools tiene licencia GPL v2+, es libre de distribuir.

**¿Funciona en todos los discos?**
Sí, smartctl soporta HDD, SSD SATA, NVMe, SAS, etc.

**¿Afecta al rendimiento?**
No, se usa cache y las llamadas son asíncronas.

**¿Qué pasa si smartctl.exe no está en el .exe?**
La aplicación detectará su ausencia y usará el fallback (datos desde arranque).

---

## 🚀 Siguiente paso

**Descarga smartctl.exe y colócalo en `bin\`**, luego prueba la aplicación con:
```bash
python main.py
```

Deberías ver datos lifetime reales y precisos para cada disco.

---

## 📝 Notas adicionales

- **Requiere privilegios de administrador**: smartctl necesita acceso de bajo nivel a los discos
- **Compatible con Windows 7+**: Funciona en todas las versiones modernas de Windows
- **Sin dependencias adicionales**: Solo necesitas el archivo `smartctl.exe`
- **Tamaño**: ~800KB, no afectará significativamente el tamaño del .exe final
