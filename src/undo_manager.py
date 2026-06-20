#!/usr/bin/env python3
"""
undo_manager.py - Gestor de Undo/Redo para Downloads Organizer Pro.

Versión SQLite: Reemplaza el almacenamiento JSON por base de datos SQLite
para proporcionar un historial robusto con soporte para transacciones ACID.

Características:
- Integración con DatabaseManager (SQLite).
- Migración automática desde JSON legacy.
- Métodos públicos compatibles con la GUI existente.
- Soporte para múltiples sesiones.
- Consultas eficientes mediante índices.

Autor: Juan Carlos Blanco Ruiz
"""

import os
import shutil
from pathlib import Path
from typing import Tuple, Dict, List, Optional


class UndoManager:
    """Gestiona las operaciones de deshacer/rehacer usando SQLite."""

    def __init__(self, db_manager=None):
        """
        Inicializa el gestor de undo/redo.
        
        :param db_manager: Instancia de DatabaseManager (opcional, se crea si no se proporciona)
        """
        if db_manager is None:
            from db_manager import DatabaseManager
            self.db = DatabaseManager()
        else:
            self.db = db_manager
        
        self._current_session_id = None

    @property
    def session_id(self) -> str:
        """Retorna o genera el ID de sesión actual."""
        if self._current_session_id is None:
            import uuid
            self._current_session_id = str(uuid.uuid4())[:8]
        return self._current_session_id

    def record_action(self, action_type: str, source: str, destination: str, 
                      file_size: int = 0) -> int:
        """
        Registra una nueva acción en el historial.
        
        :param action_type: Tipo de acción ('move', 'delete', 'rename')
        :param source: Ruta de origen
        :param destination: Ruta de destino
        :param file_size: Tamaño del archivo en bytes
        :return: ID de la acción registrada
        """
        action_id = self.db.record_action(
            action_type=action_type,
            source_path=source,
            destination_path=destination,
            file_size=file_size,
            session_id=self.session_id,
            undone=0,
            redone=0
        )
        return action_id

    def undo(self) -> Tuple[bool, str]:
        """
        Deshace la última acción registrada.
        
        :return: Tupla (éxito, mensaje)
        """
        try:
            undo_stack = self.db.get_undo_stack(limit=1)
            
            if not undo_stack:
                return False, "No hay acciones para deshacer."
            
            last_action = undo_stack[0]
            action_id = last_action['id']
            action_type = last_action['action_type']
            source = last_action['source_path']
            destination = last_action['destination_path']
            
            # Ejecutar la operación inversa
            success, msg = self._execute_undo_action(action_type, source, destination)
            
            if success:
                # Marcar la acción como deshecha en la base de datos
                self.db.mark_undone(action_id)
                return True, f"Acción deshecha: {msg}"
            else:
                return False, f"Error al deshacer: {msg}"
                
        except Exception as e:
            return False, f"Error inesperado: {str(e)}"

    def redo(self) -> Tuple[bool, str]:
        """
        Rehace la última acción deshecha.
        
        :return: Tupla (éxito, mensaje)
        """
        try:
            redo_stack = self.db.get_redo_stack(limit=1)
            
            if not redo_stack:
                return False, "No hay acciones para rehacer."
            
            last_action = redo_stack[0]
            action_id = last_action['id']
            action_type = last_action['action_type']
            source = last_action['source_path']
            destination = last_action['destination_path']
            
            # Ejecutar la operación original nuevamente
            success, msg = self._execute_redo_action(action_type, source, destination)
            
            if success:
                # Marcar la acción como rehecha en la base de datos
                self.db.mark_redone(action_id)
                return True, f"Acción rehecha: {msg}"
            else:
                return False, f"Error al rehacer: {msg}"
                
        except Exception as e:
            return False, f"Error inesperado: {str(e)}"

    def _execute_undo_action(self, action_type: str, source: str, destination: str) -> Tuple[bool, str]:
        """
        Ejecuta la operación inversa de una acción.
        
        :param action_type: Tipo de acción original
        :param source: Ruta de origen original
        :param destination: Ruta de destino original
        :return: Tupla (éxito, mensaje)
        """
        try:
            if action_type == 'move':
                # Mover el archivo de vuelta a su ubicación original
                dest_path = Path(destination)
                source_path = Path(source)
                
                if not dest_path.exists():
                    return False, f"El archivo no existe en {destination}"
                
                # Crear directorio de origen si no existe
                source_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Manejar conflictos de nombre
                if source_path.exists():
                    counter = 1
                    while source_path.exists():
                        source_path = source_path.parent / f"{source_path.stem}_{counter}{source_path.suffix}"
                        counter += 1
                
                shutil.move(str(dest_path), str(source_path))
                return True, f"{dest_path.name} movido de vuelta a {source_path}"
                
            elif action_type == 'delete':
                # Recuperar archivo desde ubicación temporal
                temp_path = Path(destination)
                source_path = Path(source)
                
                if not temp_path.exists():
                    return False, f"El archivo no existe en {destination}"
                
                # Crear directorio de origen si no existe
                source_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Manejar conflictos de nombre
                if source_path.exists():
                    counter = 1
                    while source_path.exists():
                        source_path = source_path.parent / f"{source_path.stem}_{counter}{source_path.suffix}"
                        counter += 1
                
                shutil.move(str(temp_path), str(source_path))
                return True, f"{temp_path.name} recuperado en {source_path}"
                
            elif action_type == 'rename':
                # Renombrar de vuelta al nombre original
                current_path = Path(destination)
                original_path = Path(source)
                
                if not current_path.exists():
                    return False, f"El archivo no existe en {destination}"
                
                if original_path.exists():
                    counter = 1
                    while original_path.exists():
                        original_path = original_path.parent / f"{original_path.stem}_{counter}{original_path.suffix}"
                        counter += 1
                
                current_path.rename(original_path)
                return True, f"Archivo renombrado de vuelta a {original_path.name}"
                
            else:
                return False, f"Tipo de acción no soportado: {action_type}"
                
        except Exception as e:
            return False, str(e)

    def _execute_redo_action(self, action_type: str, source: str, destination: str) -> Tuple[bool, str]:
        """
        Ejecuta la operación original nuevamente (rehacer).
        
        :param action_type: Tipo de acción original
        :param source: Ruta de origen original
        :param destination: Ruta de destino original
        :return: Tupla (éxito, mensaje)
        """
        try:
            if action_type == 'move':
                # Mover el archivo nuevamente al destino
                source_path = Path(source)
                dest_path = Path(destination)
                
                if not source_path.exists():
                    return False, f"El archivo no existe en {source}"
                
                # Crear directorio de destino si no existe
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Manejar conflictos de nombre
                if dest_path.exists():
                    counter = 1
                    while dest_path.exists():
                        dest_path = dest_path.parent / f"{dest_path.stem}_{counter}{dest_path.suffix}"
                        counter += 1
                
                shutil.move(str(source_path), str(dest_path))
                return True, f"{source_path.name} movido a {dest_path}"
                
            elif action_type == 'delete':
                # Mover el archivo nuevamente a ubicación temporal
                source_path = Path(source)
                temp_path = Path(destination)
                
                if not source_path.exists():
                    return False, f"El archivo no existe en {source}"
                
                # Crear directorio temporal si no existe
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Manejar conflictos de nombre
                if temp_path.exists():
                    counter = 1
                    while temp_path.exists():
                        temp_path = temp_path.parent / f"{temp_path.stem}_{counter}{temp_path.suffix}"
                        counter += 1
                
                shutil.move(str(source_path), str(temp_path))
                return True, f"{source_path.name} eliminado nuevamente"
                
            elif action_type == 'rename':
                # Renombrar nuevamente
                original_path = Path(source)
                new_path = Path(destination)
                
                if not original_path.exists():
                    return False, f"El archivo no existe en {source}"
                
                if new_path.exists():
                    counter = 1
                    while new_path.exists():
                        new_path = new_path.parent / f"{new_path.stem}_{counter}{new_path.suffix}"
                        counter += 1
                
                original_path.rename(new_path)
                return True, f"Archivo renombrado a {new_path.name}"
                
            else:
                return False, f"Tipo de acción no soportado: {action_type}"
                
        except Exception as e:
            return False, str(e)

    def get_history(self) -> Dict:
        """
        Retorna el estado actual del historial.
        Compatible con la interfaz usada por la GUI.
        
        :return: Diccionario con undo_stack, redo_stack, undo_count, redo_count
        """
        undo_stack = self.db.get_undo_stack(limit=50)
        redo_stack = self.db.get_redo_stack(limit=50)
        summary = self.db.get_history_summary()
        
        return {
            'undo_stack': undo_stack,
            'redo_stack': redo_stack,
            'undo_count': summary['undo_count'],
            'redo_count': summary['redo_count']
        }

    def clear_history(self):
        """Borra todo el historial de acciones."""
        try:
            self.db.cursor.execute("DELETE FROM actions")
            self.db.conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error al borrar historial: {e}")
            return False

    def get_actions_by_session(self, session_id: str) -> List[Dict]:
        """Obtiene todas las acciones de una sesión específica."""
        try:
            self.db.cursor.execute("""
                SELECT * FROM actions 
                WHERE session_id = ? 
                ORDER BY id DESC
            """, (session_id,))
            return [dict(row) for row in self.db.cursor.fetchall()]
        except Exception as e:
            print(f"❌ Error al obtener acciones por sesión: {e}")
            return []

    def close(self):
        """Cierra la conexión a la base de datos."""
        if self.db:
            self.db.close()


def main():
    """Función principal para pruebas."""
    print("🧪 Iniciando pruebas de UndoManager (SQLite)...")
    
    manager = UndoManager()
    
    # Limpiar historial previo para pruebas limpias
    manager.clear_history()
    
    # Registrar algunas acciones
    print("\n--- Registrando acciones ---")
    manager.record_action('move', '/tmp/test1.txt', '/tmp/organized/test1.txt', 1024)
    manager.record_action('delete', '/tmp/test2.txt', '/tmp/.deleted/test2.txt', 2048)
    manager.record_action('move', '/tmp/test3.txt', '/tmp/organized/test3.txt', 512)
    
    # Ver historial
    history = manager.get_history()
    print(f"Acciones disponibles para deshacer: {history['undo_count']}")
    print(f"Acciones disponibles para rehacer: {history['redo_count']}")
    
    # Probar undo
    print("\n--- Probando Undo ---")
    success, msg = manager.undo()
    print(f"Undo: {'✅' if success else '❌'} {msg}")
    
    history = manager.get_history()
    print(f"Después de undo - Undo disponibles: {history['undo_count']}, Redo disponibles: {history['redo_count']}")
    
    # Probar redo
    print("\n--- Probando Redo ---")
    success, msg = manager.redo()
    print(f"Redo: {'✅' if success else '❌'} {msg}")
    
    history = manager.get_history()
    print(f"Después de redo - Undo disponibles: {history['undo_count']}, Redo disponibles: {history['redo_count']}")
    
    manager.close()
    print("\n✅ Pruebas completadas.")


if __name__ == "__main__":
    main()