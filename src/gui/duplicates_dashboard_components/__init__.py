#!/usr/bin/env python3
"""
Componentes del Dashboard de Duplicados
Módulos reutilizables extraídos de duplicates_dashboard.py
"""

from .widgets import DuplicateWidgets
from .handlers import DuplicateHandlers
from .scan_logic import ScanLogic

__all__ = [
    'DuplicateWidgets',
    'DuplicateHandlers',
    'ScanLogic'
]
