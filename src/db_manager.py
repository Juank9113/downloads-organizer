#!/usr/bin/env python3
"""
db_manager.py - Gestor de Base de Datos SQLite para Downloads Organizer Pro.

Reemplaza y augmenta los archivos JSON para proporcionar un historial robusto,
persistencia de decisiones y preferencias con soporte para transacciones ACID.

Características:
- Migración automática desde archivos JSON existentes.
- Esquema normalizado para acciones, decisiones y preferencias.
- Consultas eficientes mediante índices.
- Manejo seguro de conexiones y transacciones.

Autor: Juan Carlos Blanco Ruiz
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any


# Rutas de la base de datos y archivos JSON legacy
DB_PATH = Path.home() / ".downloads_organizer.db"
LEGACY_HISTORY_FILE = Path.home() / ".downloads_organizer_history.json"
LEGACY_DECISIONS_FILE = Path.home() / ".downloads_organizer_decisions.json"
LEGACY_PREFS_FILE = Path.home() / ".downloads_organizer_prefs.json"


class DatabaseManager:
    """Gestiona la conexión y operaciones con la base de datos SQLite."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_schema()
        self._migrate_json_files()

    def _connect(self):
        """Establece la conexión con la base de datos."""
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row  # Permite acceso por nombre de columna
            self.cursor = self.conn.cursor()
            # Habilitar WAL para mejor concurrencia y rendimiento
            self.cursor.execute("PRAGMA journal_mode=WAL;")
            self.cursor.execute("PRAGMA foreign_keys=ON;")
        except sqlite3.Error as e:
            print(f"❌ Error al conectar a la base de datos: {e}")
            raise

    def _create_schema(self):
        """Crea las tablas necesarias si no existen."""
        schema = """
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_type TEXT NOT NULL,
            source_path TEXT NOT NULL,
            destination_path TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            file_size INTEGER DEFAULT 0,
            session_id TEXT,
            undone INTEGER DEFAULT 0,
            redone INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS decisions (
            extension TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS preferences (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_actions_type ON actions(action_type);
        CREATE INDEX IF NOT EXISTS idx_actions_timestamp ON actions(timestamp);
        CREATE INDEX IF NOT EXISTS idx_actions_session ON actions(session_id);
        CREATE INDEX IF NOT EXISTS idx_actions_undone ON actions(undone);
        """
        try:
            self.cursor.executescript(schema)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"❌ Error al crear el esquema: {e}")
            raise

    def _migrate_json_files(self):
        """Migra datos desde archivos JSON legacy a la base de datos."""
        self._migrate_history()
        self._migrate_decisions()
        self._migrate_preferences()

    def _migrate_history(self):
        """Migra el historial de undo/redo."""
        if LEGACY_HISTORY_FILE.exists():
            try:
                with open(LEGACY_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Estructura esperada: {"undo_stack": [...], "redo_stack": [...]}
                undo_stack = data.get("undo_stack", [])
                redo_stack = data.get("redo_stack", [])
                
                for action in undo_stack:
                    self.record_action(
                        action_type=action.get("action", "move"),
                        source_path=action.get("source", ""),
                        destination_path=action.get("destination", ""),
                        file_size=action.get("size", 0),
                        session_id=action.get("session_id"),
                        undone=0, redone=0
                    )
                
                for action in redo_stack:
                    self.record_action(
                        action_type=action.get("action", "move"),
                        source_path=action.get("source", ""),
                        destination_path=action.get("destination", ""),
                        file_size=action.get("size", 0),
                        session_id=action.get("session_id"),
                        undone=1, redone=1 # Marcado como deshecho y rehecho
                    )
                
                # Renombrar archivo legacy para evitar doble migración
                backup_path = LEGACY_HISTORY_FILE.with_suffix(".json.bak")
                LEGACY_HISTORY_FILE.rename(backup_path)
                print(f"✅ Historial migrado desde {LEGACY_HISTORY_FILE} -> {backup_path}")
            except Exception as e:
                print(f"️ Error al migrar historial: {e}")

    def _migrate_decisions(self):
        """Migra las decisiones del modo interactivo."""
        if LEGACY_DECISIONS_FILE.exists():
            try:
                with open(LEGACY_DECISIONS_FILE, 'r', encoding='utf-8') as f:
                    decisions = json.load(f)
                
                for ext, cat in decisions.items():
                    self.save_decision(ext, cat)
                
                backup_path = LEGACY_DECISIONS_FILE.with_suffix(".json.bak")
                LEGACY_DECISIONS_FILE.rename(backup_path)
                print(f"✅ Decisiones migradas desde {LEGACY_DECISIONS_FILE} -> {backup_path}")
            except Exception as e:
                print(f"⚠️ Error al migrar decisiones: {e}")

    def _migrate_preferences(self):
        """Migra las preferencias de la GUI."""
        if LEGACY_PREFS_FILE.exists():
            try:
                with open(LEGACY_PREFS_FILE, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
                
                for key, value in prefs.items():
                    self.save_preference(key, str(value))
                
                backup_path = LEGACY_PREFS_FILE.with_suffix(".json.bak")
                LEGACY_PREFS_FILE.rename(backup_path)
                print(f"✅ Preferencias migradas desde {LEGACY_PREFS_FILE} -> {backup_path}")
            except Exception as e:
                print(f"⚠️ Error al migrar preferencias: {e}")

    # ----------------------------------------------------------------
    # Métodos para Acciones (Undo/Redo)
    # ----------------------------------------------------------------
    def record_action(self, action_type: str, source_path: str, destination_path: str, 
                      file_size: int = 0, session_id: str = None, 
                      undone: int = 0, redone: int = 0) -> int:
        """Registra una nueva acción en la base de datos."""
        try:
            self.cursor.execute("""
                INSERT INTO actions (action_type, source_path, destination_path, file_size, session_id, undone, redone)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (action_type, source_path, destination_path, file_size, session_id, undone, redone))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"❌ Error al registrar acción: {e}")
            return -1

    def get_undo_stack(self, limit: int = 50) -> List[Dict]:
        """Obtiene las acciones disponibles para deshacer (no deshechas)."""
        try:
            self.cursor.execute("""
                SELECT * FROM actions 
                WHERE undone = 0 
                ORDER BY id DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"❌ Error al obtener undo stack: {e}")
            return []

    def get_redo_stack(self, limit: int = 50) -> List[Dict]:
        """Obtiene las acciones disponibles para rehacer (deshechas pero no rehechas)."""
        try:
            self.cursor.execute("""
                SELECT * FROM actions 
                WHERE undone = 1 AND redone = 0 
                ORDER BY id DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f" Error al obtener redo stack: {e}")
            return []

    def mark_undone(self, action_id: int):
        """Marca una acción como deshecha."""
        try:
            self.cursor.execute("UPDATE actions SET undone = 1 WHERE id = ?", (action_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"❌ Error al marcar como deshecha: {e}")

    def mark_redone(self, action_id: int):
        """Marca una acción como rehecha."""
        try:
            self.cursor.execute("UPDATE actions SET redone = 1 WHERE id = ?", (action_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"❌ Error al marcar como rehecha: {e}")

    def get_history_summary(self) -> Dict[str, int]:
        """Retorna un resumen del historial."""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM actions WHERE undone = 0")
            undo_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM actions WHERE undone = 1 AND redone = 0")
            redo_count = self.cursor.fetchone()[0]
            
            return {"undo_count": undo_count, "redo_count": redo_count}
        except sqlite3.Error as e:
            print(f"❌ Error al obtener resumen: {e}")
            return {"undo_count": 0, "redo_count": 0}

    # ----------------------------------------------------------------
    # Métodos para Decisiones (Modo Interactivo)
    # ----------------------------------------------------------------
    def save_decision(self, extension: str, category: str):
        """Guarda o actualiza una decisión para una extensión."""
        try:
            now = datetime.now().isoformat()
            self.cursor.execute("""
                INSERT INTO decisions (extension, category, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(extension) DO UPDATE SET category=excluded.category, updated_at=excluded.updated_at
            """, (extension.lower(), category, now))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"❌ Error al guardar decisión: {e}")

    def get_decision(self, extension: str) -> Optional[str]:
        """Obtiene la decisión guardada para una extensión."""
        try:
            self.cursor.execute("SELECT category FROM decisions WHERE extension = ?", (extension.lower(),))
            row = self.cursor.fetchone()
            return row['category'] if row else None
        except sqlite3.Error as e:
            print(f" Error al obtener decisión: {e}")
            return None

    def get_all_decisions(self) -> Dict[str, str]:
        """Obtiene todas las decisiones guardadas."""
        try:
            self.cursor.execute("SELECT extension, category FROM decisions")
            return {row['extension']: row['category'] for row in self.cursor.fetchall()}
        except sqlite3.Error as e:
            print(f"❌ Error al obtener todas las decisiones: {e}")
            return {}

    def clear_decisions(self):
        """Borra todas las decisiones."""
        try:
            self.cursor.execute("DELETE FROM decisions")
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"❌ Error al borrar decisiones: {e}")

    # ----------------------------------------------------------------
    # Métodos para Preferencias (GUI)
    # ----------------------------------------------------------------
    def save_preference(self, key: str, value: str):
        """Guarda o actualiza una preferencia."""
        try:
            now = datetime.now().isoformat()
            self.cursor.execute("""
                INSERT INTO preferences (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
            """, (key, value, now))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"❌ Error al guardar preferencia: {e}")

    def get_preference(self, key: str) -> Optional[str]:
        """Obtiene el valor de una preferencia."""
        try:
            self.cursor.execute("SELECT value FROM preferences WHERE key = ?", (key,))
            row = self.cursor.fetchone()
            return row['value'] if row else None
        except sqlite3.Error as e:
            print(f"❌ Error al obtener preferencia: {e}")
            return None

    def get_all_preferences(self) -> Dict[str, str]:
        """Obtiene todas las preferencias."""
        try:
            self.cursor.execute("SELECT key, value FROM preferences")
            return {row['key']: row['value'] for row in self.cursor.fetchall()}
        except sqlite3.Error as e:
            print(f"❌ Error al obtener todas las preferencias: {e}")
            return {}

    # ----------------------------------------------------------------
    # Utilidades
    # ----------------------------------------------------------------
    def close(self):
        """Cierra la conexión a la base de datos."""
        if self.conn:
            self.conn.close()
            print("✅ Conexión a la base de datos cerrada.")

    def backup(self, backup_path: Path):
        """Crea un backup de la base de datos."""
        try:
            backup_conn = sqlite3.connect(str(backup_path))
            self.conn.backup(backup_conn)
            backup_conn.close()
            print(f"✅ Backup creado en {backup_path}")
        except sqlite3.Error as e:
            print(f"❌ Error al crear backup: {e}")


def main():
    """Función principal para pruebas."""
    print("🧪 Iniciando pruebas de DatabaseManager...")
    
    db = DatabaseManager()
    
    # Prueba de acciones
    print("\n--- Acciones ---")
    db.record_action("move", "/tmp/test1.txt", "/tmp/organized/test1.txt", 1024)
    db.record_action("delete", "/tmp/test2.txt", "/tmp/.deleted/test2.txt", 2048)
    print(f"Resumen: {db.get_history_summary()}")
    print(f"Undo Stack: {db.get_undo_stack()}")
    
    # Prueba de decisiones
    print("\n--- Decisiones ---")
    db.save_decision(".dat", "Datos")
    db.save_decision(".xyz", "Otros")
    print(f"Decisión para .dat: {db.get_decision('.dat')}")
    print(f"Todas las decisiones: {db.get_all_decisions()}")
    
    # Prueba de preferencias
    print("\n--- Preferencias ---")
    db.save_preference("theme", "dark")
    db.save_preference("language", "es")
    print(f"Tema: {db.get_preference('theme')}")
    print(f"Todas las preferencias: {db.get_all_preferences()}")
    
    db.close()
    print("\n✅ Pruebas completadas.")


if __name__ == "__main__":
    main()