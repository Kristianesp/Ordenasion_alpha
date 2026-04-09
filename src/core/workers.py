#!/usr/bin/env python3
"""
Workers para el Organizador de Archivos
Maneja el procesamiento en segundo plano para análisis y organización
"""

import os
import shutil
import mimetypes
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter, defaultdict
from datetime import datetime

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox

from src.utils.constants import VARIOS_FOLDER
from .hash_manager import HashManager
from .transaction_manager import TransactionManager


class AnalysisWorker(QThread):
    """Worker para analizar carpetas y archivos en segundo plano"""

    # Señales para comunicación con la UI
    progress_update = pyqtSignal(str)
    analysis_complete = pyqtSignal(list, list, dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, folder_path: str, categories: Dict[str, List[str]], ext_to_categoria: Dict[str, str], min_percentage: int = 70, advanced_analysis: bool = True):
        super().__init__()
        self.folder_path = folder_path
        self.categories = categories
        self.ext_to_categoria = ext_to_categoria
        self.min_percentage = min_percentage  # Porcentaje mínimo de similitud
        self.advanced_analysis = advanced_analysis  # Nuevo: análisis avanzado
        self.hash_manager = HashManager()
        self.is_running = True
    
    def run(self):
        """Ejecuta el análisis de la carpeta"""
        try:
            self.progress_update.emit("🔍 Iniciando análisis de la carpeta...")
            
            # Analizar carpetas
            folder_movements = self.analyze_folders()
            self.progress_update.emit(f"📁 Analizadas {len(folder_movements)} carpetas")
            
            # Analizar archivos sueltos
            file_movements = self.analyze_loose_files()
            self.progress_update.emit(f"📄 Analizados {len(file_movements)} archivos sueltos")
            
            # Calcular estadísticas
            stats = self.calculate_statistics(folder_movements, file_movements)
            
            self.progress_update.emit("✅ Análisis completado exitosamente")
            self.analysis_complete.emit(folder_movements, file_movements, stats)
            
        except Exception as e:
            self.error_occurred.emit(f"❌ Error durante el análisis: {str(e)}")
    
    def analyze_folders(self) -> List[Dict[str, Any]]:
        """Analiza las carpetas en la ruta especificada"""
        folder_movements = []
        folder_path = Path(self.folder_path)
        
        if not folder_path.exists() or not folder_path.is_dir():
            return folder_movements
        
        # Obtener solo carpetas (no archivos)
        folders = [item for item in folder_path.iterdir() if item.is_dir()]
        
        for folder in folders:
            try:
                # FILTRO INTELIGENTE: Solo excluir carpetas del sistema críticas
                if self.is_system_folder(folder):
                    self.progress_update.emit(f"🚫 Excluyendo carpeta del sistema: {folder.name}")
                    continue
                
                # Analizar contenido de la carpeta
                total_files, total_size, category_counts = self.analyze_folder_content(folder)
                
                if total_files > 0:
                    # Determinar categoría principal
                    main_category = max(category_counts.items(), key=lambda x: x[1])[0]
                    percentage = (category_counts[main_category] / total_files) * 100
                    assigned_category = (
                        main_category if percentage >= self.min_percentage else "VARIOS"
                    )
                    
                    movement = {
                        'folder': folder,
                        'category': assigned_category,
                        'matched_category': main_category,
                        'total_files': total_files,
                        'size': total_size,
                        'percentage': percentage,
                        'extension': 'carpeta',
                        'category_counts': category_counts,
                        'is_expandable': True,
                        'below_similarity_threshold': percentage < self.min_percentage,
                    }
                    folder_movements.append(movement)
                    if percentage < self.min_percentage:
                        self.progress_update.emit(
                            f"📁 Carpeta marcada como VARIOS: {folder.name} ({percentage:.1f}% {main_category}, umbral {self.min_percentage}%)"
                        )
                    else:
                        self.progress_update.emit(
                            f"📁 Carpeta incluida: {folder.name} ({percentage:.1f}% {main_category})"
                        )
                else:
                    # Carpeta vacía - incluirla también
                    movement = {
                        'folder': folder,
                        'category': 'VARIOS',
                        'total_files': 0,
                        'size': 0,
                        'percentage': 0,
                        'extension': 'carpeta',
                        'category_counts': Counter(),
                        'is_expandable': True
                    }
                    folder_movements.append(movement)
                    self.progress_update.emit(f"📁 Carpeta vacía incluida: {folder.name}")
                    
            except Exception as e:
                self.progress_update.emit(f"⚠️ Error analizando carpeta {folder.name}: {str(e)}")
        
        return folder_movements
    
    def analyze_folder_content(self, folder_path: Path) -> tuple:
        """Analiza el contenido de una carpeta específica"""
        total_files = 0
        total_size = 0
        category_counts = Counter()
        
        try:
            # Intentar acceder al contenido de la carpeta
            for item in folder_path.iterdir():
                try:
                    if item.is_file():
                        total_files += 1
                        try:
                            total_size += item.stat().st_size
                        except (OSError, PermissionError):
                            # Si no se puede obtener el tamaño, continuar
                            pass
                        
                        # Categorizar archivo
                        category = self._categorize_path(item)
                        category_counts[category] += 1
                        
                except (PermissionError, OSError):
                    # Ignorar archivos individuales sin permisos
                    continue
                    
        except PermissionError:
            self.progress_update.emit(f"⚠️ Sin permisos para acceder a {folder_path.name}")
        except Exception as e:
            self.progress_update.emit(f"⚠️ Error analizando contenido de {folder_path.name}: {str(e)}")
        
        return total_files, total_size, category_counts
    
    def is_system_folder(self, folder_path: Path) -> bool:
        """Determina si una carpeta es del sistema y debe ser excluida"""
        folder_name = folder_path.name.lower()
        
        # CARPETAS DEL SISTEMA CRÍTICAS que SÍ deben filtrarse
        system_folders = {
            'program files',
            'program files (x86)', 
            'windows',
            'windowsapps',
            'wpsystem',
            'system volume information',
            '$recycle.bin',
            'recovery',
            'config.msi',
            'msdownld.tmp'  # Solo si es del sistema, no del usuario
        }
        
        # Verificar si es carpeta del sistema
        if folder_name in system_folders:
            return True
        
        # Verificar si está en rutas del sistema
        try:
            # Verificar si está en C:\Windows o C:\Program Files
            if 'windows' in str(folder_path).lower() or 'program files' in str(folder_path).lower():
                return True
        except:
            pass
        
        # Verificar si es carpeta oculta del sistema
        try:
            if folder_path.is_dir() and folder_path.stat().st_file_attributes & 0x2:  # Hidden
                if folder_name.startswith('$') or folder_name.startswith('.'):
                    return True
        except:
            pass
        
        # NO es carpeta del sistema - incluirla
        return False
    
    def get_folder_contents(self, folder_path: Path) -> List[Dict[str, Any]]:
        """Obtiene el contenido detallado de una carpeta para expansión"""
        contents = []
        
        try:
            for item in folder_path.iterdir():
                try:
                    if item.is_file():
                        # Archivo individual
                        file_size = 0
                        try:
                            file_size = item.stat().st_size
                        except (OSError, PermissionError):
                            pass
                        
                        extension = item.suffix.lower()
                        category = self._categorize_path(item)
                        
                        contents.append({
                            'type': 'file',
                            'path': item,
                            'name': item.name,
                            'size': file_size,
                            'category': category,
                            'extension': extension
                        })
                    elif item.is_dir():
                        # Subcarpeta
                        try:
                            sub_files = len([f for f in item.iterdir() if f.is_file()])
                            contents.append({
                                'type': 'subfolder',
                                'path': item,
                                'name': item.name,
                                'file_count': sub_files,
                                'is_expandable': True
                            })
                        except (PermissionError, OSError):
                            # Subcarpeta sin permisos
                            contents.append({
                                'type': 'subfolder',
                                'path': item,
                                'name': item.name,
                                'file_count': 0,
                                'is_expandable': False,
                                'no_access': True
                            })
                            
                except (PermissionError, OSError):
                    continue
                    
        except PermissionError:
            self.progress_update.emit(f"⚠️ Sin permisos para acceder a {folder_path.name}")
        except Exception as e:
            self.progress_update.emit(f"⚠️ Error obteniendo contenido de {folder_path.name}: {str(e)}")
        
        return contents
    
    def analyze_loose_files(self) -> List[Dict[str, Any]]:
        """Analiza archivos sueltos en la carpeta principal con análisis avanzado"""
        file_movements = []
        folder_path = Path(self.folder_path)

        if not folder_path.exists() or not folder_path.is_dir():
            return file_movements

        try:
            # Obtener solo archivos (no carpetas)
            files = [item for item in folder_path.iterdir() if item.is_file()]

            for file in files:
                try:
                    # Información básica del archivo
                    file_size = file.stat().st_size
                    extension = file.suffix.lower()
                    file_date = file.stat().st_mtime

                    # Categorizar archivo
                    category = self._categorize_path(file)

                    # Análisis avanzado (si está habilitado)
                    advanced_info = {}
                    if self.advanced_analysis:
                        advanced_info = self._get_advanced_file_info(file)

                    # Crear diccionario completo del archivo
                    movement = {
                        'file': file,
                        'category': category,
                        'extension': extension,
                        'size': file_size,
                        'date': file_date,
                        'advanced_info': advanced_info,
                        'is_expandable': True  # Para mostrar detalles avanzados
                    }

                    # Agregar información adicional para UI
                    if advanced_info:
                        movement.update({
                            'has_advanced_info': True,
                            'file_type': advanced_info.get('type', 'unknown'),
                            'description': advanced_info.get('description', ''),
                            'metadata': advanced_info.get('metadata', {})
                        })

                    file_movements.append(movement)

                except Exception as e:
                    self.progress_update.emit(f"⚠️ Error analizando archivo {file.name}: {str(e)}")

        except Exception as e:
            self.progress_update.emit(f"⚠️ Error accediendo a archivos sueltos: {str(e)}")

        return file_movements

    def _get_advanced_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Obtiene información avanzada de un archivo"""
        info = {
            'type': 'file',
            'description': '',
            'metadata': {},
            'hash': None
        }

        try:
            # Obtener información básica
            stat = file_path.stat()
            info['metadata'] = {
                'size_bytes': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'accessed': datetime.fromtimestamp(stat.st_atime)
            }

            # Calcular hash para archivos pequeños (optimización)
            if stat.st_size < 50 * 1024 * 1024:  # Menos de 50MB
                hash_value = self.hash_manager.calculate_file_hash(file_path, 'md5')
                if hash_value:
                    info['hash'] = hash_value

            # Detectar tipo de archivo por extensión
            ext = file_path.suffix.lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']:
                info['type'] = 'image'
                info['description'] = 'Imagen'
            elif ext in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm']:
                info['type'] = 'video'
                info['description'] = 'Video'
            elif ext in ['.mp3', '.flac', '.wav', '.m4a', '.aac', '.ogg']:
                info['type'] = 'audio'
                info['description'] = 'Audio'
            elif ext in ['.pdf', '.doc', '.docx', '.txt', '.rtf']:
                info['type'] = 'document'
                info['description'] = 'Documento'
            elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                info['type'] = 'archive'
                info['description'] = 'Archivo comprimido'
            elif ext in ['.exe', '.msi', '.deb', '.rpm', '.dmg']:
                info['type'] = 'executable'
                info['description'] = 'Ejecutable'
            else:
                info['type'] = 'file'
                info['description'] = f'Archivo {ext.upper()}'

        except Exception as e:
            info['description'] = f'Error obteniendo información: {str(e)}'

        return info

    def _categorize_path(self, file_path: Path) -> str:
        """Categoriza usando extensión y heurísticas simples para reducir VARIOS."""
        extension = file_path.suffix.lower()
        category = self.ext_to_categoria.get(extension)
        if category:
            return category

        guessed_type, _ = mimetypes.guess_type(str(file_path))
        if guessed_type:
            top_level_type = guessed_type.split("/", 1)[0]
            if top_level_type == "audio":
                return "MUSICA"
            if top_level_type == "video":
                return "VIDEOS"
            if top_level_type == "image":
                return "IMAGENES"
            if any(
                token in guessed_type
                for token in ("pdf", "word", "sheet", "presentation", "json", "xml")
            ):
                return "DOCUMENTOS"

        filename = file_path.name.lower()
        token_map = {
            "MUSICA": ("track", "album", "song", "mix", "audio"),
            "VIDEOS": ("movie", "trailer", "video", "clip", "episode"),
            "IMAGENES": ("img", "screenshot", "photo", "wallpaper", "camera"),
            "DOCUMENTOS": ("invoice", "report", "manual", "doc", "cv", "resume", "readme"),
            "CODIGO": ("package", "docker", "config", "script", "source", "setup"),
        }
        for guessed_category, tokens in token_map.items():
            if any(token in filename for token in tokens):
                return guessed_category

        return "VARIOS"
    
    def calculate_statistics(self, folder_movements: List[Dict], file_movements: List[Dict]) -> Dict[str, Any]:
        """Calcula estadísticas generales del análisis"""
        total_folders = len(folder_movements)
        total_files = len(file_movements)
        total_size = sum(mov.get('size', 0) for mov in folder_movements + file_movements)
        
        # Estadísticas por categoría
        category_stats = defaultdict(lambda: {'count': 0, 'size': 0})
        
        # Contar carpetas por categoría
        for mov in folder_movements:
            category = mov['category']
            category_stats[category]['count'] += 1
            category_stats[category]['size'] += mov.get('size', 0)
        
        # Contar archivos por categoría
        for mov in file_movements:
            category = mov['category']
            category_stats[category]['count'] += 1
            category_stats[category]['size'] += mov.get('size', 0)
        
        return {
            'total_folders': total_folders,
            'total_files': total_files,
            'total_size': total_size,
            'category_stats': dict(category_stats)
        }
    
    def stop(self):
        """Detiene el worker"""
        self.is_running = False


class OrganizeWorker(QThread):
    """Worker para organizar archivos y carpetas en segundo plano
    🚀 MEJORADO: Con sistema de transacciones y rollback automático"""
    
    # Señales para comunicación con la UI
    progress_update = pyqtSignal(str)
    organize_complete = pyqtSignal(bool, str)
    rollback_available = pyqtSignal(str)  # Nueva señal para indicar que hay rollback disponible
    
    def __init__(self, source_folder: str, folder_movements: List[Dict], file_movements: List[Dict], 
                 organize_by_date: bool = False, check_duplicates: bool = False):
        super().__init__()
        self.source_folder = source_folder
        self.folder_movements = folder_movements
        self.file_movements = file_movements
        self.is_running = True
        self.transaction_manager = TransactionManager()
        self.current_transaction_id = None
        self.organize_by_date = organize_by_date
        self.check_duplicates = check_duplicates
        self.hash_manager = HashManager()
        self._moved_files = []  # Track moved files for duplicate checking
    
    def run(self):
        """Ejecuta la organización de archivos y carpetas con transacciones"""
        try:
            # 🚀 MEJORA: Iniciar transacción
            total_items = len(self.folder_movements) + len(self.file_movements)
            self.current_transaction_id = self.transaction_manager.begin_transaction(
                f"Organización de {total_items} elementos en {self.source_folder}"
            )
            
            self.progress_update.emit("🚀 Iniciando organización con protección de datos...")
            
            # Crear estructura de carpetas de destino
            self.create_destination_structure()
            
            # Mover carpetas
            self.move_folders()
            
            # Mover archivos sueltos
            self.move_loose_files()
            
            # 🚀 MEJORA: Confirmar transacción
            self.transaction_manager.commit_transaction()
            
            self.progress_update.emit("✅ Organización completada exitosamente")
            self.organize_complete.emit(True, "Organización completada exitosamente")
            
            # Emitir señal de rollback disponible
            self.rollback_available.emit(self.current_transaction_id)
            
        except Exception as e:
            error_msg = f"❌ Error durante la organización: {str(e)}"
            self.progress_update.emit(error_msg)
            
            # 🚀 MEJORA: Intentar rollback automático
            if self.current_transaction_id:
                self.progress_update.emit("🔄 Intentando revertir cambios...")
                if self.transaction_manager.rollback_transaction(self.current_transaction_id):
                    error_msg += "\n✅ Cambios revertidos exitosamente"
                else:
                    error_msg += "\n⚠️ No se pudieron revertir todos los cambios"
            
            self.organize_complete.emit(False, error_msg)
    
    def create_destination_structure(self):
        """Crea la estructura de carpetas de destino solo si no existen"""
        try:
            # Crear carpeta VARIOS si no existe
            varios_path = Path(self.source_folder) / VARIOS_FOLDER
            if not varios_path.exists():
                varios_path.mkdir(exist_ok=True)
                self.progress_update.emit(f"📁 Creada carpeta: {VARIOS_FOLDER}")
            
            # Crear carpetas para cada categoría solo si no existen
            categories = set()
            for mov in self.folder_movements:
                categories.add(mov['category'])
            for mov in self.file_movements:
                categories.add(mov['category'])
                for candidate in self._build_destination_candidates(
                    mov.get('file'), mov['category']
                ):
                    if candidate != Path(self.source_folder):
                        categories.add(str(candidate.relative_to(Path(self.source_folder))))
            
            created_folders = []
            existing_folders = []
            
            for category in categories:
                if category != "VARIOS":
                    category_path = Path(self.source_folder) / category
                    if not category_path.exists():
                        category_path.mkdir(exist_ok=True)
                        created_folders.append(category)
                    else:
                        existing_folders.append(category)
            
            # Informar sobre carpetas creadas y existentes
            if created_folders:
                self.progress_update.emit(f"📁 Carpetas creadas: {', '.join(created_folders)}")
            if existing_folders:
                self.progress_update.emit(f"📁 Carpetas existentes (reutilizadas): {', '.join(existing_folders)}")
            
            if not created_folders and not existing_folders:
                self.progress_update.emit("📁 No se requieren nuevas carpetas")
            elif not created_folders:
                self.progress_update.emit("📁 Todas las carpetas ya existían")
            elif not existing_folders:
                self.progress_update.emit("📁 Estructura de carpetas creada completamente")
            
        except Exception as e:
            raise Exception(f"Error creando estructura de carpetas: {str(e)}")
    
    def move_folders(self):
        """Mueve las carpetas a sus ubicaciones de destino"""
        try:
            for i, mov in enumerate(self.folder_movements):
                if not self.is_running:
                    break
                
                folder = mov['folder']
                category = mov['category']
                
                # Determinar ruta de destino
                if category == "VARIOS":
                    dest_path = Path(self.source_folder) / VARIOS_FOLDER / folder.name
                else:
                    dest_path = Path(self.source_folder) / category / folder.name
                
                # Mover carpeta con transacción
                if dest_path.exists():
                    # Si ya existe, añadir sufijo numérico
                    counter = 1
                    while dest_path.exists():
                        new_name = f"{folder.name}_{counter}"
                        dest_path = dest_path.parent / new_name
                        counter += 1
                
                # 🚀 MEJORA: Usar safe_move_file del transaction_manager
                if self.transaction_manager.safe_move_file(folder, dest_path):
                    progress = f"📁 Movida carpeta: {folder.name} → {category}"
                    self.progress_update.emit(progress)
                else:
                    self.progress_update.emit(f"⚠️ Error moviendo carpeta: {folder.name}")
                
        except Exception as e:
            raise Exception(f"Error moviendo carpetas: {str(e)}")
    
    def move_loose_files(self):
        """Mueve los archivos sueltos a sus carpetas de destino"""
        try:
            for i, mov in enumerate(self.file_movements):
                if not self.is_running:
                    break
                
                file = mov['file']
                category = mov['category']
                
                # Determinar ruta de destino
                dest_path = self._resolve_file_destination(file, category)
                
                # Mover archivo
                if dest_path.exists():
                    if self.check_duplicates and self._is_duplicate_file(file, dest_path):
                        self.progress_update.emit(
                            f"⏭️ Duplicado omitido: {file.name} ya existe en {dest_path.parent}"
                        )
                        continue
                    # Si ya existe, añadir sufijo numérico
                    counter = 1
                    while dest_path.exists():
                        name_without_ext = file.stem
                        extension = file.suffix
                        new_name = f"{name_without_ext}_{counter}{extension}"
                        dest_path = dest_path.parent / new_name
                        counter += 1
                
                # Mostrar información sobre la carpeta de destino
                dest_folder = dest_path.parent.name
                if dest_folder == category:
                    progress = f"📄 Movido archivo: {file.name} → {category}/"
                else:
                    progress = f"📄 Movido archivo: {file.name} → {dest_folder}/"
                
                # 🚀 MEJORA: Usar safe_move_file del transaction_manager
                if self.transaction_manager.safe_move_file(file, dest_path):
                    self.progress_update.emit(progress)
                else:
                    self.progress_update.emit(f"⚠️ Error moviendo archivo: {file.name}")
                
        except Exception as e:
            raise Exception(f"Error moviendo archivos: {str(e)}")
    
    def stop(self):
        """Detiene el worker"""
        self.is_running = False

    def _resolve_file_destination(self, file_path: Path, category: str) -> Path:
        """Construye el destino final del archivo respetando organización por fecha."""
        if category == "VARIOS":
            base_dir = Path(self.source_folder) / VARIOS_FOLDER
        else:
            base_dir = Path(self.source_folder) / category

        if self.organize_by_date:
            modified = datetime.fromtimestamp(file_path.stat().st_mtime)
            base_dir = base_dir / str(modified.year) / f"{modified.month:02d}"

        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir / file_path.name

    def _build_destination_candidates(self, file_path: Path | None, category: str) -> List[Path]:
        """Retorna carpetas potenciales de destino para pre-crear estructura."""
        if category == "VARIOS":
            base_dir = Path(self.source_folder) / VARIOS_FOLDER
        else:
            base_dir = Path(self.source_folder) / category
        if not file_path or not self.organize_by_date:
            return [base_dir]
        modified = datetime.fromtimestamp(file_path.stat().st_mtime)
        year_dir = base_dir / str(modified.year)
        month_dir = year_dir / f"{modified.month:02d}"
        return [base_dir, year_dir, month_dir]

    def _is_duplicate_file(self, source: Path, destination: Path) -> bool:
        """Verifica si origen y destino son archivos idénticos."""
        if not destination.exists() or not destination.is_file():
            return False
        try:
            if source.stat().st_size != destination.stat().st_size:
                return False
            source_hash = self.hash_manager.calculate_file_hash(source, 'md5')
            dest_hash = self.hash_manager.calculate_file_hash(destination, 'md5')
            return bool(source_hash and source_hash == dest_hash)
        except Exception:
            return False
