#!/usr/bin/env python3
"""
Punto de entrada principal para el Organizador de Archivos
"""

import sys
import os
from pathlib import Path

# Añadir el directorio src al path para importaciones
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.gui.main_window import FileOrganizerGUI
from src.utils.constants import DIALOG_STYLES


def main():
    """Función principal de la aplicación"""
    # Crear aplicación Qt
    app = QApplication(sys.argv)
    app.setApplicationName("Organizador de Archivos")
    app.setApplicationVersion("2.0.0")
    
    # CRÍTICO: Permitir que se apliquen estilos globales para temas
    # Los temas se aplicarán correctamente desde la ventana principal
    
    # Configurar fuente por defecto
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    # Crear ventana principal (NO mostrar aún)
    window = FileOrganizerGUI()
    
    # CRÍTICO: Aplicar configuración ANTES de mostrar la ventana
    # Esto asegura que los temas se apliquen correctamente
    window.apply_saved_interface_settings()
    
    # AHORA mostrar la ventana con el tema ya aplicado
    window.show()
    
    # Ejecutar aplicación
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
