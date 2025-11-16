#!/usr/bin/env python3
"""
Sistema de Transacciones y Rollback para el Organizador de Archivos
Permite deshacer operaciones de movimiento/eliminación de archivos
"""

import json
import shutil
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class OperationType(Enum):
    """Tipos de operaciones que se pueden deshacer"""
    MOVE = "move"
    DELETE = "delete"
    RENAME = "rename"
    CREATE_DIR = "create_dir"


class TransactionManager:
    """
    Gestor de transacciones con capacidad de rollback automático
    
    Registra todas las operaciones de archivos y permite revertirlas
    en caso de error o por petición del usuario.
    """
    
    def __init__(self, log_file: str = "operations_log.json"):
        """
        Inicializa el gestor de transacciones
        
        Args:
            log_file: Archivo donde se registran las operaciones
        """
        self.log_file = Path(log_file)
        self.current_transaction: Optional[str] = None
        self.operations: List[Dict[str, Any]] = []
        self.is_transaction_active = False
        self._load_log()
    
    def _load_log(self):
        """Carga el log de operaciones previas"""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.operations = data.get('operations', [])
        except (json.JSONDecodeError, IOError):
            self.operations = []
    
    def _save_log(self):
        """Guarda el log de operaciones"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'operations': self.operations,
                    'last_save': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"⚠️ Error guardando log: {e}")
    
    def begin_transaction(self, description: str = "") -> str:
        """
        Inicia una nueva transacción
        
        Args:
            description: Descripción de la transacción
            
        Returns:
            ID de la transacción
        """
        transaction_id = f"txn_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        self.current_transaction = transaction_id
        self.is_transaction_active = True
        
        # Agregar marcador de inicio de transacción
        self.operations.append({
            'type': 'transaction_begin',
            'transaction_id': transaction_id,
            'description': description,
            'timestamp': datetime.now().isoformat(),
            'operations_count': 0
        })
        
        self._save_log()
        return transaction_id
    
    def commit_transaction(self) -> bool:
        """
        Confirma la transacción actual
        
        Returns:
            True si se confirmó exitosamente
        """
        if not self.is_transaction_active:
            return False
        
        # Agregar marcador de fin de transacción
        self.operations.append({
            'type': 'transaction_commit',
            'transaction_id': self.current_transaction,
            'timestamp': datetime.now().isoformat()
        })
        
        self.is_transaction_active = False
        self.current_transaction = None
        self._save_log()
        return True
    
    def safe_move_file(self, source: Path, destination: Path) -> bool:
        """
        Mueve un archivo con validación y registro
        
        Args:
            source: Ruta origen
            destination: Ruta destino
            
        Returns:
            True si se movió exitosamente
        """
        try:
            # Validaciones previas
            if not source.exists():
                raise FileNotFoundError(f"Archivo origen no existe: {source}")
            
            if not os.access(source, os.R_OK):
                raise PermissionError(f"Sin permisos de lectura: {source}")
            
            dest_dir = destination.parent
            if not dest_dir.exists():
                dest_dir.mkdir(parents=True, exist_ok=True)
                # Registrar creación de directorio
                self._log_operation(OperationType.CREATE_DIR, {
                    'path': str(dest_dir)
                })
            
            if not os.access(dest_dir, os.W_OK):
                raise PermissionError(f"Sin permisos de escritura: {dest_dir}")
            
            # Verificar espacio disponible
            required_space = source.stat().st_size
            free_space = shutil.disk_usage(dest_dir).free
            if required_space > free_space:
                raise IOError(f"Espacio insuficiente: {required_space} > {free_space}")
            
            # Mover archivo
            shutil.move(str(source), str(destination))
            
            # Registrar operación
            self._log_operation(OperationType.MOVE, {
                'source': str(source),
                'destination': str(destination),
                'size': required_space
            })
            
            return True
            
        except Exception as e:
            print(f"❌ Error moviendo {source}: {e}")
            return False
    
    def safe_delete_file(self, file_path: Path, use_trash: bool = True) -> bool:
        """
        Elimina un archivo de forma segura
        
        Args:
            file_path: Ruta del archivo a eliminar
            use_trash: Si True, mueve a papelera en lugar de eliminar
            
        Returns:
            True si se eliminó exitosamente
        """
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"Archivo no existe: {file_path}")
            
            file_size = file_path.stat().st_size
            
            if use_trash:
                # Intentar mover a papelera
                try:
                    import send2trash
                    send2trash.send2trash(str(file_path))
                    operation_type = "delete_to_trash"
                except ImportError:
                    # Si send2trash no está disponible, eliminar directamente
                    file_path.unlink()
                    operation_type = "delete_permanent"
            else:
                file_path.unlink()
                operation_type = "delete_permanent"
            
            # Registrar operación
            self._log_operation(OperationType.DELETE, {
                'path': str(file_path),
                'size': file_size,
                'operation_type': operation_type
            })
            
            return True
            
        except Exception as e:
            print(f"❌ Error eliminando {file_path}: {e}")
            return False
    
    def safe_rename_file(self, old_path: Path, new_name: str) -> bool:
        """
        Renombra un archivo de forma segura
        
        Args:
            old_path: Ruta actual del archivo
            new_name: Nuevo nombre del archivo
            
        Returns:
            True si se renombró exitosamente
        """
        try:
            if not old_path.exists():
                raise FileNotFoundError(f"Archivo no existe: {old_path}")
            
            new_path = old_path.parent / new_name
            
            if new_path.exists():
                raise FileExistsError(f"Ya existe: {new_path}")
            
            old_path.rename(new_path)
            
            # Registrar operación
            self._log_operation(OperationType.RENAME, {
                'old_path': str(old_path),
                'new_path': str(new_path),
                'old_name': old_path.name,
                'new_name': new_name
            })
            
            return True
            
        except Exception as e:
            print(f"❌ Error renombrando {old_path}: {e}")
            return False
    
    def _log_operation(self, operation_type: OperationType, details: Dict[str, Any]):
        """
        Registra una operación en el log
        
        Args:
            operation_type: Tipo de operación
            details: Detalles específicos de la operación
        """
        operation = {
            'type': operation_type.value,
            'transaction_id': self.current_transaction,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        
        self.operations.append(operation)
        self._save_log()
    
    def rollback_transaction(self, transaction_id: Optional[str] = None) -> bool:
        """
        Revierte una transacción completa
        
        Args:
            transaction_id: ID de la transacción a revertir (None = última)
            
        Returns:
            True si se revirtió exitosamente
        """
        try:
            if transaction_id is None:
                transaction_id = self.current_transaction
            
            if not transaction_id:
                print("⚠️ No hay transacción activa para revertir")
                return False
            
            # Encontrar operaciones de la transacción
            transaction_ops = [
                op for op in self.operations 
                if op.get('transaction_id') == transaction_id and op.get('type') != 'transaction_begin'
            ]
            
            if not transaction_ops:
                print(f"⚠️ No se encontraron operaciones para la transacción {transaction_id}")
                return False
            
            # Revertir en orden inverso
            success_count = 0
            error_count = 0
            
            for op in reversed(transaction_ops):
                try:
                    if op['type'] == OperationType.MOVE.value:
                        # Revertir movimiento
                        source = Path(op['details']['source'])
                        destination = Path(op['details']['destination'])
                        
                        if destination.exists():
                            shutil.move(str(destination), str(source))
                            success_count += 1
                        else:
                            print(f"⚠️ No se puede revertir: {destination} no existe")
                            error_count += 1
                    
                    elif op['type'] == OperationType.RENAME.value:
                        # Revertir renombre
                        old_path = Path(op['details']['old_path'])
                        new_path = Path(op['details']['new_path'])
                        
                        if new_path.exists():
                            new_path.rename(old_path)
                            success_count += 1
                        else:
                            print(f"⚠️ No se puede revertir: {new_path} no existe")
                            error_count += 1
                    
                    elif op['type'] == OperationType.DELETE.value:
                        # No se puede recuperar archivos eliminados permanentemente
                        print(f"⚠️ No se puede recuperar archivo eliminado: {op['details']['path']}")
                        error_count += 1
                    
                except Exception as e:
                    print(f"❌ Error revirtiendo operación: {e}")
                    error_count += 1
            
            # Registrar resultado del rollback
            self.operations.append({
                'type': 'transaction_rollback',
                'transaction_id': transaction_id,
                'timestamp': datetime.now().isoformat(),
                'reverted_operations': success_count,
                'errors': error_count
            })
            
            self._save_log()
            
            print(f"✅ Rollback completado: {success_count} operaciones revertidas, {error_count} errores")
            return error_count == 0
            
        except Exception as e:
            print(f"❌ Error durante rollback: {e}")
            return False
    
    def get_transaction_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de transacciones
        
        Args:
            limit: Número máximo de transacciones a retornar
            
        Returns:
            Lista de transacciones
        """
        transactions = []
        current_txn = None
        
        for op in reversed(self.operations):
            if op.get('type') == 'transaction_begin':
                if current_txn:
                    transactions.append(current_txn)
                    if len(transactions) >= limit:
                        break
                
                current_txn = {
                    'id': op['transaction_id'],
                    'description': op.get('description', ''),
                    'timestamp': op['timestamp'],
                    'operations': []
                }
            
            elif current_txn and op.get('transaction_id') == current_txn['id']:
                if op.get('type') not in ['transaction_begin', 'transaction_commit']:
                    current_txn['operations'].append(op)
        
        if current_txn:
            transactions.append(current_txn)
        
        return transactions
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de operaciones
        
        Returns:
            Diccionario con estadísticas
        """
        total_ops = len([op for op in self.operations if op.get('type') in 
                        [OperationType.MOVE.value, OperationType.DELETE.value, OperationType.RENAME.value]])
        
        move_ops = len([op for op in self.operations if op.get('type') == OperationType.MOVE.value])
        delete_ops = len([op for op in self.operations if op.get('type') == OperationType.DELETE.value])
        rename_ops = len([op for op in self.operations if op.get('type') == OperationType.RENAME.value])
        
        rollbacks = len([op for op in self.operations if op.get('type') == 'transaction_rollback'])
        
        return {
            'total_operations': total_ops,
            'move_operations': move_ops,
            'delete_operations': delete_ops,
            'rename_operations': rename_ops,
            'rollbacks_performed': rollbacks,
            'transactions_count': len([op for op in self.operations if op.get('type') == 'transaction_begin'])
        }
    
    def clear_old_logs(self, days_old: int = 30):
        """
        Limpia logs antiguos
        
        Args:
            days_old: Días de antigüedad para limpiar
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        self.operations = [
            op for op in self.operations
            if datetime.fromisoformat(op['timestamp']) > cutoff_date
        ]
        
        self._save_log()
        print(f"✅ Logs antiguos limpiados (>{days_old} días)")
    
    def print_statistics(self):
        """Imprime estadísticas de forma legible"""
        stats = self.get_statistics()
        
        print("\n" + "="*60)
        print("📊 ESTADÍSTICAS DEL SISTEMA DE TRANSACCIONES")
        print("="*60)
        print(f"📁 Total de operaciones: {stats['total_operations']:,}")
        print(f"➡️  Movimientos: {stats['move_operations']:,}")
        print(f"🗑️  Eliminaciones: {stats['delete_operations']:,}")
        print(f"✏️  Renombrados: {stats['rename_operations']:,}")
        print(f"↩️  Rollbacks realizados: {stats['rollbacks_performed']:,}")
        print(f"📋 Transacciones registradas: {stats['transactions_count']:,}")
        print("="*60 + "\n")
