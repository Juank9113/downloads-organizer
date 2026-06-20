#!/usr/bin/env python3
"""
stats_manager.py - Gestor de Estadísticas para Downloads Organizer Pro.

Proporciona consultas optimizadas sobre la base de datos SQLite para
generar gráficos y reportes de actividad.

Características:
- Consultas agregadas sobre acciones (move, delete).
- Agrupación por categoría detectando patrones en rutas.
- Análisis temporal (por día, semana, mes).
- Top extensiones y categorías.
- Filtros por rango de fechas.

Autor: Juan Carlos Blanco Ruiz
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta


# Categorías conocidas para agrupación automática
KNOWN_CATEGORIES = [
    "Imagenes", "Videos", "Documentos", "Audio",
    "Comprimidos", "Codigo", "Ejecutables", "Otros"
]


class StatsManager:
    """Gestiona consultas de estadísticas sobre la base de datos."""

    def __init__(self, db_manager=None):
        if db_manager is None:
            from db_manager import DatabaseManager
            self.db = DatabaseManager()
        else:
            self.db = db_manager

    def _detect_category(self, path: str) -> str:
        """Detecta la categoría a partir de la ruta de destino."""
        path_lower = path.lower()
        for cat in KNOWN_CATEGORIES:
            if f"/{cat.lower()}/" in path_lower or path_lower.endswith(f"/{cat.lower()}"):
                return cat
        return "Otros"

    def _extract_extension(self, path: str) -> str:
        """Extrae la extensión de un archivo a partir de la ruta."""
        try:
            return Path(path).suffix.lower() or "(sin extensión)"
        except Exception:
            return "(sin extensión)"

    def get_total_stats(self, days: Optional[int] = None) -> Dict:
        """
        Obtiene estadísticas totales.
        
        :param days: Número de días hacia atrás (None = todo el historial)
        :return: Diccionario con totales
        """
        try:
            where_clause = ""
            params = []
            if days:
                where_clause = "WHERE timestamp >= datetime('now', ?)"
                params.append(f"-{days} days")

            # Total de acciones
            self.db.cursor.execute(f"""
                SELECT COUNT(*) as total,
                       SUM(file_size) as total_size,
                       COUNT(DISTINCT session_id) as sessions
                FROM actions
                {where_clause}
            """, params)
            row = self.db.cursor.fetchone()
            
            # Acciones por tipo
            self.db.cursor.execute(f"""
                SELECT action_type, COUNT(*) as count
                FROM actions
                {where_clause}
                GROUP BY action_type
            """, params)
            actions_by_type = {row[0]: row[1] for row in self.db.cursor.fetchall()}

            return {
                'total_actions': row['total'] or 0,
                'total_size_bytes': row['total_size'] or 0,
                'sessions': row['sessions'] or 0,
                'actions_by_type': actions_by_type,
                'total_moves': actions_by_type.get('move', 0),
                'total_deletes': actions_by_type.get('delete', 0),
                'total_renames': actions_by_type.get('rename', 0)
            }
        except Exception as e:
            print(f"❌ Error en get_total_stats: {e}")
            return {
                'total_actions': 0, 'total_size_bytes': 0, 'sessions': 0,
                'actions_by_type': {}, 'total_moves': 0,
                'total_deletes': 0, 'total_renames': 0
            }

    def get_files_by_category(self, days: Optional[int] = None) -> List[Tuple[str, int]]:
        """
        Obtiene el número de archivos procesados por categoría.
        
        :return: Lista de tuplas (categoría, cantidad) ordenadas por cantidad DESC
        """
        try:
            where_clause = ""
            params = []
            if days:
                where_clause = "WHERE timestamp >= datetime('now', ?)"
                params.append(f"-{days} days")

            self.db.cursor.execute(f"""
                SELECT destination_path, COUNT(*) as count
                FROM actions
                {where_clause}
                GROUP BY destination_path
            """, params)
            
            category_counts = {}
            for row in self.db.cursor.fetchall():
                cat = self._detect_category(row['destination_path'])
                category_counts[cat] = category_counts.get(cat, 0) + row['count']
            
            # Ordenar por cantidad descendente
            return sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        except Exception as e:
            print(f"❌ Error en get_files_by_category: {e}")
            return []

    def get_space_by_category(self, days: Optional[int] = None) -> List[Tuple[str, int]]:
        """
        Obtiene el espacio ocupado por cada categoría (en bytes).
        
        :return: Lista de tuplas (categoría, bytes) ordenadas por bytes DESC
        """
        try:
            where_clause = ""
            params = []
            if days:
                where_clause = "WHERE timestamp >= datetime('now', ?)"
                params.append(f"-{days} days")

            self.db.cursor.execute(f"""
                SELECT destination_path, SUM(file_size) as total_size
                FROM actions
                {where_clause}
                GROUP BY destination_path
            """, params)
            
            category_space = {}
            for row in self.db.cursor.fetchall():
                cat = self._detect_category(row['destination_path'])
                category_space[cat] = category_space.get(cat, 0) + (row['total_size'] or 0)
            
            return sorted(category_space.items(), key=lambda x: x[1], reverse=True)
        except Exception as e:
            print(f"❌ Error en get_space_by_category: {e}")
            return []

    def get_activity_over_time(self, days: int = 30) -> List[Tuple[str, int]]:
        """
        Obtiene la actividad diaria en los últimos N días.
        
        :param days: Número de días hacia atrás
        :return: Lista de tuplas (fecha 'YYYY-MM-DD', cantidad)
        """
        try:
            self.db.cursor.execute("""
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM actions
                WHERE timestamp >= datetime('now', ?)
                GROUP BY DATE(timestamp)
                ORDER BY date ASC
            """, (f"-{days} days",))
            
            # Rellenar días sin actividad con 0
            results = {row['date']: row['count'] for row in self.db.cursor.fetchall()}
            
            full_timeline = []
            today = datetime.now().date()
            for i in range(days - 1, -1, -1):
                date = today - timedelta(days=i)
                date_str = date.strftime('%Y-%m-%d')
                full_timeline.append((date_str, results.get(date_str, 0)))
            
            return full_timeline
        except Exception as e:
            print(f"❌ Error en get_activity_over_time: {e}")
            return []

    def get_top_extensions(self, limit: int = 10, days: Optional[int] = None) -> List[Tuple[str, int]]:
        """
        Obtiene las N extensiones más comunes.
        
        :param limit: Número máximo de extensiones
        :param days: Filtrar por días (None = todo)
        :return: Lista de tuplas (extensión, cantidad)
        """
        try:
            where_clause = ""
            params = [limit]
            if days:
                where_clause = "WHERE timestamp >= datetime('now', ?)"
                params.insert(0, f"-{days} days")

            self.db.cursor.execute(f"""
                SELECT source_path, COUNT(*) as count
                FROM actions
                {where_clause}
                GROUP BY source_path
                ORDER BY count DESC
                LIMIT ?
            """, params)
            
            ext_counts = {}
            for row in self.db.cursor.fetchall():
                ext = self._extract_extension(row['source_path'])
                ext_counts[ext] = ext_counts.get(ext, 0) + row['count']
            
            return sorted(ext_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        except Exception as e:
            print(f"❌ Error en get_top_extensions: {e}")
            return []

    def get_hourly_activity(self, days: Optional[int] = None) -> List[Tuple[int, int]]:
        """
        Obtiene actividad por hora del día (0-23).
        
        :return: Lista de tuplas (hora, cantidad)
        """
        try:
            where_clause = ""
            params = []
            if days:
                where_clause = "WHERE timestamp >= datetime('now', ?)"
                params.append(f"-{days} days")

            self.db.cursor.execute(f"""
                SELECT CAST(strftime('%H', timestamp) AS INTEGER) as hour, COUNT(*) as count
                FROM actions
                {where_clause}
                GROUP BY hour
                ORDER BY hour
            """, params)
            
            hourly = {row['hour']: row['count'] for row in self.db.cursor.fetchall()}
            return [(h, hourly.get(h, 0)) for h in range(24)]
        except Exception as e:
            print(f"❌ Error en get_hourly_activity: {e}")
            return [(h, 0) for h in range(24)]


def main():
    """Pruebas del gestor de estadísticas."""
    print("🧪 Probando StatsManager...\n")
    
    sm = StatsManager()
    
    print("📊 Estadísticas Totales:")
    totals = sm.get_total_stats()
    for key, value in totals.items():
        print(f"  {key}: {value}")
    
    print("\n📁 Archivos por Categoría:")
    for cat, count in sm.get_files_by_category():
        print(f"  {cat}: {count} archivos")
    
    print("\n💾 Espacio por Categoría:")
    for cat, size in sm.get_space_by_category():
        size_mb = size / (1024 * 1024)
        print(f"  {cat}: {size_mb:.2f} MB")
    
    print("\n📈 Actividad últimos 7 días:")
    for date, count in sm.get_activity_over_time(days=7):
        print(f"  {date}: {count} acciones")
    
    print("\n🏆 Top 5 Extensiones:")
    for ext, count in sm.get_top_extensions(limit=5):
        print(f"  {ext}: {count} archivos")
    
    print("\n🕐 Actividad por hora (últimos 30 días):")
    for hour, count in sm.get_hourly_activity(days=30):
        if count > 0:
            print(f"  {hour:02d}:00 - {hour:02d}:59: {count} acciones")


if __name__ == "__main__":
    main()