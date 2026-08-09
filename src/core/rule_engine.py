#!/usr/bin/env python3
"""
Motor de reglas personalizadas para el Organizador de Archivos
Permite crear reglas avanzadas de categorizacion basadas en patrones
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class Rule:
    """Regla individual de categorizacion"""
    
    def __init__(self, rule_id: str, name: str, pattern: str, 
                 category: str, rule_type: str = "name", 
                 priority: int = 0, enabled: bool = True):
        self.rule_id = rule_id
        self.name = name
        self.pattern = pattern
        self.category = category
        self.rule_type = rule_type  # name, extension, regex, size, date
        self.priority = priority
        self.enabled = enabled
        self.created = datetime.now()
        self.match_count = 0
    
    def matches(self, file_path: Path) -> bool:
        """Verifica si el archivo coincide con esta regla"""
        if not self.enabled:
            return False
        
        try:
            if self.rule_type == "name":
                return self.pattern.lower() in file_path.name.lower()
            elif self.rule_type == "extension":
                return file_path.suffix.lower() == self.pattern.lower()
            elif self.rule_type == "regex":
                return bool(re.search(self.pattern, str(file_path), re.IGNORECASE))
            elif self.rule_type == "size":
                # Formato: "min-max" en bytes, ej: "1048576-" para >1MB
                size = file_path.stat().st_size
                return self._check_size(size)
            elif self.rule_type == "date":
                # Formato: "before:YYYY-MM-DD" o "after:YYYY-MM-DD"
                return self._check_date(file_path)
            return False
        except Exception:
            return False
    
    def _check_size(self, file_size: int) -> bool:
        """Verifica regla de tamaño"""
        pattern = self.pattern.strip()
        if pattern.startswith(">"):
            return file_size > int(pattern[1:])
        elif pattern.startswith("<"):
            return file_size < int(pattern[1:])
        elif "-" in pattern:
            parts = pattern.split("-")
            min_size = int(parts[0]) if parts[0] else 0
            max_size = int(parts[1]) if parts[1] else float('inf')
            return min_size <= file_size <= max_size
        return False
    
    def _check_date(self, file_path: Path) -> bool:
        """Verifica regla de fecha"""
        pattern = self.pattern.strip()
        mtime = file_path.stat().st_mtime
        file_date = datetime.fromtimestamp(mtime)
        
        if pattern.startswith("before:"):
            target = datetime.strptime(pattern[7:], "%Y-%m-%d")
            return file_date < target
        elif pattern.startswith("after:"):
            target = datetime.strptime(pattern[6:], "%Y-%m-%d")
            return file_date > target
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serializacion"""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'pattern': self.pattern,
            'category': self.category,
            'rule_type': self.rule_type,
            'priority': self.priority,
            'enabled': self.enabled,
            'match_count': self.match_count,
            'created': self.created.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rule':
        """Crea regla desde diccionario"""
        rule = cls(
            rule_id=data.get('rule_id', ''),
            name=data['name'],
            pattern=data['pattern'],
            category=data['category'],
            rule_type=data.get('rule_type', 'name'),
            priority=data.get('priority', 0),
            enabled=data.get('enabled', True)
        )
        rule.match_count = data.get('match_count', 0)
        if 'created' in data:
            try:
                rule.created = datetime.fromisoformat(data['created'])
            except ValueError:
                pass
        return rule


class RuleEngine:
    """Motor de reglas para categorizacion avanzada"""
    
    def __init__(self):
        self.rules: List[Rule] = []
        self._next_id = 1
    
    def add_rule(self, name: str, pattern: str, category: str,
                 rule_type: str = "name", priority: int = 0) -> Rule:
        """Anade una nueva regla"""
        rule = Rule(
            rule_id=f"rule_{self._next_id}",
            name=name,
            pattern=pattern,
            category=category,
            rule_type=rule_type,
            priority=priority
        )
        self.rules.append(rule)
        self._next_id += 1
        return rule
    
    def remove_rule(self, rule_id: str) -> bool:
        """Elimina una regla por ID"""
        for i, rule in enumerate(self.rules):
            if rule.rule_id == rule_id:
                del self.rules[i]
                return True
        return False
    
    def update_rule(self, rule_id: str, **kwargs) -> bool:
        """Actualiza una regla existente"""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                for key, value in kwargs.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                return True
        return False
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Obtiene una regla por ID"""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule
        return None
    
    def get_rules(self, enabled_only: bool = False) -> List[Rule]:
        """Obtiene todas las reglas"""
        if enabled_only:
            return [r for r in self.rules if r.enabled]
        return list(self.rules)
    
    def toggle_rule(self, rule_id: str) -> bool:
        """Activa/desactiva una regla"""
        rule = self.get_rule(rule_id)
        if rule:
            rule.enabled = not rule.enabled
            return True
        return False
    
    def categorize_file(self, file_path: Path) -> Optional[str]:
        """Categoriza un archivo usando las reglas (por prioridad)"""
        sorted_rules = sorted(self.rules, key=lambda r: r.priority, reverse=True)
        
        for rule in sorted_rules:
            if rule.matches(file_path):
                rule.match_count += 1
                return rule.category
        return None
    
    def get_matching_rules(self, file_path: Path) -> List[Rule]:
        """Obtiene todas las reglas que coinciden con un archivo"""
        return [r for r in self.rules if r.matches(file_path)]
    
    def export_rules(self) -> List[Dict[str, Any]]:
        """Exporta reglas como lista de diccionarios"""
        return [r.to_dict() for r in self.rules]
    
    def import_rules(self, rules_data: List[Dict[str, Any]]) -> int:
        """Importa reglas desde lista de diccionarios"""
        count = 0
        for data in rules_data:
            try:
                rule = Rule.from_dict(data)
                self.rules.append(rule)
                if self._next_id <= int(rule.rule_id.split('_')[1]):
                    self._next_id = int(rule.rule_id.split('_')[1]) + 1
                count += 1
            except Exception:
                pass
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Estadisticas de reglas"""
        total = len(self.rules)
        enabled = sum(1 for r in self.rules if r.enabled)
        total_matches = sum(r.match_count for r in self.rules)
        
        by_type = {}
        for rule in self.rules:
            by_type[rule.rule_type] = by_type.get(rule.rule_type, 0) + 1
        
        return {
            'total_rules': total,
            'enabled_rules': enabled,
            'disabled_rules': total - enabled,
            'total_matches': total_matches,
            'by_type': by_type
        }