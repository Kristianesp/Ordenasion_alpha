#!/usr/bin/env python3
"""
Sistema de Detección de Duplicados para el Organizador de Archivos
Encuentra y gestiona archivos duplicados por contenido usando hashes
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
from PyQt6.QtCore import QThread, pyqtSignal

from .hash_manager import HashManager, HashCalculationWorker


class DuplicateFinder:
    """Sistema principal para encontrar archivos duplicados"""

    def __init__(self):
        self.hash_manager = HashManager()
        self.duplicates_db: Dict[str, List[Path]] = {}
        self.file_info: Dict[Path, Dict] = {}
        
        # NUEVOS MÉTODOS DE DETECCIÓN
        self.fast_duplicates_db: Dict[str, List[Path]] = {}  # Para método rápido
        self.detection_method = "fast"  # "fast", "deep", "hybrid"

    def scan_for_duplicates_fast(self, folder_path: str, recursive: bool = True) -> Dict[str, List[Path]]:
        """
        🚀 BÚSQUEDA ULTRA-RÁPIDA: Tamaño + Nombre + Extensión
        Perfecto para la mayoría de casos - hasta 100x más rápido que MD5
        
        Args:
            folder_path: Ruta de la carpeta o disco a analizar
            
        Returns:
            Diccionario con clave_combinada -> lista de archivos duplicados
        """
        folder_path = Path(folder_path)
        if not folder_path.exists():
            return {}
        
        # Limpiar datos anteriores
        self.fast_duplicates_db = {}
        self.file_info = {}
        
        # Obtener todos los archivos (con opción recursiva)
        all_files = self._get_all_files(folder_path, recursive=recursive)
        if not all_files:
            return {}
        
        # Agrupar por: tamaño + nombre_normalizado + extensión
        fast_groups = defaultdict(list)
        
        for file_path in all_files:
            try:
                # Obtener información básica del archivo
                stat = file_path.stat()
                file_size = stat.st_size
                file_name_raw = file_path.stem.lower()  # Nombre sin extensión, minúsculas
                file_ext = file_path.suffix.lower()  # Extensión en minúsculas
                file_date = stat.st_mtime
                
                # ✅ NORMALIZAR NOMBRE: Quitar sufijos de Windows como " (1)", " (2)", etc.
                file_name_normalized = self._normalize_filename(file_name_raw)
                
                # Crear clave única: tamaño|nombre_normalizado|extensión
                fast_key = f"{file_size}|{file_name_normalized}|{file_ext}"
                fast_groups[fast_key].append(file_path)
                
                # Guardar información del archivo
                self.file_info[file_path] = {
                    'size': file_size,
                    'date': file_date,
                    'name': file_path.name,
                    'normalized_name': file_name_normalized,  # ✅ Agregar nombre normalizado
                    'extension': file_ext,
                    'fast_key': fast_key,
                    'algorithm': 'fast'
                }
                
            except (OSError, PermissionError):
                continue
        
        # Filtrar solo grupos con duplicados (2+ archivos)
        for fast_key, files_list in fast_groups.items():
            if len(files_list) > 1:
                self.fast_duplicates_db[fast_key] = files_list
        
        return self.fast_duplicates_db

    def _normalize_filename(self, filename: str) -> str:
        """
        🔧 NORMALIZA nombres de archivo para detectar duplicados de Windows
        
        Convierte:
        - 'document (1)' → 'document'
        - 'image (2)' → 'image' 
        - 'file (10)' → 'file'
        - 'normal_file' → 'normal_file' (sin cambios)
        """
        import re
        
        # Patrón para detectar sufijos de Windows: " (número)" al final
        pattern = r'\s*\(\d+\)$'
        
        # Quitar el sufijo si existe
        normalized = re.sub(pattern, '', filename).strip()
        
        return normalized

    def scan_for_duplicates(self, folder_path: str, algorithms: List[str] = None, recursive: bool = True) -> Dict[str, List[Path]]:
        """
        Escanea una carpeta en busca de archivos duplicados

        Args:
            folder_path: Ruta de la carpeta a analizar
            algorithms: Lista de algoritmos a usar ['md5', 'sha256']

        Returns:
            Diccionario con hash -> lista de archivos duplicados
        """
        if algorithms is None:
            algorithms = ['md5']

        folder_path = Path(folder_path)
        if not folder_path.exists() or not folder_path.is_dir():
            return {}

        # Calcular hashes para todos los archivos
        self.duplicates_db = {}
        self.file_info = {}

        # Obtener todos los archivos (con opción recursiva)  
        all_files = self._get_all_files(folder_path, recursive=recursive)
        if not all_files:
            return {}

        for algorithm in algorithms:
            # Agrupar archivos por tamaño primero (optimización)
            size_groups = self._group_files_by_size(all_files)

            for size, files in size_groups.items():
                if len(files) < 2:
                    continue  # No puede haber duplicados si solo hay un archivo

                # Calcular hashes para archivos del mismo tamaño
                hash_results = self.hash_manager.calculate_multiple_hashes(files, algorithm)

                # Agrupar por hash
                hash_groups = defaultdict(list)
                for file_path, hash_value in hash_results.items():
                    if hash_value:
                        hash_groups[hash_value].append(file_path)
                        # Guardar información del archivo
                        file_size, file_date = self.hash_manager.get_file_size_and_date(file_path)
                        self.file_info[file_path] = {
                            'size': file_size,
                            'date': file_date,
                            'hash': hash_value,
                            'algorithm': algorithm
                        }

                # Agregar grupos de duplicados (archivos con mismo hash)
                for hash_value, files_list in hash_groups.items():
                    if len(files_list) > 1:
                        if hash_value not in self.duplicates_db:
                            self.duplicates_db[hash_value] = []
                        self.duplicates_db[hash_value].extend(files_list)

        return self.duplicates_db
    
    def scan_for_duplicates_hybrid(self, folder_path: str, progress_callback=None, recursive: bool = True) -> Dict[str, List[Path]]:
        """
        🎯 BÚSQUEDA HÍBRIDA: Rápida primero, MD5 después (RECOMENDADO)
        
        1. Busca duplicados rápidos (tamaño + nombre + ext)
        2. Confirma con MD5 solo los sospechosos
        3. Actualiza progreso en tiempo real
        
        Args:
            folder_path: Ruta de la carpeta o disco a analizar
            progress_callback: Función para actualizar progreso
            
        Returns:
            Diccionario con hash/clave -> lista de archivos duplicados
        """
        if progress_callback:
            progress_callback("🚀 Iniciando búsqueda híbrida...")
        
        # FASE 1: Búsqueda rápida
        if progress_callback:
            progress_callback("⚡ FASE 1: Búsqueda ultra-rápida (tamaño+nombre+ext)...")
        
        fast_duplicates = self.scan_for_duplicates_fast(folder_path, recursive=recursive)
        
        if not fast_duplicates:
            if progress_callback:
                progress_callback("✅ No se encontraron duplicados")
            return {}
        
        total_fast_groups = len(fast_duplicates)
        if progress_callback:
            progress_callback(f"⚡ FASE 1 completada: {total_fast_groups} grupos sospechosos encontrados")
        
        # FASE 2: Confirmación MD5 solo para sospechosos
        if progress_callback:
            progress_callback("🔍 FASE 2: Confirmando con MD5 (solo sospechosos)...")
        
        confirmed_duplicates = {}
        processed_groups = 0
        
        for fast_key, files_list in fast_duplicates.items():
            processed_groups += 1
            if progress_callback:
                progress_callback(f"🔍 Verificando grupo {processed_groups}/{total_fast_groups} con MD5...")
            
            # Calcular MD5 solo para este grupo
            hash_results = self.hash_manager.calculate_multiple_hashes(files_list, 'md5')
            
            # Agrupar por hash MD5
            md5_groups = defaultdict(list)
            for file_path, hash_value in hash_results.items():
                if hash_value:
                    md5_groups[hash_value].append(file_path)
                    
                    # Actualizar información con hash real
                    if file_path in self.file_info:
                        self.file_info[file_path]['hash'] = hash_value
                        self.file_info[file_path]['algorithm'] = 'md5'
            
            # Agregar solo grupos confirmados con MD5
            for hash_value, confirmed_files in md5_groups.items():
                if len(confirmed_files) > 1:
                    confirmed_duplicates[hash_value] = confirmed_files
        
        self.duplicates_db = confirmed_duplicates
        
        if progress_callback:
            total_confirmed = len(confirmed_duplicates)
            progress_callback(f"✅ HÍBRIDO completado: {total_confirmed} grupos confirmados")
        
        return self.duplicates_db

    def _get_all_files(self, folder_path: Path, recursive: bool = True) -> List[Path]:
        """Obtiene archivos de una carpeta con opción recursiva
        
        Args:
            folder_path: Ruta de la carpeta a analizar
            recursive: Si True, busca en subcarpetas. Si False, solo en la carpeta actual
        """
        files = []

        try:
            if recursive:
                # Buscar recursivamente en todas las subcarpetas
                for item in folder_path.rglob('*'):
                    if item.is_file() and not self._is_system_file(item):
                        files.append(item)
            else:
                # Buscar solo en la carpeta actual (sin entrar en subcarpetas)
                for item in folder_path.glob('*'):
                    if item.is_file() and not self._is_system_file(item):
                        files.append(item)
        except (OSError, PermissionError):
            pass  # Ignorar carpetas sin acceso

        return files

    def _is_system_file(self, file_path: Path) -> bool:
        """Determina si un archivo es del sistema y debe ser ignorado"""
        try:
            # Archivos ocultos del sistema
            if file_path.name.startswith('.') or file_path.name.startswith('$'):
                return True

            # Archivos en carpetas del sistema
            path_str = str(file_path).lower()
            system_paths = [
                'system volume information',
                '$recycle.bin',
                'windows',
                'program files',
                'programdata'
            ]

            for system_path in system_paths:
                if system_path in path_str:
                    return True

        except Exception:
            pass

        return False

    def _group_files_by_size(self, files: List[Path]) -> Dict[int, List[Path]]:
        """Agrupa archivos por tamaño para optimizar el cálculo de hashes"""
        size_groups = defaultdict(list)

        for file_path in files:
            try:
                size = file_path.stat().st_size
                size_groups[size].append(file_path)
            except (OSError, AttributeError):
                continue

        return size_groups

    def get_duplicate_groups_fast(self) -> Dict[str, List[Dict]]:
        """
        Retorna los grupos de duplicados rápidos con información detallada
        
        Returns:
            Diccionario con fast_key -> lista de archivos con metadata
        """
        groups = {}
        
        for fast_key, file_paths in self.fast_duplicates_db.items():
            if len(file_paths) > 1:
                group_info = []
                for file_path in file_paths:
                    info = self.file_info.get(file_path, {})
                    group_info.append({
                        'path': file_path,
                        'name': file_path.name,
                        'size': info.get('size', 0),
                        'date': info.get('date', 0),
                        'extension': info.get('extension', ''),
                        'fast_key': fast_key,
                        'algorithm': 'fast'
                    })
                
                # Ordenar por fecha (más reciente primero)
                group_info.sort(key=lambda x: x['date'], reverse=True)
                groups[fast_key] = group_info
        
        return groups

    def get_duplicate_groups(self) -> Dict[str, List[Dict]]:
        """
        Retorna los grupos de duplicados con información detallada

        Returns:
            Diccionario con hash -> lista de archivos con metadata
        """
        groups = {}

        for hash_value, file_paths in self.duplicates_db.items():
            if len(file_paths) > 1:
                group_info = []
                for file_path in file_paths:
                    info = self.file_info.get(file_path, {})
                    group_info.append({
                        'path': file_path,
                        'name': file_path.name,
                        'size': info.get('size', 0),
                        'date': info.get('date', 0),
                        'hash': hash_value,
                        'algorithm': info.get('algorithm', 'md5')
                    })

                # Ordenar por fecha (más reciente primero)
                group_info.sort(key=lambda x: x['date'], reverse=True)
                groups[hash_value] = group_info

        return groups

    def calculate_space_saved(self) -> int:
        """
        Calcula el espacio que se puede recuperar eliminando duplicados

        Returns:
            Espacio en bytes que se puede recuperar
        """
        total_saved = 0

        for hash_value, file_paths in self.duplicates_db.items():
            if len(file_paths) > 1:
                # Mantener el archivo más reciente, eliminar los demás
                group_info = []
                for file_path in file_paths:
                    info = self.file_info.get(file_path, {})
                    group_info.append({
                        'path': file_path,
                        'size': info.get('size', 0),
                        'date': info.get('date', 0)
                    })

                # Ordenar por fecha (más reciente primero)
                group_info.sort(key=lambda x: x['date'], reverse=True)

                # Sumar el tamaño de todos los archivos excepto el más reciente
                for duplicate in group_info[1:]:
                    total_saved += duplicate['size']

        return total_saved

    def get_statistics_fast(self) -> Dict:
        """Retorna estadísticas de los duplicados rápidos encontrados"""
        total_files = sum(len(files) for files in self.fast_duplicates_db.values())
        total_groups = len([g for g in self.fast_duplicates_db.values() if len(g) > 1])
        space_saved = self._calculate_space_saved_fast()
        
        return {
            'total_duplicate_files': total_files,
            'total_duplicate_groups': total_groups,
            'space_saved_bytes': space_saved,
            'space_saved_mb': space_saved / (1024 * 1024),
            'unique_keys': len(self.fast_duplicates_db),
            'method': 'fast'
        }
    
    def _calculate_space_saved_fast(self) -> int:
        """Calcula el espacio que se puede recuperar con duplicados rápidos"""
        total_saved = 0
        
        for fast_key, file_paths in self.fast_duplicates_db.items():
            if len(file_paths) > 1:
                # Mantener el archivo más reciente, eliminar los demás
                group_info = []
                for file_path in file_paths:
                    info = self.file_info.get(file_path, {})
                    group_info.append({
                        'path': file_path,
                        'size': info.get('size', 0),
                        'date': info.get('date', 0)
                    })
                
                # Ordenar por fecha (más reciente primero)
                group_info.sort(key=lambda x: x['date'], reverse=True)
                
                # Sumar el tamaño de todos los archivos excepto el más reciente
                for duplicate in group_info[1:]:
                    total_saved += duplicate['size']
        
        return total_saved

    def get_statistics(self) -> Dict:
        """Retorna estadísticas de los duplicados encontrados"""
        total_files = sum(len(files) for files in self.duplicates_db.values())
        total_groups = len([g for g in self.duplicates_db.values() if len(g) > 1])
        space_saved = self.calculate_space_saved()

        return {
            'total_duplicate_files': total_files,
            'total_duplicate_groups': total_groups,
            'space_saved_bytes': space_saved,
            'space_saved_mb': space_saved / (1024 * 1024),
            'unique_hashes': len(self.duplicates_db)
        }

    def export_results(self, output_path: str) -> bool:
        """
        Exporta los resultados de duplicados a un archivo de texto

        Args:
            output_path: Ruta del archivo de salida

        Returns:
            True si se exportó correctamente
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("🔍 RESULTADOS DE ANÁLISIS DE DUPLICADOS\n")
                f.write("=" * 60 + "\n\n")

                stats = self.get_statistics()
                f.write(f"📊 Estadísticas Generales:\n")
                f.write(f"   • Grupos de duplicados: {stats['total_duplicate_groups']}\n")
                f.write(f"   • Archivos duplicados totales: {stats['total_duplicate_files']}\n")
                f.write(f"   • Espacio recuperable: {stats['space_saved_mb']:.2f} MB\n")
                f.write(f"   • Hashes únicos: {stats['unique_hashes']}\n\n")

                groups = self.get_duplicate_groups()
                for i, (hash_value, files) in enumerate(groups.items(), 1):
                    f.write(f"📁 Grupo {i}: {files[0]['name']}\n")
                    f.write(f"   Hash ({files[0]['algorithm']}): {hash_value[:16]}...\n")
                    f.write(f"   Tamaño: {files[0]['size'] / (1024*1024):.2f} MB\n")
                    f.write("   Archivos:\n")

                    for file_info in files:
                        status = "✅ MÁS RECIENTE" if file_info == files[0] else "❌ DUPLICADO"
                        f.write(f"      • {status}: {file_info['path']}\n")

                    f.write(f"   Espacio a recuperar: {(sum(f['size'] for f in files[1:])) / (1024*1024):.2f} MB\n\n")

            return True

        except Exception:
            return False


class DuplicateScanWorker(QThread):
    """Worker para escanear duplicados en segundo plano - MEJORADO"""

    # Señales
    scan_progress = pyqtSignal(str)
    scan_complete = pyqtSignal(dict, dict)  # duplicates_db, statistics
    duplicates_found = pyqtSignal(dict, dict)  # NUEVA: Actualización en tiempo real
    error_occurred = pyqtSignal(str)

    def __init__(self, folder_path: str, method: str = "fast", algorithms: List[str] = None, recursive: bool = True):
        super().__init__()
        self.folder_path = folder_path
        self.method = method  # "fast", "deep", "hybrid"
        self.algorithms = algorithms or ['md5']
        self.recursive = recursive  # ✅ NUEVO: Control de búsqueda recursiva
        self.duplicate_finder = DuplicateFinder()
        self.is_running = True

    def run(self):
        """Ejecuta el escaneo de duplicados con método seleccionado"""
        try:
            if self.method == "fast":
                self._run_fast_scan()
            elif self.method == "hybrid":
                self._run_hybrid_scan()
            else:  # deep
                self._run_deep_scan()
                
        except Exception as e:
            self.error_occurred.emit(f"❌ Error durante el análisis: {str(e)}")
    
    def _run_fast_scan(self):
        """Ejecuta búsqueda ultra-rápida"""
        self.scan_progress.emit("🚀 Iniciando búsqueda ULTRA-RÁPIDA...")
        self.scan_progress.emit("⚡ Analizando por tamaño + nombre + extensión...")
        
        # Escanear duplicados rápidos
        duplicates = self.duplicate_finder.scan_for_duplicates_fast(self.folder_path, recursive=self.recursive)
        
        if duplicates:
            # Emitir actualización inmediata
            statistics = self.duplicate_finder.get_statistics_fast()
            self.duplicates_found.emit(duplicates, statistics)
        
        self.scan_progress.emit("✅ Búsqueda rápida completada")
        statistics = self.duplicate_finder.get_statistics_fast()
        self.scan_complete.emit(duplicates, statistics)
    
    def _run_hybrid_scan(self):
        """Ejecuta búsqueda híbrida con actualizaciones en tiempo real"""
        def progress_callback(message):
            if self.is_running:
                self.scan_progress.emit(message)
        
        # Escanear con callback de progreso
        duplicates = self.duplicate_finder.scan_for_duplicates_hybrid(
            self.folder_path, 
            progress_callback,
            recursive=self.recursive
        )
        
        if duplicates:
            statistics = self.duplicate_finder.get_statistics()
            self.duplicates_found.emit(duplicates, statistics)
        
        statistics = self.duplicate_finder.get_statistics()
        self.scan_complete.emit(duplicates, statistics)
    
    def _run_deep_scan(self):
        """Ejecuta búsqueda profunda (MD5 completo)"""
        self.scan_progress.emit("🔍 Iniciando búsqueda PROFUNDA (MD5)...")
        self.scan_progress.emit("📁 Analizando archivos...")
        
        duplicates = self.duplicate_finder.scan_for_duplicates(self.folder_path, self.algorithms, recursive=self.recursive)
        
        if duplicates:
            statistics = self.duplicate_finder.get_statistics()
            self.duplicates_found.emit(duplicates, statistics)
        
        self.scan_progress.emit("✅ Búsqueda profunda completada")
        statistics = self.duplicate_finder.get_statistics()
        self.scan_complete.emit(duplicates, statistics)

    def stop(self):
        """Detiene el worker"""
        self.is_running = False
