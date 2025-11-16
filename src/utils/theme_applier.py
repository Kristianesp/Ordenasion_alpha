#!/usr/bin/env python3
"""
Sistema de Aplicación de Temas Mejorado
Soluciona problemas de aplicación inconsistente de temas en diálogos
"""

from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QWidget, QDialog, QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPalette

from .themes import ThemeManager


class ThemeApplier:
    """
    Clase especializada para aplicar temas de forma consistente y completa
    """
    
    @staticmethod
    def apply_theme_to_widget(widget: QWidget, theme_name: str, font_size: int = 12, 
                            force_override: bool = False) -> bool:
        """
        Aplica un tema a un widget de forma completa y forzada
        
        Args:
            widget: Widget al que aplicar el tema
            theme_name: Nombre del tema
            font_size: Tamaño de fuente
            force_override: Si True, sobrescribe estilos personalizados
        
        Returns:
            bool: True si se aplicó correctamente
        """
        try:
            # Obtener colores y estilos del tema
            colors = ThemeManager.get_theme_colors(theme_name)
            palette = ThemeManager.apply_theme_to_palette(theme_name)
            css_styles = ThemeManager.get_css_styles(theme_name, font_size)
            
            # Aplicar paleta
            widget.setPalette(palette)
            
            # Aplicar estilos CSS
            if force_override:
                # Limpiar estilos existentes y aplicar nuevos
                widget.setStyleSheet("")
                widget.setStyleSheet(css_styles)
            else:
                # Solo aplicar si no tiene estilos personalizados
                if not widget.styleSheet():
                    widget.setStyleSheet(css_styles)
            
            # Aplicar a todos los widgets hijos recursivamente
            ThemeApplier._apply_to_children(widget, palette, css_styles, force_override)
            
            # Forzar actualización visual
            widget.update()
            widget.repaint()
            
            return True
            
        except Exception as e:
            print(f"❌ Error aplicando tema a widget: {e}")
            return False
    
    @staticmethod
    def _apply_to_children(parent: QWidget, palette: QPalette, css_styles: str, 
                          force_override: bool):
        """Aplica tema a todos los widgets hijos recursivamente"""
        try:
            for child in parent.findChildren(QWidget):
                if child.parent() == parent:  # Solo hijos directos para evitar duplicados
                    try:
                        # Aplicar paleta
                        child.setPalette(palette)
                        
                        # Aplicar estilos
                        if force_override:
                            child.setStyleSheet("")
                            child.setStyleSheet(css_styles)
                        else:
                            if not child.styleSheet():
                                child.setStyleSheet(css_styles)
                        
                        # Continuar recursivamente
                        ThemeApplier._apply_to_children(child, palette, css_styles, force_override)
                        
                    except Exception:
                        continue
                        
        except Exception as e:
            print(f"❌ Error aplicando tema a hijos: {e}")
    
    @staticmethod
    def apply_theme_to_dialog(dialog: QDialog, theme_name: str, font_size: int = 12) -> bool:
        """
        Aplica tema a un diálogo de forma completa y forzada
        
        Args:
            dialog: Diálogo al que aplicar el tema
            theme_name: Nombre del tema
            font_size: Tamaño de fuente
        
        Returns:
            bool: True si se aplicó correctamente
        """
        try:
            # Obtener colores del tema
            colors = ThemeManager.get_theme_colors(theme_name)
            
            # Aplicar tema base
            ThemeApplier.apply_theme_to_widget(dialog, theme_name, font_size, force_override=True)
            
            # Aplicar estilos específicos para diálogos
            dialog_css = ThemeApplier._get_dialog_specific_css(colors, font_size)
            dialog.setStyleSheet(dialog.styleSheet() + "\n" + dialog_css)
            
            # Aplicar estilos específicos a elementos problemáticos
            ThemeApplier._fix_problematic_elements(dialog, colors)
            
            # Forzar actualización completa
            dialog.update()
            dialog.repaint()
            
            # Usar timer para re-aplicar después de que se procesen los eventos
            QTimer.singleShot(100, lambda: ThemeApplier._delayed_theme_apply(dialog, theme_name, font_size))
            
            return True
            
        except Exception as e:
            print(f"❌ Error aplicando tema a diálogo: {e}")
            return False
    
    @staticmethod
    def _get_dialog_specific_css(colors: Dict[str, str], font_size: int) -> str:
        """Genera CSS específico para diálogos"""
        return f"""
        /* Estilos específicos para diálogos */
        QDialog {{
            background-color: {colors['background']} !important;
            color: {colors['text_primary']} !important;
        }}
        
        QGroupBox {{
            background-color: {colors['surface']} !important;
            color: {colors['text_primary']} !important;
            border: 2px solid {colors['border']} !important;
            border-radius: 8px !important;
            margin-top: 10px !important;
            padding-top: 10px !important;
            font-weight: bold !important;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin !important;
            left: 10px !important;
            padding: 0 5px 0 5px !important;
            color: {colors['text_primary']} !important;
            background-color: {colors['background']} !important;
        }}
        
        QLabel {{
            color: {colors['text_primary']} !important;
            background-color: transparent !important;
        }}
        
        QLineEdit, QSpinBox {{
            background-color: {colors['surface']} !important;
            color: {colors['text_primary']} !important;
            border: 2px solid {colors['border']} !important;
            border-radius: 6px !important;
            padding: 6px !important;
        }}
        
        QComboBox {{
            background-color: {colors['surface']} !important;
            color: {colors['text_primary']} !important;
            border: 2px solid {colors['border']} !important;
            border-radius: 6px !important;
            padding: 6px !important;
        }}
        
        QComboBox::drop-down {{
            background-color: {colors['surface']} !important;
            border: none !important;
        }}
        
        QComboBox::down-arrow {{
            background-color: transparent !important;
            border: none !important;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {colors['surface']} !important;
            color: {colors['text_primary']} !important;
            border: 2px solid {colors['border']} !important;
            border-radius: 6px !important;
            selection-background-color: {colors['primary']} !important;
            selection-color: white !important;
        }}
        
        QComboBox QAbstractItemView::item {{
            background-color: {colors['surface']} !important;
            color: {colors['text_primary']} !important;
            padding: 8px !important;
            border: none !important;
        }}
        
        QComboBox QAbstractItemView::item:hover {{
            background-color: {colors['surface_variant']} !important;
            color: {colors['text_primary']} !important;
        }}
        
        QComboBox QAbstractItemView::item:selected {{
            background-color: {colors['primary']} !important;
            color: white !important;
        }}
        
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
            border-color: {colors['primary']} !important;
        }}
        
        QPushButton {{
            background-color: {colors['primary']} !important;
            color: white !important;
            border: none !important;
            border-radius: 6px !important;
            padding: 8px 16px !important;
            font-weight: bold !important;
        }}
        
        QPushButton:hover {{
            background-color: {colors['button_hover']} !important;
        }}
        
        QPushButton:pressed {{
            background-color: {colors['button_pressed']} !important;
        }}
        
        QPushButton:disabled {{
            background-color: {colors['text_disabled']} !important;
            color: {colors['text_secondary']} !important;
        }}
        
        QListWidget {{
            background-color: {colors['surface']} !important;
            color: {colors['text_primary']} !important;
            border: 2px solid {colors['border']} !important;
            border-radius: 6px !important;
        }}
        
        QListWidget::item {{
            padding: 8px !important;
            border-bottom: 1px solid {colors['border']} !important;
        }}
        
        QListWidget::item:selected {{
            background-color: {colors['primary']} !important;
            color: white !important;
        }}
        
        QListWidget::item:hover {{
            background-color: {colors['surface_variant']} !important;
        }}
        """
    
    @staticmethod
    def _fix_problematic_elements(dialog: QDialog, colors: Dict[str, str]):
        """Arregla elementos específicos que no cambian correctamente"""
        try:
            # Buscar y arreglar elementos específicos
            for widget in dialog.findChildren(QWidget):
                widget_type = type(widget).__name__
                
                if widget_type == "QGroupBox":
                    # Forzar estilos en GroupBox
                    widget.setStyleSheet(f"""
                        QGroupBox {{
                            background-color: {colors['surface']} !important;
                            color: {colors['text_primary']} !important;
                            border: 2px solid {colors['border']} !important;
                            border-radius: 8px !important;
                            margin-top: 10px !important;
                            padding-top: 10px !important;
                            font-weight: bold !important;
                        }}
                        QGroupBox::title {{
                            subcontrol-origin: margin !important;
                            left: 10px !important;
                            padding: 0 5px 0 5px !important;
                            color: {colors['text_primary']} !important;
                            background-color: {colors['background']} !important;
                        }}
                    """)
                
                elif widget_type == "QLabel":
                    # Forzar estilos en Labels
                    widget.setStyleSheet(f"""
                        QLabel {{
                            color: {colors['text_primary']} !important;
                            background-color: transparent !important;
                        }}
                    """)
                
                elif widget_type == "QComboBox":
                    # Forzar estilos específicos para QComboBox incluyendo dropdown
                    widget.setStyleSheet(f"""
                        QComboBox {{
                            background-color: {colors['surface']} !important;
                            color: {colors['text_primary']} !important;
                            border: 2px solid {colors['border']} !important;
                            border-radius: 6px !important;
                            padding: 6px !important;
                        }}
                        QComboBox::drop-down {{
                            background-color: {colors['surface']} !important;
                            border: none !important;
                        }}
                        QComboBox::down-arrow {{
                            background-color: transparent !important;
                            border: none !important;
                        }}
                        QComboBox QAbstractItemView {{
                            background-color: {colors['surface']} !important;
                            color: {colors['text_primary']} !important;
                            border: 2px solid {colors['border']} !important;
                            border-radius: 6px !important;
                            selection-background-color: {colors['primary']} !important;
                            selection-color: white !important;
                        }}
                        QComboBox QAbstractItemView::item {{
                            background-color: {colors['surface']} !important;
                            color: {colors['text_primary']} !important;
                            padding: 8px !important;
                            border: none !important;
                        }}
                        QComboBox QAbstractItemView::item:hover {{
                            background-color: {colors['surface_variant']} !important;
                            color: {colors['text_primary']} !important;
                        }}
                        QComboBox QAbstractItemView::item:selected {{
                            background-color: {colors['primary']} !important;
                            color: white !important;
                        }}
                        QComboBox:focus {{
                            border-color: {colors['primary']} !important;
                        }}
                    """)
                
                elif widget_type in ["QLineEdit", "QSpinBox"]:
                    # Forzar estilos en campos de entrada
                    widget.setStyleSheet(f"""
                        {widget_type} {{
                            background-color: {colors['surface']} !important;
                            color: {colors['text_primary']} !important;
                            border: 2px solid {colors['border']} !important;
                            border-radius: 6px !important;
                            padding: 6px !important;
                        }}
                        {widget_type}:focus {{
                            border-color: {colors['primary']} !important;
                        }}
                    """)
                
                elif widget_type == "QPushButton":
                    # Forzar estilos en botones
                    widget.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {colors['primary']} !important;
                            color: white !important;
                            border: none !important;
                            border-radius: 6px !important;
                            padding: 8px 16px !important;
                            font-weight: bold !important;
                        }}
                        QPushButton:hover {{
                            background-color: {colors['button_hover']} !important;
                        }}
                        QPushButton:pressed {{
                            background-color: {colors['button_pressed']} !important;
                        }}
                        QPushButton:disabled {{
                            background-color: {colors['text_disabled']} !important;
                            color: {colors['text_secondary']} !important;
                        }}
                    """)
                    
        except Exception as e:
            print(f"❌ Error arreglando elementos problemáticos: {e}")
    
    @staticmethod
    def _delayed_theme_apply(dialog: QDialog, theme_name: str, font_size: int):
        """Aplica tema de forma diferida para asegurar que se procese correctamente"""
        try:
            colors = ThemeManager.get_theme_colors(theme_name)
            
            # Re-aplicar estilos a elementos que pueden haber sido sobrescritos
            for widget in dialog.findChildren(QWidget):
                if widget.styleSheet() and "!important" not in widget.styleSheet():
                    # Si no tiene !important, re-aplicar
                    ThemeApplier._fix_problematic_elements(widget, colors)
            
            # Forzar actualización específica de QComboBox
            ThemeApplier._force_combo_box_refresh(dialog, colors)
            
            # Forzar actualización final
            dialog.update()
            dialog.repaint()
            
        except Exception as e:
            print(f"❌ Error en aplicación diferida de tema: {e}")
    
    @staticmethod
    def _force_combo_box_refresh(dialog: QDialog, colors: Dict[str, str]):
        """Fuerza la actualización específica de QComboBox para corregir dropdowns"""
        try:
            from PyQt6.QtWidgets import QComboBox
            
            for combo_box in dialog.findChildren(QComboBox):
                try:
                    # Obtener el texto actual
                    current_text = combo_box.currentText()
                    
                    # Forzar re-aplicación de estilos
                    combo_box.setStyleSheet(f"""
                        QComboBox {{
                            background-color: {colors['surface']} !important;
                            color: {colors['text_primary']} !important;
                            border: 2px solid {colors['border']} !important;
                            border-radius: 6px !important;
                            padding: 6px !important;
                        }}
                        QComboBox::drop-down {{
                            background-color: {colors['surface']} !important;
                            border: none !important;
                        }}
                        QComboBox::down-arrow {{
                            background-color: transparent !important;
                            border: none !important;
                        }}
                        QComboBox QAbstractItemView {{
                            background-color: {colors['surface']} !important;
                            color: {colors['text_primary']} !important;
                            border: 2px solid {colors['border']} !important;
                            border-radius: 6px !important;
                            selection-background-color: {colors['primary']} !important;
                            selection-color: white !important;
                        }}
                        QComboBox QAbstractItemView::item {{
                            background-color: {colors['surface']} !important;
                            color: {colors['text_primary']} !important;
                            padding: 8px !important;
                            border: none !important;
                        }}
                        QComboBox QAbstractItemView::item:hover {{
                            background-color: {colors['surface_variant']} !important;
                            color: {colors['text_primary']} !important;
                        }}
                        QComboBox QAbstractItemView::item:selected {{
                            background-color: {colors['primary']} !important;
                            color: white !important;
                        }}
                        QComboBox:focus {{
                            border-color: {colors['primary']} !important;
                        }}
                    """)
                    
                    # Forzar actualización del widget
                    combo_box.update()
                    combo_box.repaint()
                    
                    # Si el dropdown está abierto, cerrarlo y abrirlo para forzar refresh
                    if combo_box.view().isVisible():
                        combo_box.hidePopup()
                        combo_box.showPopup()
                    
                except Exception as e:
                    print(f"❌ Error actualizando QComboBox: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ Error en force_combo_box_refresh: {e}")
    
    @staticmethod
    def apply_theme_to_application(theme_name: str, font_size: int = 12) -> bool:
        """
        Aplica tema a toda la aplicación de forma completa
        
        Args:
            theme_name: Nombre del tema
            font_size: Tamaño de fuente
        
        Returns:
            bool: True si se aplicó correctamente
        """
        try:
            app = QApplication.instance()
            if not app:
                return False
            
            # Obtener colores y estilos
            colors = ThemeManager.get_theme_colors(theme_name)
            palette = ThemeManager.apply_theme_to_palette(theme_name)
            css_styles = ThemeManager.get_css_styles(theme_name, font_size)
            
            # Aplicar a toda la aplicación
            app.setPalette(palette)
            app.setStyleSheet(css_styles)
            
            # Aplicar a todas las ventanas principales
            for widget in app.allWidgets():
                if isinstance(widget, QWidget):
                    try:
                        widget.setPalette(palette)
                        if not widget.styleSheet():
                            widget.setStyleSheet(css_styles)
                    except Exception:
                        continue
            
            # Procesar eventos para asegurar aplicación
            app.processEvents()
            
            return True
            
        except Exception as e:
            print(f"❌ Error aplicando tema a aplicación: {e}")
            return False


# Instancia global del aplicador de temas
theme_applier = ThemeApplier()
