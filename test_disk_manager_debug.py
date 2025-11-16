#!/usr/bin/env python3
"""
Test para debuggear DiskManager específicamente
"""

import sys
from pathlib import Path

# Añadir el directorio src al path para importaciones
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_disk_manager_debug():
    """Test para debuggear DiskManager"""
    print("[TEST] Iniciando test de DiskManager...")
    
    try:
        # Test 1: Importar DiskManager
        print("[TEST] Test 1: Importando DiskManager...")
        from core.disk_manager import DiskManager
        print("[SUCCESS] DiskManager importado correctamente")
        
        # Test 2: Crear instancia DiskManager
        print("[TEST] Test 2: Creando instancia DiskManager...")
        disk_manager = DiskManager()
        print("[SUCCESS] Instancia DiskManager creada correctamente")
        
        # Test 3: Verificar estado WMI
        print("[TEST] Test 3: Verificando estado WMI...")
        if disk_manager.wmi_service:
            print("[SUCCESS] WMI service está disponible")
        else:
            print("[ERROR] WMI service NO está disponible")
            return False
        
        # Test 4: Verificar mapeo de unidades
        print("[TEST] Test 4: Verificando mapeo de unidades...")
        drive_map = disk_manager._drive_map
        print(f"[INFO] Mapeo actual: {drive_map}")
        
        if drive_map:
            print("[SUCCESS] Mapeo de unidades disponible")
            for logical, physical in drive_map.items():
                print(f"  - {logical} -> {physical}")
        else:
            print("[ERROR] Mapeo de unidades vacío")
            return False
        
        # Test 5: Probar get_disk_info
        print("[TEST] Test 5: Probando get_disk_info...")
        disks = disk_manager.get_disk_info()
        print(f"[INFO] Discos encontrados: {len(disks)}")
        
        for disk in disks:
            print(f"  - {disk.mountpoint}: {disk.total_size // (1024**3)} GB")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error en test de DiskManager: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_disk_manager_debug()
    if success:
        print("[SUCCESS] Test de DiskManager completado exitosamente")
    else:
        print("[FAIL] Test de DiskManager falló")
        sys.exit(1)
