#!/usr/bin/env python3
"""
MainWindowActions - Acciones y operaciones de MainWindow
Extraído de main_window.py para mejorar mantenibilidad
"""

import os
import time
from pathlib import Path
from collections import defaultdict

from PyQt6.QtWidgets import (
    QMessageBox, QFileDialog, QDialog
)
from PyQt6.QtCore import QTimer

from src.core.workers import AnalysisWorker, OrganizeWorker


class MainWindowActions:
    """Mixin para acciones y operaciones de MainWindow"""
    
    def browse_folder(self):
        """Abre el diálogo para seleccionar una carpeta"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "📂 Seleccionar Carpeta a Organizar"
        )
        
        if folder_path:
            self.folder_input.setText(folder_path)
            # Auto-analizar después de un pequeño delay
            QTimer.singleShot(500, self.start_analysis)
    
    def start_analysis(self):
        """Inicia el análisis de la carpeta usando el gestor de workers"""
        try:
            # Verificar que la ventana esté completamente inicializada
            if not hasattr(self, 'analyze_btn') or not self.analyze_btn:
                self.log_message("⚠️ Ventana no completamente inicializada")
                return
            
            folder_path = self.folder_input.text().strip()
            
            if not folder_path:
                QMessageBox.warning(self, "Advertencia", "Por favor, selecciona una carpeta.")
                return
            
            if not os.path.exists(folder_path):
                QMessageBox.warning(self, "Advertencia", "La carpeta seleccionada no existe.")
                return
            
            if not os.path.isdir(folder_path):
                QMessageBox.warning(self, "Advertencia", "No es una carpeta.")
                return
            
            # Limpiar resultados anteriores
            self.folder_movements = []
            self.file_movements = []
            
            # Log
            self.log_message(f"🔍 Iniciando análisis de: {folder_path}")
            
            # Crear worker
            worker_id = f"analysis_{int(time.time())}"
            analysis_worker = AnalysisWorker(
                folder_path,
                self.category_manager.get_categories(),
                self.category_manager.ext_to_categoria,
                self.similarity_spinbox.value()
            )
            
            # Guardar referencia al worker para limpieza
            if not hasattr(self, '_active_workers'):
                self._active_workers = []
            self._active_workers.append(analysis_worker)
            
            # Conectar señales
            analysis_worker.progress_update.connect(self.log_message)
            analysis_worker.analysis_complete.connect(self.on_analysis_complete)
            analysis_worker.error_occurred.connect(self.on_analysis_error)
            analysis_worker.finished.connect(lambda: self._cleanup_worker(analysis_worker))
            
            # Iniciar worker
            analysis_worker.start()
            self.log_message(f"✅ Worker de análisis iniciado: {worker_id}")
            
        except Exception as e:
            error_msg = f"❌ Error al iniciar análisis: {str(e)}"
            self.log_message(error_msg)
            QMessageBox.critical(self, "Error de Análisis", error_msg)
            
            # Restaurar botones
            if hasattr(self, 'analyze_btn'):
                self.analyze_btn.setEnabled(True)
            if hasattr(self, 'organize_btn'):
                self.organize_btn.setEnabled(True)
            if hasattr(self, 'progress_bar'):
                self.progress_bar.setVisible(False)
    
    def populate_results_table(self):
        """Llena la tabla VIRTUALIZADA con los resultados del análisis"""
        # Limpiar datos anteriores
        self.movements_model.clear_data()
        
        # Preparar datos para el modelo virtualizado
        model_data = []
        
        # Añadir carpetas
        for mov in self.folder_movements:
            model_data.append({
                'type': 'folder',
                'element': f"📁 {mov['folder'].name}",
                'category': mov['category'],
                'percentage': mov.get('percentage', 0),
                'file_count': mov.get('total_files', 0),
                'size_bytes': mov.get('size', 0),
                'size_formatted': self.format_size(mov.get('size', 0)),
                'tooltip': f"Carpeta: {mov['folder'].name}\nArchivos: {mov.get('total_files', 0)}",
                'is_group': False,
                'is_expanded': False,
                'original_data': mov
            })
        
        # Añadir archivos agrupados por categoría
        files_by_category = defaultdict(list)
        size_by_category = defaultdict(int)
        
        for mov in self.file_movements:
            files_by_category[mov['category']].append(mov)
            size_by_category[mov['category']] += mov.get('size', 0)
        
        for category, file_movs in files_by_category.items():
            total_size = size_by_category[category]
            
            model_data.append({
                'type': 'file_group',
                'element': f"📄 {len(file_movs)} archivos sueltos",
                'category': category,
                'percentage': 0,
                'file_count': len(file_movs),
                'size_bytes': total_size,
                'size_formatted': self.format_size(total_size),
                'tooltip': f"Grupo de {len(file_movs)} archivos sueltos\nCategoría: {category}",
                'is_group': True,
                'is_expanded': False,
                'group_files': file_movs
            })
        
        # Actualizar modelo
        self.movements_model.update_data(model_data)
        
        # Re-aplicar anchos de columna
        self.movements_table.setColumnWidth(0, 50)
        self.movements_table.setColumnWidth(1, 900)
        self.movements_table.setColumnWidth(2, 200)
        self.movements_table.setColumnWidth(3, 200)
        self.movements_table.setColumnWidth(4, 200)
        self.movements_table.setColumnWidth(5, 200)
        
        self.log_message(f"✅ Tabla virtualizada poblada con {len(model_data)} elementos")
        
        # Actualizar contador y estadísticas
        self.update_selection_count()
        self.update_statistics()
    
    def select_all_items(self):
        """Selecciona todos los elementos usando el modelo virtualizado"""
        self.movements_model.check_all()
        self.update_selection_count()
        self.log_message("✅ Todos los elementos seleccionados")
    
    def deselect_all_items(self):
        """Deselecciona todos los elementos"""
        self.movements_model.uncheck_all()
        self.update_selection_count()
        self.log_message("❌ Todos los elementos deseleccionados")
    
    def update_selected_statistics(self):
        """Actualiza estadísticas de elementos seleccionados"""
        try:
            selected_rows = self.movements_model.get_checked_rows()
            
            selected_size = 0
            selected_files = 0
            
            for row in selected_rows:
                data = self.movements_model.get_row_data(row)
                if data:
                    selected_size += data.get('size_bytes', 0)
                    selected_files += data.get('file_count', 0)
            
            # Actualizar etiquetas si existen
            if hasattr(self, 'selected_size_label'):
                self.selected_size_label.setText(f"💾 Tamaño seleccionado: {self.format_size(selected_size)}")
            if hasattr(self, 'selected_files_label'):
                self.selected_files_label.setText(f"📄 Archivos seleccionados: {selected_files:,}")
                
        except Exception as e:
            self.log_message(f"❌ Error actualizando estadísticas de selección: {e}")
    
    def update_statistics(self):
        """Actualiza las estadísticas generales"""
        category_stats = defaultdict(lambda: {'count': 0, 'size': 0})
        
        # Contar carpetas por categoría
        for mov in self.folder_movements:
            category = mov['category']
            category_stats[category]['count'] += 1
            category_stats[category]['size'] += mov.get('size', 0)
        
        # Contar archivos por categoría
        for mov in self.file_movements:
            category = mov['category']
            category_stats[category]['count'] += 1
            category_stats[category]['size'] += mov.get('size', 0)
        
        # Formatear estadísticas para barra de estado
        stats_text = ""
        for category in ['MUSICA', 'VIDEOS', 'IMAGENES', 'DOCUMENTOS', 'PROGRAMAS', 'CODIGO', 'VARIOS']:
            if category in category_stats:
                count = category_stats[category]['count']
                if count > 0:
                    percentage = (count / (len(self.folder_movements) + len(self.file_movements))) * 100
                    stats_text += f"{category}({percentage:.0f}%) • "
        
        if stats_text.endswith("• "):
            stats_text = stats_text[:-2]
        
        if stats_text:
            self.stats_label.setText(f"📈 {stats_text}")
        else:
            self.stats_label.setText("📈 MÚSICA(0%) • VIDEOS(0%) • IMÁG(0%) • VARIOS(0%)")
        
        # Actualizar estadísticas detalladas
        self.update_detailed_statistics(category_stats)
    
    def update_detailed_statistics(self, category_stats):
        """Actualiza las estadísticas detalladas"""
        # Calcular totales
        total_size = sum(stats['size'] for stats in category_stats.values())
        total_files = sum(stats['count'] for stats in category_stats.values())
        
        # Actualizar etiquetas
        self.total_size_label.setText(f"💾 {self.format_size(total_size)}")
        self.total_files_label.setText(f"📄 {total_files:,} archivos")
        
        # Formatear por categoría
        category_text = ""
        category_count = 0
        
        sorted_categories = sorted(category_stats.items(), key=lambda x: x[1]['count'], reverse=True)
        
        for category, stats in sorted_categories:
            if stats['count'] > 0:
                count = stats['count']
                size = stats['size']
                category_text += f"<b>{category}:</b> {count:,} archivos ({self.format_size(size)})<br/>"
                category_count += 1
        
        if category_text:
            category_text = f"<div style='margin-bottom: 8px;'><b>📊 {category_count} categorías detectadas:</b></div>" + category_text
            self.category_stats_label.setText(category_text)
        else:
            self.category_stats_label.setText("📁 <b>Por categoría:</b> Sin datos detectados")
        
        # Actualizar categorías disponibles
        categories = self.category_manager.get_categories()
        available_text = ""
        total_extensions = 0
        
        for category, extensions in categories.items():
            available_text += f"<b>{category}:</b> {len(extensions)} extensiones<br/>"
            total_extensions += len(extensions)
        
        if available_text:
            available_text = f"<div style='margin-bottom: 8px;'><b>⚙️ {len(categories)} categorías ({total_extensions} extensiones):</b></div>" + available_text
            self.available_categories_label.setText(available_text)
        else:
            self.available_categories_label.setText("⚙️ <b>Categorías disponibles:</b> Sin datos")
    
    def start_organization(self):
        """Inicia la organización usando el modelo virtualizado"""
        # Obtener elementos seleccionados
        selected_folder_movements = []
        selected_file_movements = []
        
        selected_rows = self.movements_model.get_checked_rows()
        
        for row in selected_rows:
            row_data = self.movements_model.get_row_data(row)
            
            if not row_data:
                continue
            
            row_type = row_data.get('type', '')
            
            if row_type == 'folder':
                original_data = row_data.get('original_data')
                if original_data:
                    selected_folder_movements.append(original_data)
                    
            elif row_type == 'file_group':
                group_files = row_data.get('group_files', [])
                selected_file_movements.extend(group_files)
        
        # Verificar modo
        move_folders = self.move_folders_checkbox.isChecked()
        
        if not move_folders:
            selected_folder_movements = []
            self.log_message("ℹ️ Modo: Solo archivos sueltos")
        else:
            self.log_message("ℹ️ Modo: Carpetas completas + archivos sueltos")
        
        if not selected_folder_movements and not selected_file_movements:
            QMessageBox.warning(self, "Advertencia", "No hay elementos seleccionados.")
            return
        
        # Calcular tamaño total
        total_selected_size = 0
        for mov in selected_folder_movements:
            total_selected_size += mov.get('size', 0)
        for mov in selected_file_movements:
            total_selected_size += mov.get('size', 0)
        
        formatted_size = self.format_size(total_selected_size)
        
        # Confirmación
        if move_folders:
            confirm_message = f"¿Proceder a organizar {len(selected_folder_movements)} carpetas y {len(selected_file_movements)} archivos?\n\n"
        else:
            confirm_message = f"¿Proceder a organizar solo {len(selected_file_movements)} archivos sueltos?\n\n"
            confirm_message += "⚠️ Las carpetas serán ignoradas.\n\n"
        
        confirm_message += f"Tamaño total: {formatted_size}\n\n"
        confirm_message += "Esta acción moverá los elementos seleccionados."
        
        reply = QMessageBox.question(
            self, 
            "Confirmar Organización",
            confirm_message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        folder_path = self.folder_input.text().strip()
        
        # Crear worker
        worker_id = f"organize_{int(time.time())}"
        organize_worker = OrganizeWorker(folder_path, selected_folder_movements, selected_file_movements)
        
        # Guardar referencia
        if not hasattr(self, '_active_workers'):
            self._active_workers = []
        self._active_workers.append(organize_worker)
        
        # Conectar señales
        organize_worker.progress_update.connect(self.log_message)
        organize_worker.organize_complete.connect(self.on_organize_complete)
        organize_worker.finished.connect(lambda: self._cleanup_worker(organize_worker))
        
        # Iniciar
        organize_worker.start()
        self.log_message(f"✅ Worker de organización iniciado: {worker_id}")
    
    def on_organize_complete(self, success, message):
        """Maneja completación de la organización"""
        # Restaurar UI
        self.organize_btn.setEnabled(True)
        self.organize_btn.setText("📁 Organizar Archivos")
        self.progress_bar.setVisible(False)
        
        if success:
            self.log_message("✅ " + message)
            QMessageBox.information(self, "Organización Completada", message)
        else:
            self.log_message("❌ " + message)
            QMessageBox.critical(self, "Error de Organización", message)
    
    def open_configuration(self):
        """Abre la ventana de configuración"""
        from src.gui.config_dialog import ConfigDialog
        
        dialog = ConfigDialog(self, self.category_manager)
        
        # Aplicar tema
        self.apply_theme_to_dialog_simple(dialog)
        
        # Conectar señal
        dialog.interface_changes_requested.connect(self.apply_interface_changes)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Actualizar categorías
            self.category_manager = dialog.category_manager
            self.update_categories_info()
    
    def _cleanup_worker(self, worker):
        """Limpia un worker después de finalizar"""
        try:
            if worker in self._active_workers:
                self._active_workers.remove(worker)
            worker.deleteLater()
        except Exception:
            pass
    
    def format_size(self, size_bytes):
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
