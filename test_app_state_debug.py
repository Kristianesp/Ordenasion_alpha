#!/usr/bin/env python3
"""
Test para debuggear ApplicationState específicamente
"""

import sys
from pathlib import Path

# Añadir el directorio src al path para importaciones
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_app_state_debug():
    """Test para debuggear ApplicationState"""
    print("[TEST] Iniciando test de ApplicationState...")
    
    try:
        # Test 1: Importar ApplicationState
        print("[TEST] Test 1: Importando ApplicationState...")
        from core.application_state import app_state
        print("[SUCCESS] ApplicationState importado correctamente")
        
        # Test 2: Obtener DiskManager
        print("[TEST] Test 2: Obteniendo DiskManager...")
        disk_manager = app_state.get_disk_manager()
        
        if disk_manager:
            print("[SUCCESS] DiskManager obtenido correctamente")
            
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
                
        else:
            print("[ERROR] No se pudo obtener DiskManager")
            return False
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error en test de ApplicationState: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_app_state_debug()
    if success:
        print("[SUCCESS] Test de ApplicationState completado exitosamente")
    else:
        print("[FAIL] Test de ApplicationState falló")
        sys.exit(1)
