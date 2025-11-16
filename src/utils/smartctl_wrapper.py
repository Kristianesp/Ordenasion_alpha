"""
Wrapper para smartctl.exe - Obtiene datos SMART reales lifetime de los discos
"""
import subprocess
import json
import os
import sys
from typing import Optional, Dict, Any, List
from pathlib import Path


class SmartctlWrapper:
    """Wrapper para interactuar con smartctl.exe"""
    
    def __init__(self):
        """Inicializa el wrapper y localiza smartctl.exe"""
        self.smartctl_path = self._find_smartctl()
    
    def _log(self, message: str) -> None:
        """Imprime mensajes con emojis de forma segura en Windows."""
        from .logger import _safe_print
        _safe_print(message)
        
    def _find_smartctl(self) -> Optional[str]:
        """Encuentra la ruta a smartctl.exe"""
        # Opción 1: En la carpeta bin/ del proyecto
        if getattr(sys, 'frozen', False):
            # Si estamos en un .exe compilado
            base_path = Path(sys._MEIPASS)
        else:
            # Si estamos en desarrollo
            base_path = Path(__file__).parent.parent.parent
        
        smartctl_bin = base_path / "bin" / "smartctl.exe"
        if smartctl_bin.exists():
            self._log(f"✅ smartctl.exe encontrado en: {smartctl_bin}")
            return str(smartctl_bin)
        
        # Opción 2: En el PATH del sistema
        try:
            result = subprocess.run(
                ["where", "smartctl.exe"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                path = result.stdout.strip().split('\n')[0]
                self._log(f"✅ smartctl.exe encontrado en PATH: {path}")
                return path
        except Exception:
            pass
        
        self._log("⚠️ smartctl.exe no encontrado. Coloca smartctl.exe en la carpeta bin/")
        return None
    
    def is_available(self) -> bool:
        """Verifica si smartctl está disponible"""
        return self.smartctl_path is not None
    
    def get_disk_smart_data(self, physical_drive: str, timeout: int = 10, max_retries: int = 2, device_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos SMART reales de un disco físico con reintentos y timeout configurable
        
        Args:
            physical_drive: ID del disco físico (ej: "PHYSICALDRIVE0" o "/dev/nvme0")
            timeout: Timeout en segundos para la ejecución de smartctl
            max_retries: Número máximo de reintentos con backoff exponencial
        
        Returns:
            Diccionario con datos SMART o None si hay error
        """
        if not self.is_available():
            return None
        
        # Convertir formato de disco físico a formato que smartctl entiende en Windows
        # Intentar múltiples formatos para compatibilidad
        device = None
        if 'PHYSICALDRIVE' in physical_drive:
            drive_num = physical_drive.replace('PHYSICALDRIVE', '').strip()
            # Formato estándar para Windows: /dev/pdX
            device = f"/dev/pd{drive_num}"
        elif physical_drive.startswith('/dev/'):
            # Ya está en formato correcto
            device = physical_drive
        else:
            # Intentar como está
            device = physical_drive
        
        if not device:
            self._log(f"⚠️ No se pudo determinar formato de dispositivo para {physical_drive}")
            return None
        
        for attempt in range(max_retries + 1):
            try:
                # Ejecutar smartctl con salida JSON
                # -a: toda la información SMART
                # -j: salida en formato JSON
                # -d: especificar tipo de dispositivo si se conoce (sat, nvme, etc.)
                cmd = [self.smartctl_path, "-a", "-j"]
                if device_type:
                    cmd.extend(["-d", device_type])
                cmd.append(device)
                
                # Aumentar timeout progresivamente en reintentos
                current_timeout = timeout + (attempt * 5)
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=current_timeout,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                
                # Códigos de retorno de smartctl:
                # 0 = OK
                # 1 = Error de línea de comandos
                # 2 = Error al abrir dispositivo
                # 4 = OK con warnings (datos válidos)
                # 64 = Error de sintaxis
                # 128 = Error fatal
                if result.returncode in [0, 4]:  # 0 = OK, 4 = OK con warnings
                    try:
                        # Verificar que stdout no esté vacío
                        if not result.stdout or not result.stdout.strip():
                            self._log(f"⚠️ smartctl no devolvió datos para {device}")
                            if attempt < max_retries:
                                continue
                            return None
                        
                        data = json.loads(result.stdout)
                        
                        # Verificar que sea un diccionario válido
                        if not isinstance(data, dict):
                            self._log(f"⚠️ smartctl devolvió datos en formato incorrecto para {device}")
                            if attempt < max_retries:
                                continue
                            return None
                        
                        parsed_data = self._parse_smart_json(data)
                        
                        # Validar que los datos parseados sean válidos
                        if self._validate_smart_data(parsed_data):
                            if attempt > 0:
                                self._log(f"✅ smartctl exitoso en intento {attempt + 1} para {device}")
                            return parsed_data
                        else:
                            self._log(f"⚠️ Datos SMART inválidos para {device}")
                            if attempt < max_retries:
                                continue
                            return None
                            
                    except json.JSONDecodeError as e:
                        self._log(f"⚠️ Error parseando JSON de smartctl para {device}: {e}")
                        # Si hay salida, puede ser un mensaje de error en texto
                        if result.stderr:
                            self._log(f"  stderr: {result.stderr[:200]}")
                        if attempt < max_retries:
                            continue
                        return None
                elif result.returncode == 2:
                    # Error al abrir dispositivo - puede ser permisos o dispositivo no existe
                    error_msg = result.stderr.strip() if result.stderr else "Error desconocido"
                    if "Permission denied" in error_msg or "Access denied" in error_msg:
                        self._log(f"⚠️ Permisos insuficientes para acceder a {device}. Ejecuta como administrador.")
                    else:
                        self._log(f"⚠️ No se pudo abrir dispositivo {device}: {error_msg[:100]}")
                    # No reintentar si es un error de permisos
                    return None
                else:
                    error_msg = result.stderr.strip() if result.stderr else f"Código {result.returncode}"
                    self._log(f"⚠️ smartctl retornó código {result.returncode} para {device}: {error_msg[:100]}")
                    if attempt < max_retries:
                        continue
                    return None
                    
            except subprocess.TimeoutExpired:
                self._log(f"⚠️ Timeout ({current_timeout}s) ejecutando smartctl para {physical_drive} (intento {attempt + 1})")
                if attempt < max_retries:
                    # Backoff exponencial: esperar 1s, 2s, 4s...
                    import time
                    time.sleep(2 ** attempt)
                    continue
                return None
            except Exception as e:
                self._log(f"❌ Error ejecutando smartctl: {e}")
                if attempt < max_retries:
                    import time
                    time.sleep(2 ** attempt)
                    continue
                return None
        
        return None
    
    def _parse_smart_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parsea la salida JSON de smartctl y extrae datos relevantes
        
        Args:
            data: Diccionario JSON de smartctl
            
        Returns:
            Diccionario con datos procesados
        """
        result = {
            'disk_model': data.get('model_name', 'Desconocido'),
            'serial_number': data.get('serial_number', 'N/A'),
            'firmware': data.get('firmware_version', 'N/A'),
            'smart_status': data.get('smart_status', {}).get('passed', False),
            'device_type': None,
            'temperature': None,
            'power_on_hours': None,
            'power_cycles': None,
            'read_bytes': None,
            'write_bytes': None,
            'read_count': None,
            'write_count': None,
            'health_percentage': 100
        }
        
        self._log(f"📋 Parseando datos SMART de: {result['disk_model']}")
        
        # Para discos NVMe, la estructura es diferente (PRIORITARIO)
        if 'nvme_smart_health_information_log' in data:
            nvme_log = data['nvme_smart_health_information_log']
            result['device_type'] = 'nvme'
            
            # La temperatura puede venir en diferentes formatos
            temp_value = nvme_log.get('temperature', None)
            if temp_value is not None:
                # Si es un diccionario, puede tener 'value' o 'current'
                if isinstance(temp_value, dict):
                    temp_value = temp_value.get('value') or temp_value.get('current') or temp_value.get('temperature')
                # Convertir de Kelvin a Celsius si es necesario (temperaturas > 200 probablemente están en Kelvin)
                if isinstance(temp_value, (int, float)):
                    if temp_value > 200:  # Probablemente en Kelvin
                        temp_value = temp_value - 273.15
                    result['temperature'] = int(temp_value) if temp_value else None
                else:
                    result['temperature'] = None
            else:
                result['temperature'] = None
            result['power_on_hours'] = nvme_log.get('power_on_hours', None)
            result['power_cycles'] = nvme_log.get('power_cycles', None)
            
            # Datos de lectura/escritura en unidades de 1000 bloques de 512 bytes
            data_units_read = nvme_log.get('data_units_read', 0)
            data_units_written = nvme_log.get('data_units_written', 0)
            
            self._log(f"  📊 NVMe - data_units_read: {data_units_read:,}, data_units_written: {data_units_written:,}")
            
            # Convertir a bytes (cada unidad = 1000 bloques de 512 bytes = 512,000 bytes)
            result['read_bytes'] = data_units_read * 512000
            result['write_bytes'] = data_units_written * 512000
            
            # Calcular contadores de operaciones (estimado: promedio 64KB por operación)
            avg_op_size = 64 * 1024
            result['read_count'] = result['read_bytes'] // avg_op_size if result['read_bytes'] > 0 else 0
            result['write_count'] = result['write_bytes'] // avg_op_size if result['write_bytes'] > 0 else 0
            
            # Porcentaje de vida útil disponible
            available_spare = nvme_log.get('available_spare', 100)
            result['health_percentage'] = available_spare
            
            self._log(f"  ✅ NVMe parsed: {result['read_bytes']/1024**4:.1f} TB leídos, Temp: {result['temperature']}°C, Horas: {result['power_on_hours']:,}")
        
        # Obtener atributos SMART para discos SATA/ATA
        elif 'ata_smart_attributes' in data:
            smart_attrs = data.get('ata_smart_attributes', {}).get('table', [])
            result['device_type'] = 'ata'
            self._log(f"  📊 Disco SATA/ATA con {len(smart_attrs)} atributos SMART")
            
            for attr in smart_attrs:
                attr_id = attr.get('id', 0)
                attr_name = attr.get('name', '')
                raw_value = attr.get('raw', {}).get('value', 0)
                
                # ID 9: Power On Hours
                if attr_id == 9 or 'Power_On_Hours' in attr_name:
                    result['power_on_hours'] = raw_value
                    self._log(f"    ⏰ Power On Hours: {raw_value:,} horas")
                
                # ID 12: Power Cycle Count
                elif attr_id == 12 or 'Power_Cycle' in attr_name:
                    result['power_cycles'] = raw_value
                    self._log(f"    🔄 Power Cycles: {raw_value:,}")
                
                # ID 194: Temperature
                elif attr_id == 194 or 'Temperature' in attr_name:
                    result['temperature'] = raw_value
                    self._log(f"    🌡️ Temperature: {raw_value}°C")
                
                # ID 241: Total LBAs Written (SSDs SATA - en unidades de 32MiB típicamente)
                elif attr_id == 241:
                    # La mayoría de SSDs SATA reportan en unidades de 32MiB (33,554,432 bytes)
                    result['write_bytes'] = raw_value * 32 * 1024 * 1024  # 32 MiB
                    self._log(f"    ✍️ Total LBAs Written: {raw_value:,} unidades ({result['write_bytes']/1024**4:.2f} TB)")
                
                # ID 242: Total LBAs Read (SSDs SATA - en unidades de 32MiB típicamente)
                elif attr_id == 242:
                    result['read_bytes'] = raw_value * 32 * 1024 * 1024  # 32 MiB
                    self._log(f"    📖 Total LBAs Read: {raw_value:,} unidades ({result['read_bytes']/1024**4:.2f} TB)")
            
            # Calcular contadores de operaciones para SATA si tenemos datos
            if result['read_bytes'] is not None and result['write_bytes'] is not None:
                avg_op_size = 64 * 1024
                result['read_count'] = result['read_bytes'] // avg_op_size if result['read_bytes'] > 0 else 0
                result['write_count'] = result['write_bytes'] // avg_op_size if result['write_bytes'] > 0 else 0
                self._log(f"  ✅ SATA parsed: Temp: {result['temperature']}°C, Horas: {result['power_on_hours']:,}, Ciclos: {result['power_cycles']:,}")
            
            # Si no encontramos los atributos 241/242, el disco podría no reportarlos
            if result['read_bytes'] is None and result['write_bytes'] is None:
                self._log(f"  ⚠️ Disco SATA no reporta atributos de lectura/escritura (241/242)")
        else:
            self._log(f"  ⚠️ Estructura SMART desconocida - ni NVMe ni ATA")
        
        return result
    
    def _validate_smart_data(self, data: Dict[str, Any]) -> bool:
        """
        Valida que los datos SMART parseados sean coherentes y válidos
        
        Args:
            data: Diccionario con datos SMART parseados
            
        Returns:
            True si los datos son válidos, False en caso contrario
        """
        if not data or not isinstance(data, dict):
            return False
        
        # Verificar que al menos tengamos información básica del disco
        if not data.get('disk_model') or data.get('disk_model') == 'Desconocido':
            return False
        
        # Validar temperatura si está presente
        temp = data.get('temperature')
        if temp is not None:
            if not isinstance(temp, (int, float)) or temp < -50 or temp > 150:
                return False
        
        # Validar horas de encendido si está presente
        hours = data.get('power_on_hours')
        if hours is not None:
            if not isinstance(hours, (int, float)) or hours < 0 or hours > 1000000:
                return False
        
        # Validar ciclos de encendido si está presente
        cycles = data.get('power_cycles')
        if cycles is not None:
            if not isinstance(cycles, (int, float)) or cycles < 0 or cycles > 100000:
                return False
        
        # Validar bytes de lectura/escritura si están presentes
        read_bytes = data.get('read_bytes')
        write_bytes = data.get('write_bytes')
        
        if read_bytes is not None:
            if not isinstance(read_bytes, (int, float)) or read_bytes < 0:
                return False
        
        if write_bytes is not None:
            if not isinstance(write_bytes, (int, float)) or write_bytes < 0:
                return False
        
        # Si tenemos ambos bytes, verificar que no sean sospechosamente pequeños
        # Nota: Algunos discos nuevos o con poco uso pueden tener valores bajos, pero válidos
        # Solo rechazar si ambos son exactamente 0 (lo cual es sospechoso)
        if read_bytes is not None and write_bytes is not None:
            # Si ambos son 0, puede ser un disco nuevo o que no reporta estos atributos
            # Esto es válido para algunos HDDs que no reportan atributos 241/242
            if read_bytes == 0 and write_bytes == 0:
                # Permitir si es un HDD (puede no reportar estos atributos)
                # Rechazar solo si parece ser un SSD que debería reportarlos
                pass  # No rechazar automáticamente, dejar que el código que llama decida
        
        # Validar porcentaje de salud si está presente
        health = data.get('health_percentage')
        if health is not None:
            if not isinstance(health, (int, float)) or health < 0 or health > 100:
                return False
        
        return True
    
    def scan_all_disks(self) -> List[Dict[str, Any]]:
        """
        Escanea todos los discos disponibles usando smartctl --scan (método profesional)
        
        Returns:
            Lista de diccionarios con información de cada disco detectado
            [{"device": "/dev/pd0", "type": "sat", "physical_drive": "PHYSICALDRIVE0"}, ...]
        """
        if not self.is_available():
            return []
        
        disks = []
        
        try:
            # Método 1: Usar smartctl --scan (método profesional recomendado)
            # Esto lista automáticamente todos los discos con su tipo
            cmd = [self.smartctl_path, "--scan"]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode == 0 and result.stdout:
                # Parsear salida de --scan
                # Formato típico: /dev/pd0 -d sat # /dev/pd0, ATA device
                for line in result.stdout.strip().split('\n'):
                    if line.strip() and not line.strip().startswith('#'):
                        parts = line.split('#')[0].strip().split()
                        if parts:
                            device = parts[0]
                            device_type = None
                            if '-d' in parts:
                                idx = parts.index('-d')
                                if idx + 1 < len(parts):
                                    device_type = parts[idx + 1]
                            
                            # Extraer número de disco físico
                            if '/dev/pd' in device:
                                drive_num = device.replace('/dev/pd', '').strip()
                                physical_drive = f"PHYSICALDRIVE{drive_num}"
                                
                                disk_info = {
                                    'device': device,
                                    'physical_drive': physical_drive,
                                    'type': device_type,
                                    'raw_line': line
                                }
                                disks.append(disk_info)
                                self._log(f"✅ Disco detectado: {physical_drive} -> {device} (tipo: {device_type or 'auto'})")
            
            # Si --scan no funcionó, usar método de escaneo manual
            if not disks:
                self._log("⚠️ smartctl --scan no devolvió resultados, usando escaneo manual...")
                for i in range(10):
                    device = f"/dev/pd{i}"
                    cmd = [self.smartctl_path, "-i", device]
                    
                    try:
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=2,
                            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                        )
                        
                        if result.returncode in [0, 4]:
                            disk_info = {
                                'device': device,
                                'physical_drive': f"PHYSICALDRIVE{i}",
                                'type': None,
                                'raw_line': ''
                            }
                            disks.append(disk_info)
                            self._log(f"✅ Disco detectado (manual): PHYSICALDRIVE{i} -> {device}")
                    except subprocess.TimeoutExpired:
                        continue
                    except Exception:
                        continue
            
            return disks
            
        except Exception as e:
            from .logger import error
            error(f"Error escaneando discos: {e}")
            return []
    
    def get_disk_info_quick(self, physical_drive: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información básica del disco (modelo, número de serie) sin datos SMART completos
        Útil para mapeo rápido de unidades
        
        Args:
            physical_drive: ID del disco físico (ej: "PHYSICALDRIVE0")
        
        Returns:
            Diccionario con información básica o None
        """
        if not self.is_available():
            return None
        
        # Convertir formato de disco físico
        device = None
        if 'PHYSICALDRIVE' in physical_drive:
            drive_num = physical_drive.replace('PHYSICALDRIVE', '').strip()
            device = f"/dev/pd{drive_num}"
        elif physical_drive.startswith('/dev/'):
            device = physical_drive
        else:
            device = physical_drive
        
        if not device:
            return None
        
        try:
            # Usar -i para información básica (más rápido que -a)
            cmd = [self.smartctl_path, "-i", "-j", device]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode in [0, 4] and result.stdout:
                try:
                    data = json.loads(result.stdout)
                    return {
                        'model_name': data.get('model_name', 'Desconocido'),
                        'serial_number': data.get('serial_number', 'N/A'),
                        'device': device,
                        'physical_drive': physical_drive
                    }
                except json.JSONDecodeError:
                    return None
            
            return None
            
        except Exception:
            return None
