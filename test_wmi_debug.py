#!/usr/bin/env python3
"""
Test para debuggear el problema de WMI
"""

import sys
from pathlib import Path

# Añadir el directorio src al path para importaciones
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_wmi_debug():
    """Test para debuggear WMI"""
    print("[TEST] Iniciando test de WMI...")
    
    try:
        # Test 1: Importar wmi directamente
        print("[TEST] Test 1: Importando wmi directamente...")
        import wmi
        print("[SUCCESS] WMI importado correctamente")
        
        # Test 2: Crear instancia WMI
        print("[TEST] Test 2: Creando instancia WMI...")
        wmi_service = wmi.WMI()
        print("[SUCCESS] Instancia WMI creada correctamente")
        
        # Test 3: Obtener discos físicos
        print("[TEST] Test 3: Obteniendo discos físicos...")
        physical_disks = wmi_service.Win32_DiskDrive()
        print(f"[SUCCESS] Encontrados {len(physical_disks)} discos físicos")
        
        for disk in physical_disks:
            print(f"  - {disk.DeviceID}: {disk.Model}")
        
        # Test 4: Obtener particiones
        print("[TEST] Test 4: Obteniendo particiones...")
        partitions = wmi_service.Win32_DiskPartition()
        print(f"[SUCCESS] Encontradas {len(partitions)} particiones")
        
        # Test 5: Obtener discos lógicos
        print("[TEST] Test 5: Obteniendo discos lógicos...")
        logical_disks = wmi_service.Win32_LogicalDisk()
        print(f"[SUCCESS] Encontrados {len(logical_disks)} discos lógicos")
        
        for disk in logical_disks:
            if disk.DriveType == 3:  # Disco fijo
                print(f"  - {disk.DeviceID}: {disk.VolumeName or 'Sin nombre'}")
        
        # Test 6: Mapeo completo
        print("[TEST] Test 6: Creando mapeo completo...")
        drive_map = {}
        
        for physical_disk in physical_disks:
            print(f"[DEBUG] Disco físico: {physical_disk.DeviceID}")
            for partition in physical_disk.associators("Win32_DiskDriveToDiskPartition"):
                print(f"[DEBUG]   Partición: {partition.DeviceID}")
                for logical_disk in partition.associators("Win32_LogicalDiskToPartition"):
                    psutil_key = physical_disk.DeviceID.replace('\\\\.\\', '').upper()
                    logical_drive = logical_disk.DeviceID.upper()
                    drive_map[logical_drive] = psutil_key
                    print(f"[DEBUG]   Mapeado: {logical_drive} -> {psutil_key}")
        
        print(f"[SUCCESS] Mapeo final: {drive_map}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error en test de WMI: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_wmi_debug()
    if success:
        print("[SUCCESS] Test de WMI completado exitosamente")
    else:
        print("[FAIL] Test de WMI falló")
        sys.exit(1)
