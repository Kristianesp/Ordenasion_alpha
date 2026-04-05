#!/usr/bin/env python3
"""
Componentes UI avanzados para DiskViewer
Incluye constructores de UI y actualizadores de información
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QProgressBar, QTextEdit, QFrame, QSplitter,
    QMessageBox, QCheckBox, QComboBox, QSizePolicy, QScrollArea,
    QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.core.disk_manager import DiskInfo


class DiskViewerUIBuilder:
    """Constructor de la interfaz de usuario de DiskViewer"""
    
    @staticmethod
    def create_unified_header(parent, system_info_label, safe_mode_checkbox, refresh_btn):
        """Crea el header unificado con información del sistema y controles"""
        unified_header = QFrame()
        unified_header.setToolTip("🖥️ Muestra información en tiempo real del sistema: CPU, RAM, estado de seguridad y discos monitoreados")
        unified_header.setObjectName("system_info_group")
        unified_header.setFrameShape(QFrame.Shape.Box)
        unified_header.setLineWidth(0)
        unified_header.setMinimumHeight(45)
        unified_header.setMaximumHeight(45)
        
        unified_layout = QHBoxLayout(unified_header)
        unified_layout.setContentsMargins(10, 6, 10, 6)
        unified_layout.setSpacing(12)
        
        # Título
        title_label = QLabel("🖥️ INFORMACIÓN DEL SISTEMA:")
        title_label.setObjectName("system_info_title")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        unified_layout.addWidget(title_label)
        
        # Información del sistema
        system_info_label.setText("Cargando información del sistema...")
        system_info_label.setObjectName("system_info_label")
        system_info_label.setWordWrap(False)
        unified_layout.addWidget(system_info_label, stretch=1)
        
        unified_layout.addStretch()
        
        # Modo seguro
        safe_mode_label = QLabel("🛡️ Modo Seguro:")
        safe_mode_label.setToolTip("🛡️ Configuración de seguridad para proteger los datos del sistema")
        safe_mode_label.setObjectName("safe_mode_label")
        unified_layout.addWidget(safe_mode_label)
        
        safe_mode_checkbox.setToolTip("🛡️ Cuando está activado, solo permite análisis y visualización sin modificar archivos")
        safe_mode_checkbox.setChecked(True)
        safe_mode_checkbox.setObjectName("safe_mode_checkbox")
        unified_layout.addWidget(safe_mode_checkbox)
        
        # Botón refresh
        refresh_btn.setText("🔄 Actualizar")
        refresh_btn.setToolTip("🔄 Actualiza la información de discos")
        refresh_btn.setObjectName("refresh_btn")
        refresh_btn.setFixedHeight(26)
        refresh_btn.setFixedWidth(90)
        unified_layout.addWidget(refresh_btn)
        
        return unified_header
    
    @staticmethod
    def create_disks_table():
        """Crea y configura la tabla de discos"""
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "💿 Unidad", "📁 Punto de Montaje", "💾 Total", "📊 Usado", 
            "🆓 Libre", "📈 % Uso", "🛡️ Sistema", "🔍"
        ])
        
        table.verticalHeader().setDefaultSectionSize(45)
        table.setMinimumHeight(120)
        table.setMaximumHeight(600)
        table.setRowCount(0)
        table.setAlternatingRowColors(True)
        table.setShowGrid(True)
        table.setGridStyle(Qt.PenStyle.SolidLine)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Configurar header
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        
        table.setColumnWidth(0, 80)
        table.setColumnWidth(5, 80)
        table.setColumnWidth(6, 100)
        table.setColumnWidth(7, 130)
        
        header.setToolTip("💿 Unidad: Letra de la unidad del disco\n"
                         "📁 Punto de Montaje: Ruta donde está montado el disco\n"
                         "💾 Total: Espacio total del disco\n"
                         "📊 Usado: Espacio utilizado actualmente\n"
                         "🆓 Libre: Espacio disponible\n"
                         "📈 % Uso: Porcentaje de espacio utilizado\n"
                         "🛡️ Sistema: Indica si es unidad del sistema\n"
                         "🔍 Botón para analizar y organizar el disco")
        
        return table
    
    @staticmethod
    def create_analysis_panel():
        """Crea el panel de análisis del disco seleccionado"""
        analysis_group = QGroupBox("🔍 ANÁLISIS DEL DISCO SELECCIONADO")
        analysis_group.setToolTip("🔍 Panel de análisis detallado que se muestra cuando seleccionas un disco específico")
        analysis_group.setObjectName("analysis_group")
        analysis_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        analysis_group.setMinimumHeight(400)
        
        analysis_layout = QVBoxLayout(analysis_group)
        analysis_layout.setSpacing(12)
        
        # Fila de títulos
        headers_row = QHBoxLayout()
        headers_row.setSpacing(20)
        headers_row.setContentsMargins(0, 0, 0, 0)
        
        basic_header = QLabel("💾 INFORMACIÓN BÁSICA")
        basic_header.setObjectName("card_header")
        basic_header.setFixedHeight(50)
        basic_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        headers_row.addWidget(basic_header)
        
        health_header = QLabel("🩺 ESTADO Y SALUD")
        health_header.setObjectName("card_header")
        health_header.setFixedHeight(50)
        health_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        headers_row.addWidget(health_header)
        
        content_header = QLabel("📁 CONTENIDO")
        content_header.setObjectName("card_header")
        content_header.setFixedHeight(50)
        content_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        headers_row.addWidget(content_header)
        
        analysis_layout.addLayout(headers_row)
        
        # Fila de contenido
        content_row = QHBoxLayout()
        content_row.setSpacing(20)
        content_row.setContentsMargins(0, 0, 0, 0)
        
        # Tarjeta básica
        basic_card = QFrame()
        basic_card.setObjectName("analysis_card_large")
        basic_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        basic_card.setMinimumHeight(250)
        basic_card_layout = QVBoxLayout(basic_card)
        basic_card_layout.setSpacing(8)
        basic_card_layout.setContentsMargins(0, 0, 0, 0)
        
        basic_content_frame = QFrame()
        basic_content_frame.setObjectName("analysis_inner_frame")
        basic_inner_layout = QVBoxLayout(basic_content_frame)
        basic_inner_layout.setSpacing(4)
        basic_inner_layout.setContentsMargins(12, 8, 12, 8)
        
        basic_info_label = QLabel("Selecciona un disco para ver su información básica")
        basic_info_label.setObjectName("basic_info_label")
        basic_info_label.setWordWrap(True)
        basic_info_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        basic_inner_layout.addWidget(basic_info_label)
        
        basic_card_layout.addWidget(basic_content_frame)
        content_row.addWidget(basic_card, stretch=2)
        
        # Tarjeta de salud
        health_card = QFrame()
        health_card.setObjectName("analysis_card_medium")
        health_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        health_card.setMinimumHeight(250)
        health_card_layout = QVBoxLayout(health_card)
        health_card_layout.setSpacing(8)
        health_card_layout.setContentsMargins(0, 0, 0, 0)
        
        health_content_frame = QFrame()
        health_content_frame.setObjectName("analysis_inner_frame")
        health_inner_layout = QVBoxLayout(health_content_frame)
        health_inner_layout.setSpacing(4)
        health_inner_layout.setContentsMargins(12, 8, 12, 8)
        
        health_label = QLabel("Selecciona un disco para ver su estado de salud")
        health_label.setObjectName("health_label")
        health_label.setWordWrap(True)
        health_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        health_inner_layout.addWidget(health_label)
        
        health_card_layout.addWidget(health_content_frame)
        content_row.addWidget(health_card, stretch=2)
        
        # Tarjeta de contenido
        content_card = QFrame()
        content_card.setObjectName("analysis_card_medium")
        content_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_card.setMinimumHeight(250)
        content_card_layout = QVBoxLayout(content_card)
        content_card_layout.setSpacing(8)
        content_card_layout.setContentsMargins(0, 0, 0, 0)
        
        content_content_frame = QFrame()
        content_content_frame.setObjectName("analysis_inner_frame")
        content_inner_layout = QVBoxLayout(content_content_frame)
        content_inner_layout.setSpacing(4)
        content_inner_layout.setContentsMargins(12, 8, 12, 8)
        
        content_label = QLabel("Selecciona un disco para ver su contenido")
        content_label.setObjectName("content_label")
        content_label.setWordWrap(True)
        content_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        content_inner_layout.addWidget(content_label)
        
        content_card_layout.addWidget(content_content_frame)
        content_row.addWidget(content_card, stretch=1)
        
        analysis_layout.addLayout(content_row)
        
        # Log display
        log_display = QTextEdit()
        log_display.setObjectName("log_display")
        log_display.setReadOnly(True)
        log_display.setPlaceholderText("📝 El registro de actividades aparecerá aquí...")
        log_display.setMinimumHeight(80)
        log_display.setMaximumHeight(120)
        analysis_layout.addWidget(log_display)
        
        return analysis_group, {
            'basic_header': basic_header,
            'health_header': health_header,
            'content_header': content_header,
            'basic_card': basic_card,
            'health_card': health_card,
            'content_card': content_card,
            'basic_content_frame': basic_content_frame,
            'health_content_frame': health_content_frame,
            'content_content_frame': content_content_frame,
            'basic_info_label': basic_info_label,
            'health_label': health_label,
            'content_label': content_label,
            'log_display': log_display
        }


class DiskInfoUpdater:
    """Actualizador de información de discos"""
    
    @staticmethod
    def update_basic_info(basic_info_label: QLabel, disk_info: DiskInfo, theme_name: str):
        """Actualiza la etiqueta de información básica"""
        from src.utils.themes import ThemeManager
        colors = ThemeManager.get_theme_colors(theme_name)
        
        info_html = f"""
        <div style="color: {colors['text_primary']}; line-height: 1.8;">
            <div style="margin-bottom: 6px;"><b>💿 Unidad:</b> {disk_info.device}</div>
            <div style="margin-bottom: 6px;"><b>📁 Tipo:</b> {disk_info.fstype}</div>
            <div style="margin-bottom: 6px;"><b>💾 Capacidad:</b> {disk_info.total_human}</div>
            <div style="margin-bottom: 6px;"><b>📊 Usado:</b> {disk_info.used_human}</div>
            <div style="margin-bottom: 6px;"><b>🆓 Libre:</b> {disk_info.free_human}</div>
            <div style="margin-bottom: 6px;"><b>📈 Uso:</b> {disk_info.usage_percent:.1f}%</div>
            <div><b>🏷️ Etiqueta:</b> {getattr(disk_info, 'label', 'N/A')}</div>
        </div>
        """
        basic_info_label.setText(info_html)
    
    @staticmethod
    def update_health_html(health_label: QLabel, disk_info: DiskInfo, health_data: Dict[str, Any], theme_name: str):
        """Actualiza la etiqueta de salud con HTML tematizado"""
        from src.utils.themes import ThemeManager
        colors = ThemeManager.get_theme_colors(theme_name)
        
        score = health_data.get('score', 0)
        if score >= 90:
            status_color = colors['success']; status_icon = "🟢"; status_text = "EXCELENTE"
        elif score >= 75:
            status_color = colors['success']; status_icon = "🟢"; status_text = "SALUDABLE"
        elif score >= 60:
            status_color = colors['warning']; status_icon = "🟡"; status_text = "ATENCIÓN"
        elif score >= 40:
            status_color = colors['warning']; status_icon = "🟠"; status_text = "ADVERTENCIA"
        else:
            status_color = colors['error']; status_icon = "🔴"; status_text = "CRÍTICO"
        
        text_color = colors['text_primary']
        
        health_text = f"""
        <div style="margin-bottom: 15px; padding: 12px; background-color: {status_color}20; border-radius: 8px; border-left: 5px solid {status_color};">
            <div style="color: {status_color}; font-weight: bold; font-size: 14px; margin-bottom: 8px;">
                {status_icon} Estado: {status_text}
            </div>
            <div style="color: {text_color}; margin-bottom: 5px;">
                📊 Puntuación de Salud: <span style="font-weight: bold; color: {status_color};">{score}/100</span>
            </div>
            <div style="color: {text_color}; margin-bottom: 5px;">
                💾 Uso del Disco: <span style="font-weight: bold;">{disk_info.usage_percent:.1f}%</span>
            </div>
            <div style="color: {text_color}; margin-bottom: 8px;">
                💡 Acción: <span style="font-weight: bold;">{health_data.get('status', 'Desconocido')}</span>
            </div>
        </div>
        """
        
        factors = health_data.get('factors', [])
        if factors:
            surface_color = colors['surface']
            accent_color = colors['primary']
            health_text += f"""
            <div style="margin-bottom: 15px; padding: 12px; background-color: {surface_color}; border-radius: 8px; border-left: 4px solid {accent_color};">
                <div style="color: {accent_color}; font-weight: bold; margin-bottom: 8px;">🔍 FACTORES DE SALUD:</div>
            """
            for factor in factors:
                factor_score = factor.get('score', 0)
                factor_color = colors['success'] if factor_score > 0 else colors['error']
                factor_icon = "✅" if factor_score > 0 else "❌"
                health_text += f"""
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; padding: 6px; background-color: {surface_color}; border-radius: 4px;">
                    <div style="color: {text_color};">{factor_icon} {factor.get('name', 'Unknown')}</div>
                    <div style="color: {factor_color}; font-weight: bold;">{factor_score}</div>
                </div>
                """
            health_text += "</div>"
        
        health_label.setText(health_text)
    
    @staticmethod
    def update_content_info(content_label: QLabel, disk_info: DiskInfo, theme_name: str):
        """Actualiza la etiqueta de contenido"""
        from src.utils.themes import ThemeManager
        colors = ThemeManager.get_theme_colors(theme_name)
        
        content_html = f"""
        <div style="color: {colors['text_primary']}; line-height: 1.8;">
            <div style="margin-bottom: 6px;"><b>📁 Total Archivos:</b> Calculando...</div>
            <div style="margin-bottom: 6px;"><b>📂 Total Carpetas:</b> Calculando...</div>
            <div style="margin-bottom: 6px;"><b>🗂️ Tipos de Archivo:</b> Analizando...</div>
            <div><b>⚠️ Problemas:</b> Ninguno detectado</div>
        </div>
        """
        content_label.setText(content_html)
