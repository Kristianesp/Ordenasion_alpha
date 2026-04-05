#!/usr/bin/env python3
"""
Componentes de la Ventana Principal
Módulos reutilizables extraídos de main_window.py
"""

from .setup import MainWindowSetup
from .handlers import MainWindowHandlers
from .actions import MainWindowActions
from src.core.worker_manager import WorkerManager

__all__ = [
    'MainWindowSetup',
    'MainWindowHandlers', 
    'MainWindowActions',
    'WorkerManager'
]
