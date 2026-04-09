#!/usr/bin/env python3
"""
Sistema de Temas Profesionales para el Organizador de Archivos
Diseño UI/UX 2025 con accesibilidad WCAG 2.1 AA - Completo
"""

from typing import Dict, Any
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt
from .modern_styles import get_modern_css_styles


class ThemeManager:
    """Gestor de temas profesionales con amplia selección de diseño"""

    # 🎨 Sistema Completo de Temas Profesionales con Accesibilidad WCAG 2.1 AA
    THEMES = {
        # ===== TEMAS BÁSICOS CLÁSICOS =====
        "🌞 Claro Elegante": {
            "name": "elegant_light",
            "description": "Perfecto equilibrio profesional",
            "colors": {
                "primary": "#1976d2",        # Azul Material Design - Ratio 4.5:1
                "secondary": "#42a5f5",      # Azul claro accesible
                "accent": "#ff9800",         # Naranja vibrante - Ratio 3.1:1
                "background": "#fafafa",     # Gris muy claro - Ratio 15.8:1
                "surface": "#ffffff",        # Blanco puro - Ratio 21:1
                "surface_variant": "#f5f5f5", # Superficie alternativa
                "text_primary": "#212121",   # Negro suave - Ratio 16.6:1
                "text_secondary": "#757575", # Gris medio - Ratio 4.6:1
                "text_disabled": "#bdbdbd",  # Gris claro para deshabilitado
                "border": "#e0e0e0",         # Borde sutil - Ratio 1.8:1
                "border_focus": "#1976d2",   # Borde en foco
                "success": "#388e3c",        # Verde Material - Ratio 4.5:1
                "warning": "#f57c00",        # Naranja advertencia - Ratio 4.5:1
                "error": "#d32f2f",          # Rojo error - Ratio 5.4:1
                "info": "#1976d2",           # Azul información
                "button_primary": "#1976d2",
                "button_hover": "#1565c0",
                "button_pressed": "#0d47a1",
                "table_header": "#f8f9fa",
                "table_row_even": "#ffffff",
                "table_row_odd": "#fafafa",
                "table_selected": "#e3f2fd",
                "shadow_light": "rgba(0, 0, 0, 0.08)",
                "shadow_medium": "rgba(0, 0, 0, 0.12)",
                "shadow_strong": "rgba(0, 0, 0, 0.16)"
            }
        },
        
        "🌙 Oscuro Profesional": {
            "name": "professional_dark",
            "description": "Modo oscuro corporativo",
            "colors": {
                "primary": "#2196f3",        # Azul Material Dark - Ratio 4.5:1
                "secondary": "#64b5f6",      # Azul claro para dark
                "accent": "#ff9800",         # Naranja vibrante
                "background": "#121212",     # Negro Material Dark
                "surface": "#1e1e1e",        # Superficie elevada
                "surface_variant": "#2d2d2d", # Superficie alternativa
                "text_primary": "#ffffff",   # Blanco puro - Ratio 21:1
                "text_secondary": "#b3b3b3", # Gris claro - Ratio 4.6:1
                "text_disabled": "#666666",  # Gris medio para deshabilitado
                "border": "#373737",         # Borde visible en dark
                "border_focus": "#2196f3",   # Borde en foco
                "success": "#4caf50",        # Verde Material Dark
                "warning": "#ff9800",        # Naranja advertencia
                "error": "#f44336",          # Rojo error Material
                "info": "#2196f3",           # Azul información
                "button_primary": "#2196f3",
                "button_hover": "#1976d2",
                "button_pressed": "#1565c0",
                "table_header": "#2d2d2d",
                "table_row_even": "#1e1e1e",
                "table_row_odd": "#252525",
                "table_selected": "#1a237e",
                "shadow_light": "rgba(0, 0, 0, 0.2)",
                "shadow_medium": "rgba(0, 0, 0, 0.3)",
                "shadow_strong": "rgba(0, 0, 0, 0.4)"
            }
        },

        "💼 Corporativo Azul": {
            "name": "corporate_blue",
            "description": "Diseño empresarial premium",
            "colors": {
                "primary": "#1565c0",        # Azul corporativo - Ratio 4.8:1
                "secondary": "#42a5f5",      # Azul medio accesible
                "accent": "#00acc1",         # Cian corporativo
                "background": "#f8f9fa",     # Gris azulado muy claro
                "surface": "#ffffff",        # Blanco superficie
                "surface_variant": "#eceff1", # Gris azulado claro
                "text_primary": "#263238",   # Azul gris oscuro - Ratio 12.6:1
                "text_secondary": "#546e7a", # Azul gris medio - Ratio 4.5:1
                "text_disabled": "#90a4ae",  # Gris azulado claro
                "border": "#cfd8dc",         # Borde azul gris
                "border_focus": "#1565c0",   # Borde foco azul
                "success": "#2e7d32",        # Verde corporativo
                "warning": "#ef6c00",        # Naranja corporativo
                "error": "#c62828",          # Rojo corporativo
                "info": "#1565c0",           # Azul información
                "button_primary": "#1565c0",
                "button_hover": "#0d47a1",
                "button_pressed": "#01579b",
                "table_header": "#eceff1",
                "table_row_even": "#ffffff",
                "table_row_odd": "#f8f9fa",
                "table_selected": "#e1f5fe",
                "shadow_light": "rgba(38, 50, 56, 0.08)",
                "shadow_medium": "rgba(38, 50, 56, 0.12)",
                "shadow_strong": "rgba(38, 50, 56, 0.16)"
            }
        },

        "🌿 Naturaleza Profesional": {
            "name": "nature_professional",
            "description": "Inspirado en la naturaleza, empresarial",
            "colors": {
                "primary": "#2e7d32",        # Verde Material - Ratio 4.5:1
                "secondary": "#66bb6a",      # Verde claro accesible
                "accent": "#8bc34a",         # Verde lima vibrante
                "background": "#f1f8e9",     # Verde muy suave
                "surface": "#ffffff",        # Blanco superficie
                "surface_variant": "#e8f5e8", # Verde muy claro
                "text_primary": "#1b5e20",   # Verde oscuro - Ratio 9.8:1
                "text_secondary": "#388e3c", # Verde medio - Ratio 4.5:1
                "text_disabled": "#a5d6a7",  # Verde claro deshabilitado
                "border": "#c8e6c9",         # Borde verde suave
                "border_focus": "#2e7d32",   # Borde foco verde
                "success": "#2e7d32",        # Verde éxito
                "warning": "#f57c00",        # Naranja advertencia
                "error": "#d32f2f",          # Rojo error
                "info": "#1976d2",           # Azul información
                "button_primary": "#2e7d32",
                "button_hover": "#1b5e20",
                "button_pressed": "#0d5302",
                "table_header": "#e8f5e8",
                "table_row_even": "#ffffff",
                "table_row_odd": "#f1f8e9",
                "table_selected": "#c8e6c9",
                "shadow_light": "rgba(27, 94, 32, 0.08)",
                "shadow_medium": "rgba(27, 94, 32, 0.12)",
                "shadow_strong": "rgba(27, 94, 32, 0.16)"
            }
        },

        # ===== TEMAS MODERNOS CREATIVOS =====
        "🟣 Morado Innovador": {
            "name": "purple_innovative",
            "description": "Inspiración tech y creatividad",
            "colors": {
                "primary": "#7c3aed",        # Morado vibrante profesional
                "secondary": "#8b5cf6",      # Morado claro
                "accent": "#ec4899",         # Rosa vibrante
                "background": "#faf5ff",     # Morado muy claro
                "surface": "#ffffff",        # Blanco superficie
                "surface_variant": "#f3e8ff", # Morado claro
                "text_primary": "#581c87",   # Morado muy oscuro
                "text_secondary": "#7c2d12", # Morado oscuro
                "text_disabled": "#c4b5fd",  # Morado claro deshabilitado
                "border": "#c4b5fd",         # Morado medio
                "border_focus": "#7c3aed",   # Borde foco morado
                "success": "#059669",        # Verde esmeralda
                "warning": "#d97706",        # Naranja
                "error": "#dc2626",          # Rojo
                "info": "#7c3aed",           # Morado información
                "button_primary": "#7c3aed",
                "button_hover": "#6d28d9",
                "button_pressed": "#5b21b6",
                "table_header": "#f3e8ff",
                "table_row_even": "#ffffff",
                "table_row_odd": "#faf5ff",
                "table_selected": "#e0e7ff",
                "shadow_light": "rgba(124, 58, 237, 0.08)",
                "shadow_medium": "rgba(124, 58, 237, 0.12)",
                "shadow_strong": "rgba(124, 58, 237, 0.16)"
            }
        },

        "🟠 Energía Profesional": {
            "name": "energy_professional",
            "description": "Dinámico y motivador",
            "colors": {
                "primary": "#ea580c",        # Naranja vibrante profesional
                "secondary": "#f97316",      # Naranja brillante
                "accent": "#fbbf24",         # Amarillo dorado
                "background": "#fff7ed",     # Naranja muy claro
                "surface": "#ffffff",        # Blanco superficie
                "surface_variant": "#fed7aa", # Naranja claro
                "text_primary": "#9a3412",   # Naranja muy oscuro
                "text_secondary": "#c2410c", # Naranja oscuro
                "text_disabled": "#fdba74",  # Naranja medio deshabilitado
                "border": "#fdba74",         # Naranja medio
                "border_focus": "#ea580c",   # Borde foco naranja
                "success": "#059669",        # Verde esmeralda
                "warning": "#d97706",        # Naranja
                "error": "#dc2626",          # Rojo
                "info": "#ea580c",           # Naranja información
                "button_primary": "#ea580c",
                "button_hover": "#dc2626",
                "button_pressed": "#b91c1c",
                "table_header": "#fed7aa",
                "table_row_even": "#ffffff",
                "table_row_odd": "#fff7ed",
                "table_selected": "#fef3c7",
                "shadow_light": "rgba(234, 88, 12, 0.08)",
                "shadow_medium": "rgba(234, 88, 12, 0.12)",
                "shadow_strong": "rgba(234, 88, 12, 0.16)"
            }
        },

        "⚫ Lujo Minimalista": {
            "name": "luxury_minimal",
            "description": "Sofisticado y elegante",
            "colors": {
                "primary": "#374151",           # Gris elegante profundo
                "secondary": "#4b5563",         # Gris medio elegante
                "accent": "#f59e0b",            # Ámbar dorado elegante
                "background": "#f9fafb",        # Gris muy claro sofisticado
                "surface": "#ffffff",          # Blanco superficie
                "surface_variant": "#f3f4f6",  # Gris claro elegante
                "text_primary": "#111827",      # Gris muy oscuro
                "text_secondary": "#6b7280",    # Gris medio
                "text_disabled": "#9ca3af",     # Gris claro deshabilitado
                "border": "#d1d5db",            # Gris claro para bordes
                "border_focus": "#374151",      # Borde foco gris oscuro
                "success": "#059669",           # Verde esmeralda
                "warning": "#d97706",           # Naranja
                "error": "#dc2626",             # Rojo
                "info": "#374151",              # Gris información
                "button_primary": "#374151",
                "button_hover": "#4b5563",
                "button_pressed": "#1f2937",
                "table_header": "#f3f4f6",
                "table_row_even": "#ffffff",
                "table_row_odd": "#f9fafb",
                "table_selected": "#f3f4f6",
                "shadow_light": "rgba(55, 65, 81, 0.08)",
                "shadow_medium": "rgba(55, 65, 81, 0.12)",
                "shadow_strong": "rgba(55, 65, 81, 0.16)"
            }
        },

        "🌊 Océano Tranquilo": {
            "name": "ocean_calm",
            "description": "Serenidad y productividad",
            "colors": {
                "primary": "#0891b2",           # Azul oceánico profundo
                "secondary": "#06b6d4",          # Cian brillante
                "accent": "#14b8a6",            # Verde esmeralda azulado
                "background": "#f0fdfa",        # Verde muy claro azulado
                "surface": "#ffffff",           # Blanco superficie
                "surface_variant": "#ccfbf1",   # Verde agua claro
                "text_primary": "#134e4a",      # Verde agua oscuro
                "text_secondary": "#436c7a",     # Azul medio
                "text_disabled": "#99f5e7",     # Verde agua claro deshabilitado
                "border": "#a7f3d0",            # Verde agua medio
                "border_focus": "#0891b2",      # Borde foco azul oceánico
                "success": "#059669",           # Verde esmeralda
                "warning": "#f59e0b",           # Ámbar
                "error": "#dc2626",             # Rojo
                "info": "#0891b2",              # Azul oceánico información
                "button_primary": "#0891b2",
                "button_hover": "#0e7490",
                "button_pressed": "#155e75",
                "table_header": "#ccfbf1",
                "table_row_even": "#ffffff",
                "table_row_odd": "#f0fdfa",
                "table_selected": "#a7f3d0",
                "shadow_light": "rgba(8, 145, 178, 0.08)",
                "shadow_medium": "rgba(8, 145, 178, 0.12)",
                "shadow_strong": "rgba(8, 145, 178, 0.16)"
            }
        },

        "🌸 Pastel Sofisticado": {
            "name": "pastel_sophisticated",
            "description": "Suave y moderno",
            "colors": {
                "primary": "#ec4899",           # Rosa vibrante suave
                "secondary": "#f472b6",         # Rosa medio
                "accent": "#a78bfa",            # Morado pastel
                "background": "#fefefe",        # Blanco puro
                "surface": "#ffffff",           # Blanco superficie
                "surface_variant": "#fdf2f8",   # Rosa muy claro
                "text_primary": "#831843",      # Rosa muy oscuro
                "text_secondary": "#9d174d",    # Rosa oscuro
                "text_disabled": "#f9a8d4",     # Rosa claro deshabilitado
                "border": "#fce7f3",           # Rosa claro para bordes
                "border_focus": "#ec4899",      # Borde foco rosa
                "success": "#10b981",           # Verde esmeralda suave
                "warning": "#f59e0b",           # Ámbar
                "error": "#ef4444",             # Rojo suave
                "info": "#3b82f6",              # Azul suave
                "button_primary": "#ec4899",
                "button_hover": "#db2777",
                "button_pressed": "#be185d",
                "table_header": "#fdf2f8",
                "table_row_even": "#ffffff",
                "table_row_odd": "#fefefe",
                "table_selected": "#fce7f3",
                "shadow_light": "rgba(236, 72, 153, 0.08)",
                "shadow_medium": "rgba(236, 72, 153, 0.12)",
                "shadow_strong": "rgba(236, 72, 153, 0.16)"
            }
        },

        "🎯 Ultra Moderno": {
            "name": "ultra_modern",
            "description": "Futurista y profesional",
            "colors": {
                "primary": "#6366f1",           # Índigo eléctrico
                "secondary": "#818cf8",         # Índigo claro
                "accent": "#06d6a0",            # Verde eléctrico
                "background": "#f8fafc",        # Gris ultra claro
                "surface": "#ffffff",           # Blanco superficie
                "surface_variant": "#f1f5f9",   # Gris muy claro
                "text_primary": "#0f172a",      # Negro ultra profundo
                "text_secondary": "#475569",    # Gris medio profundo
                "text_disabled": "#94a3b8",     # Gris claro
                "border": "#e2e8f0",           # Gris claro para bordes
                "border_focus": "#6366f1",      # Borde foco índigo
                "success": "#10b981",           # Verde esmeralda
                "warning": "#f59e0b",           # Ámbar
                "error": "#ef4444",             # Rojo
                "info": "#06b6d4",              # Cian
                "button_primary": "#6366f1",
                "button_hover": "#4f46e5",
                "button_pressed": "#4338ca",
                "table_header": "#f1f5f9",
                "table_row_even": "#ffffff",
                "table_row_odd": "#f8fafc",
                "table_selected": "#e0e7ff",
                "shadow_light": "rgba(99, 102, 241, 0.08)",
                "shadow_medium": "rgba(99, 102, 241, 0.12)",
                "shadow_strong": "rgba(99, 102, 241, 0.16)"
            }
        },

        # ===== TEMAS ESPECIALIZADOS =====
        "🎨 Diseño Creativo": {
            "name": "design_creative",
            "description": "Perfecto para diseñadores",
            "colors": {
                "primary": "#7c3aed",           # Morado creativo
                "secondary": "#a855f7",          # Morado medio
                "accent": "#f59e0b",             # Ámbar creativo
                "background": "#fefefe",         # Blanco puro
                "surface": "#ffffff",            # Blanco superficie
                "surface_variant": "#e0e7ff",   # Morado muy claro
                "text_primary": "#4c1d95",      # Morado muy oscuro
                "text_secondary": "#5529a6",    # Morado oscuro
                "text_disabled": "#c4b5fd",     # Morado claro deshabilitado
                "border": "#ddd6fe",            # Morado claro para bordes
                "border_focus": "#7c3aed",      # Borde foco morado
                "success": "#10b981",           # Verde esmeralda
                "warning": "#f59e0b",           # Ámbar
                "error": "#ef4444",              # Rojo
                "info": "#3b82f6",              # Azul
                "button_primary": "#7c3aed",
                "button_hover": "#6d28d9",
                "button_pressed": "#5b21b6",
                "table_header": "#e0e7ff",
                "table_row_even": "#ffffff",
                "table_row_odd": "#fefefe",
                "table_selected": "#ddd6fe",
                "shadow_light": "rgba(124, 58, 237, 0.08)",
                "shadow_medium": "rgba(124, 58, 237, 0.12)",
                "shadow_strong": "rgba(124, 58, 237, 0.16)"
            }
        },

        "⛅ Modo Productivo": {
            "name": "productive_mode",
            "description": "Enfoque y concentración",
            "colors": {
                "primary": "#059669",           # Verde productivo
                "secondary": "#10b981",         # Verde medio
                "accent": "#f59e0b",             # Ámbar atención
                "background": "#f0fdf4",        # Verde muy claro
                "surface": "#ffffff",           # Blanco superficie
                "surface_variant": "#dcfce7",   # Verde claro
                "text_primary": "#065f46",      # Verde muy oscuro
                "text_secondary": "#047857",    # Verde oscuro
                "text_disabled": "#86efac",    # Verde claro deshabilitado
                "border": "#bbf7d0",            # Verde medio claro
                "border_focus": "#059669",      # Borde foco verde
                "success": "#059669",           # Verde éxito
                "warning": "#f59e0b",           # Naranja atención
                "error": "#dc2626",             # Rojo
                "info": "#3b82f6",              # Azul información
                "button_primary": "#059669",
                "button_hover": "#047857",
                "button_pressed": "#065f46",
                "table_header": "#dcfce7",
                "table_row_even": "#ffffff",
                "table_row_odd": "#f0fdf4",
                "table_selected": "#bbf7d0",
                "shadow_light": "rgba(5, 150, 105, 0.08)",
                "shadow_medium": "rgba(5, 150, 105, 0.12)",
                "shadow_strong": "rgba(5, 150, 105, 0.16)"
            }
        }
    }

    @classmethod
    def get_theme_colors(cls, theme_name: str) -> Dict[str, str]:
        """Obtiene los colores de un tema específico CON CACHÉ"""
        # ✅ OPTIMIZACIÓN: Intentar obtener del caché primero
        from .theme_cache import theme_cache
        cached_colors = theme_cache.get_colors(theme_name)
        if cached_colors:
            return cached_colors
        
        # Verificar si el tema existe por nombre exacto
        if theme_name in cls.THEMES:
            colors = cls.THEMES[theme_name]["colors"]
            theme_cache.set_colors(theme_name, colors)
            return colors
        
        # Verificar por nombre interno (name)
        for theme_data in cls.THEMES.values():
            if theme_data["name"] == theme_name:
                colors = theme_data["colors"]
                theme_cache.set_colors(theme_name, colors)
                return colors

        # Compatibilidad con nombres antiguos
        theme_mapping = {
            "Moderno Claro": "🌞 Claro Elegante",
            "Moderno Oscuro": "🌙 Oscuro Profesional",
            "Profesional Azul": "💼 Corporativo Azul",
            "Naturaleza Verde": "🌿 Naturaleza Profesional"
        }
        
        if theme_name in theme_mapping:
            mapped_theme = theme_mapping[theme_name]
            from .logger import info
            info(f"Mapeando tema '{theme_name}' → '{mapped_theme}'")
            colors = cls.THEMES[mapped_theme]["colors"]
            theme_cache.set_colors(theme_name, colors)
            return colors

        # Si no se encuentra el tema, mostrar advertencia y usar el tema por defecto
        from .logger import warn
        warn(f"Tema '{theme_name}' no encontrado. Usando '🌞 Claro Elegante' por defecto.")
        colors = cls.THEMES["🌞 Claro Elegante"]["colors"]
        theme_cache.set_colors(theme_name, colors)
        return colors

    @classmethod
    def get_theme_names(cls) -> list:
        """Obtiene la lista de nombres de temas disponibles"""
        return list(cls.THEMES.keys())

    @classmethod
    def get_theme_by_name(cls, name: str) -> str:
        """Obtiene el nombre mostrado del tema por su nombre interno"""
        for display_name, theme_data in cls.THEMES.items():
            if theme_data["name"] == name:
                return display_name
        return "🌞 Claro Elegante"  # Fallback

    @classmethod
    def get_theme_description(cls, theme_name: str) -> str:
        """Obtiene la descripción de un tema"""
        if theme_name in cls.THEMES:
            return cls.THEMES[theme_name].get("description", "Tema profesional")
        return "Tema profesional"

    @classmethod
    def apply_theme_to_palette(cls, theme_name: str) -> QPalette:
        """Aplica un tema a una paleta de Qt CON CACHÉ"""
        # ✅ OPTIMIZACIÓN: Intentar obtener del caché primero
        from .theme_cache import theme_cache
        cached_palette = theme_cache.get_palette(theme_name)
        if cached_palette:
            return cached_palette
        
        colors = cls.get_theme_colors(theme_name)
        palette = QPalette()
        
        # Colores principales
        palette.setColor(QPalette.ColorRole.Window, QColor(colors["background"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(colors["text_primary"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(colors["surface"]))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors.get("surface_variant", colors["surface"])))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors["surface"]))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(colors["text_primary"]))
        palette.setColor(QPalette.ColorRole.Text, QColor(colors["text_primary"]))
        palette.setColor(QPalette.ColorRole.Button, QColor(colors["primary"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(colors["error"]))
        palette.setColor(QPalette.ColorRole.Link, QColor(colors["info"]))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(colors["primary"]))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        
        # ✅ Guardar en caché
        theme_cache.set_palette(theme_name, palette)
        
        return palette

    @classmethod
    def get_css_styles(cls, theme_name: str, font_size: int = 12) -> str:
        """Genera estilos CSS modernos CON CACHÉ - OPTIMIZADO"""
        # ✅ OPTIMIZACIÓN CRÍTICA: Intentar obtener del caché primero
        from .theme_cache import theme_cache
        cached_css = theme_cache.get_css(theme_name, font_size)
        if cached_css:
            return cached_css
        
        # Si no está en caché, generar y cachear
        colors = cls.get_theme_colors(theme_name)
        css = get_modern_css_styles(colors, font_size)
        theme_cache.set_css(theme_name, font_size, css)
        return css
    
    @classmethod
    def get_theme_color(cls, theme_name: str, color_key: str, fallback: str = "#000000") -> str:
        """
        Obtiene un color específico del tema de forma segura
        
        Args:
            theme_name: Nombre del tema
            color_key: Clave del color (ej: 'primary', 'background', 'text_primary')
            fallback: Color de respaldo si no se encuentra
        
        Returns:
            str: Color en formato hexadecimal
        """
        colors = cls.get_theme_colors(theme_name)
        return colors.get(color_key, fallback)
    
    @classmethod
    def get_semantic_color(cls, theme_name: str, semantic: str) -> str:
        """
        Obtiene un color semántico del tema (success, error, warning, info)
        
        Args:
            theme_name: Nombre del tema
            semantic: Tipo semántico ('success', 'error', 'warning', 'info')
        
        Returns:
            str: Color en formato hexadecimal
        """
        colors = cls.get_theme_colors(theme_name)
        semantic_map = {
            'success': colors.get('success', '#388e3c'),
            'error': colors.get('error', '#d32f2f'),
            'warning': colors.get('warning', '#f57c00'),
            'info': colors.get('info', colors.get('primary', '#1976d2'))
        }
        return semantic_map.get(semantic, colors.get('primary', '#1976d2'))
    
    @classmethod
    def format_css_with_theme(cls, theme_name: str, css_template: str) -> str:
        """
        Formatea un template CSS reemplazando variables de tema
        
        Args:
            theme_name: Nombre del tema
            css_template: Template CSS con placeholders {color_key}
        
        Returns:
            str: CSS formateado con colores del tema
        """
        colors = cls.get_theme_colors(theme_name)
        try:
            return css_template.format(**colors)
        except KeyError as e:
            from .logger import warn
            warn(f"Color no encontrado en template CSS: {e}")
            return css_template


# Compatibilidad con código legacy
Moderno_claro = "🌞 Claro Elegante"
Moderno_oscuro = "🌙 Oscuro Profesional"