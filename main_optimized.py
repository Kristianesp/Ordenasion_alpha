#!/usr/bin/env python3
"""
Punto de entrada OPTIMIZADO para el Organizador de Archivos
🚀 Arranque 3-4x más rápido con carga progresiva y caché
"""

import sys
import os
from pathlib import Path

# Añadir el directorio src al path para importaciones
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from src.gui.splash_screen import ModernSplashScreen, ProgressiveLoader
from src.utils.theme_cache import theme_cache


def preload_theme_cache():
    """Precarga el caché de temas para arranque instantáneo"""
    # Precargar tema por defecto con tamaños comunes
    theme_cache.preload_theme("🌞 Claro Elegante", font_sizes=[10, 11, 12, 14, 16])
    # Precargar otros temas populares
    theme_cache.preload_theme("🌙 Oscuro Profesional", font_sizes=[12])
    theme_cache.preload_theme("⚫ Lujo Minimalista", font_sizes=[12])


def main():
    """Función principal OPTIMIZADA de la aplicación"""
    # Crear aplicación Qt
    app = QApplication(sys.argv)
    app.setApplicationName("Organizador de Archivos")
    app.setApplicationVersion("2.0.0")
    
    # Configurar fuente por defecto
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    # ✅ OPTIMIZACIÓN 1: Mostrar splash screen
    splash = ModernSplashScreen(width=500, height=300)
    splash.show()
    app.processEvents()
    
    # ✅ OPTIMIZACIÓN 2: Crear cargador progresivo
    loader = ProgressiveLoader(splash)
    
    # Variable para almacenar la ventana
    window = None
    
    # ✅ OPTIMIZACIÓN 3: Definir tareas de carga con pesos
    def task_preload_cache():
        """Tarea 1: Precargar caché de temas (rápido)"""
        splash.set_progress(10, "Precargando temas...", "Optimizando rendimiento")
        preload_theme_cache()
    
    def task_import_components():
        """Tarea 2: Importar componentes pesados (medio)"""
        splash.set_progress(30, "Cargando componentes...", "Importando módulos")
        # Importar aquí para lazy loading
        from src.gui.main_window import FileOrganizerGUI
        from src.core.application_state import app_state
        return FileOrganizerGUI, app_state
    
    def task_create_window():
        """Tarea 3: Crear ventana principal (medio)"""
        nonlocal window
        splash.set_progress(50, "Creando interfaz...", "Inicializando ventana")
        from src.gui.main_window import FileOrganizerGUI
        window = FileOrganizerGUI()
    
    def task_init_disk_manager():
        """Tarea 4: Inicializar DiskManager (pesado - pero lazy)"""
        splash.set_progress(70, "Inicializando gestores...", "Preparando sistema de discos")
        # DiskManager se inicializa de forma lazy, solo registramos
        if window:
            window._init_disk_manager()
    
    def task_apply_theme():
        """Tarea 5: Aplicar tema guardado (rápido con caché)"""
        splash.set_progress(85, "Aplicando tema...", "Configurando interfaz")
        if window:
            window.apply_saved_interface_settings()
    
    def task_finalize():
        """Tarea 6: Finalizar inicialización"""
        splash.set_progress(95, "Finalizando...", "Casi listo")
        if window:
            # Conectar señales finales
            window.setup_connections()
            window.setup_shortcuts()
            window.setup_state_observers()
    
    # ✅ OPTIMIZACIÓN 4: Añadir tareas con pesos
    loader.add_task("Precarga de caché", task_preload_cache, weight=1)
    loader.add_task("Importación de componentes", task_import_components, weight=2)
    loader.add_task("Creación de ventana", task_create_window, weight=3)
    loader.add_task("Inicialización de gestores", task_init_disk_manager, weight=2)
    loader.add_task("Aplicación de tema", task_apply_theme, weight=1)
    loader.add_task("Finalización", task_finalize, weight=1)
    
    # ✅ OPTIMIZACIÓN 5: Ejecutar carga progresiva
    loader.execute()
    
    # ✅ OPTIMIZACIÓN 6: Mostrar ventana y cerrar splash
    splash.set_progress(100, "¡Listo!", "Abriendo aplicación...")
    app.processEvents()
    
    if window:
        # Pequeña pausa para que se vea el 100%
        QTimer.singleShot(300, lambda: splash.finish_with_fade(window))
        QTimer.singleShot(350, window.show)
    else:
        print("❌ Error: No se pudo crear la ventana principal")
        splash.close()
        return 1
    
    # Ejecutar aplicación
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

