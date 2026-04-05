#!/usr/bin/env python3
"""
DuplicateHandlers - Manejadores de eventos del Dashboard de Duplicados
Extraído de duplicates_dashboard.py para mejorar mantenibilidad
"""

import os
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import QMessageBox, QFileDialog
from PyQt6.QtCore import QTimer


class DuplicateHandlers:
    """Mixin para manejadores de eventos del Dashboard de Duplicados"""
    
    def setup_connections(self):
        """Configura las conexiones de señales"""
        # Las conexiones se configuran en los widgets
        pass
    
    def on_selection_changed(self, top_left, bottom_right, roles):
        """Maneja cambios en la selección"""
        self.update_statistics_from_table()
    
    def on_method_changed(self):
        """Maneja cambio de método de búsqueda"""
        method = self.method_combo.currentData()
        self.current_method = method
        
        method_names = {
            "fast": "⚡ Rápido",
            "md5": "📋 Estándar (MD5)",
            "sha256": "🔐 Seguro (SHA256)"
        }
        
        self.status_update.emit(f"Método cambiado a: {method_names.get(method, method)}")
        
        # Actualizar tooltip
        descriptions = {
            "fast": "Solo compara tamaños - muy rápido pero menos preciso",
            "md5": "Compara hashes MD5 - equilibrio entre velocidad y precisión",
            "sha256": "Compara hashes SHA256 - más lento pero 100% preciso"
        }
        self.method_combo.setToolTip(descriptions.get(method, ""))
    
    def on_recursive_changed(self):
        """Maneja cambio de búsqueda recursiva"""
        is_recursive = self.recursive_checkbox.isChecked()
        self.status_update.emit(f"Búsqueda {'recursiva' if is_recursive else 'no recursiva'}")
    
    def select_folder(self):
        """Selecciona una carpeta para buscar duplicados"""
        folder = QFileDialog.getExistingDirectory(
            self, "📁 Seleccionar Carpeta para Buscar Duplicados"
        )
        
        if folder:
            self.current_folder = folder
            self.folder_input.setText(folder)
            self.scan_btn.setEnabled(True)
            
            folder_name = Path(folder).name
            self.status_update.emit(f"📁 Carpeta seleccionada: {folder_name}")
    
    def start_scan(self):
        """Inicia el escaneo de duplicados"""
        if not self.current_folder or not os.path.exists(self.current_folder):
            QMessageBox.warning(self, "Advertencia", "Por favor selecciona una carpeta válida.")
            return
        
        # Deshabilitar botón durante escaneo
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("🔍 Escaneando...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Modo indeterminado
        
        # Limpiar datos anteriores
        self.duplicates_data = {}
        self.clear_statistics()
        
        # Obtener configuración
        method = self.method_combo.currentData()
        recursive = self.recursive_checkbox.isChecked()
        
        # Crear finder
        self.duplicate_finder = DuplicateFinder(
            self.current_folder,
            method=method,
            recursive=recursive
        )
        
        # Crear worker
        self.scan_worker = DuplicateScanWorker(self.duplicate_finder)
        
        # Conectar señales
        self.scan_worker.duplicates_found.connect(self.on_duplicates_found)
        self.scan_worker.scan_finished.connect(self.on_scan_finished)
        self.scan_worker.error_occurred.connect(self.on_scan_error)
        
        # Iniciar
        self.scan_worker.start()
        self.status_update.emit(f"🔍 Iniciando búsqueda de duplicados en {self.current_folder}...")
    
    def on_duplicates_found(self, duplicates_data, statistics):
        """Maneja cuando se encuentran duplicados"""
        self.duplicates_data = duplicates_data
        
        # Actualizar barra de progreso
        if hasattr(statistics, 'progress'):
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(int(statistics.progress * 100))
        
        self.status_update.emit(f"📊 Encontrados {len(duplicates_data)} grupos de duplicados")
    
    def on_scan_finished(self):
        """Maneja finalización del escaneo"""
        # Restaurar UI
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("🔍 INICIAR BÚSQUEDA")
        self.progress_bar.setVisible(False)
        
        # Poblar tabla
        self.populate_table()
        
        # Actualizar estadísticas
        self.update_statistics_from_table()
        
        self.status_update.emit("✅ Búsqueda completada")
    
    def on_scan_error(self, error_message):
        """Maneja errores durante el escaneo"""
        # Restaurar UI
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("🔍 INICIAR BÚSQUEDA")
        self.progress_bar.setVisible(False)
        
        # Mostrar error
        QMessageBox.critical(self, "Error de Escaneo", error_message)
        self.status_update.emit(f"❌ Error: {error_message}")
    
    def clear_statistics(self):
        """Limpia las estadísticas"""
        # Resetear etiquetas de estadísticas
        stat_labels = [
            'total_space_label', 'duplicate_files_label', 'duplicate_groups_label',
            'scan_time_label', 'analyzed_files_label', 'recoverable_space_label'
        ]
        
        default_values = ["0 MB", "0", "0", "0s", "0", "0 MB"]
        
        for label_name, default_value in zip(stat_labels, default_values):
            if hasattr(self, label_name):
                getattr(self, label_name).setText(default_value)
    
    def update_statistics_from_table(self):
        """Actualiza estadísticas desde la tabla"""
        try:
            total_space = 0
            duplicate_files = 0
            duplicate_groups = 0
            
            # Iterar sobre datos
            for hash_key, files in self.duplicates_data.items():
                if len(files) > 1:
                    duplicate_groups += 1
                    duplicate_files += len(files) - 1  # Excluir original
                    
                    # Calcular espacio
                    for file_path in files[1:]:
                        try:
                            if os.path.exists(file_path):
                                total_space += os.path.getsize(file_path)
                        except:
                            pass
            
            # Actualizar etiquetas
            self._update_stat_label('total_space_label', f"{total_space / (1024*1024):.1f} MB")
            self._update_stat_label('duplicate_files_label', str(duplicate_files))
            self._update_stat_label('duplicate_groups_label', str(duplicate_groups))
            self._update_stat_label('recoverable_space_label', f"{total_space / (1024*1024):.1f} MB")
            
            # Actualizar contador de resultados
            self.results_count_label.setText(f"📊 {duplicate_groups} grupos encontrados")
            
        except Exception as e:
            self.status_update.emit(f"❌ Error actualizando estadísticas: {e}")
    
    def _update_stat_label(self, label_name, value):
        """Actualiza una etiqueta de estadística si existe"""
        if hasattr(self, label_name):
            getattr(self, label_name).setText(value)
    
    def apply_quick_filter(self, filter_text):
        """Aplica un filtro rápido"""
        self.filter_input.setText(filter_text)
        self.apply_filters()
    
    def apply_filters(self):
        """Aplica filtros a la tabla"""
        filter_text = self.filter_input.text().strip().lower()
        
        if not filter_text:
            # Sin filtro - mostrar todo
            self.populate_table()
            return
        
        # Filtrar datos
        filtered_data = {}
        
        for hash_key, files in self.duplicates_data.items():
            # Verificar si algún archivo coincide con el filtro
            for file_path in files:
                file_name = os.path.basename(file_path).lower()
                
                # Soporte para filtros especiales
                if filter_text.startswith("size:>"):
                    # Filtro por tamaño
                    try:
                        size_threshold = float(filter_text.split(">")[1].replace("MB", "")) * 1024 * 1024
                        if os.path.exists(file_path):
                            if os.path.getsize(file_path) > size_threshold:
                                if hash_key not in filtered_data:
                                    filtered_data[hash_key] = files
                                break
                    except:
                        pass
                elif filter_text.startswith("recent:"):
                    # Filtro por fecha reciente
                    try:
                        days = int(filter_text.split(":")[1].replace("days", ""))
                        if os.path.exists(file_path):
                            mtime = os.path.getmtime(file_path)
                            file_date = datetime.fromtimestamp(mtime)
                            days_old = (datetime.now() - file_date).days
                            if days_old <= days:
                                if hash_key not in filtered_data:
                                    filtered_data[hash_key] = files
                                break
                    except:
                        pass
                else:
                    # Filtro por nombre
                    if filter_text in file_name:
                        if hash_key not in filtered_data:
                            filtered_data[hash_key] = files
                        break
        
        # Mostrar resultados filtrados
        self.populate_table_with_filtered_data(filtered_data)
        
        count = len(filtered_data)
        self.results_count_label.setText(f"📊 {count} grupos (filtrado)")
    
    def _debounced_filter(self):
        """Ejecuta filtro con debounce"""
        self.search_timer.stop()
        self.pending_search_query = self.filter_input.text()
        self.search_timer.start(self.search_delay_ms)
    
    def _execute_search(self):
        """Ejecuta la búsqueda pendiente"""
        query = self.pending_search_query
        self.pending_search_query = ""
        self.apply_quick_filter(query)
    
    def go_to_next_page(self):
        """Va a la siguiente página"""
        if hasattr(self.duplicates_model, 'next_page'):
            self.duplicates_model.next_page()
            self.update_pagination_controls()
    
    def go_to_previous_page(self):
        """Va a la página anterior"""
        if hasattr(self.duplicates_model, 'previous_page'):
            self.duplicates_model.previous_page()
            self.update_pagination_controls()
    
    def update_pagination_controls(self):
        """Actualiza los controles de paginación"""
        if hasattr(self.duplicates_model, 'get_pagination_info'):
            info = self.duplicates_model.get_pagination_info()
            self.page_info_label.setText(f"Página {info['current']} de {info['total']}")
            self.prev_page_btn.setEnabled(info['has_prev'])
            self.next_page_btn.setEnabled(info['has_next'])
    
    def select_all_duplicates(self):
        """Selecciona todos los duplicados"""
        if hasattr(self.duplicates_model, 'check_all'):
            self.duplicates_model.check_all()
            self.status_update.emit("✅ Todos los duplicados seleccionados")
    
    def deselect_all_duplicates(self):
        """Deselecciona todos los duplicados"""
        if hasattr(self.duplicates_model, 'uncheck_all'):
            self.duplicates_model.uncheck_all()
            self.status_update.emit("❌ Todos los duplicados deseleccionados")
    
    def delete_selected(self):
        """Elimina los duplicados seleccionados"""
        # Implementación en scan_logic o actions
        pass
    
    def move_selected(self):
        """Mueve los duplicados seleccionados"""
        # Implementación en scan_logic o actions
        pass
    
    def show_context_menu(self, position):
        """Muestra menú contextual"""
        menu = QMenu(self)
        
        open_action = menu.addAction("📂 Abrir ubicación")
        open_action.triggered.connect(self.open_file_location)
        
        menu.addSeparator()
        
        delete_action = menu.addAction("🗑️ Eliminar")
        delete_action.triggered.connect(self.delete_selected)
        
        move_action = menu.addAction("📁 Mover a...")
        move_action.triggered.connect(self.move_selected)
        
        # Mostrar menú
        index = self.duplicates_table.indexAt(position)
        if index.isValid():
            menu.exec_(self.duplicates_table.viewport().mapToGlobal(position))
    
    def open_file_location(self):
        """Abre la ubicación del archivo"""
        # Implementación específica
        pass
