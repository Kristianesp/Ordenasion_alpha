#!/usr/bin/env python3
"""
Gestor de Hashes para el Organizador de Archivos
Maneja el cálculo de hashes MD5/SHA256 para detección de duplicados
MEJORADO: Con caché de hashes y procesamiento paralelo
"""

import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt6.QtCore import QThread, pyqtSignal

from .hash_cache import HashCache


class HashManager:
    """Gestor principal de hashes para archivos con caché inteligente"""

    def __init__(self, use_cache: bool = True):
        self.supported_algorithms = {
            'md5': hashlib.md5,
            'sha256': hashlib.sha256
        }
        self.use_cache = use_cache
        self.cache = HashCache() if use_cache else None

    def calculate_file_hash(self, file_path: Path, algorithm: str = 'md5', chunk_size: int = 8192, 
                           max_size_mb: int = 5000, timeout_seconds: int = 300) -> Optional[str]:
        """
        Calcula el hash de un archivo usando el algoritmo especificado
        MEJORADO: Con caché, límites de seguridad y hash parcial para archivos gigantes

        Args:
            file_path: Ruta del archivo
            algorithm: Algoritmo a usar ('md5' o 'sha256')
            chunk_size: Tamaño de chunk para archivos grandes
            max_size_mb: Tamaño máximo en MB antes de usar hash parcial
            timeout_seconds: Timeout máximo para calcular hash

        Returns:
            Hash del archivo o None si hay error
        """
        if not file_path.exists() or not file_path.is_file():
            return None

        try:
            # 🚀 MEJORA: Intentar obtener del caché primero
            if self.use_cache and self.cache:
                cached_hash = self.cache.get_hash(file_path, algorithm)
                if cached_hash:
                    return cached_hash
            
            # Verificar tamaño del archivo
            file_size = file_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            # 🚀 MEJORA: Para archivos muy grandes, usar hash parcial
            if file_size_mb > max_size_mb:
                hash_value = self._calculate_partial_hash(file_path, algorithm, chunk_size)
            else:
                # Hash completo normal
                hash_func = self.supported_algorithms.get(algorithm.lower())
                if not hash_func:
                    return None

                hash_obj = hash_func()
                
                import time
                start_time = time.time()

                with open(file_path, 'rb') as f:
                    while chunk := f.read(chunk_size):
                        # 🚀 MEJORA: Verificar timeout
                        if time.time() - start_time > timeout_seconds:
                            raise TimeoutError(f"Hash calculation timeout: {file_path}")
                        hash_obj.update(chunk)

                hash_value = hash_obj.hexdigest()
            
            # 🚀 MEJORA: Guardar en caché
            if self.use_cache and self.cache and hash_value:
                self.cache.save_hash(file_path, hash_value, algorithm)
            
            return hash_value

        except (OSError, PermissionError, IOError, TimeoutError) as e:
            return None
    
    def _calculate_partial_hash(self, file_path: Path, algorithm: str = 'md5', 
                                chunk_size: int = 8192, sample_size_mb: int = 10) -> Optional[str]:
        """
        Calcula hash parcial para archivos muy grandes
        Lee: primeros 5MB + últimos 5MB + tamaño del archivo
        Suficiente para identificar duplicados sin leer todo el archivo
        
        Args:
            file_path: Ruta del archivo
            algorithm: Algoritmo a usar
            chunk_size: Tamaño de chunk
            sample_size_mb: Tamaño total a muestrear (dividido entre inicio y fin)
        
        Returns:
            Hash parcial del archivo
        """
        try:
            hash_func = self.supported_algorithms.get(algorithm.lower())
            if not hash_func:
                return None
            
            hash_obj = hash_func()
            file_size = file_path.stat().st_size
            
            # Incluir tamaño del archivo en el hash
            hash_obj.update(str(file_size).encode())
            
            sample_bytes = sample_size_mb * 1024 * 1024
            half_sample = sample_bytes // 2
            
            with open(file_path, 'rb') as f:
                # Leer primeros MB
                bytes_read = 0
                while bytes_read < half_sample:
                    chunk = f.read(min(chunk_size, half_sample - bytes_read))
                    if not chunk:
                        break
                    hash_obj.update(chunk)
                    bytes_read += len(chunk)
                
                # Saltar al final y leer últimos MB
                if file_size > half_sample * 2:
                    f.seek(file_size - half_sample)
                    bytes_read = 0
                    while bytes_read < half_sample:
                        chunk = f.read(min(chunk_size, half_sample - bytes_read))
                        if not chunk:
                            break
                        hash_obj.update(chunk)
                        bytes_read += len(chunk)
            
            return hash_obj.hexdigest()
            
        except (OSError, PermissionError, IOError):
            return None

    def calculate_multiple_hashes(self, file_paths: List[Path], algorithm: str = 'md5', 
                                  max_workers: int = 4) -> Dict[Path, Optional[str]]:
        """
        Calcula hashes para múltiples archivos
        🚀 MEJORADO: Procesamiento paralelo con ThreadPoolExecutor (3-4x más rápido)

        Args:
            file_paths: Lista de rutas de archivos
            algorithm: Algoritmo a usar
            max_workers: Número de hilos paralelos (por defecto 4)

        Returns:
            Diccionario con ruta -> hash
        """
        results = {}
        
        # Si hay pocos archivos, procesamiento secuencial es más eficiente
        if len(file_paths) < 10:
            for file_path in file_paths:
                results[file_path] = self.calculate_file_hash(file_path, algorithm)
            return results
        
        # 🚀 MEJORA: Procesamiento paralelo para muchos archivos
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Enviar todas las tareas
            future_to_path = {
                executor.submit(self.calculate_file_hash, path, algorithm): path 
                for path in file_paths
            }
            
            # Recolectar resultados a medida que se completan
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    hash_value = future.result()
                    results[path] = hash_value
                except Exception as e:
                    results[path] = None
        
        return results

    def get_file_size_and_date(self, file_path: Path) -> Tuple[int, float]:
        """
        Obtiene el tamaño y fecha de modificación de un archivo

        Returns:
            Tupla (tamaño_en_bytes, timestamp_modificacion)
        """
        try:
            stat = file_path.stat()
            return stat.st_size, stat.st_mtime
        except (OSError, AttributeError):
            return 0, 0.0

    def is_large_file(self, file_path: Path, threshold_mb: int = 100) -> bool:
        """
        Determina si un archivo es considerado grande

        Args:
            file_path: Ruta del archivo
            threshold_mb: Umbral en MB

        Returns:
            True si el archivo es grande
        """
        try:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            return size_mb > threshold_mb
        except (OSError, AttributeError):
            return False


class HashCalculationWorker(QThread):
    """Worker para calcular hashes en segundo plano"""

    # Señales
    hash_calculated = pyqtSignal(Path, str, str)  # file_path, hash, algorithm
    calculation_complete = pyqtSignal(dict)  # results dict
    error_occurred = pyqtSignal(str)
    progress_update = pyqtSignal(int, int)  # current, total

    def __init__(self, file_paths: List[Path], algorithm: str = 'md5'):
        super().__init__()
        self.file_paths = file_paths
        self.algorithm = algorithm
        self.hash_manager = HashManager()
        self.is_running = True

    def run(self):
        """Ejecuta el cálculo de hashes"""
        try:
            results = {}
            total_files = len(self.file_paths)

            for i, file_path in enumerate(self.file_paths):
                if not self.is_running:
                    break

                try:
                    hash_value = self.hash_manager.calculate_file_hash(file_path, self.algorithm)

                    if hash_value:
                        results[file_path] = hash_value
                        self.hash_calculated.emit(file_path, hash_value, self.algorithm)
                    else:
                        results[file_path] = None

                except Exception as e:
                    self.error_occurred.emit(f"Error procesando {file_path}: {str(e)}")
                    results[file_path] = None

                # Actualizar progreso
                self.progress_update.emit(i + 1, total_files)

            self.calculation_complete.emit(results)

        except Exception as e:
            self.error_occurred.emit(f"Error durante el cálculo: {str(e)}")

    def stop(self):
        """Detiene el worker"""
        self.is_running = False
