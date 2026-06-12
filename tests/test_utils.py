"""
Tests para el módulo de utilidades
Autor: Juan Carlos Blanco Ruiz
"""
import unittest
import tempfile
import shutil
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils import (
    get_file_size_str,
    get_file_info,
    safe_move,
    clean_old_files,
    create_backup,
    validate_directory
)


class TestGetFileSizeStr(unittest.TestCase):
    """Tests para la función get_file_size_str"""

    def test_bytes(self):
        self.assertEqual(get_file_size_str(500), "500.0 B")

    def test_kilobytes(self):
        self.assertEqual(get_file_size_str(1024), "1.0 KB")

    def test_megabytes(self):
        self.assertEqual(get_file_size_str(1024 * 1024), "1.0 MB")

    def test_gigabytes(self):
        self.assertEqual(get_file_size_str(1024 ** 3), "1.0 GB")

    def test_terabytes(self):
        self.assertEqual(get_file_size_str(1024 ** 4), "1.0 TB")

    def test_zero(self):
        self.assertEqual(get_file_size_str(0), "0.0 B")


class TestGetFileInfo(unittest.TestCase):
    """Tests para la función get_file_info"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test.txt"
        self.test_file.write_text("contenido de prueba")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_file_exists(self):
        info = get_file_info(self.test_file)
        self.assertEqual(info["name"], "test.txt")
        self.assertEqual(info["extension"], ".txt")
        self.assertIn("size", info)
        self.assertIn("size_str", info)

    def test_file_not_exists(self):
        info = get_file_info(Path("/archivo/inexistente.txt"))
        self.assertEqual(info, {})

    def test_hidden_file(self):
        hidden_file = Path(self.temp_dir) / ".oculto"
        hidden_file.write_text("oculto")
        info = get_file_info(hidden_file)
        self.assertTrue(info["is_hidden"])


class TestSafeMove(unittest.TestCase):
    """Tests para la función safe_move"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.src_dir = Path(self.temp_dir) / "origen"
        self.dst_dir = Path(self.temp_dir) / "destino"
        self.src_dir.mkdir()
        self.dst_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_move_file(self):
        src_file = self.src_dir / "archivo.txt"
        src_file.write_text("contenido")
        dst_file = self.dst_dir / "archivo.txt"

        success, message = safe_move(src_file, dst_file)
        self.assertTrue(success)
        self.assertTrue(dst_file.exists())
        self.assertFalse(src_file.exists())

    def test_move_nonexistent_file(self):
        src_file = self.src_dir / "no_existe.txt"
        dst_file = self.dst_dir / "destino.txt"

        success, message = safe_move(src_file, dst_file)
        self.assertFalse(success)

    def test_move_with_duplicate(self):
        src_file = self.src_dir / "archivo.txt"
        src_file.write_text("contenido")
        dst_file = self.dst_dir / "archivo.txt"
        dst_file.write_text("ya existe")

        success, message = safe_move(src_file, dst_file, overwrite=False)
        self.assertTrue(success)
        # Debe haber creado un archivo con nombre único
        self.assertTrue(self.dst_dir.exists())


class TestValidateDirectory(unittest.TestCase):
    """Tests para la función validate_directory"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_existing_directory(self):
        valid, message = validate_directory(self.temp_dir)
        self.assertTrue(valid)

    def test_nonexistent_directory_no_create(self):
        valid, message = validate_directory("/ruta/inexistente", create=False)
        self.assertFalse(valid)

    def test_nonexistent_directory_with_create(self):
        new_dir = Path(self.temp_dir) / "nueva_carpeta"
        valid, message = validate_directory(str(new_dir), create=True)
        self.assertTrue(valid)
        self.assertTrue(new_dir.exists())


class TestCreateBackup(unittest.TestCase):
    """Tests para la función create_backup"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "original.txt"
        self.test_file.write_text("contenido original")
        self.backup_dir = Path(self.temp_dir) / "backups"

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_create_backup(self):
        backup_path = create_backup(self.test_file, self.backup_dir)
        self.assertIsNotNone(backup_path)
        self.assertTrue(backup_path.exists())
        self.assertIn("backup", backup_path.name)

    def test_backup_nonexistent_file(self):
        fake_file = Path(self.temp_dir) / "no_existe.txt"
        backup_path = create_backup(fake_file, self.backup_dir)
        self.assertIsNone(backup_path)


if __name__ == "__main__":
    unittest.main()
