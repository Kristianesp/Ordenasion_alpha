#!/usr/bin/env python3
"""
Splash Screen Optimizado para Carga Progresiva
Muestra progreso mientras se cargan componentes pesados
"""

from PyQt6.QtWidgets import QSplashScreen, QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
from typing import Callable


class ModernSplashScreen(QSplashScreen):
    """
    Splash screen moderno con barra de progreso
    Muestra el progreso de carga de la aplicación
    """
    
    def __init__(self, width: int = 500, height: int = 300):
        # Crear pixmap transparente
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        super().__init__(pixmap)
        
        self.width = width
        self.height = height
        self.progress = 0
        self.message = "Iniciando..."
        self.sub_message = ""
        
        # Configurar ventana
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        
        # Dibujar splash inicial
        self.draw_splash()
    
    def draw_splash(self):
        """Dibuja el splash screen con progreso"""
        pixmap = QPixmap(self.width, self.height)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fondo con gradiente
        from PyQt6.QtGui import QLinearGradient
        gradient = QLinearGradient(0, 0, 0, self.height)
        gradient.setColorAt(0, QColor("#1976d2"))
        gradient.setColorAt(1, QColor("#0d47a1"))
        
        # Dibujar fondo redondeado
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.width, self.height, 20, 20)
        
        # Título
        painter.setPen(QColor("white"))
        title_font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.drawText(0, 60, self.width, 40, Qt.AlignmentFlag.AlignCenter, "📁 Organizador de Archivos")
        
        # Versión
        version_font = QFont("Segoe UI", 10)
        painter.setFont(version_font)
        painter.drawText(0, 100, self.width, 20, Qt.AlignmentFlag.AlignCenter, "v2.0 - Edición Profesional")
        
        # Mensaje principal
        message_font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        painter.setFont(message_font)
        painter.drawText(0, 150, self.width, 30, Qt.AlignmentFlag.AlignCenter, self.message)
        
        # Sub-mensaje
        if self.sub_message:
            sub_font = QFont("Segoe UI", 9)
            painter.setFont(sub_font)
            painter.setPen(QColor("#e3f2fd"))
            painter.drawText(0, 180, self.width, 20, Qt.AlignmentFlag.AlignCenter, self.sub_message)
        
        # Barra de progreso
        progress_y = 220
        progress_height = 8
        progress_width = self.width - 80
        progress_x = 40
        
        # Fondo de la barra
        painter.setBrush(QColor("#1565c0"))
        painter.drawRoundedRect(progress_x, progress_y, progress_width, progress_height, 4, 4)
        
        # Progreso actual
        if self.progress > 0:
            filled_width = int(progress_width * (self.progress / 100))
            painter.setBrush(QColor("#4fc3f7"))
            painter.drawRoundedRect(progress_x, progress_y, filled_width, progress_height, 4, 4)
        
        # Porcentaje
        percent_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        painter.setFont(percent_font)
        painter.setPen(QColor("white"))
        painter.drawText(0, 240, self.width, 20, Qt.AlignmentFlag.AlignCenter, f"{int(self.progress)}%")
        
        painter.end()
        
        self.setPixmap(pixmap)
    
    def set_progress(self, progress: int, message: str = None, sub_message: str = None):
        """
        Actualiza el progreso y mensaje
        
        Args:
            progress: Progreso de 0 a 100
            message: Mensaje principal
            sub_message: Mensaje secundario (opcional)
        """
        self.progress = min(100, max(0, progress))
        if message:
            self.message = message
        if sub_message is not None:
            self.sub_message = sub_message
        
        self.draw_splash()
        QApplication.processEvents()
    
    def finish_with_fade(self, window):
        """Cierra el splash con efecto de fade"""
        # Usar el método finish estándar
        self.finish(window)


class ProgressiveLoader:
    """
    Cargador progresivo de componentes
    Ejecuta tareas de inicialización mostrando progreso
    """
    
    def __init__(self, splash: ModernSplashScreen = None):
        self.splash = splash
        self.tasks = []
        self.current_task = 0
    
    def add_task(self, name: str, function: Callable, weight: int = 1):
        """
        Añade una tarea de carga
        
        Args:
            name: Nombre descriptivo de la tarea
            function: Función a ejecutar
            weight: Peso relativo de la tarea (para cálculo de progreso)
        """
        self.tasks.append({
            'name': name,
            'function': function,
            'weight': weight
        })
    
    def execute(self):
        """Ejecuta todas las tareas mostrando progreso"""
        total_weight = sum(task['weight'] for task in self.tasks)
        accumulated_weight = 0
        
        for i, task in enumerate(self.tasks):
            self.current_task = i
            
            # Calcular progreso
            progress = int((accumulated_weight / total_weight) * 100)
            
            # Actualizar splash
            if self.splash:
                self.splash.set_progress(
                    progress,
                    f"Cargando: {task['name']}",
                    f"Paso {i + 1} de {len(self.tasks)}"
                )
            
            # Ejecutar tarea
            try:
                task['function']()
            except Exception as e:
                print(f"Error en tarea '{task['name']}': {e}")
            
            # Actualizar peso acumulado
            accumulated_weight += task['weight']
            
            # Pequeña pausa para que se vea el progreso
            QApplication.processEvents()
        
        # Progreso completo
        if self.splash:
            self.splash.set_progress(100, "¡Listo!", "Iniciando aplicación...")

