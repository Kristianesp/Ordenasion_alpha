#!/usr/bin/env python3
"""
Configuración de la Aplicación
Maneja las preferencias del usuario como tema y tamaño de fuente
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class AppConfig:
    """Gestor de configuración de la aplicación"""
    
    DEFAULT_CONFIG = {
        "interface": {
            "font_size": 14,
            "theme": "Moderno Claro"  # TEMA CLARO COMO PREDETERMINADO PARA EVITAR PROBLEMAS
        },
        "categories": {
            "auto_save": True,
            "backup_enabled": True
        },
        "analysis": {
            "min_similarity": 70,
            "auto_analyze": True
        },
        "health": {
            "temperature": {
                "cool_min": 40,
                "moderate": 65,
                "high": 75,
                "critical": 85
            },
            "tbw_per_tb": 150,  # TB autorizados por TB de capacidad
            "tbw_bands": {
                "medium": 0.5,
                "high": 0.8
            },
            "tbw_by_type": {
                "nvme": 150,
                "ata": 150,
                "hdd": 0
            },
            "degrade_on_smart_fail": True,
            "hours_bands": {
                "moderate": 10000,
                "high": 30000,
                "very_high": 50000
            },
            "cycles_bands": {
                "moderate": 2000,
                "high": 10000
            },
            "weights": {
                "temp": 0.35,
                "tbw": 0.35,
                "hours": 0.20,
                "cycles": 0.10
            }
        }
    }
    
    def __init__(self, config_file: str = "app_config.json"):
        self.config_file = Path(config_file)
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Carga la configuración desde el archivo"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Fusionar con configuración por defecto
                    return self.merge_configs(self.DEFAULT_CONFIG, loaded_config)
            else:
                # Crear archivo con configuración por defecto
                self.save_config(self.DEFAULT_CONFIG)
                return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            from .logger import error
            error(f"Error cargando configuración: {e}")
            return self.DEFAULT_CONFIG.copy()
    
    def merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """Fusiona configuración por defecto con la cargada"""
        merged = default.copy()
        
        for key, value in loaded.items():
            if key in merged:
                if isinstance(value, dict) and isinstance(merged[key], dict):
                    merged[key] = self.merge_configs(merged[key], value)
                else:
                    merged[key] = value
        
        return merged
    
    def save_config(self, config: Optional[Dict] = None) -> bool:
        """Guarda la configuración en el archivo"""
        try:
            if config is None:
                config = self.config
            
            # Crear directorio si no existe
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            from .logger import error
            error(f"Error guardando configuración: {e}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración por ruta de claves"""
        try:
            keys = key_path.split('.')
            value = self.config
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
        except:
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """Establece un valor de configuración por ruta de claves"""
        try:
            keys = key_path.split('.')
            config = self.config
            
            # Navegar hasta el penúltimo nivel
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # Establecer el valor
            config[keys[-1]] = value
            
            # Guardar configuración
            return self.save_config()
        except Exception as e:
            from .logger import error
            error(f"Error estableciendo configuración: {e}")
            return False
    
    def get_font_size(self) -> int:
        """Obtiene el tamaño de fuente configurado"""
        return self.get("interface.font_size", 12)
    
    def set_font_size(self, size: int) -> bool:
        """Establece el tamaño de fuente"""
        return self.set("interface.font_size", size)
    
    def get_theme(self) -> str:
        """Obtiene el tema configurado"""
        return self.get("interface.theme", "Moderno Claro")
    
    def set_theme(self, theme: str) -> bool:
        """Establece el tema"""
        return self.set("interface.theme", theme)
    
    def get_min_similarity(self) -> int:
        """Obtiene el porcentaje mínimo de similitud"""
        return self.get("analysis.min_similarity", 70)
    
    def set_min_similarity(self, percentage: int) -> bool:
        """Establece el porcentaje mínimo de similitud"""
        return self.set("analysis.min_similarity", percentage)
    
    def reset_to_default(self) -> bool:
        """Restaura la configuración por defecto"""
        self.config = self.DEFAULT_CONFIG.copy()
        return self.save_config()
    
    def export_config(self, filepath: str) -> bool:
        """Exporta la configuración a un archivo"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            from .logger import error
            error(f"Error exportando configuración: {e}")
            return False
    
    def import_config(self, filepath: str) -> bool:
        """Importa configuración desde un archivo"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Fusionar con configuración actual
            self.config = self.merge_configs(self.config, imported_config)
            return self.save_config()
        except Exception as e:
            from .logger import error
            error(f"Error importando configuración: {e}")
            return False
