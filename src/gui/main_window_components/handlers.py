#!/usr/bin/env python3
"""
MainWindowHandlers - Manejadores de eventos y señales de MainWindow
Extraído de main_window.py para mejorar mantenibilidad
"""

from PyQt6.QtWidgets import QMessageBox, QFileDialog, QMenu
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QTimer, Qt
from collections import defaultdict
import os


class MainWindowHandlers:
    """Mixin para manejadores de eventos de MainWindow"""
    
    def setup_connections(self):
        """Configura las conexiones básicas de señales y slots"""
        try:
            # Conectar menú contextual de la tabla
            if hasattr(self, 'movements_table'):
                self.movements_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                self.movements_table.customContextMenuRequested.connect(self.show_context_menu)
            
            self.log_message("✅ Conexiones básicas configuradas")
        except Exception as e:
            self.log_message(f"❌ Error configurando conexiones: {e}")
    
    def setup_shortcuts(self):
        """Configura atajos de teclado"""
        try:
            from PyQt6.QtGui import QKeySequence, QShortcut
            
            # Atajo para analizar (F5)
            shortcut_analyze = QShortcut(QKeySequence("F5"), self)
            shortcut_analyze.activated.connect(self.start_analysis)
            
            # Atajo para organizar (F9)
            shortcut_organize = QShortcut(QKeySequence("F9"), self)
            shortcut_organize.activated.connect(self.start_organization)
            
            self.log_message("✅ Atajos de teclado configurados")
        except Exception as e:
            self.log_message(f"❌ Error configurando atajos: {e}")
    
    def setup_state_observers(self):
        """Configura observadores del estado centralizado"""
        try:
            from src.core.application_state import app_state, EventType
            
            # Verificar que app_state esté disponible
            if not hasattr(app_state, 'state_changed'):
                self.log_message("⚠️ app_state no está completamente inicializado")
                return
            
            # Conectar señales del estado centralizado
            try:
                app_state.state_changed.connect(self.on_state_changed)
            except Exception as e:
                self.log_message(f"⚠️ Error conectando state_changed: {e}")
            
            try:
                app_state.theme_changed.connect(self.on_theme_changed)
            except Exception as e:
                self.log_message(f"⚠️ Error conectando theme_changed: {e}")
            
            try:
                app_state.disk_selected.connect(self.on_disk_selected)
            except Exception as e:
                self.log_message(f"⚠️ Error conectando disk_selected: {e}")
            
            self.log_message("✅ Observadores del estado centralizado configurados")
            
        except Exception as e:
            self.log_message(f"❌ Error configurando observadores: {e}")
    
    def on_state_changed(self, event):
        """Maneja cambios del estado de la aplicación"""
        try:
            from src.core.application_state import EventType
            
            event_type = event.event_type
            data = event.data
            
            if event_type == EventType.THEME_CHANGED:
                pass  # Se maneja en on_theme_changed
            elif event_type == EventType.DISK_SELECTED:
                pass  # Se maneja en on_disk_selected
            elif event_type == EventType.WORKER_STARTED:
                worker_id = data.get("worker_id")
                if worker_id:
                    self.log_message(f"🚀 Worker iniciado: {worker_id}")
            elif event_type == EventType.WORKER_FINISHED:
                worker_id = data.get("worker_id")
                if worker_id:
                    self.log_message(f"✅ Worker completado: {worker_id}")
            elif event_type == EventType.MEMORY_CLEANUP:
                cache_name = data.get("cache_name")
                self.log_message(f"🧹 Limpieza de memoria: {cache_name}")
                
        except Exception as e:
            self.log_message(f"❌ Error manejando cambio de estado: {e}")
    
    def on_theme_changed(self, theme_name: str):
        """Maneja cambios de tema"""
        try:
            self.log_message(f"🎨 Tema cambiado a: {theme_name}")
        except Exception as e:
            self.log_message(f"❌ Error manejando cambio de tema: {e}")
    
    def on_disk_selected(self, disk_path: str):
        """Maneja selección de disco"""
        try:
            self.log_message(f"💾 Disco seleccionado: {disk_path}")
        except Exception as e:
            self.log_message(f"❌ Error manejando selección de disco: {e}")
    
    def on_worker_started(self, worker_id: str, worker_type: str):
        """Maneja inicio de workers"""
        try:
            self.log_message(f"🚀 Worker iniciado: {worker_type} ({worker_id})")
            
            if "Analysis" in worker_type:
                self.analyze_btn.setEnabled(False)
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)
            elif "Organize" in worker_type:
                self.organize_btn.setEnabled(False)
                self.organize_btn.setText("🔄 Organizando...")
                
        except Exception as e:
            self.log_message(f"❌ Error manejando inicio de worker: {e}")
    
    def on_worker_completed(self, worker_id: str, success: bool):
        """Maneja completación de workers"""
        try:
            status = "✅ exitoso" if success else "❌ con errores"
            self.log_message(f"🏁 Worker completado: {worker_id} - {status}")
            
            # Restaurar UI
            self.analyze_btn.setEnabled(True)
            self.organize_btn.setEnabled(True)
            self.organize_btn.setText("📁 Organizar Archivos")
            self.progress_bar.setVisible(False)
            
        except Exception as e:
            self.log_message(f"❌ Error manejando completación de worker: {e}")
    
    def on_worker_progress(self, worker_id: str, progress: float):
        """Maneja progreso de workers"""
        try:
            if self.progress_bar.isVisible():
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(int(progress * 100))
                
        except Exception as e:
            self.log_message(f"❌ Error manejando progreso de worker: {e}")
    
    def on_worker_error(self, worker_id: str, error_message: str):
        """Maneja errores de workers"""
        try:
            self.log_message(f"❌ Error en worker {worker_id}: {error_message}")
            
            # Restaurar UI en caso de error
            self.analyze_btn.setEnabled(True)
            self.organize_btn.setEnabled(True)
            self.organize_btn.setText("📁 Organizar Archivos")
            self.progress_bar.setVisible(False)
            
        except Exception as e:
            self.log_message(f"❌ Error manejando error de worker: {e}")
    
    def on_memory_warning(self, warning_type: str, memory_mb: float):
        """Maneja advertencias de memoria"""
        try:
            self.log_message(f"⚠️ Advertencia de memoria: {warning_type} ({memory_mb:.1f} MB)")
            
            if memory_mb > 500:
                QMessageBox.warning(
                    self, 
                    "Advertencia de Memoria",
                    f"El uso de memoria es alto: {memory_mb:.1f} MB\n\n"
                    "Se recomienda cerrar otras aplicaciones."
                )
                
        except Exception as e:
            self.log_message(f"❌ Error manejando advertencia de memoria: {e}")
    
    def on_memory_cleanup(self, stats):
        """Maneja limpieza de memoria completada"""
        try:
            self.log_message(f"🧹 Limpieza completada: {stats.cache_size_mb:.1f} MB caché")
        except Exception as e:
            self.log_message(f"❌ Error manejando limpieza de memoria: {e}")
    
    def on_folder_path_changed(self, text):
        """Maneja el cambio en el campo de ruta de carpeta"""
        if text.strip() and os.path.exists(text.strip()):
            QTimer.singleShot(1000, self.start_analysis)
    
    def on_analysis_complete(self, folder_movements, file_movements, stats):
        """Maneja la completación del análisis"""
        self.folder_movements = folder_movements
        self.file_movements = file_movements
        
        # Llenar tabla
        self.populate_results_table()
        
        # Habilitar botones
        self.analyze_btn.setEnabled(True)
        self.organize_btn.setEnabled(True)
        
        # Ocultar progreso
        self.progress_bar.setVisible(False)
        
        # Log
        total_items = len(folder_movements) + len(file_movements)
        self.log_message(f"✅ Análisis completado: {total_items} elementos encontrados")
        
        # Mostrar estadísticas
        if stats:
            self.log_message(f"📊 Estadísticas: {stats.get('total_folders', 0)} carpetas, {stats.get('total_files', 0)} archivos")
            self.update_statistics()
            self.update_selected_statistics()
    
    def on_analysis_error(self, error_message):
        """Maneja errores durante el análisis"""
        self.log_message(error_message)
        
        # Habilitar botones
        self.analyze_btn.setEnabled(True)
        self.organize_btn.setEnabled(False)
        
        # Ocultar progreso
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(self, "Error de Análisis", error_message)
    
    def on_model_data_changed(self, top_left, bottom_right, roles):
        """Maneja cambios en el modelo de datos"""
        self.update_selection_count()
        self.update_selected_statistics()
    
    def on_table_double_clicked(self, index):
        """Maneja doble clic en la tabla"""
        row = index.row()
        data = self.movements_model.get_row_data(row)
        
        if data and data.get('is_group'):
            # Expandir/colapsar grupo
            self.toggle_file_group_expansion(row)
    
    def toggle_file_group_expansion(self, group_row):
        """Alterna expansión de grupo de archivos"""
        data = self.movements_model.get_row_data(group_row)
        
        if data and data.get('is_group'):
            if data.get('is_expanded'):
                self.collapse_file_group(group_row, data['category'])
            else:
                self.expand_file_group(group_row, data['category'], data.get('group_files', []))
    
    def expand_file_group(self, group_row, category, group_files):
        """Expande un grupo de archivos"""
        self.movements_model.expand_file_group(group_row, group_files)
        self.log_message(f"📂 Grupo expandido: {len(group_files)} archivos de {category}")
    
    def collapse_file_group(self, group_row, category):
        """Colapsa un grupo de archivos"""
        self.movements_model.collapse_file_group(group_row)
        self.log_message(f"📁 Grupo colapsado: {category}")
    
    def update_selection_count(self):
        """Actualiza el contador de elementos seleccionados"""
        try:
            total = self.movements_model.rowCount()
            selected = sum(1 for i in range(total) if self.movements_model.is_row_checked(i))
            
            self.selection_count_label.setText(f"📊 Elementos: {selected}/{total} seleccionados")
            
            # Actualizar estadísticas de selección
            self.update_selected_statistics()
            
        except Exception as e:
            self.log_message(f"❌ Error actualizando contador: {e}")
    
    def on_header_clicked(self, logical_index):
        """Maneja clic en header de columna"""
        try:
            column_names = ["☑️", "📂 Elemento", "📁 Destino", "📊 %", "📄 Archivos", "💾 Tamaño"]
            column_name = column_names[logical_index] if logical_index < len(column_names) else f"Columna {logical_index}"
            self.log_message(f"📊 Ordenando por: {column_name}")
        except Exception:
            pass
    
    def on_disk_selected_for_organize(self, disk_path):
        """Maneja selección de disco para organizar"""
        try:
            self.folder_input.setText(disk_path)
            self.main_tabs.setCurrentIndex(0)  # Cambiar a pestaña organizar
            self.log_message(f"💾 Disco seleccionado para organizar: {disk_path}")
            QTimer.singleShot(500, self.start_analysis)
        except Exception as e:
            self.log_message(f"❌ Error seleccionando disco: {e}")
    
    def show_context_menu(self, position):
        """Muestra menú contextual para la tabla de movimientos"""
        try:
            # Obtener la fila donde se hizo clic
            index = self.movements_table.indexAt(position)
            if not index.isValid():
                return
                
            row = index.row()
            
            # Obtener información del elemento
            model = self.movements_table.model()
            element_data = model.data(model.index(row, 1), Qt.ItemDataRole.DisplayRole)
            destination_data = model.data(model.index(row, 2), Qt.ItemDataRole.DisplayRole)
            
            if not element_data:
                return
            
            # Crear menú contextual
            menu = QMenu(self)
            
            # Acción para abrir ubicación del archivo
            if hasattr(self, 'folder_path') and self.folder_path:
                open_location_action = QAction("📁 Abrir ubicación", self)
                open_location_action.triggered.connect(lambda: self.open_file_location(self.folder_path))
                menu.addAction(open_location_action)
            
            # Acción para expandir/contraer grupo (si es aplicable)
            row_data = model.get_row_data(row) if hasattr(model, 'get_row_data') else None
            if row_data and row_data.get('is_group', False):
                if row_data.get('is_expanded', False):
                    collapse_action = QAction("📁 Contraer grupo", self)
                    collapse_action.triggered.connect(lambda: model.collapse_group(row) if hasattr(model, 'collapse_group') else None)
                    menu.addAction(collapse_action)
                else:
                    expand_action = QAction("📂 Expandir grupo", self)
                    expand_action.triggered.connect(lambda: model.expand_group(row) if hasattr(model, 'expand_group') else None)
                    menu.addAction(expand_action)
            
            # Mostrar menú
            menu.exec(self.movements_table.mapToGlobal(position))
            
        except Exception as e:
            self.log_message(f"❌ Error en menú contextual: {str(e)}")
    
    def open_file_location(self, folder_path):
        """Abre la ubicación del archivo en el explorador"""
        try:
            import subprocess
            import sys
            
            if sys.platform == "win32":
                # Windows - abrir explorer
                subprocess.Popen(f'explorer "{folder_path}"')
            elif sys.platform == "darwin":
                # macOS
                subprocess.Popen(["open", folder_path])
            else:
                # Linux
                subprocess.Popen(["xdg-open", folder_path])
                
        except Exception as e:
            self.log_message(f"❌ Error abriendo ubicación: {str(e)}")
