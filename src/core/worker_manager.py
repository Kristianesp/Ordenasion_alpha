#!/usr/bin/env python3
"""
Gestor Centralizado de Workers para el Organizador de Archivos
Controla la ejecución, cancelación y limpieza de workers
"""

import threading
import time
from typing import Dict, Any, Optional, List, Type
from dataclasses import dataclass
from enum import Enum
from PyQt6.QtCore import QObject, QThread, pyqtSignal

from .application_state import app_state, EventType
from .memory_manager import memory_manager


class WorkerStatus(Enum):
    """Estados de un worker"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class WorkerInfo:
    """Información de un worker"""
    worker_id: str
    worker_type: str
    worker: QThread
    status: WorkerStatus
    started_at: float
    completed_at: Optional[float] = None
    error_message: Optional[str] = None
    progress: float = 0.0


class WorkerManager(QObject):
    """
    Gestor centralizado de workers con control de concurrencia
    Evita ejecución simultánea de workers incompatibles
    """
    
    # Señales para comunicación
    worker_started = pyqtSignal(str, str)  # worker_id, worker_type
    worker_completed = pyqtSignal(str, bool)  # worker_id, success
    worker_progress = pyqtSignal(str, float)  # worker_id, progress
    worker_error = pyqtSignal(str, str)  # worker_id, error_message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # === CONFIGURACIÓN ===
        self.max_concurrent_workers = 2  # Máximo 2 workers simultáneos
        self.worker_timeout = 300  # Timeout de 5 minutos
        
        # === REGISTROS ===
        self.active_workers: Dict[str, WorkerInfo] = {}
        self.worker_queue: List[WorkerInfo] = []
        self.worker_history: List[WorkerInfo] = []
        
        # === LOCKING ===
        self.lock = threading.RLock()
        
        # === CONFIGURACIÓN DE WORKERS ===
        self.worker_configs = {
            "AnalysisWorker": {
                "max_concurrent": 1,
                "priority": 1,
                "timeout": 180
            },
            "OrganizeWorker": {
                "max_concurrent": 1,
                "priority": 2,
                "timeout": 300
            },
            "DuplicateScanWorker": {
                "max_concurrent": 1,
                "priority": 3,
                "timeout": 600
            },
            "HashCalculationWorker": {
                "max_concurrent": 2,
                "priority": 4,
                "timeout": 120
            }
        }
        
        # Conectar con ApplicationState
        app_state.add_observer(self._on_state_changed)
    
    def _on_state_changed(self, event):
        """Maneja cambios del estado de la aplicación"""
        if event.event_type == EventType.WORKER_STARTED:
            worker_id = event.data.get("worker_id")
            if worker_id:
                self._update_worker_status(worker_id, WorkerStatus.RUNNING)
        
        elif event.event_type == EventType.WORKER_FINISHED:
            worker_id = event.data.get("worker_id")
            if worker_id:
                self._update_worker_status(worker_id, WorkerStatus.COMPLETED)
    
    def start_worker(self, worker_id: str, worker: QThread, worker_type: str) -> bool:
        """
        Inicia un worker con control de concurrencia
        
        Args:
            worker_id: Identificador único del worker
            worker: Instancia del worker (QThread)
            worker_type: Tipo de worker (nombre de la clase)
        
        Returns:
            bool: True si se inició correctamente, False si no se pudo iniciar
        """
        with self.lock:
            # Verificar si ya existe un worker con este ID
            if worker_id in self.active_workers:
                print(f"Worker {worker_id} ya está activo")
                return False
            
            # Verificar límites de concurrencia
            if not self._can_start_worker(worker_type):
                print(f"No se puede iniciar {worker_type}: límite de concurrencia alcanzado")
                return False
            
            # Crear información del worker
            worker_info = WorkerInfo(
                worker_id=worker_id,
                worker_type=worker_type,
                worker=worker,
                status=WorkerStatus.PENDING,
                started_at=time.time()
            )
            
            # Registrar worker
            self.active_workers[worker_id] = worker_info
            
            # Conectar señales del worker
            self._connect_worker_signals(worker, worker_id)
            
            # Iniciar worker
            try:
                worker.start()
                worker_info.status = WorkerStatus.RUNNING
                
                # Registrar en ApplicationState
                app_state.register_worker(worker_id, worker)
                
                # Registrar en MemoryManager
                memory_manager.register_worker(worker_id, worker)
                
                # Emitir señales
                self.worker_started.emit(worker_id, worker_type)
                
                print(f"Worker {worker_id} ({worker_type}) iniciado correctamente")
                return True
                
            except Exception as e:
                # Error al iniciar
                worker_info.status = WorkerStatus.ERROR
                worker_info.error_message = str(e)
                
                # Limpiar registro
                del self.active_workers[worker_id]
                
                self.worker_error.emit(worker_id, str(e))
                print(f"Error iniciando worker {worker_id}: {e}")
                return False
    
    def _can_start_worker(self, worker_type: str) -> bool:
        """Verifica si se puede iniciar un worker del tipo especificado"""
        config = self.worker_configs.get(worker_type, {})
        max_concurrent = config.get("max_concurrent", 1)
        
        # Contar workers activos del mismo tipo
        same_type_count = sum(
            1 for info in self.active_workers.values()
            if info.worker_type == worker_type and info.status == WorkerStatus.RUNNING
        )
        
        # Verificar límite total de workers
        if len(self.active_workers) >= self.max_concurrent_workers:
            return False
        
        # Verificar límite específico del tipo
        if same_type_count >= max_concurrent:
            return False
        
        return True
    
    def _connect_worker_signals(self, worker: QThread, worker_id: str):
        """Conecta las señales del worker para monitoreo"""
        try:
            # Señales comunes de QThread
            worker.finished.connect(lambda: self._on_worker_finished(worker_id))
            
            # Señales específicas según el tipo de worker
            if hasattr(worker, 'progress_update'):
                worker.progress_update.connect(
                    lambda msg: self._on_worker_progress(worker_id, msg)
                )
            
            if hasattr(worker, 'error_occurred'):
                worker.error_occurred.connect(
                    lambda msg: self._on_worker_error(worker_id, msg)
                )
            
            if hasattr(worker, 'analysis_complete'):
                worker.analysis_complete.connect(
                    lambda *args: self._on_worker_completed(worker_id, True)
                )
            
            if hasattr(worker, 'organize_complete'):
                worker.organize_complete.connect(
                    lambda success, msg: self._on_worker_completed(worker_id, success)
                )
            
            if hasattr(worker, 'duplicates_found'):
                worker.duplicates_found.connect(
                    lambda *args: self._on_worker_progress(worker_id, "Duplicados encontrados")
                )
            
        except Exception as e:
            print(f"Error conectando señales del worker {worker_id}: {e}")
    
    def _on_worker_finished(self, worker_id: str):
        """Maneja la finalización de un worker"""
        with self.lock:
            if worker_id in self.active_workers:
                worker_info = self.active_workers[worker_id]
                
                if worker_info.status == WorkerStatus.RUNNING:
                    worker_info.status = WorkerStatus.COMPLETED
                    worker_info.completed_at = time.time()
                
                # Mover a historial
                self.worker_history.append(worker_info)
                
                # Limpiar registro activo
                del self.active_workers[worker_id]
                
                # Desregistrar de ApplicationState
                app_state.unregister_worker(worker_id)
                
                # Desregistrar de MemoryManager
                memory_manager.unregister_worker(worker_id)
                
                # Emitir señal
                success = worker_info.status == WorkerStatus.COMPLETED
                self.worker_completed.emit(worker_id, success)
                
                print(f"Worker {worker_id} finalizado: {worker_info.status.value}")
    
    def _on_worker_progress(self, worker_id: str, message: str):
        """Maneja actualizaciones de progreso del worker"""
        with self.lock:
            if worker_id in self.active_workers:
                worker_info = self.active_workers[worker_id]
                
                # Actualizar progreso (simplificado)
                worker_info.progress = min(worker_info.progress + 0.1, 1.0)
                
                self.worker_progress.emit(worker_id, worker_info.progress)
    
    def _on_worker_error(self, worker_id: str, error_message: str):
        """Maneja errores del worker"""
        with self.lock:
            if worker_id in self.active_workers:
                worker_info = self.active_workers[worker_id]
                worker_info.status = WorkerStatus.ERROR
                worker_info.error_message = error_message
                
                self.worker_error.emit(worker_id, error_message)
                print(f"Error en worker {worker_id}: {error_message}")
    
    def _on_worker_completed(self, worker_id: str, success: bool):
        """Maneja completación exitosa del worker"""
        with self.lock:
            if worker_id in self.active_workers:
                worker_info = self.active_workers[worker_id]
                worker_info.status = WorkerStatus.COMPLETED if success else WorkerStatus.ERROR
                worker_info.completed_at = time.time()
    
    def cancel_worker(self, worker_id: str) -> bool:
        """Cancela un worker activo"""
        with self.lock:
            if worker_id not in self.active_workers:
                return False
            
            worker_info = self.active_workers[worker_id]
            
            try:
                # Intentar cancelar el worker
                if hasattr(worker_info.worker, 'terminate'):
                    worker_info.worker.terminate()
                elif hasattr(worker_info.worker, 'stop'):
                    worker_info.worker.stop()
                
                worker_info.status = WorkerStatus.CANCELLED
                worker_info.completed_at = time.time()
                
                # Limpiar registro
                del self.active_workers[worker_id]
                
                # Desregistrar de managers
                app_state.unregister_worker(worker_id)
                memory_manager.unregister_worker(worker_id)
                
                print(f"Worker {worker_id} cancelado")
                return True
                
            except Exception as e:
                print(f"Error cancelando worker {worker_id}: {e}")
                return False
    
    def cancel_all_workers(self):
        """Cancela todos los workers activos"""
        with self.lock:
            worker_ids = list(self.active_workers.keys())
            
            for worker_id in worker_ids:
                self.cancel_worker(worker_id)
            
            print(f"Cancelados {len(worker_ids)} workers")
    
    def get_worker_status(self, worker_id: str) -> Optional[WorkerStatus]:
        """Obtiene el estado de un worker"""
        with self.lock:
            if worker_id in self.active_workers:
                return self.active_workers[worker_id].status
            return None
    
    def get_active_workers(self) -> Dict[str, WorkerInfo]:
        """Obtiene información de workers activos"""
        with self.lock:
            return self.active_workers.copy()
    
    def get_worker_history(self) -> List[WorkerInfo]:
        """Obtiene el historial de workers"""
        with self.lock:
            return self.worker_history.copy()
    
    def cleanup_old_history(self, max_history: int = 100):
        """Limpia el historial antiguo de workers"""
        with self.lock:
            if len(self.worker_history) > max_history:
                self.worker_history = self.worker_history[-max_history:]
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de workers"""
        with self.lock:
            stats = {
                "active_workers": len(self.active_workers),
                "total_history": len(self.worker_history),
                "workers_by_type": {},
                "workers_by_status": {}
            }
            
            # Contar por tipo
            for worker_info in self.active_workers.values():
                worker_type = worker_info.worker_type
                stats["workers_by_type"][worker_type] = stats["workers_by_type"].get(worker_type, 0) + 1
            
            # Contar por estado
            for worker_info in self.active_workers.values():
                status = worker_info.status.value
                stats["workers_by_status"][status] = stats["workers_by_status"].get(status, 0) + 1
            
            return stats
    
    def cleanup(self):
        """Limpieza completa del gestor de workers"""
        try:
            # Cancelar todos los workers activos
            self.cancel_all_workers()
            
            # Limpiar historial
            self.worker_history.clear()
            
            # Desconectar observador
            app_state.remove_observer(self._on_state_changed)
            
            print("WorkerManager limpiado correctamente")
            
        except Exception as e:
            print(f"Error en limpieza de WorkerManager: {e}")


# Instancia global del gestor de workers
worker_manager = WorkerManager()
