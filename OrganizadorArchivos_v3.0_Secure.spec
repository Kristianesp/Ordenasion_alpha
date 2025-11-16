# -*- mode: python ; coding: utf-8 -*-

# Configuración SEGURA para PyInstaller
# EXE NO MANIPULABLE NI DESCOMPRIMIBLE
# Configuración de máxima seguridad

import os
from pathlib import Path

# Directorio base del proyecto
base_dir = Path('.')

# Datos adicionales que necesita la aplicación
datas = [
    ('src', 'src'),  # Incluir toda la carpeta src
    ('app_config.json', '.'),
    ('categories_config.json', '.'),
    ('hash_cache.db', '.'),
    ('bin/smartctl.exe', 'bin'),  # Incluir smartctl
]

# Módulos ocultos que PyInstaller no detecta automáticamente
hiddenimports = [
    'src.gui.main_window',
    'src.gui.duplicates_dashboard', 
    'src.gui.disk_viewer',
    'src.gui.config_dialog',
    'src.gui.table_models',
    'src.core.category_manager',
    'src.core.disk_manager',
    'src.core.duplicate_finder',
    'src.core.hash_cache',
    'src.core.hash_manager',
    'src.core.transaction_manager',
    'src.core.workers',
    'src.core.health_service',
    'src.utils.app_config',
    'src.utils.constants',
    'src.utils.professional_styles',
    'src.utils.themes',
    'src.utils.logger',
    'src.utils.smartctl_wrapper',
    'PyQt6.QtCore',
    'PyQt6.QtGui', 
    'PyQt6.QtWidgets',
    'hashlib',
    'sqlite3',
    'pathlib',
    'threading',
    'multiprocessing',
    'concurrent.futures',
    'json',
    'datetime',
    'subprocess',
    'psutil',
    'wmi',
]

a = Analysis(
    ['main.py'],
    pathex=['.', 'src'],
    binaries=[('bin/smartctl.exe', 'bin')],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=True,  # 🔒 SEGURIDAD: No crear archivo de datos separado
    optimize=2,      # Optimización máxima
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],  # Sin archivos adicionales
    name='OrganizadorArchivos_v3.0_Secure',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,      # 🔒 SEGURIDAD: Eliminar símbolos de debug
    upx=True,        # 🔒 SEGURIDAD: Comprimir con UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
