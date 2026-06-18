#!/usr/bin/env python3
"""
interactive_mode.py - Modo Interactivo para Downloads Organizer Pro.

Permite al usuario decidir qué hacer con archivos de extensiones no reconocidas
en lugar de moverlos automáticamente a "Otros".

Características:
- Diálogo interactivo en CLI y GUI
- Persistencia de decisiones en JSON
- Opción de aplicar decisión a todos los archivos con la misma extensión
- Creación de nuevas categorías dinámicamente
- Muestra el nombre del archivo en los prompts
- Prompts con salto de línea para detección en GUI

Autor: Juan Carlos Blanco Ruiz
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Ruta del archivo de decisiones persistentes
DECISIONS_FILE = Path.home() / ".downloads_organizer_decisions.json"


class InteractiveMode:
    """Gestiona el modo interactivo para archivos ambiguos."""

    def __init__(self, decisions_file: Path = DECISIONS_FILE):
        self.decisions_file = decisions_file
        self.decisions: Dict[str, str] = {}  # {extension: categoria}
        self.load_decisions()

    def load_decisions(self):
        """Carga las decisiones previas desde el archivo JSON."""
        if self.decisions_file.exists():
            try:
                with open(self.decisions_file, 'r', encoding='utf-8') as f:
                    self.decisions = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️ Error al cargar decisiones: {e}")
                self.decisions = {}

    def save_decisions(self):
        """Guarda las decisiones en el archivo JSON."""
        try:
            with open(self.decisions_file, 'w', encoding='utf-8') as f:
                json.dump(self.decisions, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"❌ Error al guardar decisiones: {e}")

    def get_decision(self, extension: str) -> Optional[str]:
        """
        Retorna la decisión guardada para una extensión.
        Si no hay decisión, retorna None.
        """
        return self.decisions.get(extension.lower())

    def save_decision(self, extension: str, category: str, remember: bool = True):
        """
        Guarda una decisión para una extensión.
        
        :param extension: Extensión del archivo (ej: '.dat')
        :param category: Categoría seleccionada
        :param remember: Si True, guarda la decisión para futuras ejecuciones
        """
        if remember:
            self.decisions[extension.lower()] = category
            self.save_decisions()

    def clear_decisions(self):
        """Borra todas las decisiones guardadas."""
        self.decisions.clear()
        self.save_decisions()

    def get_all_decisions(self) -> Dict[str, str]:
        """Retorna todas las decisiones guardadas."""
        return self.decisions.copy()


def ask_user_cli(extension: str, filename: str, available_categories: List[str]) -> Tuple[str, bool]:
    """
    Pregunta al usuario en modo CLI qué hacer con un archivo de extensión desconocida.
    
    :param extension: Extensión del archivo (ej: '.dat')
    :param filename: Nombre del archivo
    :param available_categories: Lista de categorías disponibles
    :return: Tupla (acción, recordar) donde acción puede ser:
             - nombre de categoría existente
             - 'new:nombre' para crear nueva categoría
             - 'keep' para mantener en Downloads
             - 'skip' para saltar este archivo
    """
    print(f"\n{'='*60}")
    print(f"⚠️ Archivo '{filename}' con extensión no reconocida: {extension}")
    print(f"{'='*60}")
    print("\n¿Qué deseas hacer con archivos de este tipo?")
    
    # Mostrar categorías disponibles
    for i, category in enumerate(available_categories, 1):
        print(f"  [{i}] Mover a: {category}")
    
    print(f"  [{len(available_categories) + 1}] Crear nueva categoría")
    print(f"  [{len(available_categories) + 2}] Mantener en Downloads (no mover)")
    print(f"  [{len(available_categories) + 3}] Saltar este archivo")
    
    # IMPORTANTE: Imprimir prompt CON salto de línea para que la GUI lo detecte
    # Sin end='' para que subprocess.Popen pueda leer la línea completa
    print("\nTu selección (número):")
    
    while True:
        try:
            choice = input().strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(available_categories):
                category = available_categories[choice_num - 1]
                # IMPORTANTE: Imprimir prompt CON salto de línea
                print(f"¿Recordar esta decisión para todos los .{extension}? (s/n):")
                remember = input().strip().lower() == 's'
                return category, remember
            
            elif choice_num == len(available_categories) + 1:
                # IMPORTANTE: Imprimir prompt CON salto de línea
                print("Nombre de la nueva categoría:")
                new_category = input().strip()
                if new_category:
                    # IMPORTANTE: Imprimir prompt CON salto de línea
                    print(f"¿Recordar esta decisión para todos los .{extension}? (s/n):")
                    remember = input().strip().lower() == 's'
                    return f"new:{new_category}", remember
                else:
                    print("❌ Nombre de categoría no válido")
                    # IMPORTANTE: Imprimir prompt CON salto de línea
                    print("\nTu selección (número):")
            
            elif choice_num == len(available_categories) + 2:
                # IMPORTANTE: Imprimir prompt CON salto de línea
                print(f"¿Recordar esta decisión para todos los .{extension}? (s/n):")
                remember = input().strip().lower() == 's'
                return 'keep', remember
            
            elif choice_num == len(available_categories) + 3:
                return 'skip', False
            
            else:
                print("❌ Opción no válida")
                # IMPORTANTE: Imprimir prompt CON salto de línea
                print("\nTu selección (número):")
        
        except ValueError:
            print("❌ Por favor, ingresa un número válido")
            # IMPORTANTE: Imprimir prompt CON salto de línea
            print("\nTu selección (número):")
        except KeyboardInterrupt:
            print("\n\n⚠️ Operación cancelada por el usuario")
            return 'skip', False


def ask_user_gui(extension: str, filename: str, available_categories: List[str]) -> Dict:
    """
    Retorna la información necesaria para que la GUI muestre un diálogo.
    La GUI debe llamar a este método y mostrar su propio diálogo.
    
    :param extension: Extensión del archivo
    :param filename: Nombre del archivo
    :param available_categories: Lista de categorías disponibles
    :return: Diccionario con la información del diálogo
    """
    return {
        'type': 'interactive_dialog',
        'extension': extension,
        'filename': filename,
        'available_categories': available_categories,
        'message': f'Archivo "{filename}" con extensión no reconocida: {extension}',
        'options': {
            'categories': available_categories,
            'create_new': True,
            'keep_original': True,
            'skip': True,
            'remember_decision': True
        }
    }


def process_interactive_files(
    files: List[Path],
    categories: Dict[str, List[str]],
    mode: str = 'cli',
    decisions_file: Path = DECISIONS_FILE
) -> Dict:
    """
    Procesa archivos en modo interactivo.
    
    :param files: Lista de archivos a procesar
    :param categories: Diccionario de categorías {nombre: [extensiones]}
    :param mode: 'cli' o 'gui'
    :param decisions_file: Ruta del archivo de decisiones
    :return: Diccionario con resultados {archivo: acción}
    """
    interactive = InteractiveMode(decisions_file)
    available_categories = list(categories.keys())
    results = {}
    
    for file_path in files:
        extension = file_path.suffix.lower()
        filename = file_path.name
        
        # Verificar si ya hay una decisión guardada
        saved_decision = interactive.get_decision(extension)
        
        if saved_decision:
            results[str(file_path)] = saved_decision
            print(f"✅ {filename} -> {saved_decision} (decisión guardada)")
            continue
        
        # Preguntar al usuario
        if mode == 'cli':
            action, remember = ask_user_cli(extension, filename, available_categories)
        else:
            # En modo GUI, retornar información para diálogo
            dialog_info = ask_user_gui(extension, filename, available_categories)
            # La GUI debe manejar esto y retornar la decisión
            print(f"📋 GUI debe mostrar diálogo: {dialog_info}")
            action = 'skip'
            remember = False
        
        # Procesar la acción
        if action.startswith('new:'):
            # Crear nueva categoría
            new_category = action[4:]
            categories[new_category] = [extension]
            action = new_category
        
        if action != 'skip':
            interactive.save_decision(extension, action, remember)
        
        results[str(file_path)] = action
    
    return results


def main():
    """Función principal para pruebas en CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Modo Interactivo - Downloads Organizer")
    parser.add_argument('--test', action='store_true', help="Ejecutar prueba interactiva")
    parser.add_argument('--clear', action='store_true', help="Borrar todas las decisiones")
    parser.add_argument('--show', action='store_true', help="Mostrar decisiones guardadas")
    
    args = parser.parse_args()
    
    interactive = InteractiveMode()
    
    if args.clear:
        interactive.clear_decisions()
        print("✅ Todas las decisiones han sido borradas")
    
    elif args.show:
        decisions = interactive.get_all_decisions()
        if decisions:
            print("\n📋 Decisiones guardadas:")
            for ext, category in decisions.items():
                print(f"  {ext} -> {category}")
        else:
            print("\n⚠️ No hay decisiones guardadas")
    
    elif args.test:
        # Simular prueba interactiva
        test_files = [
            Path("/tmp/test1.dat"),
            Path("/tmp/test2.xyz"),
            Path("/tmp/test3.abc")
        ]
        
        test_categories = {
            "Documentos": [".pdf", ".doc", ".docx"],
            "Imágenes": [".jpg", ".png", ".gif"],
            "Código": [".py", ".js", ".java"]
        }
        
        print("\n🧪 Prueba de Modo Interactivo\n")
        results = process_interactive_files(test_files, test_categories, mode='cli')
        
        print("\n📊 Resultados:")
        for file_path, action in results.items():
            print(f"  {file_path} -> {action}")


if __name__ == "__main__":
    main()