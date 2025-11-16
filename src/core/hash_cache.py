#!/usr/bin/env python3
"""
Sistema de Caché de Hashes para el Organizador de Archivos
Almacena hashes calculados previamente para evitar recálculos innecesarios
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional, Dict, Tuple
from datetime import datetime
import threading


class HashCache:
    """
    Caché persistente de hashes con invalidación automática por fecha de modificación
    
    Almacena hashes en SQLite para evitar recalcular archivos que no han cambiado.
    Esto puede acelerar análisis repetidos entre 10x y 50x.
    """
    
    def __init__(self, db_path: str = "hash_cache.db"):
        """
        Inicializa el sistema de caché
        
        Args:
            db_path: Ruta del archivo de base de datos SQLite
        """
        self.db_path = Path(db_path)
        self.lock = threading.Lock()  # Para acceso thread-safe
        self._create_tables()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Crea una nueva conexión a la base de datos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _create_tables(self):
        """Crea las tablas necesarias si no existen"""
        with self.lock:
            conn = self._get_connection()
            try:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS hash_cache (
                        file_path TEXT PRIMARY KEY,
                        file_size INTEGER NOT NULL,
                        mtime REAL NOT NULL,
                        hash_value TEXT NOT NULL,
                        algorithm TEXT NOT NULL,
                        cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        hit_count INTEGER DEFAULT 0
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_mtime ON hash_cache(mtime);
                    CREATE INDEX IF NOT EXISTS idx_algorithm ON hash_cache(algorithm);
                    CREATE INDEX IF NOT EXISTS idx_cached_at ON hash_cache(cached_at);
                    
                    -- Tabla de estadísticas
                    CREATE TABLE IF NOT EXISTS cache_stats (
                        id INTEGER PRIMARY KEY,
                        total_hits INTEGER DEFAULT 0,
                        total_misses INTEGER DEFAULT 0,
                        total_saved_time_seconds REAL DEFAULT 0,
                        last_cleanup TIMESTAMP
                    );
                    
                    -- Inicializar estadísticas si no existen
                    INSERT OR IGNORE INTO cache_stats (id) VALUES (1);
                """)
                conn.commit()
            finally:
                conn.close()
    
    def get_hash(self, file_path: Path, algorithm: str = 'md5') -> Optional[str]:
        """
        Obtiene el hash desde el caché si el archivo no ha sido modificado
        
        Args:
            file_path: Ruta del archivo
            algorithm: Algoritmo usado ('md5' o 'sha256')
        
        Returns:
            Hash del archivo si está en caché y es válido, None en caso contrario
        """
        try:
            # Obtener información actual del archivo
            stat = file_path.stat()
            current_mtime = stat.st_mtime
            current_size = stat.st_size
            file_path_str = str(file_path.resolve())
            
            with self.lock:
                conn = self._get_connection()
                try:
                    cursor = conn.execute("""
                        SELECT hash_value, mtime, file_size 
                        FROM hash_cache 
                        WHERE file_path = ? AND algorithm = ?
                    """, (file_path_str, algorithm))
                    
                    result = cursor.fetchone()
                    
                    if result:
                        cached_mtime = result['mtime']
                        cached_size = result['file_size']
                        
                        # Verificar si el archivo no ha cambiado
                        if cached_mtime == current_mtime and cached_size == current_size:
                            # Incrementar contador de hits
                            conn.execute("""
                                UPDATE hash_cache 
                                SET hit_count = hit_count + 1 
                                WHERE file_path = ? AND algorithm = ?
                            """, (file_path_str, algorithm))
                            
                            # Actualizar estadísticas globales
                            conn.execute("""
                                UPDATE cache_stats 
                                SET total_hits = total_hits + 1 
                                WHERE id = 1
                            """)
                            
                            conn.commit()
                            return result['hash_value']
                        else:
                            # Archivo modificado, eliminar entrada obsoleta
                            conn.execute("""
                                DELETE FROM hash_cache 
                                WHERE file_path = ? AND algorithm = ?
                            """, (file_path_str, algorithm))
                            conn.commit()
                    
                    # Cache miss
                    conn.execute("""
                        UPDATE cache_stats 
                        SET total_misses = total_misses + 1 
                        WHERE id = 1
                    """)
                    conn.commit()
                    
                finally:
                    conn.close()
            
            return None
            
        except (OSError, sqlite3.Error) as e:
            return None
    
    def save_hash(self, file_path: Path, hash_value: str, algorithm: str = 'md5'):
        """
        Guarda un hash en el caché
        
        Args:
            file_path: Ruta del archivo
            hash_value: Hash calculado
            algorithm: Algoritmo usado ('md5' o 'sha256')
        """
        try:
            stat = file_path.stat()
            mtime = stat.st_mtime
            file_size = stat.st_size
            file_path_str = str(file_path.resolve())
            
            with self.lock:
                conn = self._get_connection()
                try:
                    conn.execute("""
                        INSERT OR REPLACE INTO hash_cache 
                        (file_path, file_size, mtime, hash_value, algorithm, cached_at, hit_count)
                        VALUES (?, ?, ?, ?, ?, ?, COALESCE(
                            (SELECT hit_count FROM hash_cache WHERE file_path = ? AND algorithm = ?), 
                            0
                        ))
                    """, (file_path_str, file_size, mtime, hash_value, algorithm, 
                          datetime.now().isoformat(), file_path_str, algorithm))
                    
                    conn.commit()
                finally:
                    conn.close()
                    
        except (OSError, sqlite3.Error) as e:
            pass  # Silenciosamente ignorar errores de caché
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Obtiene estadísticas del caché
        
        Returns:
            Diccionario con estadísticas de uso del caché
        """
        with self.lock:
            conn = self._get_connection()
            try:
                # Estadísticas globales
                cursor = conn.execute("""
                    SELECT total_hits, total_misses, total_saved_time_seconds 
                    FROM cache_stats WHERE id = 1
                """)
                stats = cursor.fetchone()
                
                # Estadísticas de la tabla
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_entries,
                        SUM(hit_count) as total_hit_count,
                        AVG(hit_count) as avg_hits_per_entry
                    FROM hash_cache
                """)
                cache_stats = cursor.fetchone()
                
                # Calcular hit rate
                total_requests = stats['total_hits'] + stats['total_misses']
                hit_rate = (stats['total_hits'] / total_requests * 100) if total_requests > 0 else 0
                
                return {
                    'total_hits': stats['total_hits'],
                    'total_misses': stats['total_misses'],
                    'hit_rate_percentage': round(hit_rate, 2),
                    'total_entries': cache_stats['total_entries'],
                    'total_hit_count': cache_stats['total_hit_count'] or 0,
                    'avg_hits_per_entry': round(cache_stats['avg_hits_per_entry'] or 0, 2),
                    'estimated_time_saved_seconds': stats['total_saved_time_seconds']
                }
            finally:
                conn.close()
    
    def cleanup_old_entries(self, days_old: int = 30):
        """
        Elimina entradas antiguas que no se han usado recientemente
        
        Args:
            days_old: Número de días para considerar una entrada como antigua
        """
        with self.lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute("""
                    DELETE FROM hash_cache 
                    WHERE cached_at < datetime('now', '-' || ? || ' days')
                    AND hit_count < 2
                """, (days_old,))
                
                deleted = cursor.rowcount
                
                # Actualizar última limpieza
                conn.execute("""
                    UPDATE cache_stats 
                    SET last_cleanup = CURRENT_TIMESTAMP 
                    WHERE id = 1
                """)
                
                conn.commit()
                return deleted
            finally:
                conn.close()
    
    def clear_cache(self):
        """Limpia completamente el caché"""
        with self.lock:
            conn = self._get_connection()
            try:
                conn.execute("DELETE FROM hash_cache")
                conn.execute("""
                    UPDATE cache_stats 
                    SET total_hits = 0, total_misses = 0, total_saved_time_seconds = 0 
                    WHERE id = 1
                """)
                conn.commit()
            finally:
                conn.close()
    
    def get_cache_size(self) -> Tuple[int, float]:
        """
        Obtiene el tamaño del caché
        
        Returns:
            Tupla (número_de_entradas, tamaño_en_mb)
        """
        with self.lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute("SELECT COUNT(*) as count FROM hash_cache")
                count = cursor.fetchone()['count']
                
                # Tamaño del archivo de base de datos
                db_size_mb = self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
                
                return count, round(db_size_mb, 2)
            finally:
                conn.close()
    
    def print_statistics(self):
        """Imprime estadísticas del caché de forma legible"""
        stats = self.get_statistics()
        cache_size = self.get_cache_size()
        
        print("\n" + "="*60)
        print("📊 ESTADÍSTICAS DEL CACHÉ DE HASHES")
        print("="*60)
        print(f"✅ Cache Hits: {stats['total_hits']:,}")
        print(f"❌ Cache Misses: {stats['total_misses']:,}")
        print(f"📈 Hit Rate: {stats['hit_rate_percentage']:.2f}%")
        print(f"💾 Entradas en caché: {cache_size[0]:,}")
        print(f"📦 Tamaño del caché: {cache_size[1]:.2f} MB")
        print(f"⏱️  Tiempo estimado ahorrado: {stats['estimated_time_saved_seconds']:.1f}s")
        print("="*60 + "\n")
