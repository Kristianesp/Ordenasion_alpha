#!/usr/bin/env python3
"""
Estado Centralizado de la Aplicación
Patrón Singleton + Observer para gestión unificada del estado
"""

import threading
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal

from .category_manager import CategoryManager
from .disk_manager import DiskManager
from src.utils.app_config import AppConfig


class EventType(Enum):
    """Tipos de eventos del sistema"""
    STATE_CHANGED = "state_changed"
    THEME_CHANGED = "theme_changed"
    CATEGORIES_UPDATED = "categories_updated"
    DISK_SELECTED = "disk_selected"
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_COMPLETED = "analysis_completed"
    WORKER_STARTED = "worker_started"
    WORKER_FINISHED = "worker_finished"
    MEMORY_CLEANUP = "memory_cleanup"


@dataclass
class ApplicationEvent:
    """Evento del sistema con datos"""
    event_type: EventType
    data: Dict[str, Any]
    timestamp: float
    source: str


class ApplicationState(QObject):
    """
    Estado centralizado de la aplicación con patrón Singleton + Observer
    Thread-safe y optimizado para performance
    """
    
    # Señales Qt para comunicación con UI
    state_changed = pyqtSignal(ApplicationEvent)
    theme_changed = pyqtSignal(str)
    categories_updated = pyqtSignal()
    disk_selected = pyqtSignal(str)
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Implementación Singleton thread-safe"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        super().__init__()
        
        # === COMPONENTES PRINCIPALES ===
        self.category_manager: Optional[CategoryManager] = None
        self.disk_manager: Optional[DiskManager] = None
        self.app_config: Optional[AppConfig] = None
        
        # === ESTADO DE LA APLICACIÓN ===
        self.current_theme: str = "elegant_light"
        self.current_font_size: int = 12
        self.current_disk: Optional[str] = None
        self.is_analysis_running: bool = False
        self.is_organization_running: bool = False
        
        # === GESTIÓN DE WORKERS ===
        self.active_workers: Dict[str, Any] = {}
        self.worker_lock = threading.Lock()
        
        # === CACHÉS Y MEMORIA ===
        self.caches: Dict[str, Any] = {}
        self.cache_lock = threading.Lock()
        
        # === OBSERVADORES ===
        self._observers: List[Callable[[ApplicationEvent], None]] = []
        self._observer_lock = threading.Lock()
        
        # === INICIALIZACIÓN ===
        self._initialize_components()
        self._initialized = True
        
        # Emitir evento de inicialización
        self._emit_event(EventType.STATE_CHANGED, {
            "component": "ApplicationState",
            "action": "initialized"
        }, "ApplicationState")
    
    def _initialize_components(self):
        """Inicializa los componentes principales de forma segura"""
        try:
            # Inicializar configuración
            self.app_config = AppConfig()
            
            # Sincronizar con ThemeManager (temporalmente comentado)
            # self.current_theme = theme_manager.current_theme
            # self.current_font_size = theme_manager.current_font_size
            self.current_theme = "🌞 Claro Elegante"  # Valor por defecto
            self.current_font_size = 12  # Valor por defecto
            
            # Inicializar gestor de categorías
            self.category_manager = CategoryManager()
            
            # DiskManager se inicializa de forma lazy cuando se necesite
            self.disk_manager = None
            
            self._emit_event(EventType.STATE_CHANGED, {
                "component": "components",
                "action": "initialized",
                "theme": self.current_theme,
                "font_size": self.current_font_size
            }, "ApplicationState")
            
        except Exception as e:
            self._emit_event(EventType.STATE_CHANGED, {
                "component": "components",
                "action": "initialization_error",
                "error": str(e)
            }, "ApplicationState")
    
    def get_disk_manager(self) -> Optional[DiskManager]:
        """Obtiene DiskManager con inicialización lazy thread-safe"""
        if self.disk_manager is None:
            with self._lock:
                if self.disk_manager is None:
                    try:
                        from .disk_manager import DiskManager
                        self.disk_manager = DiskManager()
                        self._emit_event(EventType.STATE_CHANGED, {
                            "component": "disk_manager",
                            "action": "initialized"
                        }, "ApplicationState")
                    except Exception as e:
                        self._emit_event(EventType.STATE_CHANGED, {
                            "component": "disk_manager",
                            "action": "initialization_error",
                            "error": str(e)
                        }, "ApplicationState")
                        return None
        return self.disk_manager
    
    def set_theme(self, theme: str):
        """Cambia el tema de la aplicación usando el ThemeManager optimizado"""
        if theme != self.current_theme:
            old_theme = self.current_theme
            
            # Usar ThemeManager optimizado (temporalmente comentado)
            # if theme_manager.set_theme(theme):
            self.current_theme = theme
                
            # Guardar en configuración
            if self.app_config:
                self.app_config.set_theme(theme)
                
            # Emitir eventos
            self._emit_event(EventType.THEME_CHANGED, {
                "old_theme": old_theme,
                "new_theme": theme
            }, "ApplicationState")
                
            self.theme_changed.emit(theme)
            # else:
            #     print(f"❌ No se pudo cambiar el tema a: {theme}")
    
    def set_font_size(self, font_size: int):
        """Cambia el tamaño de fuente usando el ThemeManager optimizado"""
        if font_size != self.current_font_size:
            old_size = self.current_font_size
            
            # Usar ThemeManager optimizado (temporalmente comentado)
            # if theme_manager.set_font_size(font_size):
            self.current_font_size = font_size
                
            # Guardar en configuración
            if self.app_config:
                self.app_config.set_font_size(font_size)
                
            self._emit_event(EventType.STATE_CHANGED, {
                "component": "font_size",
                "old_size": old_size,
                "new_size": font_size
            }, "ApplicationState")
            # else:
            #     print(f"❌ No se pudo cambiar el tamaño de fuente a: {font_size}")
    
    def set_current_disk(self, disk_path: str):
        """Establece el disco actualmente seleccionado"""
        if disk_path != self.current_disk:
            old_disk = self.current_disk
            self.current_disk = disk_path
            
            self._emit_event(EventType.DISK_SELECTED, {
                "old_disk": old_disk,
                "new_disk": disk_path
            }, "ApplicationState")
            
            self.disk_selected.emit(disk_path)
    
    def register_worker(self, worker_id: str, worker):
        """Registra un worker activo"""
        with self.worker_lock:
            self.active_workers[worker_id] = worker
            
            self._emit_event(EventType.WORKER_STARTED, {
                "worker_id": worker_id,
                "worker_type": type(worker).__name__
            }, "ApplicationState")
    
    def unregister_worker(self, worker_id: str):
        """Desregistra un worker completado"""
        with self.worker_lock:
            if worker_id in self.active_workers:
                del self.active_workers[worker_id]
                
                self._emit_event(EventType.WORKER_FINISHED, {
                    "worker_id": worker_id
                }, "ApplicationState")
    
    def get_active_workers(self) -> Dict[str, Any]:
        """Obtiene lista de workers activos"""
        with self.worker_lock:
            return self.active_workers.copy()
    
    def terminate_all_workers(self):
        """Termina todos los workers activos"""
        with self.worker_lock:
            for worker_id, worker in self.active_workers.items():
                try:
                    if hasattr(worker, 'terminate'):
                        worker.terminate()
                    elif hasattr(worker, 'stop'):
                        worker.stop()
                except Exception as e:
                    self._emit_event(EventType.STATE_CHANGED, {
                        "component": "worker_termination",
                        "worker_id": worker_id,
                        "error": str(e)
                    }, "ApplicationState")
            
            self.active_workers.clear()
    
    def set_cache(self, cache_name: str, data: Any):
        """Establece datos en caché"""
        with self.cache_lock:
            self.caches[cache_name] = data
    
    def get_cache(self, cache_name: str) -> Optional[Any]:
        """Obtiene datos del caché"""
        with self.cache_lock:
            return self.caches.get(cache_name)
    
    def clear_cache(self, cache_name: Optional[str] = None):
        """Limpia caché específico o todos los cachés"""
        with self.cache_lock:
            if cache_name:
                if cache_name in self.caches:
                    del self.caches[cache_name]
            else:
                self.caches.clear()
            
            self._emit_event(EventType.MEMORY_CLEANUP, {
                "cache_name": cache_name or "all",
                "action": "cleared"
            }, "ApplicationState")
    
    def add_observer(self, observer: Callable[[ApplicationEvent], None]):
        """Añade un observador del estado"""
        with self._observer_lock:
            if observer not in self._observers:
                self._observers.append(observer)
    
    def remove_observer(self, observer: Callable[[ApplicationEvent], None]):
        """Remueve un observador del estado"""
        with self._observer_lock:
            if observer in self._observers:
                self._observers.remove(observer)
    
    def _emit_event(self, event_type: EventType, data: Dict[str, Any], source: str):
        """Emite un evento a todos los observadores"""
        import time
        
        event = ApplicationEvent(
            event_type=event_type,
            data=data,
            timestamp=time.time(),
            source=source
        )
        
        # Emitir señal Qt
        self.state_changed.emit(event)
        
        # Notificar observadores Python
        with self._observer_lock:
            for observer in self._observers:
                try:
                    observer(event)
                except Exception as e:
                    # Log error pero no interrumpir otros observadores
                    from ..utils.logger import error
                    error(f"Error en observador: {e}")
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Obtiene un resumen del estado actual"""
        return {
            "theme": self.current_theme,
            "font_size": self.current_font_size,
            "current_disk": self.current_disk,
            "active_workers": len(self.active_workers),
            "cache_count": len(self.caches),
            "observers_count": len(self._observers),
            "is_analysis_running": self.is_analysis_running,
            "is_organization_running": self.is_organization_running
        }
    
    def cleanup(self):
        """Limpieza completa del estado"""
        # Terminar workers
        self.terminate_all_workers()
        
        # Limpiar cachés
        self.clear_cache()
        
        # Limpiar observadores
        with self._observer_lock:
            self._observers.clear()
        
        # Limpiar ThemeManager (temporalmente comentado)
        # theme_manager.cleanup()
        
        self._emit_event(EventType.STATE_CHANGED, {
            "component": "ApplicationState",
            "action": "cleanup_completed"
        }, "ApplicationState")


# Instancia global del estado
app_state = ApplicationState()
