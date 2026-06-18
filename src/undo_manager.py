#!/usr/bin/env python3
"""
undo_manager.py - Sistema de Deshacer/Rehacer para Downloads Organizer Pro.

Características:
- Registro de operaciones (mover, renombrar, eliminar).
- Persistencia en JSON (el historial se mantiene al cerrar la app).
- Pilas de Deshacer (Undo) y Rehacer (Redo).
- Manejo de conflictos (si el archivo original ya existe).
- Integración con CLI y GUI.

Autor: Juan Carlos Blanco Ruiz
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple


# Ruta por defecto para el historial (oculto en el home del usuario)
HISTORY_FILE = Path.home() / ".downloads_organizer_history.json"


class UndoManager:
    """Gestiona el historial de operaciones para permitir Deshacer/Rehacer."""

    def __init__(self, history_file: Path = HISTORY_FILE):
        self.history_file = history_file
        self.undo_stack: List[Dict] = []
        self.redo_stack: List[Dict] = []
        self._load()

    def _load(self):
        """Carga el historial desde el archivo JSON."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.undo_stack = data.get('undo_stack', [])
                    self.redo_stack = data.get('redo_stack', [])
            except (json.JSONDecodeError, IOError) as e:
                print(f"️ Error al cargar historial: {e}. Iniciando historial vacío.")
                self.undo_stack = []
                self.redo_stack = []

    def _save(self):
        """Guarda el historial actual en el archivo JSON."""
        try:
            data = {
                'undo_stack': self.undo_stack,
                'redo_stack': self.redo_stack
            }
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"❌ Error al guardar historial: {e}")

    def record_action(self, action: str, source: str, destination: str):
        """
        Registra una nueva operación en la pila de Deshacer.
        Limpia la pila de Rehacer al registrar una nueva acción.
        
        :param action: Tipo de acción ('move', 'rename', 'delete')
        :param source: Ruta original del archivo
        :param destination: Ruta final del archivo
        """
        # Si hacemos una nueva acción, el "Rehacer" pierde sentido
        self.redo_stack.clear()
        
        self.undo_stack.append({
            'action': action,
            'source': str(source),
            'destination': str(destination),
            'timestamp': datetime.now().isoformat()
        })
        
        self._save()
        print(f"✅ Acción registrada: {action} | {source} -> {destination}")

    def undo(self) -> Tuple[bool, str]:
        """
        Deshace la última operación.
        Mueve el archivo de 'destination' de vuelta a 'source'.
        """
        if not self.undo_stack:
            return False, "No hay acciones para deshacer."

        action_data = self.undo_stack.pop()
        action = action_data['action']
        source = action_data['source']
        destination = action_data['destination']

        try:
            if action == 'move' or action == 'rename':
                self._reverse_move(destination, source)
            elif action == 'delete':
                # Nota: Recuperar un archivo eliminado permanentemente es imposible.
                # Esto solo funciona si se movió a la papelera.
                return False, "No se puede deshacer una eliminación permanente."
            
            # Mover la acción a la pila de Rehacer
            self.redo_stack.append(action_data)
            self._save()
            return True, f"Acción deshecha: {source} <- {destination}"
            
        except Exception as e:
            # Si falla, volvemos a poner la acción en la pila de Deshacer
            self.undo_stack.append(action_data)
            self._save()
            return False, f"Error al deshacer: {str(e)}"

    def redo(self) -> Tuple[bool, str]:
        """
        Rehace la última operación deshecha.
        Mueve el archivo de 'source' a 'destination' nuevamente.
        """
        if not self.redo_stack:
            return False, "No hay acciones para rehacer."

        action_data = self.redo_stack.pop()
        action = action_data['action']
        source = action_data['source']
        destination = action_data['destination']

        try:
            if action == 'move' or action == 'rename':
                self._apply_move(source, destination)
            
            # Mover la acción de vuelta a la pila de Deshacer
            self.undo_stack.append(action_data)
            self._save()
            return True, f"Acción rehecha: {source} -> {destination}"
            
        except Exception as e:
            self.redo_stack.append(action_data)
            self._save()
            return False, f"Error al rehacer: {str(e)}"

    def _apply_move(self, source: str, destination: str):
        """Mueve un archivo de origen a destino, creando carpetas si es necesario."""
        src_path = Path(source)
        dst_path = Path(destination)
        
        if not src_path.exists():
            raise FileNotFoundError(f"El archivo origen no existe: {source}")
        
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_path), str(dst_path))

    def _reverse_move(self, destination: str, source: str):
        """Mueve un archivo de vuelta a su origen (para Undo)."""
        dst_path = Path(destination)
        src_path = Path(source)
        
        if not dst_path.exists():
            raise FileNotFoundError(f"El archivo destino no existe: {destination}. ¿Fue movido o eliminado manualmente?")
        
        # Si ya existe un archivo en la ruta original, evitamos sobrescribirlo
        if src_path.exists():
            # Añadimos un sufijo para no perder datos
            new_source = str(src_path) + f"_restored_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            print(f"️ Conflicto: {source} ya existe. Restaurando como {new_source}")
            src_path = Path(new_source)
        
        src_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(dst_path), str(src_path))

    def get_history(self) -> Dict:
        """Retorna el historial completo para la GUI/CLI."""
        return {
            'undo_stack': self.undo_stack,
            'redo_stack': self.redo_stack,
            'undo_count': len(self.undo_stack),
            'redo_count': len(self.redo_stack)
        }

    def clear_history(self):
        """Borra todo el historial."""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self._save()
        print("🧹 Historial borrado.")


# ----------------------------------------------------------------------
# CLI para pruebas rápidas
# ----------------------------------------------------------------------
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Gestor de Deshacer/Rehacer")
    parser.add_argument('--status', action='store_true', help="Ver estado del historial")
    parser.add_argument('--undo', action='store_true', help="Deshacer última acción")
    parser.add_argument('--redo', action='store_true', help="Rehacer última acción")
    parser.add_argument('--clear', action='store_true', help="Borrar historial")
    
    args = parser.parse_args()
    manager = UndoManager()
    
    if args.status:
        history = manager.get_history()
        print(f"📊 Acciones para Deshacer: {history['undo_count']}")
        print(f"🔄 Acciones para Rehacer: {history['redo_count']}")
        if history['undo_stack']:
            print("\nÚltimas acciones:")
            for act in history['undo_stack'][-3:]:
                print(f"  - [{act['timestamp']}] {act['action']}: {act['source']} -> {act['destination']}")
                
    elif args.undo:
        success, msg = manager.undo()
        print(f"{'✅' if success else '❌'} {msg}")
        
    elif args.redo:
        success, msg = manager.redo()
        print(f"{'✅' if success else '❌'} {msg}")
        
    elif args.clear:
        manager.clear_history()
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()