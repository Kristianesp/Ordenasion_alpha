@echo off
echo ========================================
echo Descarga de smartctl.exe
echo ========================================
echo.
echo Este script te ayudara a obtener smartctl.exe
echo.
echo OPCION 1: Descargar e instalar smartmontools
echo ---------------------------------------------
echo 1. Se abrira la pagina de descarga de smartmontools
echo 2. Descarga: smartmontools-7.4-1.win32-setup.exe
echo 3. Ejecuta el instalador
echo 4. Copia smartctl.exe desde C:\Program Files\smartmontools\bin\
echo 5. Pegalo en la carpeta bin\ de este proyecto
echo.
echo OPCION 2: Usar winget (si lo tienes instalado)
echo ---------------------------------------------
echo 1. winget install smartmontools
echo 2. Copia smartctl.exe desde la carpeta de instalacion
echo 3. Pegalo en la carpeta bin\ de este proyecto
echo.
pause
echo.
echo Abriendo pagina de descarga...
start https://sourceforge.net/projects/smartmontools/files/smartmontools/7.4/smartmontools-7.4-1.win32-setup.exe/download
echo.
echo Cuando hayas copiado smartctl.exe a bin\, ejecuta:
echo python main.py
echo.
echo Deberias ver: "smartctl disponible - Se usaran datos SMART reales lifetime"
echo.
pause
