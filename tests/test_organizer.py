"""
Pruebas unitarias para Downloads Organizer
Autor: Juan Carlos Blanco Ruiz
"""
import unittest
import tempfile
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.organizer import DownloadsOrganizer


class TestDownloadsOrganizer(unittest.TestCase):
    """Pruebas para la clase DownloadsOrganizer"""
    
    def setUp(self):
        """Configuración antes de cada prueba"""
        self.test_dir = tempfile.mkdtemp()
        self.downloads_dir = Path(self.test_dir) / "Downloads"
        self.organized_dir = Path(self.test_dir) / "Organized"
        
        self.downloads_dir.mkdir()
        self.organized_dir.mkdir()
        
        self.test_files = {
            "foto.jpg": "imagen de prueba",
            "documento.pdf": "documento de prueba",
            "video.mp4": "video de prueba",
            "musica.mp3": "audio de prueba",
            "script.py": "print('hola')"
        }
        
        for filename, content in self.test_files.items():
            file_path = self.downloads_dir / filename
            file_path.write_text(content)
        
        self.organizer = DownloadsOrganizer()
        self.organizer.downloads_dir = self.downloads_dir
        self.organizer.organized_dir = self.organized_dir

    def tearDown(self):
        """Limpieza después de cada prueba"""
        shutil.rmtree(self.test_dir)

    def test_get_file_category(self):
        """Prueba la categorización de archivos"""
        test_cases = [
            (".jpg", "Imagenes"),
            (".pdf", "Documentos"),
            (".mp4", "Videos"),
            (".mp3", "Musica"),
            (".py", "Codigo"),
            (".exe", "Programas"),
            (".zip", "Archivos_Comprimidos"),
            (".xyz", "Otros"),
            (".tmp", "EXCLUDED"),
        ]
        
        for extension, expected_category in test_cases:
            category = self.organizer.get_file_category(extension)
            self.assertEqual(category, expected_category)

    def test_get_unique_filename(self):
        """Prueba la generación de nombres únicos"""
        test_file = self.organized_dir / "test.txt"
        test_file.write_text("contenido")
        
        unique_path = self.organizer.get_unique_filename(test_file)
        self.assertNotEqual(unique_path, test_file)

    def test_organize_file(self):
        """Prueba la organización de un archivo individual"""
        file_path = self.downloads_dir / "foto.jpg"
        success, message = self.organizer.organize_file(file_path)
        
        self.assertTrue(success)
        self.assertIn("Imagenes", message)
        
        dest_path = self.organized_dir / "Imagenes" / "foto.jpg"
        self.assertTrue(dest_path.exists())

    def test_create_category_folders(self):
        """Prueba la creación de carpetas de categorías"""
        self.organizer.create_category_folders()
        
        categories = ["Imagenes", "Documentos", "Videos", "Musica", "Codigo", "Programas", "Archivos_Comprimidos", "Otros"]
        
        for category in categories:
            folder = self.organized_dir / category
            self.assertTrue(folder.exists())
            self.assertTrue(folder.is_dir())

    def test_organize_all(self):
        """Prueba la organización de todos los archivos"""
        self.organizer.organize_all()
        
        for filename in self.test_files.keys():
            original_path = self.downloads_dir / filename
            self.assertFalse(original_path.exists())


class TestConfig(unittest.TestCase):
    """Pruebas para la configuración"""
    
    def test_custom_config(self):
        """Prueba la carga de configuración personalizada"""
        import json
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            custom_config = {
                "downloads_dir": "/custom/path",
                "organized_dir": "/custom/organized"
            }
            json.dump(custom_config, f)
            config_path = f.name
        
        try:
            organizer = DownloadsOrganizer(config_path=config_path)
            self.assertEqual(organizer.downloads_dir, Path("/custom/path"))
            self.assertEqual(organizer.organized_dir, Path("/custom/organized"))
        finally:
            Path(config_path).unlink()


if __name__ == "__main__":
    unittest.main()