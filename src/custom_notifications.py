"""
Módulo de notificaciones personalizadas para Downloads Organizer
Autor: Juan Carlos Blanco Ruiz
Email: juancarlosblancoruiz@gmail.com
"""
import subprocess
import smtplib
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuración por defecto
NOTIFICATION_CONFIG = {
    "desktop": True,
    "sound": False,
    "email": False,
    "email_to": "juancarlosblancoruiz@gmail.com",
    "email_from": "downloads-organizer@localhost",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "",
    "smtp_password": "",
    "log_file": str(Path.home() / ".downloads_organizer_notifications.log")
}

class NotificationManager:
    """Gestor de notificaciones para el organizador"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa el gestor de notificaciones
        
        Args:
            config: Configuración personalizada de notificaciones
        """
        self.config = NOTIFICATION_CONFIG.copy()
        if config:
            self.config.update(config)
        
        # Configurar logging
        self.logger = logging.getLogger("Notifications")
        self.logger.setLevel(logging.INFO)
        
        # Handler para archivo
        file_handler = logging.FileHandler(self.config["log_file"])
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.logger.addHandler(file_handler)
        
        # Handler para consola (solo errores)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        self.logger.addHandler(console_handler)

    def send_desktop_notification(self, title: str, message: str, urgency: str = "normal") -> bool:
        """
        Envía una notificación de escritorio
        
        Args:
            title: Título de la notificación
            message: Mensaje de la notificación
            urgency: Urgencia (low, normal, critical)
        
        Returns:
            True si se envió correctamente, False en caso contrario
        """
        if not self.config["desktop"]:
            return False
        
        try:
            # Intentar con notify-send (Linux)
            subprocess.run([
                "notify-send",
                "-u", urgency,
                "-t", "5000",  # 5 segundos
                title,
                message
            ], check=True, capture_output=True)
            self.logger.info(f"Desktop notification sent: {title}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                # Intentar con osascript (macOS)
                script = f'display notification "{message}" with title "{title}"'
                subprocess.run(["osascript", "-e", script], check=True)
                self.logger.info(f"macOS notification sent: {title}")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.logger.warning("Desktop notifications not available on this system")
                return False

    def send_email_notification(self, subject: str, body: str) -> bool:
        """
        Envía una notificación por email
        
        Args:
            subject: Asunto del email
            body: Cuerpo del email
        
        Returns:
            True si se envió correctamente, False en caso contrario
        """
        if not self.config["email"]:
            return False
        
        if not self.config["smtp_user"] or not self.config["smtp_password"]:
            self.logger.warning("Email credentials not configured")
            return False
        
        try:
            msg = MIMEMultipart()
            msg["From"] = self.config["email_from"]
            msg["To"] = self.config["email_to"]
            msg["Subject"] = subject
            
            msg.attach(MIMEText(body, "plain"))
            
            server = smtplib.SMTP(self.config["smtp_server"], self.config["smtp_port"])
            server.starttls()
            server.login(self.config["smtp_user"], self.config["smtp_password"])
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email notification sent: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            return False

    def play_sound(self, sound_type: str = "info") -> bool:
        """
        Reproduce un sonido de notificación
        
        Args:
            sound_type: Tipo de sonido (info, warning, error)
        
        Returns:
            True si se reprodujo correctamente
        """
        if not self.config["sound"]:
            return False
        
        try:
            if sound_type == "info":
                sound_file = "/usr/share/sounds/freedesktop/stereo/message.oga"
            elif sound_type == "warning":
                sound_file = "/usr/share/sounds/freedesktop/stereo/warning.oga"
            elif sound_type == "error":
                sound_file = "/usr/share/sounds/freedesktop/stereo/dialog-error.oga"
            else:
                sound_file = "/usr/share/sounds/freedesktop/stereo/message.oga"
            
            if Path(sound_file).exists():
                subprocess.run(["paplay", sound_file], check=False, capture_output=True)
                return True
            else:
                # Intentar con el comando 'beep' o 'play'
                subprocess.run(["beep"], check=False, capture_output=True)
                return True
        except Exception:
            return False

    def notify_start(self, total_files: int) -> None:
        """Notifica el inicio de la organización"""
        message = f"Iniciando organización de {total_files} archivo(s)"
        self.send_desktop_notification("🚀 Downloads Organizer", message)
        self.logger.info(f"Started organizing {total_files} files")

    def notify_complete(self, stats: Dict[str, int]) -> None:
        """Notifica la finalización de la organización"""
        message = f"Completado: {stats['moved']} movidos, {stats['errors']} errores"
        self.send_desktop_notification(
            "✅ Downloads Organizer", 
            message, 
            "low" if stats['errors'] == 0 else "normal"
        )
        
        if stats['errors'] > 0:
            self.play_sound("warning")
        else:
            self.play_sound("info")

    def notify_error(self, error_message: str) -> None:
        """Notifica un error crítico"""
        self.send_desktop_notification(" Error en Downloads Organizer", error_message, "critical")
        self.play_sound("error")
        self.logger.error(f"Critical error: {error_message}")

    def notify_file_moved(self, filename: str, category: str) -> None:
        """Notifica que un archivo fue movido"""
        # No enviar notificación por cada archivo (sería molesto)
        self.logger.debug(f"Moved: {filename} -> {category}")

    def notify_storage_warning(self, usage_percent: int) -> None:
        """Notifica que el almacenamiento está bajo"""
        if usage_percent >= 90:
            message = f"⚠️ Almacenamiento crítico: {usage_percent}% usado"
            self.send_desktop_notification("Storage Warning", message, "critical")
            self.play_sound("error")
        elif usage_percent >= 75:
            message = f"⚠️ Almacenamiento bajo: {usage_percent}% usado"
            self.send_desktop_notification("Storage Warning", message, "normal")
            self.play_sound("warning")
        
        self.logger.warning(f"Storage usage at {usage_percent}%")

# Función de conveniencia para uso rápido
def send_notification(title: str, message: str, urgency: str = "normal") -> bool:
    """
    Función simple para enviar una notificación rápida
    Args:
        title: Título de la notificación
        message: Mensaje de la notificación
        urgency: Urgencia (low, normal, critical)

    Returns:
        True si se envió correctamente
    """
    notifier = NotificationManager({"desktop": True})
    return notifier.send_desktop_notification(title, message, urgency)

def log_to_file(message: str, log_file: str = "organizer.log") -> None:
    """
    Guarda un mensaje en el archivo de log
    Args:
        message: Mensaje a guardar
        log_file: Nombre del archivo de log
    """
    log_path = Path.home() / log_file
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()}: {message}\n")

# Ejemplo de uso
if __name__ == "__main__":
    # Probar notificaciones
    notifier = NotificationManager()
    notifier.send_desktop_notification("Test", "¡Las notificaciones funcionan!")
    log_to_file("Test de notificación realizado")