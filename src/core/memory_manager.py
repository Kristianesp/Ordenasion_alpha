#!/usr/bin/env python3
"""
Gestor de Memoria Inteligente para el Organizador de Archivos
Sistema automático de limpieza y optimización de memoria
"""

import gc
import threading
import time
import weakref
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class MemoryEventType(Enum):
    """Tipos de eventos de memoria"""
    CLEANUP_STARTED = "cleanup_started"
    CLEANUP_COMPLETED = "cleanup_completed"
    CACHE_CLEARED = "cache_cleared"
    WORKER_TERMINATED = "worker_terminated"
    MEMORY_WARNING = "memory_warning"
    MEMORY_OPTIMIZED = "memory_optimized"


@dataclass
class MemoryStats:
    """Estadísticas de memoria"""
    total_objects: int
    cache_size_mb: float
    active_workers: int
    memory_usage_mb: float
    timestamp: float


class MemoryManager(QObject):
    """
    Gestor inteligente de memoria con limpieza automática
    Monitorea y optimiza el uso de memoria de la aplicación
    """
    
    # Señales para comunicación
    memory_warning = pyqtSignal(str, float)  # warning_type, memory_mb
    cleanup_completed = pyqtSignal(MemoryStats)
    optimization_completed = pyqtSignal(MemoryStats)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # === CONFIGURACIÓN ===
        self.max_cache_size_mb = 100  # Máximo 100MB de caché
        self.max_workers = 3  # Máximo 3 workers simultáneos
        self.cleanup_interval_ms = 30000  # Limpieza cada 30 segundos
        self.memory_warning_threshold_mb = 200  # Advertencia a 200MB
        
        # === REGISTROS ===
        self.caches: Dict[str, Dict[str, Any]] = {}
        self.workers: Dict[str, Any] = {}
        self.temp_files: List[Path] = []
        self.weak_refs: List[weakref.ref] = []
        
        # === LOCKING ===
        self.lock = threading.RLock()
        
        # === TIMERS ===
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.perform_cleanup)
        self.cleanup_timer.start(self.cleanup_interval_ms)
        
        # === ESTADÍSTICAS ===
        self.stats_history: List[MemoryStats] = []
        self.max_stats_history = 50
        
        # Inicializar
        self._initialize_monitoring()
    
    def _initialize_monitoring(self):
        """Inicializa el monitoreo de memoria"""
        try:
            # Registrar caché inicial
            self.register_cache("application_state", {})
            self.register_cache("theme_cache", {})
            self.register_cache("disk_info_cache", {})
            
            # Log inicial
            self._log_memory_event(MemoryEventType.CLEANUP_STARTED, {
                "action": "initialization",
                "max_cache_mb": self.max_cache_size_mb
            })
            
        except Exception as e:
            print(f"Error inicializando MemoryManager: {e}")
    
    def register_cache(self, cache_name: str, initial_data: Dict[str, Any] = None):
        """Registra un nuevo caché para monitoreo"""
        with self.lock:
            if cache_name not in self.caches:
                self.caches[cache_name] = {
                    "data": initial_data or {},
                    "created_at": time.time(),
                    "last_accessed": time.time(),
                    "access_count": 0,
                    "size_bytes": 0
                }
                
                self._log_memory_event(MemoryEventType.CACHE_CLEARED, {
                    "cache_name": cache_name,
                    "action": "registered"
                })
    
    def get_cache(self, cache_name: str, key: str = None) -> Optional[Any]:
        """Obtiene datos del caché con estadísticas"""
        with self.lock:
            if cache_name not in self.caches:
                return None
            
            cache_info = self.caches[cache_name]
            cache_info["last_accessed"] = time.time()
            cache_info["access_count"] += 1
            
            if key is None:
                return cache_info["data"]
            else:
                return cache_info["data"].get(key)
    
    def set_cache(self, cache_name: str, key: str, value: Any):
        """Establece datos en el caché con estadísticas"""
        with self.lock:
            if cache_name not in self.caches:
                self.register_cache(cache_name)
            
            cache_info = self.caches[cache_name]
            cache_info["data"][key] = value
            cache_info["last_accessed"] = time.time()
            
            # Calcular tamaño aproximado
            try:
                import sys
                cache_info["size_bytes"] = sys.getsizeof(cache_info["data"])
            except:
                cache_info["size_bytes"] = 0
    
    def clear_cache(self, cache_name: str = None):
        """Limpia un caché específico o todos los cachés"""
        with self.lock:
            if cache_name:
                if cache_name in self.caches:
                    self.caches[cache_name]["data"].clear()
                    self.caches[cache_name]["size_bytes"] = 0
                    
                    self._log_memory_event(MemoryEventType.CACHE_CLEARED, {
                        "cache_name": cache_name,
                        "action": "cleared"
                    })
            else:
                for name in self.caches:
                    self.caches[name]["data"].clear()
                    self.caches[name]["size_bytes"] = 0
                
                self._log_memory_event(MemoryEventType.CACHE_CLEARED, {
                    "cache_name": "all",
                    "action": "cleared"
                })
    
    def register_worker(self, worker_id: str, worker):
        """Registra un worker para monitoreo"""
        with self.lock:
            self.workers[worker_id] = {
                "worker": worker,
                "started_at": time.time(),
                "type": type(worker).__name__
            }
            
            # Verificar límite de workers
            if len(self.workers) > self.max_workers:
                self._log_memory_event(MemoryEventType.MEMORY_WARNING, {
                    "warning_type": "too_many_workers",
                    "current_count": len(self.workers),
                    "max_allowed": self.max_workers
                })
    
    def unregister_worker(self, worker_id: str):
        """Desregistra un worker completado"""
        with self.lock:
            if worker_id in self.workers:
                worker_info = self.workers[worker_id]
                del self.workers[worker_id]
                
                self._log_memory_event(MemoryEventType.WORKER_TERMINATED, {
                    "worker_id": worker_id,
                    "duration": time.time() - worker_info["started_at"],
                    "type": worker_info["type"]
                })
    
    def register_temp_file(self, file_path: Path):
        """Registra un archivo temporal para limpieza"""
        with self.lock:
            if file_path not in self.temp_files:
                self.temp_files.append(file_path)
    
    def cleanup_temp_files(self):
        """Limpia archivos temporales registrados"""
        with self.lock:
            cleaned_files = []
            for file_path in self.temp_files[:]:  # Copia para iterar
                try:
                    if file_path.exists():
                        file_path.unlink()
                        cleaned_files.append(str(file_path))
                    self.temp_files.remove(file_path)
                except Exception as e:
                    print(f"Error limpiando archivo temporal {file_path}: {e}")
            
            if cleaned_files:
                self._log_memory_event(MemoryEventType.CLEANUP_COMPLETED, {
                    "action": "temp_files_cleaned",
                    "files_count": len(cleaned_files)
                })
    
    def register_weak_ref(self, obj: Any):
        """Registra una referencia débil para limpieza automática"""
        with self.lock:
            weak_ref = weakref.ref(obj, self._weak_ref_callback)
            self.weak_refs.append(weak_ref)
    
    def _weak_ref_callback(self, weak_ref):
        """Callback para referencias débiles eliminadas"""
        with self.lock:
            if weak_ref in self.weak_refs:
                self.weak_refs.remove(weak_ref)
    
    def perform_cleanup(self):
        """Realiza limpieza automática de memoria"""
        try:
            self._log_memory_event(MemoryEventType.CLEANUP_STARTED, {
                "action": "automatic_cleanup"
            })
            
            # Limpiar cachés antiguos
            self._cleanup_old_caches()
            
            # Limpiar archivos temporales
            self.cleanup_temp_files()
            
            # Limpiar referencias débiles muertas
            self._cleanup_dead_weak_refs()
            
            # Forzar garbage collection
            collected = gc.collect()
            
            # Obtener estadísticas finales
            stats = self.get_memory_stats()
            self.stats_history.append(stats)
            
            # Mantener solo el historial reciente
            if len(self.stats_history) > self.max_stats_history:
                self.stats_history = self.stats_history[-self.max_stats_history:]
            
            # Emitir evento de completado
            self.cleanup_completed.emit(stats)
            
            self._log_memory_event(MemoryEventType.CLEANUP_COMPLETED, {
                "action": "automatic_cleanup",
                "objects_collected": collected,
                "cache_size_mb": stats.cache_size_mb,
                "active_workers": stats.active_workers
            })
            
        except Exception as e:
            print(f"Error en limpieza automática: {e}")
    
    def _cleanup_old_caches(self):
        """Limpia cachés que no se han usado recientemente"""
        current_time = time.time()
        cache_timeout = 300  # 5 minutos
        
        with self.lock:
            caches_to_clear = []
            for cache_name, cache_info in self.caches.items():
                if current_time - cache_info["last_accessed"] > cache_timeout:
                    caches_to_clear.append(cache_name)
            
            for cache_name in caches_to_clear:
                self.clear_cache(cache_name)
    
    def _cleanup_dead_weak_refs(self):
        """Limpia referencias débiles que ya no apuntan a objetos válidos"""
        with self.lock:
            alive_refs = []
            for weak_ref in self.weak_refs:
                if weak_ref() is not None:  # Verificar si el objeto sigue vivo
                    alive_refs.append(weak_ref)
            
            self.weak_refs = alive_refs
    
    def get_memory_stats(self) -> MemoryStats:
        """Obtiene estadísticas actuales de memoria"""
        with self.lock:
            # Calcular tamaño total de cachés
            total_cache_size = sum(
                cache_info["size_bytes"] for cache_info in self.caches.values()
            )
            cache_size_mb = total_cache_size / (1024 * 1024)
            
            # Contar objetos en memoria
            total_objects = len(gc.get_objects())
            
            # Obtener uso de memoria aproximado
            try:
                import psutil
                process = psutil.Process()
                memory_usage_mb = process.memory_info().rss / (1024 * 1024)
            except ImportError:
                memory_usage_mb = 0  # Fallback si psutil no está disponible
            
            return MemoryStats(
                total_objects=total_objects,
                cache_size_mb=cache_size_mb,
                active_workers=len(self.workers),
                memory_usage_mb=memory_usage_mb,
                timestamp=time.time()
            )
    
    def optimize_memory(self):
        """Optimización manual de memoria"""
        try:
            self._log_memory_event(MemoryEventType.CLEANUP_STARTED, {
                "action": "manual_optimization"
            })
            
            # Limpieza completa
            self.perform_cleanup()
            
            # Limpiar cachés grandes
            with self.lock:
                for cache_name, cache_info in self.caches.items():
                    if cache_info["size_bytes"] > 10 * 1024 * 1024:  # 10MB
                        self.clear_cache(cache_name)
            
            # Forzar múltiples ciclos de garbage collection
            for _ in range(3):
                gc.collect()
            
            # Estadísticas finales
            stats = self.get_memory_stats()
            self.optimization_completed.emit(stats)
            
            self._log_memory_event(MemoryEventType.MEMORY_OPTIMIZED, {
                "action": "manual_optimization",
                "final_stats": {
                    "objects": stats.total_objects,
                    "cache_mb": stats.cache_size_mb,
                    "memory_mb": stats.memory_usage_mb
                }
            })
            
        except Exception as e:
            print(f"Error en optimización de memoria: {e}")
    
    def _log_memory_event(self, event_type: MemoryEventType, data: Dict[str, Any]):
        """Registra eventos de memoria para debugging"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] MEMORY: {event_type.value} - {data}")
    
    def get_stats_history(self) -> List[MemoryStats]:
        """Obtiene el historial de estadísticas"""
        with self.lock:
            return self.stats_history.copy()
    
    def cleanup(self):
        """Limpieza completa del gestor de memoria"""
        try:
            # Detener timer
            self.cleanup_timer.stop()
            
            # Terminar todos los workers
            with self.lock:
                for worker_id, worker_info in self.workers.items():
                    try:
                        worker = worker_info["worker"]
                        if hasattr(worker, 'terminate'):
                            worker.terminate()
                        elif hasattr(worker, 'stop'):
                            worker.stop()
                    except Exception as e:
                        print(f"Error terminando worker {worker_id}: {e}")
                
                self.workers.clear()
            
            # Limpiar todos los cachés
            self.clear_cache()
            
            # Limpiar archivos temporales
            self.cleanup_temp_files()
            
            # Limpiar referencias débiles
            self.weak_refs.clear()
            
            # Limpieza final
            gc.collect()
            
            self._log_memory_event(MemoryEventType.CLEANUP_COMPLETED, {
                "action": "final_cleanup"
            })
            
        except Exception as e:
            print(f"Error en limpieza final: {e}")


# Instancia global del gestor de memoria
memory_manager = MemoryManager()
