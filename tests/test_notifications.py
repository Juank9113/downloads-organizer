"""
Tests para el módulo de notificaciones
Autor: Juan Carlos Blanco Ruiz
"""
import unittest
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.custom_notifications import NotificationManager, log_to_file


class TestNotificationManager(unittest.TestCase):
    """Tests para NotificationManager"""

    def test_init_default(self):
        notifier = NotificationManager()
        self.assertIsNotNone(notifier.config)
        self.assertTrue(notifier.config["desktop"])

    def test_init_custom_config(self):
        custom = {"desktop": False, "sound": True}
        notifier = NotificationManager(config=custom)
        self.assertFalse(notifier.config["desktop"])
        self.assertTrue(notifier.config["sound"])

    def test_send_notification_disabled(self):
        notifier = NotificationManager({"desktop": False})
        result = notifier.send_desktop_notification("Test", "Mensaje")
        self.assertFalse(result)


class TestLogToFile(unittest.TestCase):
    """Tests para la función log_to_file"""

    def test_log_to_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            log_file = f.name

        try:
            log_to_file("Mensaje de prueba", log_file)
            with open(log_file, 'r') as f:
                content = f.read()
                self.assertIn("Mensaje de prueba", content)
        finally:
            Path(log_file).unlink()


if __name__ == "__main__":
    unittest.main()
