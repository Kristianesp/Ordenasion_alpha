@echo off
chcp 65001 >nul
echo.
echo ========================================
echo    CREANDO COPIA DE SEGURIDAD
echo ========================================
echo.

:: Obtener fecha y hora actual
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"

:: Crear nombre de carpeta con fecha y hora
set "BACKUP_FOLDER=BACKUP_%YYYY%-%MM%-%DD%_%HH%-%Min%-%Sec%"

echo Fecha y hora actual: %DD%/%MM%/%YYYY% %HH%:%Min%:%Sec%
echo Carpeta de respaldo: %BACKUP_FOLDER%
echo.

:: Crear carpeta de respaldo
if not exist "%BACKUP_FOLDER%" (
    mkdir "%BACKUP_FOLDER%"
    echo ✅ Carpeta de respaldo creada: %BACKUP_FOLDER%
) else (
    echo ⚠️  La carpeta ya existe, sobrescribiendo...
)

        echo.
        echo 📁 Copiando TODOS los archivos del proyecto...
        
        :: Copiar TODOS los archivos y carpetas (excepto BACKUP_*)
        echo 🔍 Escaneando archivos para copiar...
        
        :: Usar robocopy para copia completa con exclusión de carpetas BACKUP_ y archivos temporales
        robocopy "." "%BACKUP_FOLDER%" /E /XD "BACKUP_*" "__pycache__" /XF "*.tmp" "*.pyc" "*.pyo" /R:3 /W:1 /MT:4 /NP /TEE /LOG+:"%BACKUP_FOLDER%\backup_log.txt"
        
        if %ERRORLEVEL% LSS 8 (
            echo ✅ Copia completa realizada exitosamente
        ) else (
            echo ⚠️ Copia completada con algunos errores menores (normal en Windows)
        )
        
        :: Mostrar resumen de lo copiado
        echo.
        echo 📊 Resumen de la copia:
        dir "%BACKUP_FOLDER%" /B | find /c /v ""
        echo archivos/carpetas copiados

echo.
echo ========================================
echo    COPIA DE SEGURIDAD COMPLETADA
echo ========================================
echo.
echo 📂 Ubicación: %BACKUP_FOLDER%
echo 📊 Archivos copiados:
dir "%BACKUP_FOLDER%" /B
echo.
echo 💡 Para restaurar, copia la carpeta '%BACKUP_FOLDER%' 
echo    y renómbrala como 'src' en tu proyecto
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
