#!/usr/bin/env python3
"""
Logger unificado para Windows/EXE: imprime emojis cuando es posible y degrada a ASCII
sin interrumpir la ejecución. Provee niveles simples de logging y cache con TTL.
"""
import sys
import time
from typing import Callable, Dict, Any, Optional


def _safe_print(message: str) -> None:
    """Imprime mensajes con emojis de forma segura en Windows.
    Si la consola no soporta el carácter, lo omite sin romper la ejecución."""
    try:
        print(message)
    except UnicodeEncodeError:
        try:
            enc = sys.stdout.encoding or 'cp1252'
            safe = message.encode(enc, errors='ignore').decode(enc, errors='ignore')
            print(safe)
        except Exception:
            print(message.encode('ascii', errors='ignore').decode('ascii', errors='ignore'))


def _log(prefix: str, msg: str) -> None:
    _safe_print(f"{prefix} {msg}")


def info(msg: str) -> None:
    _log("ℹ️", msg)


def warn(msg: str) -> None:
    _log("⚠️", msg)


def error(msg: str) -> None:
    _log("❌", msg)


def debug(msg: str) -> None:
    # Debug no siempre con emoji para reducir ruido
    _safe_print(f"[DEBUG] {msg}")


def success(msg: str) -> None:
    _log("✅", msg)


def critical(msg: str) -> None:
    _log("🔴", msg)


class SmartCache:
    """Cache de sesión con TTL para datos SMART"""
    
    def __init__(self, ttl_seconds: int = 30):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl_seconds
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Obtiene datos del cache si no han expirado"""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if time.time() - entry['timestamp'] > self._ttl:
            del self._cache[key]
            return None
        
        return entry['data']
    
    def set(self, key: str, data: Dict[str, Any]) -> None:
        """Guarda datos en el cache con timestamp"""
        self._cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def clear(self) -> None:
        """Limpia todo el cache"""
        self._cache.clear()
    
    def size(self) -> int:
        """Retorna el número de entradas en el cache"""
        return len(self._cache)


