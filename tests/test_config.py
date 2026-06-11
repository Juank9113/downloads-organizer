"""
Pruebas para el módulo de configuración
Autor: Juan Carlos Blanco Ruiz
"""
import unittest
import tempfile
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import ConfigManager


class TestConfigManager(unittest.TestCase):
    """Pruebas para ConfigManager"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.json"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_default_config(self):
        manager = ConfigManager()
        self.assertIsNotNone(manager.config)
        self.assertIn("downloads_dir", manager.config)
        self.assertIn("organized_dir", manager.config)

    def test_load_config_from_file(self):
        custom_config = {"downloads_dir": "/test/downloads", "auto_clean": True}
        
        with open(self.config_path, 'w') as f:
            json.dump(custom_config, f)
        
        manager = ConfigManager(config_path=str(self.config_path))
        self.assertEqual(manager.config["downloads_dir"], "/test/downloads")
        self.assertTrue(manager.config["auto_clean"])

    def test_save_config(self):
        manager = ConfigManager(config_path=str(self.config_path))
        manager.config["test_key"] = "test_value"
        
        result = manager.save(manager.config)
        self.assertTrue(result)
        
        with open(self.config_path, 'r') as f:
            saved_config = json.load(f)
            self.assertEqual(saved_config["test_key"], "test_value")

    def test_get_category_for_extension(self):
        manager = ConfigManager()
        
        test_cases = [
            (".jpg", "Imagenes"),
            (".pdf", "Documentos"),
            (".mp4", "Videos"),
            (".mp3", "Musica"),
            (".py", "Codigo"),
            (".exe", "Programas"),
            (".zip", "Archivos_Comprimidos"),
        ]
        
        for extension, expected_category in test_cases:
            category = manager.get_category_for_extension(extension)
            self.assertEqual(category, expected_category)


if __name__ == "__main__":
    unittest.main()