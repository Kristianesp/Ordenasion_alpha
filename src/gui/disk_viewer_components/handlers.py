#!/usr/bin/env python3
"""
Manejadores de Eventos para DiskViewer
Módulo extraído para manejar señales, eventos y lógica de interacción
"""

from typing import Optional, Callable
from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox, QWidget
from PyQt6.QtCore import QTimer


class DiskViewerHandlers:
    """Clase especializada en manejar eventos y señales del DiskViewer"""
    
    @staticmethod
    def create_analyze_handler(widget: QWidget, row: int) -> Callable:
        """Crea un manejador para el botón de analizar disco"""
        def handler():
            try:
                mount_item = widget.disks_table.item(row, 1)
                if mount_item:
                    mountpoint = mount_item.text()
                    widget.log_message(f"🔍 Analizando disco: {mountpoint}")
                    
                    # Emitir señal para que la ventana principal maneje el análisis
                    if hasattr(widget, 'analysis_requested'):
                        widget.analysis_requested.emit(mountpoint)
                    
                    # Actualizar información del disco seleccionado
                    widget.update_selected_disk_info(mountpoint)
            except Exception as e:
                widget.log_message(f"❌ Error al analizar disco: {str(e)}")
                QMessageBox.critical(
                    widget,
                    "Error",
                    f"Error al analizar el disco:\n{str(e)}"
                )
        return handler
    
    @staticmethod
    def on_disk_selection_changed(widget: QWidget):
        """Maneja el cambio de selección en la tabla de discos"""
        try:
            selected_items = widget.disks_table.selectedItems()
            if not selected_items:
                return
            
            # Obtener la fila seleccionada
            current_row = selected_items[0].row()
            
            # Obtener el mountpoint
            mount_item = widget.disks_table.item(current_row, 1)
            if mount_item:
                mountpoint = mount_item.text()
                widget.current_selection = mountpoint
                
                # Emitir señal con la ruta del disco seleccionado
                if hasattr(widget, 'disk_selected'):
                    widget.disk_selected.emit(mountpoint)
                
                # Actualizar información detallada
                widget.update_selected_disk_info(mountpoint)
                
        except Exception as e:
            widget.log_message(f"⚠️ Error en selección de disco: {str(e)}")
    
    @staticmethod
    def on_debounce_timeout(widget: QWidget):
        """Maneja el timeout del debounce para operaciones pesadas"""
        try:
            if widget.pending_analysis:
                mountpoint = widget.pending_analysis
                widget.pending_analysis = None
                
                widget.log_message(f"🔄 Iniciando análisis programado: {mountpoint}")
                
                # Programar análisis pesado
                widget._schedule_heavy_analysis(mountpoint)
        except Exception as e:
            widget.log_message(f"❌ Error en debounce: {str(e)}")
    
    @staticmethod
    def schedule_heavy_analysis(widget: QWidget, mountpoint: str):
        """Programa un análisis pesado con debounce"""
        try:
            # Cancelar cualquier análisis pendiente
            if widget.debounce_timer.isActive():
                widget.debounce_timer.stop()
            
            # Guardar mountpoint pendiente
            widget.pending_analysis = mountpoint
            
            # Iniciar timer de debounce (500ms)
            widget.debounce_timer.start(500)
            
            widget.log_message(f"⏳ Análisis programado: {mountpoint}")
        except Exception as e:
            widget.log_message(f"❌ Error al programar análisis: {str(e)}")
    
    @staticmethod
    def cleanup_cache(widget: QWidget):
        """Limpia la caché SMART manteniendo solo entradas prioritarias"""
        try:
            if not hasattr(widget, '_smart_cache'):
                return
            
            # Mantener solo entradas con prioridad alta (> 70)
            entries_to_remove = []
            for path, priority in getattr(widget, '_cache_priority', {}).items():
                if priority < 70:
                    entries_to_remove.append(path)
            
            for path in entries_to_remove:
                if path in widget._smart_cache:
                    del widget._smart_cache[path]
                if path in getattr(widget, '_cache_priority', {}):
                    del widget._cache_priority[path]
            
            # Reducir prioridad de todas las entradas restantes
            for path in getattr(widget, '_cache_priority', {}):
                widget._cache_priority[path] = max(0, widget._cache_priority[path] - 10)
            
            widget.log_message(f"🧹 Caché limpiada: {len(entries_to_remove)} entradas eliminadas")
        except Exception as e:
            widget.log_message(f"⚠️ Error limpiando caché: {str(e)}")
    
    @staticmethod
    def on_safe_mode_changed(widget: QWidget, enabled: bool):
        """Maneja el cambio del modo seguro"""
        try:
            if hasattr(widget, 'disk_manager') and widget.disk_manager:
                widget.disk_manager.set_safe_mode(enabled)
                widget.log_message(f"🛡️ Modo seguro {'activado' if enabled else 'desactivado'}")
                
                # Actualizar información del sistema
                if hasattr(widget, 'update_system_info'):
                    widget.update_system_info()
        except Exception as e:
            widget.log_message(f"❌ Error al cambiar modo seguro: {str(e)}")
    
    @staticmethod
    def refresh_disks(widget: QWidget):
        """Refresca la información de todos los discos (wrapper para manejo de errores)"""
        try:
            if hasattr(widget, 'refresh_disks'):
                widget.refresh_disks()
        except Exception as e:
            widget.log_message(f"❌ Error al refrescar discos: {str(e)}")
            QMessageBox.critical(
                widget,
                "Error",
                f"Error al actualizar discos:\n{str(e)}"
            )
    
    def __init__(self, disk_viewer=None):
        """Inicializa el manejador con referencia al widget padre"""
        self.disk_viewer = disk_viewer
    
    def on_cell_clicked(self, row: int, column: int):
        """Maneja el click en una celda de la tabla"""
        if self.disk_viewer is None:
            return
        try:
            mount_item = self.disk_viewer.disks_table.item(row, 1)
            if mount_item:
                mountpoint = mount_item.text()
                self.disk_viewer.current_selection = mountpoint
                self.disk_viewer.log_message(f"📁 Disco seleccionado: {mountpoint}")
                
                # Emitir señal con la ruta del disco seleccionado
                if hasattr(self.disk_viewer, 'disk_selected'):
                    self.disk_viewer.disk_selected.emit(mountpoint)
                
                # Actualizar información detallada
                self.disk_viewer.update_selected_disk_info(mountpoint)
        except Exception as e:
            if self.disk_viewer:
                self.disk_viewer.log_message(f"⚠️ Error en selección de disco: {str(e)}")
    
    def refresh_disks(self):
        """Refresca la información de todos los discos"""
        if self.disk_viewer is None:
            return
        try:
            self.disk_viewer._refresh_disks_internal()
        except Exception as e:
            self.disk_viewer.log_message(f"❌ Error al refrescar discos: {str(e)}")
            QMessageBox.critical(
                self.disk_viewer,
                "Error",
                f"Error al actualizar discos:\n{str(e)}"
            )
    
    def on_disk_selection_changed(self):
        """Maneja el cambio de selección en la tabla de discos"""
        if self.disk_viewer is None:
            return
        DiskViewerHandlers.on_disk_selection_changed(self.disk_viewer)
    
    def on_analyze_and_organize(self, row: int):
        """Analiza y organiza el disco en la fila especificada"""
        if self.disk_viewer is None:
            return
        try:
            mount_item = self.disk_viewer.disks_table.item(row, 1)
            if mount_item:
                mountpoint = mount_item.text()
                self.disk_viewer.log_message(f"🔍 Analizando disco: {mountpoint}")
                
                # Emitir señal para que la ventana principal maneje el análisis
                if hasattr(self.disk_viewer, 'analysis_requested'):
                    self.disk_viewer.analysis_requested.emit(mountpoint)
                
                # Actualizar información del disco seleccionado
                self.disk_viewer.update_selected_disk_info(mountpoint)
        except Exception as e:
            if self.disk_viewer:
                self.disk_viewer.log_message(f"❌ Error al analizar disco: {str(e)}")
                QMessageBox.critical(
                    self.disk_viewer,
                    "Error",
                    f"Error al analizar el disco:\n{str(e)}"
                )
