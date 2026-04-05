#!/usr/bin/env python3
"""
ScanLogic - Lógica de escaneo y operaciones del Dashboard de Duplicados
Extraído de duplicates_dashboard.py para mejorar mantenibilidad
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import QMessageBox, QFileDialog


class ScanLogic:
    """Mixin para lógica de escaneo y operaciones del Dashboard de Duplicados"""
    
    def populate_table(self):
        """Pobla la tabla con datos de duplicados"""
        if not self.duplicates_data:
            return
        
        # Preparar datos para el modelo
        model_data = []
        
        for hash_key, files in self.duplicates_data.items():
            if len(files) > 1:  # Solo grupos con duplicados
                # Primera fila - grupo principal
                first_file = files[0]
                file_size = os.path.getsize(first_file) if os.path.exists(first_file) else 0
                
                model_data.append({
                    'hash': hash_key,
                    'file_path': first_file,
                    'file_name': os.path.basename(first_file),
                    'size': file_size,
                    'size_formatted': self._format_size(file_size),
                    'group_index': 0,
                    'total_in_group': len(files),
                    'is_duplicate': False,
                    'checked': False
                })
                
                # Filas adicionales - duplicados
                for i, file_path in enumerate(files[1:], 1):
                    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    
                    model_data.append({
                        'hash': hash_key,
                        'file_path': file_path,
                        'file_name': os.path.basename(file_path),
                        'size': file_size,
                        'size_formatted': self._format_size(file_size),
                        'group_index': i,
                        'total_in_group': len(files),
                        'is_duplicate': True,
                        'checked': False
                    })
        
        # Actualizar modelo
        if hasattr(self, 'duplicates_model'):
            self.duplicates_model.update_data(model_data)
    
    def populate_table_with_filtered_data(self, filtered_data):
        """Pobla la tabla con datos filtrados"""
        # Guardar datos originales temporalmente
        original_data = self.duplicates_data
        self.duplicates_data = filtered_data
        
        # Poblar tabla
        self.populate_table()
        
        # Restaurar datos originales
        self.duplicates_data = original_data
    
    def delete_selected(self):
        """Elimina los archivos duplicados seleccionados"""
        try:
            # Obtener filas seleccionadas
            selected_rows = self._get_checked_rows()
            
            if not selected_rows:
                QMessageBox.warning(self, "Advertencia", "No hay archivos seleccionados para eliminar.")
                return
            
            # Confirmar eliminación
            count = len(selected_rows)
            reply = QMessageBox.question(
                self,
                "Confirmar Eliminación",
                f"¿Estás seguro de que deseas eliminar {count} archivos?\n\n⚠️ Esta acción no se puede deshacer.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            # Eliminar archivos
            deleted_count = 0
            failed_count = 0
            
            for row in selected_rows:
                if hasattr(self.duplicates_model, 'get_row_data'):
                    data = self.duplicates_model.get_row_data(row)
                    if data:
                        file_path = data.get('file_path')
                        if file_path and os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                                deleted_count += 1
                                self.status_update.emit(f"🗑️ Eliminado: {os.path.basename(file_path)}")
                            except Exception as e:
                                failed_count += 1
                                self.status_update.emit(f"❌ Error eliminando {os.path.basename(file_path)}: {e}")
            
            # Mostrar resultado
            message = f"✅ {deleted_count} archivos eliminados exitosamente."
            if failed_count > 0:
                message += f"\n⚠️ {failed_count} archivos no pudieron ser eliminados."
            
            QMessageBox.information(self, "Eliminación Completada", message)
            
            # Refrescar vista
            self.refresh_view()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al eliminar archivos: {e}")
    
    def move_selected(self):
        """Mueve los archivos duplicados seleccionados a otra carpeta"""
        try:
            # Obtener filas seleccionadas
            selected_rows = self._get_checked_rows()
            
            if not selected_rows:
                QMessageBox.warning(self, "Advertencia", "No hay archivos seleccionados para mover.")
                return
            
            # Seleccionar carpeta de destino
            dest_folder = QFileDialog.getExistingDirectory(
                self, "📁 Seleccionar Carpeta de Destino"
            )
            
            if not dest_folder:
                return
            
            # Mover archivos
            moved_count = 0
            failed_count = 0
            
            for row in selected_rows:
                if hasattr(self.duplicates_model, 'get_row_data'):
                    data = self.duplicates_model.get_row_data(row)
                    if data:
                        file_path = data.get('file_path')
                        if file_path and os.path.exists(file_path):
                            try:
                                file_name = os.path.basename(file_path)
                                dest_path = os.path.join(dest_folder, file_name)
                                
                                # Manejar nombres duplicados
                                if os.path.exists(dest_path):
                                    base, ext = os.path.splitext(file_name)
                                    counter = 1
                                    while os.path.exists(dest_path):
                                        dest_path = os.path.join(dest_folder, f"{base}_{counter}{ext}")
                                        counter += 1
                                
                                shutil.move(file_path, dest_path)
                                moved_count += 1
                                self.status_update.emit(f"📁 Movido: {file_name}")
                            except Exception as e:
                                failed_count += 1
                                self.status_update.emit(f"❌ Error moviendo {file_name}: {e}")
            
            # Mostrar resultado
            message = f"✅ {moved_count} archivos movidos exitosamente a:\n{dest_folder}"
            if failed_count > 0:
                message += f"\n⚠️ {failed_count} archivos no pudieron ser movidos."
            
            QMessageBox.information(self, "Movimiento Completado", message)
            
            # Refrescar vista
            self.refresh_view()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al mover archivos: {e}")
    
    def _get_checked_rows(self):
        """Obtiene las filas marcadas con checkbox"""
        checked_rows = []
        
        if hasattr(self.duplicates_model, 'get_checked_rows'):
            checked_rows = self.duplicates_model.get_checked_rows()
        
        return checked_rows
    
    def _format_size(self, size_bytes):
        """Formatea tamaño en bytes a formato legible"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / (1024 ** 2):.1f} MB"
        elif size_bytes < 1024 ** 4:
            return f"{size_bytes / (1024 ** 3):.1f} GB"
        else:
            return f"{size_bytes / (1024 ** 4):.1f} TB"
    
    def refresh_view(self):
        """Refresca la vista actual"""
        # Volver a poblar la tabla
        self.populate_table()
        
        # Actualizar estadísticas
        self.update_statistics_from_table()
        
        self.status_update.emit("🔄 Vista refrescada")
    
    def update_statistics_from_selection(self):
        """Actualiza estadísticas basadas en la selección actual"""
        try:
            selected_rows = self._get_checked_rows()
            
            selected_space = 0
            selected_count = 0
            
            for row in selected_rows:
                if hasattr(self.duplicates_model, 'get_row_data'):
                    data = self.duplicates_model.get_row_data(row)
                    if data:
                        selected_space += data.get('size', 0)
                        selected_count += 1
            
            # Actualizar etiquetas si existen
            self._update_stat_label('selected_space_label', f"{selected_space / (1024*1024):.1f} MB")
            self._update_stat_label('selected_count_label', str(selected_count))
            
        except Exception as e:
            self.status_update.emit(f"❌ Error actualizando estadísticas de selección: {e}")
    
    def _update_stat_label(self, label_name, value):
        """Actualiza una etiqueta de estadística si existe"""
        if hasattr(self, label_name):
            getattr(self, label_name).setText(value)
    
    def open_file_location(self):
        """Abre la ubicación del archivo seleccionado"""
        try:
            # Obtener fila seleccionada
            indexes = self.duplicates_table.selectedIndexes()
            if not indexes:
                return
            
            row = indexes[0].row()
            
            if hasattr(self.duplicates_model, 'get_row_data'):
                data = self.duplicates_model.get_row_data(row)
                if data:
                    file_path = data.get('file_path')
                    if file_path and os.path.exists(file_path):
                        # Abrir explorador en la ubicación del archivo
                        if os.name == 'nt':  # Windows
                            os.startfile(os.path.dirname(file_path))
                        elif os.name == 'posix':  # macOS/Linux
                            subprocess.run(['xdg-open' if os.name == 'posix' else 'open', os.path.dirname(file_path)])
                        
                        self.status_update.emit(f"📂 Abriendo ubicación: {file_path}")
        except Exception as e:
            self.status_update.emit(f"❌ Error abriendo ubicación: {e}")
