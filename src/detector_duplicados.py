#!/usr/bin/env python3
"""
detector_duplicados.py - Módulo de detección de archivos duplicados
para Downloads Organizer Pro.

Características:
- Detección por contenido (hash SHA256)
- Detección por nombre (archivos con mismo nombre en diferentes carpetas)
- Filtro por tamaño mínimo
- Exclusión de extensiones
- Modo simulación
- Reporte detallado
- Integración con CLI y GUI

Autor: Juan Carlos Blanco Ruiz
Email: juancarlosblancoruiz@gmail.com
"""

import hashlib
import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Tuple, Optional


# Extensiones a ignorar por defecto (archivos temporales del sistema)
EXTENSIONES_A_EXCLUIR = {
    '.tmp', '.temp', '.crdownload', '.part', '.download',
    '.lnk', '.ini', '.db', '.log'
}

# Tamaño mínimo por defecto (1 KB) para evitar procesar archivos muy pequeños
TAMANO_MINIMO_DEFAULT = 1024


class ArchivoInfo:
    """Información detallada de un archivo."""
    
    def __init__(self, ruta: Path):
        self.ruta = ruta
        self.nombre = ruta.name
        self.extension = ruta.suffix.lower()
        self.tamano = ruta.stat().st_size
        self.fecha_modificacion = datetime.fromtimestamp(ruta.stat().st_mtime)
        self.hash: Optional[str] = None
    
    def calcular_hash(self, algoritmo: str = 'sha256') -> str:
        """Calcula el hash del archivo."""
        if self.hash is not None:
            return self.hash
        
        hasher = hashlib.new(algoritmo)
        try:
            with open(self.ruta, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hasher.update(chunk)
            self.hash = hasher.hexdigest()
        except (PermissionError, OSError) as e:
            print(f"  ⚠️ Error al leer {self.ruta}: {e}")
            self.hash = None
        
        return self.hash
    
    def __repr__(self):
        return f"ArchivoInfo({self.ruta}, {self.tamano} bytes)"
    
    def to_dict(self) -> dict:
        """Convierte a diccionario para serialización JSON."""
        return {
            'ruta': str(self.ruta),
            'nombre': self.nombre,
            'extension': self.extension,
            'tamano': self.tamano,
            'tamano_human': self._tamano_human(),
            'fecha_modificacion': self.fecha_modificacion.isoformat(),
            'hash': self.hash
        }
    
    def _tamano_human(self) -> str:
        """Convierte el tamaño a formato legible."""
        for unidad in ['B', 'KB', 'MB', 'GB', 'TB']:
            if self.tamano < 1024:
                return f"{self.tamano:.2f} {unidad}"
            self.tamano /= 1024
        return f"{self.tamano:.2f} PB"


class GrupoDuplicados:
    """Grupo de archivos duplicados."""
    
    def __init__(self, clave: str, tipo: str = 'contenido'):
        self.clave = clave
        self.tipo = tipo  # 'contenido' o 'nombre'
        self.archivos: List[ArchivoInfo] = []
    
    @property
    def cantidad(self) -> int:
        return len(self.archivos)
    
    @property
    def espacio_recuperable(self) -> int:
        """Espacio que se liberaría eliminando todos los duplicados menos uno."""
        if self.cantidad <= 1:
            return 0
        # Mantener el más reciente, eliminar el resto
        archivos_ordenados = sorted(
            self.archivos, 
            key=lambda a: a.fecha_modificacion, 
            reverse=True
        )
        return sum(a.tamano for a in archivos_ordenados[1:])
    
    @property
    def archivo_original(self) -> Optional[ArchivoInfo]:
        """El archivo más reciente (se considera el original)."""
        if not self.archivos:
            return None
        return max(self.archivos, key=lambda a: a.fecha_modificacion)
    
    @property
    def duplicados(self) -> List[ArchivoInfo]:
        """Todos los archivos excepto el original."""
        if not self.archivos:
            return []
        original = self.archivo_original
        return [a for a in self.archivos if a != original]
    
    def to_dict(self) -> dict:
        """Convierte a diccionario para serialización JSON."""
        return {
            'clave': self.clave,
            'tipo': self.tipo,
            'cantidad': self.cantidad,
            'espacio_recuperable': self.espacio_recuperable,
            'espacio_recuperable_human': self._tamano_human(self.espacio_recuperable),
            'archivo_original': self.archivo_original.to_dict() if self.archivo_original else None,
            'duplicados': [a.to_dict() for a in self.duplicados]
        }
    
    @staticmethod
    def _tamano_human(bytes_val: int) -> str:
        for unidad in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024:
                return f"{bytes_val:.2f} {unidad}"
            bytes_val /= 1024
        return f"{bytes_val:.2f} PB"


class DetectorDuplicados:
    """Detector principal de archivos duplicados."""
    
    def __init__(
        self,
        carpeta: Path,
        tamano_minimo: int = TAMANO_MINIMO_DEFAULT,
        extensiones_excluir: Optional[set] = None,
        recursivo: bool = True,
        algoritmo_hash: str = 'sha256',
        modo_simulacion: bool = True
    ):
        self.carpeta = carpeta
        self.tamano_minimo = tamano_minimo
        self.extensiones_excluir = extensiones_excluir or EXTENSIONES_A_EXCLUIR
        self.recursivo = recursivo
        self.algoritmo_hash = algoritmo_hash
        self.modo_simulacion = modo_simulacion
        
        self.grupos_contenido: List[GrupoDuplicados] = []
        self.grupos_nombre: List[GrupoDuplicados] = []
        self.total_archivos_analizados = 0
        self.total_archivos_ignorados = 0
        self.errores: List[str] = []
    
    def analizar(self) -> Dict:
        """Ejecuta el análisis completo de duplicados."""
        print(f"\n{'='*60}")
        print(f"🔍 DETECTOR DE DUPLICADOS")
        print(f"{'='*60}")
        print(f"📁 Carpeta: {self.carpeta}")
        print(f" Tamaño mínimo: {self.tamano_minimo} bytes")
        print(f"🚫 Extensiones excluidas: {', '.join(self.extensiones_excluir)}")
        print(f"🔁 Recursivo: {'Sí' if self.recursivo else 'No'}")
        print(f"🔐 Algoritmo hash: {self.algoritmo_hash}")
        print(f" Modo simulación: {'Sí' if self.modo_simulacion else 'No'}")
        print(f"{'='*60}\n")
        
        # Paso 1: Recopilar archivos
        print("⏳ Paso 1: Recopilando archivos...")
        archivos = self._recopilar_archivos()
        print(f"   ✅ {self.total_archivos_analizados} archivos válidos")
        if self.total_archivos_ignorados > 0:
            print(f"   ⏭️ {self.total_archivos_ignorados} archivos ignorados")
        
        if not archivos:
            print("\n️ No se encontraron archivos para analizar.")
            return self._generar_reporte()
        
        # Paso 2: Detectar duplicados por nombre
        print("\n⏳ Paso 2: Detectando duplicados por nombre...")
        self.grupos_nombre = self._detectar_por_nombre(archivos)
        print(f"   ✅ {len(self.grupos_nombre)} grupos encontrados")
        
        # Paso 3: Detectar duplicados por contenido
        print("\n⏳ Paso 3: Detectando duplicados por contenido (hashing)...")
        self.grupos_contenido = self._detectar_por_contenido(archivos)
        print(f"   ✅ {len(self.grupos_contenido)} grupos encontrados")
        
        # Paso 4: Generar reporte
        return self._generar_reporte()
    
    def _recopilar_archivos(self) -> List[ArchivoInfo]:
        """Recopila todos los archivos de la carpeta."""
        archivos = []
        
        if self.recursivo:
            iterator = self.carpeta.rglob('*')
        else:
            iterator = self.carpeta.glob('*')
        
        for ruta in iterator:
            if not ruta.is_file():
                continue
            
            # Ignorar extensiones excluidas
            if ruta.suffix.lower() in self.extensiones_excluir:
                self.total_archivos_ignorados += 1
                continue
            
            # Ignorar archivos muy pequeños
            try:
                tamano = ruta.stat().st_size
            except OSError as e:
                self.errores.append(f"Error al acceder a {ruta}: {e}")
                continue
            
            if tamano < self.tamano_minimo:
                self.total_archivos_ignorados += 1
                continue
            
            try:
                info = ArchivoInfo(ruta)
                archivos.append(info)
                self.total_archivos_analizados += 1
            except Exception as e:
                self.errores.append(f"Error al procesar {ruta}: {e}")
        
        return archivos
    
    def _detectar_por_nombre(self, archivos: List[ArchivoInfo]) -> List[GrupoDuplicados]:
        """Detecta archivos con el mismo nombre."""
        grupos_nombre = defaultdict(list)
        
        for archivo in archivos:
            grupos_nombre[archivo.nombre.lower()].append(archivo)
        
        # Filtrar solo los que tienen más de un archivo
        grupos = []
        for nombre, lista_archivos in grupos_nombre.items():
            if len(lista_archivos) > 1:
                grupo = GrupoDuplicados(clave=nombre, tipo='nombre')
                grupo.archivos = lista_archivos
                grupos.append(grupo)
        
        return grupos
    
    def _detectar_por_contenido(self, archivos: List[ArchivoInfo]) -> List[GrupoDuplicados]:
        """Detecta archivos con el mismo contenido usando hashing."""
        # Optimización: agrupar primero por tamaño
        grupos_tamano = defaultdict(list)
        for archivo in archivos:
            grupos_tamano[archivo.tamano].append(archivo)
        
        # Solo calcular hash para archivos con el mismo tamaño
        grupos_hash = defaultdict(list)
        total = sum(len(lista) for lista in grupos_tamano.values() if len(lista) > 1)
        procesados = 0
        
        for tamano, lista_archivos in grupos_tamano.items():
            if len(lista_archivos) <= 1:
                continue
            
            for archivo in lista_archivos:
                archivo.calcular_hash(self.algoritmo_hash)
                procesados += 1
                if archivo.hash is not None:
                    grupos_hash[archivo.hash].append(archivo)
                
                # Mostrar progreso
                if procesados % 50 == 0 or procesados == total:
                    print(f"   🔄 Procesando: {procesados}/{total} archivos")
        
        # Filtrar solo los que tienen más de un archivo con el mismo hash
        grupos = []
        for hash_val, lista_archivos in grupos_hash.items():
            if len(lista_archivos) > 1:
                grupo = GrupoDuplicados(clave=hash_val, tipo='contenido')
                grupo.archivos = lista_archivos
                grupos.append(grupo)
        
        return grupos
    
    def _generar_reporte(self) -> Dict:
        """Genera el reporte final del análisis."""
        total_duplicados_contenido = sum(g.cantidad - 1 for g in self.grupos_contenido)
        total_duplicados_nombre = sum(g.cantidad - 1 for g in self.grupos_nombre)
        espacio_recuperable_contenido = sum(g.espacio_recuperable for g in self.grupos_contenido)
        espacio_recuperable_nombre = sum(g.espacio_recuperable for g in self.grupos_nombre)
        
        reporte = {
            'fecha': datetime.now().isoformat(),
            'carpeta': str(self.carpeta),
            'total_archivos_analizados': self.total_archivos_analizados,
            'total_archivos_ignorados': self.total_archivos_ignorados,
            'duplicados_por_contenido': {
                'grupos': len(self.grupos_contenido),
                'archivos_duplicados': total_duplicados_contenido,
                'espacio_recuperable': espacio_recuperable_contenido,
                'espacio_recuperable_human': GrupoDuplicados._tamano_human(espacio_recuperable_contenido)
            },
            'duplicados_por_nombre': {
                'grupos': len(self.grupos_nombre),
                'archivos_duplicados': total_duplicados_nombre,
                'espacio_recuperable': espacio_recuperable_nombre,
                'espacio_recuperable_human': GrupoDuplicados._tamano_human(espacio_recuperable_nombre)
            },
            'grupos_contenido': [g.to_dict() for g in self.grupos_contenido],
            'grupos_nombre': [g.to_dict() for g in self.grupos_nombre],
            'errores': self.errores,
            'modo_simulacion': self.modo_simulacion
        }
        
        # Imprimir resumen
        print(f"\n{'='*60}")
        print(f" RESUMEN DEL ANÁLISIS")
        print(f"{'='*60}")
        print(f"📁 Archivos analizados: {self.total_archivos_analizados}")
        print(f"⏭️ Archivos ignorados: {self.total_archivos_ignorados}")
        print(f"\n🔐 Duplicados por contenido:")
        print(f"   - Grupos: {len(self.grupos_contenido)}")
        print(f"   - Archivos duplicados: {total_duplicados_contenido}")
        print(f"   - Espacio recuperable: {GrupoDuplicados._tamano_human(espacio_recuperable_contenido)}")
        print(f"\n📝 Duplicados por nombre:")
        print(f"   - Grupos: {len(self.grupos_nombre)}")
        print(f"   - Archivos duplicados: {total_duplicados_nombre}")
        print(f"   - Espacio recuperable: {GrupoDuplicados._tamano_human(espacio_recuperable_nombre)}")
        print(f"{'='*60}\n")
        
        if self.errores:
            print(f"⚠️ {len(self.errores)} errores durante el análisis")
        
        return reporte
    
    def eliminar_duplicados(
        self,
        grupos: Optional[List[GrupoDuplicados]] = None,
        mover_a_papelera: bool = True
    ) -> Dict:
        """Elimina o mueve a papelera los archivos duplicados."""
        if self.modo_simulacion:
            print("\n🧪 MODO SIMULACIÓN - No se realizarán cambios reales")
        
        if grupos is None:
            grupos = self.grupos_contenido
        
        resultados = {
            'eliminados': [],
            'errores': [],
            'espacio_liberado': 0
        }
        
        for grupo in grupos:
            for duplicado in grupo.duplicados:
                try:
                    if self.modo_simulacion:
                        print(f"   🧪 [SIMULACIÓN] Se eliminaría: {duplicado.ruta}")
                        resultados['eliminados'].append(str(duplicado.ruta))
                        resultados['espacio_liberado'] += duplicado.tamano
                    else:
                        if mover_a_papelera:
                            # Mover a papelera del sistema (requiere send2trash)
                            try:
                                from send2trash import send2trash
                                send2trash(str(duplicado.ruta))
                                print(f"   🗑️ Movido a papelera: {duplicado.ruta}")
                            except ImportError:
                                # Fallback: eliminar permanentemente
                                duplicado.ruta.unlink()
                                print(f"   ❌ Eliminado: {duplicado.ruta}")
                        else:
                            duplicado.ruta.unlink()
                            print(f"   ❌ Eliminado: {duplicado.ruta}")
                        
                        resultados['eliminados'].append(str(duplicado.ruta))
                        resultados['espacio_liberado'] += duplicado.tamano
                
                except Exception as e:
                    error_msg = f"Error al eliminar {duplicado.ruta}: {e}"
                    print(f"   ⚠️ {error_msg}")
                    resultados['errores'].append(error_msg)
        
        resultados['espacio_liberado_human'] = GrupoDuplicados._tamano_human(resultados['espacio_liberado'])
        
        print(f"\n✅ Operación completada")
        print(f"   - Archivos procesados: {len(resultados['eliminados'])}")
        print(f"   - Espacio liberado: {resultados['espacio_liberado_human']}")
        if resultados['errores']:
            print(f"   - Errores: {len(resultados['errores'])}")
        
        return resultados
    
    def exportar_reporte(self, archivo_salida: Path) -> None:
        """Exporta el reporte a un archivo JSON."""
        reporte = self._generar_reporte()
        
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Reporte exportado a: {archivo_salida}")


def main():
    """Función principal para ejecución desde CLI."""
    parser = argparse.ArgumentParser(
        description='Detector de archivos duplicados para Downloads Organizer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python3 detector_duplicados.py --carpeta ~/Downloads
  python3 detector_duplicados.py --carpeta ~/Downloads --simular
  python3 detector_duplicados.py --carpeta ~/Downloads --eliminar
  python3 detector_duplicados.py --carpeta ~/Downloads --exportar reporte.json
        """
    )
    
    parser.add_argument(
        '--carpeta', '-c',
        type=Path,
        default=Path.home() / 'Downloads',
        help='Carpeta a analizar (default: ~/Downloads)'
    )
    parser.add_argument(
        '--simular', '-s',
        action='store_true',
        default=True,
        help='Modo simulación (default: True)'
    )
    parser.add_argument(
        '--real',
        action='store_true',
        help='Ejecutar en modo real (elimina archivos)'
    )
    parser.add_argument(
        '--eliminar',
        action='store_true',
        help='Eliminar duplicados después del análisis'
    )
    parser.add_argument(
        '--exportar', '-e',
        type=Path,
        help='Exportar reporte a archivo JSON'
    )
    parser.add_argument(
        '--tamano-minimo',
        type=int,
        default=TAMANO_MINIMO_DEFAULT,
        help=f'Tamaño mínimo en bytes (default: {TAMANO_MINIMO_DEFAULT})'
    )
    parser.add_argument(
        '--no-recursivo',
        action='store_true',
        help='No buscar en subcarpetas'
    )
    parser.add_argument(
        '--algoritmo',
        choices=['md5', 'sha1', 'sha256', 'sha512'],
        default='sha256',
        help='Algoritmo de hash (default: sha256)'
    )
    
    args = parser.parse_args()
    
    # Validar carpeta
    if not args.carpeta.exists():
        print(f"❌ Error: La carpeta '{args.carpeta}' no existe")
        sys.exit(1)
    
    if not args.carpeta.is_dir():
        print(f"❌ Error: '{args.carpeta}' no es una carpeta")
        sys.exit(1)
    
    # Determinar modo simulación
    modo_simulacion = not args.real
    
    # Crear detector
    detector = DetectorDuplicados(
        carpeta=args.carpeta,
        tamano_minimo=args.tamano_minimo,
        recursivo=not args.no_recursivo,
        algoritmo_hash=args.algoritmo,
        modo_simulacion=modo_simulacion
    )
    
    # Analizar
    reporte = detector.analizar()
    
    # Eliminar duplicados si se solicita
    if args.eliminar:
        if modo_simulacion:
            respuesta = input("\n¿Deseas ejecutar en modo real? (s/n): ")
            if respuesta.lower() == 's':
                detector.modo_simulacion = False
                detector.eliminar_duplicados()
            else:
                print("Operación cancelada")
        else:
            confirmacion = input(f"\n️ ¿Eliminar {reporte['duplicados_por_contenido']['archivos_duplicados']} archivos duplicados? (s/n): ")
            if confirmacion.lower() == 's':
                detector.eliminar_duplicados()
            else:
                print("Operación cancelada")
    
    # Exportar reporte
    if args.exportar:
        detector.exportar_reporte(args.exportar)
    
    return reporte


if __name__ == '__main__':
    main()