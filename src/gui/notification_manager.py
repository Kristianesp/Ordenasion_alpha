#!/usr/bin/env python3
"""
Sistema de Notificaciones y Feedback Mejorado
Componente moderno para mostrar mensajes, progreso y alertas al usuario
"""

import time
from typing import Dict, Any, Optional, List
from enum import Enum
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QFrame, QGraphicsOpacityEffect, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal,
    QRect, QPoint, QSize
)
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QIcon


class NotificationType(Enum):
    """Tipos de notificaciones"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    PROGRESS = "progress"


class NotificationPriority(Enum):
    """Prioridades de notificaciones"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class ModernNotification(QWidget):
    """
    Notificación moderna con animaciones y diseño profesional
    """
    
    # Señales
    notification_closed = pyqtSignal(str)  # notification_id
    notification_clicked = pyqtSignal(str)  # notification_id
    
    def __init__(self, notification_id: str, title: str, message: str, 
                 notification_type: NotificationType = NotificationType.INFO,
                 priority: NotificationPriority = NotificationPriority.NORMAL,
                 duration: int = 5000, parent=None):
        super().__init__(parent)
        
        self.notification_id = notification_id
        self.title = title
        self.message = message
        self.notification_type = notification_type
        self.priority = priority
        self.duration = duration
        
        # Configuración de UI
        self.setFixedSize(350, 120)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Animaciones
        self.fade_animation = None
        self.slide_animation = None
        
        # Timer para auto-cierre
        self.auto_close_timer = QTimer()
        self.auto_close_timer.setSingleShot(True)
        self.auto_close_timer.timeout.connect(self.close_notification)
        
        self.init_ui()
        self.setup_animations()
        
        # Iniciar auto-cierre si tiene duración
        if duration > 0:
            self.auto_close_timer.start(duration)
    
    def init_ui(self):
        """Inicializa la interfaz de la notificación"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Contenedor principal con estilo
        main_frame = QFrame()
        main_frame.setObjectName("notification_frame")
        main_frame.setStyleSheet(self._get_frame_style())
        
        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(15, 15, 15, 15)
        frame_layout.setSpacing(8)
        
        # Header con título y botón de cerrar
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Icono del tipo
        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)
        icon_label.setPixmap(self._get_type_icon())
        header_layout.addWidget(icon_label)
        
        # Título
        title_label = QLabel(self.title)
        title_label.setObjectName("notification_title")
        title_label.setStyleSheet(self._get_title_style())
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label)
        
        # Botón de cerrar
        close_btn = QPushButton("×")
        close_btn.setObjectName("close_button")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(self._get_close_button_style())
        close_btn.clicked.connect(self.close_notification)
        header_layout.addWidget(close_btn)
        
        frame_layout.addLayout(header_layout)
        
        # Mensaje
        message_label = QLabel(self.message)
        message_label.setObjectName("notification_message")
        message_label.setStyleSheet(self._get_message_style())
        message_label.setWordWrap(True)
        message_label.setWordWrap(True)
        frame_layout.addWidget(message_label)
        
        # Barra de progreso (si es tipo PROGRESS)
        if self.notification_type == NotificationType.PROGRESS:
            self.progress_bar = QProgressBar()
            self.progress_bar.setObjectName("notification_progress")
            self.progress_bar.setStyleSheet(self._get_progress_style())
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            frame_layout.addWidget(self.progress_bar)
        
        layout.addWidget(main_frame)
        
        # Configurar cursor para indicar que es clickeable
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def setup_animations(self):
        """Configura las animaciones de entrada y salida"""
        # Animación de opacidad
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        # Animación de entrada (fade in)
        self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(300)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Animación de salida (fade out)
        self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(200)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_out_animation.finished.connect(self.hide)
        
        # Iniciar animación de entrada
        self.fade_in_animation.start()
    
    def _get_frame_style(self) -> str:
        """Obtiene el estilo del frame según el tipo"""
        colors = self._get_type_colors()
        
        return f"""
        QFrame#notification_frame {{
            background-color: {colors['background']};
            border: 2px solid {colors['border']};
            border-radius: 12px;
            box-shadow: 0 4px 12px {colors['shadow']};
        }}
        QFrame#notification_frame:hover {{
            border-color: {colors['hover_border']};
            box-shadow: 0 6px 16px {colors['hover_shadow']};
        }}
        """
    
    def _get_title_style(self) -> str:
        """Obtiene el estilo del título"""
        colors = self._get_type_colors()
        
        return f"""
        QLabel#notification_title {{
            color: {colors['text']};
            font-weight: bold;
            font-size: 14px;
            background: transparent;
        }}
        """
    
    def _get_message_style(self) -> str:
        """Obtiene el estilo del mensaje"""
        colors = self._get_type_colors()
        
        return f"""
        QLabel#notification_message {{
            color: {colors['text_secondary']};
            font-size: 12px;
            background: transparent;
        }}
        """
    
    def _get_close_button_style(self) -> str:
        """Obtiene el estilo del botón de cerrar"""
        colors = self._get_type_colors()
        
        return f"""
        QPushButton#close_button {{
            background-color: transparent;
            color: {colors['text_secondary']};
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: bold;
        }}
        QPushButton#close_button:hover {{
            background-color: {colors['hover_background']};
            color: {colors['text']};
        }}
        QPushButton#close_button:pressed {{
            background-color: {colors['pressed_background']};
        }}
        """
    
    def _get_progress_style(self) -> str:
        """Obtiene el estilo de la barra de progreso"""
        colors = self._get_type_colors()
        
        return f"""
        QProgressBar#notification_progress {{
            border: 1px solid {colors['border']};
            border-radius: 6px;
            background-color: {colors['progress_background']};
            text-align: center;
            color: {colors['text']};
        }}
        QProgressBar#notification_progress::chunk {{
            background-color: {colors['primary']};
            border-radius: 5px;
        }}
        """
    
    def _get_type_colors(self) -> Dict[str, str]:
        """Obtiene los colores según el tipo de notificación"""
        color_schemes = {
            NotificationType.INFO: {
                'background': '#e3f2fd',
                'border': '#2196f3',
                'hover_border': '#1976d2',
                'text': '#1976d2',
                'text_secondary': '#1565c0',
                'primary': '#2196f3',
                'shadow': 'rgba(33, 150, 243, 0.3)',
                'hover_shadow': 'rgba(33, 150, 243, 0.4)',
                'hover_background': 'rgba(33, 150, 243, 0.1)',
                'pressed_background': 'rgba(33, 150, 243, 0.2)',
                'progress_background': '#ffffff'
            },
            NotificationType.SUCCESS: {
                'background': '#e8f5e8',
                'border': '#4caf50',
                'hover_border': '#388e3c',
                'text': '#2e7d32',
                'text_secondary': '#388e3c',
                'primary': '#4caf50',
                'shadow': 'rgba(76, 175, 80, 0.3)',
                'hover_shadow': 'rgba(76, 175, 80, 0.4)',
                'hover_background': 'rgba(76, 175, 80, 0.1)',
                'pressed_background': 'rgba(76, 175, 80, 0.2)',
                'progress_background': '#ffffff'
            },
            NotificationType.WARNING: {
                'background': '#fff3e0',
                'border': '#ff9800',
                'hover_border': '#f57c00',
                'text': '#ef6c00',
                'text_secondary': '#f57c00',
                'primary': '#ff9800',
                'shadow': 'rgba(255, 152, 0, 0.3)',
                'hover_shadow': 'rgba(255, 152, 0, 0.4)',
                'hover_background': 'rgba(255, 152, 0, 0.1)',
                'pressed_background': 'rgba(255, 152, 0, 0.2)',
                'progress_background': '#ffffff'
            },
            NotificationType.ERROR: {
                'background': '#ffebee',
                'border': '#f44336',
                'hover_border': '#d32f2f',
                'text': '#c62828',
                'text_secondary': '#d32f2f',
                'primary': '#f44336',
                'shadow': 'rgba(244, 67, 54, 0.3)',
                'hover_shadow': 'rgba(244, 67, 54, 0.4)',
                'hover_background': 'rgba(244, 67, 54, 0.1)',
                'pressed_background': 'rgba(244, 67, 54, 0.2)',
                'progress_background': '#ffffff'
            },
            NotificationType.PROGRESS: {
                'background': '#f3e5f5',
                'border': '#9c27b0',
                'hover_border': '#7b1fa2',
                'text': '#6a1b9a',
                'text_secondary': '#7b1fa2',
                'primary': '#9c27b0',
                'shadow': 'rgba(156, 39, 176, 0.3)',
                'hover_shadow': 'rgba(156, 39, 176, 0.4)',
                'hover_background': 'rgba(156, 39, 176, 0.1)',
                'pressed_background': 'rgba(156, 39, 176, 0.2)',
                'progress_background': '#ffffff'
            }
        }
        
        return color_schemes.get(self.notification_type, color_schemes[NotificationType.INFO])
    
    def _get_type_icon(self) -> QPixmap:
        """Obtiene el icono según el tipo de notificación"""
        icons = {
            NotificationType.INFO: "ℹ️",
            NotificationType.SUCCESS: "✅",
            NotificationType.WARNING: "⚠️",
            NotificationType.ERROR: "❌",
            NotificationType.PROGRESS: "🔄"
        }
        
        # Crear pixmap con emoji
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dibujar emoji (simplificado)
        painter.setFont(QFont("Segoe UI Emoji", 16))
        painter.drawText(0, 0, 24, 24, Qt.AlignmentFlag.AlignCenter, icons.get(self.notification_type, "ℹ️"))
        
        painter.end()
        return pixmap
    
    def set_progress(self, value: int):
        """Establece el progreso (solo para notificaciones de tipo PROGRESS)"""
        if self.notification_type == NotificationType.PROGRESS and hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(value)
    
    def update_message(self, message: str):
        """Actualiza el mensaje de la notificación"""
        self.message = message
        # Buscar y actualizar el label del mensaje
        for child in self.findChildren(QLabel):
            if child.objectName() == "notification_message":
                child.setText(message)
                break
    
    def close_notification(self):
        """Cierra la notificación con animación"""
        # Detener timer de auto-cierre
        self.auto_close_timer.stop()
        
        # Iniciar animación de salida
        self.fade_out_animation.start()
        
        # Emitir señal
        self.notification_closed.emit(self.notification_id)
    
    def mousePressEvent(self, event):
        """Maneja clics en la notificación"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.notification_clicked.emit(self.notification_id)
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        """Maneja el hover sobre la notificación"""
        # Pausar auto-cierre al hacer hover
        if self.auto_close_timer.isActive():
            self.auto_close_timer.stop()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Maneja cuando se sale del hover"""
        # Reanudar auto-cierre al salir del hover
        if self.duration > 0:
            remaining_time = self.duration - (time.time() - self.start_time if hasattr(self, 'start_time') else 0)
            if remaining_time > 0:
                self.auto_close_timer.start(int(remaining_time))
        super().leaveEvent(event)


class NotificationManager(QWidget):
    """
    Gestor de notificaciones que maneja múltiples notificaciones
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuración
        self.max_notifications = 5
        self.notification_spacing = 10
        self.position_offset = 20
        
        # Almacenamiento
        self.notifications: Dict[str, ModernNotification] = {}
        self.notification_queue: List[Dict[str, Any]] = []
        
        # Configuración de posición
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        
        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(self.notification_spacing)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Posicionar en la esquina superior derecha
        self._position_window()
    
    def _position_window(self):
        """Posiciona la ventana en la esquina superior derecha"""
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.right() - 370  # Ancho de notificación + margen
            y = parent_rect.top() + self.position_offset
            self.move(x, y)
    
    def show_notification(self, notification_id: str, title: str, message: str,
                         notification_type: NotificationType = NotificationType.INFO,
                         priority: NotificationPriority = NotificationPriority.NORMAL,
                         duration: int = 5000) -> bool:
        """Muestra una nueva notificación"""
        try:
            # Verificar si ya existe
            if notification_id in self.notifications:
                self.update_notification(notification_id, title, message)
                return True
            
            # Crear notificación
            notification = ModernNotification(
                notification_id, title, message, notification_type, priority, duration, self
            )
            
            # Conectar señales
            notification.notification_closed.connect(self._on_notification_closed)
            notification.notification_clicked.connect(self._on_notification_clicked)
            
            # Verificar límite de notificaciones
            if len(self.notifications) >= self.max_notifications:
                # Remover la más antigua
                oldest_id = min(self.notifications.keys(), key=lambda k: self.notifications[k].creation_time)
                self._remove_notification(oldest_id)
            
            # Añadir timestamp
            notification.creation_time = time.time()
            
            # Guardar referencia
            self.notifications[notification_id] = notification
            
            # Añadir al layout
            self.layout.addWidget(notification)
            
            # Mostrar
            notification.show()
            
            # Reposicionar ventana
            self._reposition_notifications()
            
            return True
            
        except Exception as e:
            print(f"❌ Error mostrando notificación: {e}")
            return False
    
    def update_notification(self, notification_id: str, title: str = None, message: str = None):
        """Actualiza una notificación existente"""
        if notification_id in self.notifications:
            notification = self.notifications[notification_id]
            
            if title:
                notification.title = title
            if message:
                notification.update_message(message)
    
    def set_progress(self, notification_id: str, value: int):
        """Establece el progreso de una notificación"""
        if notification_id in self.notifications:
            self.notifications[notification_id].set_progress(value)
    
    def _remove_notification(self, notification_id: str):
        """Remueve una notificación"""
        if notification_id in self.notifications:
            notification = self.notifications[notification_id]
            
            # Remover del layout
            self.layout.removeWidget(notification)
            
            # Cerrar y eliminar
            notification.close()
            notification.deleteLater()
            
            # Remover de la lista
            del self.notifications[notification_id]
            
            # Reposicionar
            self._reposition_notifications()
    
    def _on_notification_closed(self, notification_id: str):
        """Maneja el cierre de una notificación"""
        self._remove_notification(notification_id)
    
    def _on_notification_clicked(self, notification_id: str):
        """Maneja el clic en una notificación"""
        # Aquí se puede añadir lógica específica según el tipo de notificación
        print(f"Notificación clickeada: {notification_id}")
    
    def _reposition_notifications(self):
        """Reposiciona todas las notificaciones"""
        # Ajustar tamaño de la ventana
        total_height = sum(notif.height() for notif in self.notifications.values())
        total_height += (len(self.notifications) - 1) * self.notification_spacing
        
        self.resize(370, max(total_height, 50))
        
        # Reposicionar ventana
        self._position_window()
    
    def clear_all(self):
        """Limpia todas las notificaciones"""
        for notification_id in list(self.notifications.keys()):
            self._remove_notification(notification_id)
    
    def get_notification_count(self) -> int:
        """Obtiene el número de notificaciones activas"""
        return len(self.notifications)


# Instancia global del gestor de notificaciones
notification_manager = NotificationManager()
