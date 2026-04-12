# Smartctl.exe - Herramienta para datos SMART

## ¿Qué es smartctl?
`smartctl.exe` es una herramienta que permite leer datos **SMART lifetime reales** de los discos duros y SSDs, incluyendo:
- Total de datos leídos/escritos desde la fabricación del disco
- Horas de encendido totales
- Ciclos de encendido
- Temperatura
- Estado de salud del disco

## Descargar smartctl.exe

### Opción 1: Descarga directa (Recomendado)
1. Ve a: https://sourceforge.net/projects/smartmontools/files/smartmontools/7.4/
2. Descarga: `smartmontools-7.4-1.win32-setup.exe`
3. Ejecuta el instalador
4. Navega a `C:\Program Files\smartmontools\bin\`
5. **Copia `smartctl.exe`** a esta carpeta `bin/`

### Opción 2: Instalación completa
Si prefieres instalar smartmontools en tu sistema:
```bash
winget install smartmontools
```

Luego copia `smartctl.exe` de la carpeta de instalación a `bin/`

## Verificación
Una vez colocado `smartctl.exe` en esta carpeta, la aplicación lo detectará automáticamente y mostrará:
```
✅ smartctl disponible - Se usarán datos SMART reales lifetime
```

## Sin smartctl.exe
Si no colocas `smartctl.exe`, la aplicación funcionará pero mostrará:
```
⚠️ smartctl no disponible - Se usarán datos desde arranque
```

Y los datos I/O serán desde el último arranque del sistema (menos precisos).

## Compilación a .exe
Cuando compiles la aplicación con PyInstaller, `smartctl.exe` se incluirá automáticamente en el ejecutable final.
