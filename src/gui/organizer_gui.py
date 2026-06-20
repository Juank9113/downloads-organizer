#!/usr/bin/env python3
"""
Downloads Organizer Pro - GUI con estilo iOS
Integración completa: Undo/Redo + Duplicados + Modo Interactivo + Dashboard
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import sys
import os
import threading
import json
import traceback
import re
import signal
from pathlib import Path
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

DetectorDuplicados = None
GrupoDuplicados = None
UndoManager = None

try:
    from detector_duplicados import DetectorDuplicados, GrupoDuplicados
    print("✅ detector_duplicados importado correctamente")
except Exception as e:
    print(f"⚠️ No se pudo importar detector_duplicados: {e}")

try:
    from undo_manager import UndoManager
    print("✅ undo_manager importado correctamente")
except Exception as e:
    print(f"⚠️ No se pudo importar undo_manager: {e}")


# Tooltip flotante
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind('<Enter>', self.show_tip)
        widget.bind('<Leave>', self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 10
        y = self.widget.winfo_rooty() + 10
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("Segoe UI", 9))
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


# Diálogo interactivo visual con radio buttons
class InteractiveDialog(tk.Toplevel):
    def __init__(self, parent, prompt_text, options, process_stdin, title="Selecciona una opción"):
        super().__init__(parent)
        self.process_stdin = process_stdin
        self.options = options
        self.title(title)
        self.geometry("500x500")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.selected_var = tk.IntVar(value=0)
        self.new_category_var = tk.StringVar(value="")
        self.new_category_entry = None

        msg_label = ttk.Label(self, text="¿Qué deseas hacer con este archivo?", 
                              wraplength=450, font=("Segoe UI", 11, "bold"))
        msg_label.pack(pady=10, padx=20)

        options_frame = ttk.Frame(self)
        options_frame.pack(pady=5, padx=20, fill=tk.X)

        for opt_num, opt_text in options:
            rb = ttk.Radiobutton(options_frame, text=opt_text, 
                                  variable=self.selected_var, value=opt_num,
                                  command=lambda n=opt_num: self._on_option_select(n))
            rb.pack(anchor=tk.W, pady=2, padx=10)

        self.new_cat_frame = ttk.Frame(self)
        ttk.Label(self.new_cat_frame, text="Nombre de la nueva categoría:", 
                  font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=10)
        self.new_category_entry = ttk.Entry(self.new_cat_frame, textvariable=self.new_category_var, width=25)
        self.new_category_entry.pack(side=tk.LEFT, padx=5)
        self.new_cat_frame.pack_forget()

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=15)

        ttk.Button(btn_frame, text="Enviar", command=self.send_response,
                   style="iosAccent.TButton", width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.cancel,
                   style="ios.TButton", width=12).pack(side=tk.LEFT, padx=5)

        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')

    def _on_option_select(self, option_num):
        create_new_num = None
        for num, text in self.options:
            if "Crear nueva categoría" in text or "nueva categoría" in text.lower():
                create_new_num = num
                break
        
        if option_num == create_new_num:
            self.new_cat_frame.pack(pady=5)
            self.new_category_entry.focus_set()
        else:
            self.new_cat_frame.pack_forget()

    def send_response(self):
        selected = self.selected_var.get()
        if selected == 0:
            messagebox.showwarning("Sin selección", "Por favor, selecciona una opción.")
            return
        
        create_new_num = None
        for num, text in self.options:
            if "Crear nueva categoría" in text or "nueva categoría" in text.lower():
                create_new_num = num
                break
        
        if selected == create_new_num:
            new_cat = self.new_category_var.get().strip()
            if not new_cat:
                messagebox.showwarning("Campo vacío", "Por favor, escribe el nombre de la nueva categoría.")
                return
            if self.process_stdin:
                try:
                    self.process_stdin.write(str(selected) + "\n")
                    self.process_stdin.flush()
                    self.process_stdin.write(new_cat + "\n")
                    self.process_stdin.flush()
                except Exception as e:
                    print(f"Error al enviar respuesta: {e}")
            self.destroy()
            return
        
        if self.process_stdin:
            try:
                self.process_stdin.write(str(selected) + "\n")
                self.process_stdin.flush()
            except Exception as e:
                print(f"Error al enviar respuesta: {e}")
        self.destroy()

    def cancel(self):
        if self.process_stdin:
            try:
                self.process_stdin.write("\n")
                self.process_stdin.flush()
            except Exception:
                pass
        self.destroy()


class RememberDialog(tk.Toplevel):
    def __init__(self, parent, prompt_text, process_stdin):
        super().__init__(parent)
        self.process_stdin = process_stdin
        self.title("Recordar decisión")
        self.geometry("400x180")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        ttk.Label(self, text=prompt_text, wraplength=350, font=("Segoe UI", 11)).pack(pady=20, padx=20)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        def send_resp(resp):
            if self.process_stdin:
                try:
                    self.process_stdin.write(resp + "\n")
                    self.process_stdin.flush()
                except Exception:
                    pass
            self.destroy()

        ttk.Button(btn_frame, text="Sí, recordar", command=lambda: send_resp("s"),
                   style="iosAccent.TButton", width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="No recordar", command=lambda: send_resp("n"),
                   style="ios.TButton", width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(self, text="Cancelar", command=self.cancel, style="ios.TButton", width=12).pack(pady=10)

        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f'+{x}+{y}')

    def cancel(self):
        if self.process_stdin:
            try:
                self.process_stdin.write("\n")
                self.process_stdin.flush()
            except Exception:
                pass
        self.destroy()


# Toggle Switch
class ToggleSwitch(ttk.Frame):
    def __init__(self, master, variable, command=None, tooltip_text=None, **kwargs):
        super().__init__(master, **kwargs)
        self.variable = variable
        self.command = command
        self.width = 40
        self.height = 22
        self.anim_pos = 0 if variable.get() else 18
        self.target_pos = 0 if variable.get() else 18
        self.anim_speed = 0.18

        container = ttk.Frame(self)
        container.pack(fill=tk.X, pady=2)

        self.label_left = ttk.Label(container, text="Simulado", font=("Segoe UI", 9, "bold"))
        self.label_left.pack(side=tk.LEFT, padx=(0, 8))

        self.canvas = tk.Canvas(container, width=self.width, height=self.height,
                                highlightthickness=0, bg="white")
        self.canvas.pack(side=tk.LEFT, padx=5)

        self.label_right = ttk.Label(container, text="Real", font=("Segoe UI", 9))
        self.label_right.pack(side=tk.LEFT, padx=(8, 0))

        if tooltip_text:
            Tooltip(self.canvas, tooltip_text)

        self.canvas.bind("<Button-1>", self._on_click)
        self.variable.trace_add("write", lambda *args: self._animate())
        self._update()

    def _on_click(self, event):
        self.variable.set(not self.variable.get())
        if self.command:
            self.command()

    def _animate(self):
        self.target_pos = 0 if self.variable.get() else 18
        self._animate_step(True)

    def _animate_step(self, bounce=False):
        diff = self.target_pos - self.anim_pos
        if abs(diff) < 0.5 and not bounce:
            self.anim_pos = self.target_pos
            self._update()
            return
        if bounce and abs(diff) < 2:
            self.anim_pos = self.target_pos + (diff * 0.3)
            self._update()
            self.after(20, lambda: self._animate_step(False))
            return
        self.anim_pos += diff * self.anim_speed
        self._update()
        self.after(16, lambda: self._animate_step(True if abs(diff) > 2 else False))

    def _update(self):
        self.canvas.delete("all")
        color_off = "#e5e5ea"
        color_on = "#0d6efd"
        progress = self.anim_pos / 18
        current_color = self._interpolate_color(color_off, color_on, progress)

        r = self.height / 2
        self.canvas.create_arc(0, 0, self.height, self.height,
                               start=90, extent=180,
                               fill=current_color, outline=current_color)
        self.canvas.create_arc(self.width - self.height, 0, self.width, self.height,
                               start=270, extent=180,
                               fill=current_color, outline=current_color)
        self.canvas.create_rectangle(r, 0, self.width - r, self.height,
                                     fill=current_color, outline=current_color)

        margin = 1
        circle_size = self.height - 2 * margin
        circle_x = margin + self.anim_pos
        circle_y = margin
        self.canvas.create_oval(circle_x + 1, circle_y + 1,
                                circle_x + circle_size + 1, circle_y + circle_size + 1,
                                fill="#c0c0c0", outline="")
        self.canvas.create_oval(circle_x, circle_y,
                                circle_x + circle_size, circle_y + circle_size,
                                fill="white", outline="#d1d1d6", width=1)

        if self.variable.get():
            self.label_left.config(font=("Segoe UI", 9))
            self.label_right.config(font=("Segoe UI", 9, "bold"))
        else:
            self.label_left.config(font=("Segoe UI", 9, "bold"))
            self.label_right.config(font=("Segoe UI", 9))

    @staticmethod
    def _interpolate_color(color1, color2, factor):
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        r = max(0, min(255, int(r1 + (r2 - r1) * factor)))
        g = max(0, min(255, int(g1 + (g2 - g1) * factor)))
        b = max(0, min(255, int(b1 + (b2 - b1) * factor)))
        return f"#{r:02x}{g:02x}{b:02x}"


class ThemeToggleSwitch(ttk.Frame):
    def __init__(self, master, variable, command=None, tooltip_text=None, is_dark_mode=False, **kwargs):
        super().__init__(master, **kwargs)
        self.variable = variable
        self.command = command
        self.is_dark_mode = is_dark_mode
        self.width = 40
        self.height = 22
        self.anim_pos = 18 if variable.get() else 0
        self.target_pos = 18 if variable.get() else 0
        self.anim_speed = 0.18

        container = ttk.Frame(self)
        container.pack(fill=tk.X, pady=2)

        self.label_left = ttk.Label(container, text="☀️ Claro", font=("Segoe UI", 9, "bold"))
        self.label_left.pack(side=tk.LEFT, padx=(0, 8))

        canvas_bg = "#2d2d2d" if is_dark_mode else "white"
        self.canvas = tk.Canvas(container, width=self.width, height=self.height,
                                highlightthickness=0, bg=canvas_bg)
        self.canvas.pack(side=tk.LEFT, padx=5)

        self.label_right = ttk.Label(container, text=" Oscuro", font=("Segoe UI", 9))
        self.label_right.pack(side=tk.LEFT, padx=(8, 0))

        if tooltip_text:
            Tooltip(self.canvas, tooltip_text)

        self.canvas.bind("<Button-1>", self._on_click)
        self.variable.trace_add("write", lambda *args: self._animate())
        self._update()

    def _on_click(self, event):
        self.variable.set(not self.variable.get())
        if self.command:
            self.command()

    def _animate(self):
        self.target_pos = 18 if self.variable.get() else 0
        self._animate_step(True)

    def _animate_step(self, bounce=False):
        diff = self.target_pos - self.anim_pos
        if abs(diff) < 0.5 and not bounce:
            self.anim_pos = self.target_pos
            self._update()
            return
        if bounce and abs(diff) < 2:
            self.anim_pos = self.target_pos + (diff * 0.3)
            self._update()
            self.after(20, lambda: self._animate_step(False))
            return
        self.anim_pos += diff * self.anim_speed
        self._update()
        self.after(16, lambda: self._animate_step(True if abs(diff) > 2 else False))

    def _update(self):
        self.canvas.delete("all")
        canvas_bg = "#2d2d2d" if self.is_dark_mode else "white"
        self.canvas.configure(bg=canvas_bg)
        color_off = "#e5e5ea"
        color_on = "#0d6efd"
        progress = self.anim_pos / 18
        current_color = self._interpolate_color(color_off, color_on, progress)

        r = self.height / 2
        self.canvas.create_arc(0, 0, self.height, self.height,
                               start=90, extent=180,
                               fill=current_color, outline=current_color)
        self.canvas.create_arc(self.width - self.height, 0, self.width, self.height,
                               start=270, extent=180,
                               fill=current_color, outline=current_color)
        self.canvas.create_rectangle(r, 0, self.width - r, self.height,
                                     fill=current_color, outline=current_color)

        margin = 1
        circle_size = self.height - 2 * margin
        circle_x = margin + self.anim_pos
        circle_y = margin
        self.canvas.create_oval(circle_x + 1, circle_y + 1,
                                circle_x + circle_size + 1, circle_y + circle_size + 1,
                                fill="#c0c0c0", outline="")
        self.canvas.create_oval(circle_x, circle_y,
                                circle_x + circle_size, circle_y + circle_size,
                                fill="white", outline="#d1d1d6", width=1)

        if self.variable.get():
            self.label_left.config(font=("Segoe UI", 9))
            self.label_right.config(font=("Segoe UI", 9, "bold"))
        else:
            self.label_left.config(font=("Segoe UI", 9, "bold"))
            self.label_right.config(font=("Segoe UI", 9))

    @staticmethod
    def _interpolate_color(color1, color2, factor):
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        r = max(0, min(255, int(r1 + (r2 - r1) * factor)))
        g = max(0, min(255, int(g1 + (g2 - g1) * factor)))
        b = max(0, min(255, int(b1 + (b2 - b1) * factor)))
        return f"#{r:02x}{g:02x}{b:02x}"


PERFILES = {
    "General": {"archivo": "config_default.json", "descripcion": "Organización estándar", "icono": ""},
    "Desarrollador": {"archivo": "config_dev.json", "descripcion": "Código y proyectos", "icono": "💻"},
    "Estudiante": {"archivo": "estudiante.json", "descripcion": "Apuntes y tareas", "icono": ""},
    "Diseñador": {"archivo": "disenador.json", "descripcion": "Fuentes e imágenes", "icono": ""},
    "Profesional": {"archivo": "profesional.json", "descripcion": "Documentos laborales", "icono": "💼"},
    "Limpieza": {"archivo": "config_limpieza.json", "descripcion": "Limpieza profunda", "icono": ""},
    "Backup": {"archivo": "config_backup.json", "descripcion": "Respaldos", "icono": "💾"},
    "Multimedia": {"archivo": "config_multimedia.json", "descripcion": "Vídeos y música", "icono": "🎬"},
    "Personalizado": {"archivo": "", "descripcion": "Configuración propia", "icono": "⚙️"}
}

PREFS_FILE = Path.home() / ".downloads_organizer_prefs.json"


class DownloadsOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Downloads Organizer Pro")
        self.root.geometry("1200x900")
        self.root.minsize(950, 750)

        self.style = ttk.Style()
        self.preferences = self._load_preferences()

        self.downloads_dir = tk.StringVar(value=self.preferences.get("downloads_dir", str(Path.home() / "Downloads")))
        self.organized_dir = tk.StringVar(value=self.preferences.get("organized_dir", str(Path.home() / "Downloads_Organized")))
        self.simulate_mode = tk.BooleanVar(value=self.preferences.get("simulate_mode", True))
        self.interactive_mode = tk.BooleanVar(value=self.preferences.get("interactive_mode", False))
        self.config_file = tk.StringVar(value="")
        self.selected_profile = tk.StringVar(value=self.preferences.get("selected_profile", "General"))
        self.dark_mode = tk.BooleanVar(value=self.preferences.get("dark_mode", False))
        self.progress_var = tk.DoubleVar(value=0)
        self.status_text = tk.StringVar(value="Listo para organizar")

        self.dup_folder = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.dup_min_size = tk.StringVar(value="1024")
        self.dup_recursive = tk.BooleanVar(value=True)
        self.dup_simulate = tk.BooleanVar(value=True)

        self.current_detector = None
        self.current_reporte = None
        self.dup_selected_files = set()

        self.last_delete_was_simulation = False

        self.undo_manager = None
        if UndoManager:
            try:
                self.undo_manager = UndoManager()
                print("✅ UndoManager inicializado correctamente")
            except Exception as e:
                print(f"⚠️ Error al inicializar UndoManager: {e}")
                self.undo_manager = None

        self.current_process = None
        self.process_alive = False

        # Configurar cierre seguro
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        try:
            self._setup_ios_styles()
            self._create_header()
            self._create_segmented_control()
            self._create_pages()
            self._create_progress_and_status()
        except Exception as e:
            print(f"❌ Error fatal durante la creación de la GUI: {e}")
            traceback.print_exc()
            sys.exit(1)

        self._on_profile_change()
        self._on_simulate_change()
        self._apply_theme()

        if self.undo_manager:
            self.root.after(100, self._update_undo_redo_panel)

    def on_closing(self):
        """Cerrar aplicación de forma FORZOSA y segura."""
        print("\n🛑 === CERRANDO APLICACIÓN ===")
        
        # 1. Matar proceso hijo AGRESIVAMENTE
        if self.current_process:
            try:
                print("🛑 Terminando proceso hijo...")
                self.current_process.kill()
                self.current_process.wait(timeout=1)
                print("✅ Proceso hijo terminado")
            except Exception as e:
                print(f"⚠️ Proceso ya terminado o error: {e}")
        
        # 2. Cerrar undo_manager
        if self.undo_manager and hasattr(self.undo_manager, 'close'):
            try:
                self.undo_manager.close()
                print("✅ UndoManager cerrado")
            except Exception as e:
                print(f"⚠️ Error al cerrar UndoManager: {e}")
        
        # 3. Destruir ventana de forma forzada
        try:
            print("✅ Destruyendo ventana...")
            self.root.quit()
            self.root.destroy()
            print("✅ Aplicación cerrada\n")
        except Exception as e:
            print(f"⚠️ Error al destruir: {e}")
        
        # 4. Forzar salida si algo queda colgado
        import os
        os._exit(0)

    def _load_preferences(self):
        try:
            if PREFS_FILE.exists():
                with open(PREFS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {}

    def _save_preferences(self):
        try:
            prefs = {
                "dark_mode": self.dark_mode.get(),
                "downloads_dir": self.downloads_dir.get(),
                "organized_dir": self.organized_dir.get(),
                "simulate_mode": self.simulate_mode.get(),
                "interactive_mode": self.interactive_mode.get(),
                "selected_profile": self.selected_profile.get()
            }
            with open(PREFS_FILE, 'w', encoding='utf-8') as f:
                json.dump(prefs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando preferencias: {e}")

    def _setup_ios_styles(self):
        font_family = "TkDefaultFont"
        self.style.configure(".", font=(font_family, 10))
        self.style.configure("TLabel", font=(font_family, 10))
        self.style.configure("TLabelframe.Label", font=(font_family, 10, "bold"))

        if self.dark_mode.get():
            primary_color = "#6c757d"
            accent_color = "#adb5bd"
            bg_color = "#212529"
        else:
            primary_color = "#0d6efd"
            accent_color = "#0dcaf0"
            bg_color = "#ffffff"

        self.style.configure("TLabelframe", bordercolor=primary_color)
        self.style.configure("TLabelframe.Label", foreground=primary_color, font=(font_family, 10, "bold"))

        self.style.configure("ios.TEntry", fieldbackground=bg_color, bordercolor="#c6c6c8",
                             lightcolor="#c6c6c8", borderwidth=1, focusthickness=0, padding=8)
        self.style.map("ios.TEntry", fieldbackground=[("focus", bg_color)])

        self.style.configure("ios.TButton", font=(font_family, 9, "bold"), padding=5,
                             borderwidth=0, focusthickness=0, relief="flat",
                             background=primary_color, foreground="white")
        self.style.map("ios.TButton",
                       background=[("active", accent_color), ("pressed", primary_color)],
                       foreground=[("active", "white"), ("pressed", "white")])

        self.style.configure("iosAccent.TButton", font=(font_family, 9, "bold"), padding=5,
                             borderwidth=0, foreground="white", background=primary_color)
        self.style.map("iosAccent.TButton",
                       background=[("active", accent_color), ("pressed", primary_color)])

        self.style.configure("ios.Horizontal.TProgressbar", thickness=6, troughcolor="#e5e5ea",
                             background="#34c759", bordercolor="#34c759", lightcolor="#34c759",
                             darkcolor="#34c759")

    def _create_header(self):
        header = ttk.Frame(self.root, bootstyle="primary", padding=20)
        header.pack(fill=tk.X, side=tk.TOP)
        ttk.Label(header, text="Downloads Organizer Pro", font=("Segoe UI", 22, "bold"),
                  bootstyle="inverse-primary").pack()
        ttk.Label(header, text="Organiza tus descargas automáticamente", font=("Segoe UI", 11),
                  bootstyle="inverse-primary").pack(pady=(5, 0))

    def _create_segmented_control(self):
        seg_frame = ttk.Frame(self.root)
        seg_frame.pack(fill=tk.X, padx=15, pady=(10, 5), side=tk.TOP)

        self.btn_config = ttk.Button(seg_frame, text="Configuración",
                                     command=lambda: self._show_page(0), style="ios.TButton")
        self.btn_run = ttk.Button(seg_frame, text="Ejecutar",
                                  command=lambda: self._show_page(1), style="ios.TButton")
        self.btn_stats = ttk.Button(seg_frame, text="Estadísticas",
                                    command=lambda: self._show_page(2), style="ios.TButton")
        self.btn_duplicates = ttk.Button(seg_frame, text="Duplicados",
                                         command=lambda: self._show_page(3), style="ios.TButton")

        for btn in (self.btn_config, self.btn_run, self.btn_stats, self.btn_duplicates):
            btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.pages_container = ttk.Frame(self.root)
        self.pages_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15, side=tk.TOP)

        self.pages = [ttk.Frame(self.pages_container) for _ in range(4)]
        self.pages[0].pack(fill=tk.BOTH, expand=True)
        for page in self.pages[1:]:
            page.pack_forget()

    def _show_page(self, index):
        for page in self.pages:
            page.pack_forget()
        self.pages[index].pack(fill=tk.BOTH, expand=True)
        buttons = [self.btn_config, self.btn_run, self.btn_stats, self.btn_duplicates]
        for i, btn in enumerate(buttons):
            if i == index:
                btn.config(style="iosAccent.TButton")
            else:
                btn.config(style="ios.TButton")

    def _create_pages(self):
        self._create_config_page(self.pages[0])
        self._create_run_page(self.pages[1])
        self._create_stats_page(self.pages[2])
        self._create_duplicates_page(self.pages[3])

    def _create_config_page(self, parent):
        theme_frame = ttk.Labelframe(parent, text="  Tema visual  ", padding=10)
        theme_frame.pack(fill=tk.X, pady=(0, 10))

        inner = ttk.Frame(theme_frame)
        inner.pack(fill=tk.X, pady=5)
        ttk.Label(inner, text="Modo Claro/Oscuro:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 20))

        self.theme_toggle = ThemeToggleSwitch(
            inner, variable=self.dark_mode, command=self._toggle_theme,
            tooltip_text="Alterna entre tema claro (Cosmo) y oscuro (Darkly)",
            is_dark_mode=self.dark_mode.get()
        )
        self.theme_toggle.pack(side=tk.LEFT, padx=10)
        ttk.Label(theme_frame, text="Cambia el aspecto completo de la aplicación entre claro y oscuro.",
                  font=("Segoe UI", 9), bootstyle="secondary").pack(anchor=tk.W, pady=(5, 0))

        profile_frame = ttk.Labelframe(parent, text="  Selector de Perfiles  ", padding=10)
        profile_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(profile_frame, text="Selecciona un perfil:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))
        combo_prof = ttk.Frame(profile_frame)
        combo_prof.pack(fill=tk.X, pady=(0, 10))
        self.profile_combo = ttk.Combobox(combo_prof, textvariable=self.selected_profile,
                                          values=list(PERFILES.keys()), state="readonly",
                                          bootstyle="info", font=("Segoe UI", 10))
        self.profile_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.profile_combo.bind("<<ComboboxSelected>>", lambda e: self._on_profile_change())
        ttk.Button(combo_prof, text="Aplicar Perfil", command=self._on_profile_change,
                   style="iosAccent.TButton", width=12).pack(side=tk.RIGHT)

        self.profile_desc_var = tk.StringVar()
        ttk.Label(profile_frame, textvariable=self.profile_desc_var,
                  font=("Segoe UI", 9), bootstyle="secondary").pack(anchor=tk.W)

        folders_frame = ttk.Labelframe(parent, text="  Carpetas  ", padding=10)
        folders_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(folders_frame, text="Carpeta de origen:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        src_f = ttk.Frame(folders_frame)
        src_f.pack(fill=tk.X, pady=(0, 10))
        ttk.Entry(src_f, textvariable=self.downloads_dir, style="ios.TEntry").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(src_f, text="Seleccionar...", command=self._browse_downloads, style="ios.TButton", width=12).pack(side=tk.RIGHT)

        ttk.Label(folders_frame, text="Carpeta de destino:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        dst_f = ttk.Frame(folders_frame)
        dst_f.pack(fill=tk.X)
        ttk.Entry(dst_f, textvariable=self.organized_dir, style="ios.TEntry").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(dst_f, text="Seleccionar...", command=self._browse_organized, style="ios.TButton", width=12).pack(side=tk.RIGHT)

        sim_frame = ttk.Labelframe(parent, text="  Modo de Ejecución  ", padding=10)
        sim_frame.pack(fill=tk.X, pady=(0, 10))

        sim_container = ttk.Frame(sim_frame)
        sim_container.pack(fill=tk.X, pady=5)
        ttk.Label(sim_container, text="Modo simulación:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 20))

        self.simulate_toggle = ToggleSwitch(
            sim_container, variable=self.simulate_mode, command=self._on_simulate_change,
            tooltip_text="Simulado: solo previsualiza los cambios.\nReal: mueve/renombra archivos realmente."
        )
        self.simulate_toggle.pack(side=tk.LEFT, padx=10)

        inter_container = ttk.Frame(sim_frame)
        inter_container.pack(fill=tk.X, pady=5)
        ttk.Label(inter_container, text="Modo interactivo:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 20))
        self.interactive_check = ttk.Checkbutton(inter_container, variable=self.interactive_mode,
                                                  command=self._on_interactive_change)
        self.interactive_check.pack(side=tk.LEFT, padx=10)
        Tooltip(self.interactive_check, "Pregunta qué hacer con archivos de extensiones desconocidas.\nSe mostrarán ventanas con botones.")
        ttk.Label(inter_container, text="Ventanas con botones para elegir opciones",
                  font=("Segoe UI", 9), bootstyle="info").pack(side=tk.LEFT, padx=10)

        ttk.Label(sim_frame,
                  text="Simulado: previsualiza sin mover archivos.\nReal: ejecuta la organización real.",
                  wraplength=700, bootstyle="info", font=("Segoe UI", 9), justify=tk.LEFT).pack(anchor=tk.W, pady=(5, 0))

        extra_frame = ttk.Labelframe(parent, text="  Opciones avanzadas  ", padding=10)
        extra_frame.pack(fill=tk.X)

        ttk.Label(extra_frame, text="Archivo de configuración (JSON):", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        cfg_f = ttk.Frame(extra_frame)
        cfg_f.pack(fill=tk.X)
        ttk.Entry(cfg_f, textvariable=self.config_file, style="ios.TEntry").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(cfg_f, text="Examinar...", command=self._browse_config, style="ios.TButton", width=12).pack(side=tk.RIGHT)

    def _create_run_page(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 15))

        center_frame = ttk.Frame(button_frame)
        center_frame.pack(anchor=tk.CENTER)

        self.run_button = ttk.Button(center_frame, text="Organizar", command=self._run_organizer,
                                     style="iosAccent.TButton", width=12)
        self.run_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(center_frame, text="Limpiar", command=self._clear_output,
                   style="ios.TButton", width=10).pack(side=tk.LEFT, padx=5)

        out_group = ttk.Labelframe(parent, text="  Salida del programa  ", padding=10)
        out_group.pack(fill=tk.BOTH, expand=True)

        self.output_text = tk.Text(out_group, wrap=tk.WORD, font=("Consolas", 10),
                                   bg="#1e1e1e", fg="#d4d4d4", insertbackground="#ffffff",
                                   relief=tk.FLAT, bd=0)
        scroll = ttk.Scrollbar(out_group, orient=tk.VERTICAL, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=scroll.set)
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.interactive_info_label = ttk.Label(parent, text="", font=("Segoe UI", 10))
        self.interactive_info_label.pack_forget()

    def _create_stats_page(self, parent):
        main_btn_frame = ttk.Frame(parent)
        main_btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Button(main_btn_frame, text="📊 Abrir Dashboard Completo", 
                   command=self._open_dashboard,
                   style="iosAccent.TButton", width=25).pack(pady=5)
        
        ttk.Label(main_btn_frame, 
                  text="Abre una ventana con gráficos interactivos, filtros y exportación",
                  font=("Segoe UI", 9), bootstyle="secondary").pack()
        
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        quick_frame = ttk.Frame(parent)
        quick_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(quick_frame, text="Estadísticas Rápidas (texto):", 
                  font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_frame, text="Cargar", command=self._load_stats,
                   style="ios.TButton", width=12).pack(side=tk.LEFT, padx=5)

        stats_group = ttk.Labelframe(parent, text="  Información en texto  ", padding=10)
        stats_group.pack(fill=tk.BOTH, expand=True)

        self.stats_text = tk.Text(stats_group, wrap=tk.WORD, font=("Consolas", 10),
                                  bg="#1e1e1e", fg="#d4d4d4", insertbackground="#ffffff",
                                  relief=tk.FLAT, bd=0)
        scroll = ttk.Scrollbar(stats_group, orient=tk.VERTICAL, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=scroll.set)
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _open_dashboard(self):
        """Abre la ventana del dashboard de estadísticas."""
        print("\n📊 Abriendo dashboard...")
        try:
            print("📦 Importando módulos...")
            from stats_dashboard import StatsDashboard
            from db_manager import DatabaseManager
            
            print("🗄️ Creando DatabaseManager...")
            db = DatabaseManager()
            
            print("🎨 Creando dashboard...")
            dashboard = StatsDashboard(self.root, db_manager=db, 
                                        is_dark_mode=self.dark_mode.get())
            
            print("✅ Dashboard creado correctamente")
            dashboard.focus_set()
            
        except ImportError as e:
            print(f"❌ Error de importación: {e}")
            messagebox.showerror("Error de Importación", 
                f"No se pudo cargar el módulo de estadísticas:\n{e}\n\n"
                "Asegúrate de tener instalado matplotlib:\n"
                "pip install matplotlib>=3.7.0")
        except Exception as e:
            print(f"❌ Error al abrir dashboard: {e}")
            print(traceback.format_exc())
            messagebox.showerror("Error al abrir dashboard", 
                f"Error al abrir dashboard:\n{e}\n\n"
                f"Detalles:\n{traceback.format_exc()}")

    def _create_duplicates_page(self, parent):
        print("   Iniciando creación de página de duplicados...")
        history_frame = ttk.Frame(parent, padding=10)
        history_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(history_frame, text="Historial de Operaciones", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W)
        self.undo_redo_label = ttk.Label(history_frame,
                                         text="↩️ Deshacer: 0 disponibles  |  ↪️ Rehacer: 0 disponibles",
                                         font=("TkDefaultFont", 10))
        self.undo_redo_label.pack(pady=5)
        print("   Historial creado.")

        config_frame = ttk.Frame(parent, padding=10)
        config_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(config_frame, text="Carpeta a analizar:", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        folder_frame = ttk.Frame(config_frame)
        folder_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Entry(folder_frame, textvariable=self.dup_folder).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(folder_frame, text="Examinar...", command=self._browse_dup_folder).pack(side=tk.RIGHT)

        options_frame = ttk.Frame(config_frame)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(options_frame, text="Tamaño mínimo (bytes):").pack(side=tk.LEFT, pady=5, padx=(0, 10))
        size_entry = tk.Entry(options_frame, textvariable=self.dup_min_size, width=15)
        size_entry.pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(options_frame, text="Búsqueda recursiva:").pack(side=tk.LEFT, pady=5, padx=(0, 5))
        tk.Checkbutton(options_frame, variable=self.dup_recursive).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(options_frame, text="Modo simulación:").pack(side=tk.LEFT, pady=5, padx=(0, 5))
        tk.Checkbutton(options_frame, variable=self.dup_simulate).pack(side=tk.LEFT)
        print("   Configuración creada.")

        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(button_frame, text="🔍 Analizar Duplicados", command=self._analyze_duplicates,
                   style="iosAccent.TButton", width=18).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Eliminar", command=self._delete_selected_duplicates,
                   style="iosAccent.TButton", width=12).pack(side=tk.LEFT, padx=5)
        self.undo_button = ttk.Button(button_frame, text="↩️ Deshacer", command=self._do_undo,
                                      style="ios.TButton", width=12, state=tk.DISABLED)
        self.undo_button.pack(side=tk.LEFT, padx=5)
        self.redo_button = ttk.Button(button_frame, text="↪️ Rehacer", command=self._do_redo,
                                      style="ios.TButton", width=12, state=tk.DISABLED)
        self.redo_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🧹 Limpiar", command=self._clear_dup_results,
                   style="ios.TButton", width=12).pack(side=tk.RIGHT, padx=5)
        print("   Botones creados.")

        self.dup_summary_frame = ttk.Frame(parent)
        self.dup_summary_frame.pack(fill=tk.X, pady=(0, 10))
        self.dup_summary_label = ttk.Label(self.dup_summary_frame, text="", font=("TkDefaultFont", 10, "bold"))
        self.dup_summary_label.pack()

        results_frame = ttk.Frame(parent)
        results_frame.pack(fill=tk.BOTH, expand=True)
        self.dup_text = tk.Text(results_frame, wrap=tk.WORD, font=("TkFixedFont", 9),
                                relief=tk.FLAT, bd=0, state=tk.DISABLED)
        scroll_y = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.dup_text.yview)
        scroll_x = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.dup_text.xview)
        self.dup_text.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.dup_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.dup_text.bind("<Double-1>", self._on_dup_text_double_click)

        self.dup_placeholder = ttk.Label(results_frame,
                                         text="Haz clic en 'Analizar Duplicados' para comenzar",
                                         font=("TkDefaultFont", 11))
        self.dup_placeholder.pack(pady=50)

        self.dup_text.tag_configure('header', foreground='blue', font=('TkDefaultFont', 10, 'bold'))
        self.dup_text.tag_configure('original', foreground='green')
        self.dup_text.tag_configure('duplicate', foreground='orange')
        self.dup_text.tag_configure('selected', foreground='red', font=('TkFixedFont', 9, 'bold'))
        self.dup_text.tag_configure('restored', foreground='green', font=('TkFixedFont', 9, 'bold'))
        print("  ✅ Página de duplicados creada correctamente")

    def _on_dup_text_double_click(self, event):
        try:
            index = self.dup_text.index(f"@{event.x},{event.y}")
            line_num = int(index.split('.')[0])
            line_content = self.dup_text.get(f"{line_num}.0", f"{line_num}.end").strip()
            clean_line = line_content
            if clean_line.startswith('⭐ '):
                clean_line = clean_line[2:]
            if clean_line.startswith('[ ]') or clean_line.startswith('[✓]'):
                file_path = clean_line[4:].strip()
                if line_content.startswith('⭐ ['):
                    checkbox_start = 2
                else:
                    checkbox_start = 0
                if file_path in self.dup_selected_files:
                    self.dup_selected_files.remove(file_path)
                    self.dup_text.config(state=tk.NORMAL)
                    if line_content.startswith('⭐'):
                        self.dup_text.delete(f"{line_num}.{checkbox_start}", f"{line_num}.{checkbox_start+3}")
                        self.dup_text.insert(f"{line_num}.{checkbox_start}", '[ ]')
                    else:
                        self.dup_text.delete(f"{line_num}.0", f"{line_num}.3")
                        self.dup_text.insert(f"{line_num}.0", '[ ]')
                    self.dup_text.tag_remove('selected', f"{line_num}.0", f"{line_num}.end")
                    self.dup_text.config(state=tk.DISABLED)
                else:
                    self.dup_selected_files.add(file_path)
                    self.dup_text.config(state=tk.NORMAL)
                    if line_content.startswith('⭐'):
                        self.dup_text.delete(f"{line_num}.{checkbox_start}", f"{line_num}.{checkbox_start+3}")
                        self.dup_text.insert(f"{line_num}.{checkbox_start}", '[✓]')
                    else:
                        self.dup_text.delete(f"{line_num}.0", f"{line_num}.3")
                        self.dup_text.insert(f"{line_num}.0", '[✓]')
                    self.dup_text.tag_add('selected', f"{line_num}.0", f"{line_num}.end")
                    self.dup_text.config(state=tk.DISABLED)
                self.status_text.set(f"Seleccionados: {len(self.dup_selected_files)} archivos")
        except Exception as e:
            print(f"Error en doble clic: {e}")

    def _browse_dup_folder(self):
        folder = filedialog.askdirectory(initialdir=self.dup_folder.get())
        if folder:
            self.dup_folder.set(folder)

    def _analyze_duplicates(self):
        if not DetectorDuplicados:
            messagebox.showerror("Error", "El módulo detector_duplicados no está disponible.")
            return
        folder = Path(self.dup_folder.get())
        if not folder.exists():
            messagebox.showerror("Error", f"La carpeta '{folder}' no existe")
            return
        self.status_text.set("Analizando duplicados...")
        self.dup_selected_files.clear()
        self.current_detector = None
        self.current_reporte = None
        if hasattr(self, 'dup_placeholder'):
            self.dup_placeholder.pack_forget()
        self.dup_text.config(state=tk.NORMAL)
        self.dup_text.delete(1.0, tk.END)
        self.dup_text.insert(tk.END, "🔍 Analizando... por favor espere\n")
        self.dup_text.config(state=tk.DISABLED)
        thread = threading.Thread(target=self._run_duplicate_analysis, args=(folder,))
        thread.daemon = True
        thread.start()

    def _run_duplicate_analysis(self, folder):
        try:
            try:
                min_size = int(self.dup_min_size.get())
            except ValueError:
                min_size = 1024
            detector = DetectorDuplicados(
                carpeta=folder,
                tamano_minimo=min_size,
                recursivo=self.dup_recursive.get(),
                modo_simulacion=self.dup_simulate.get()
            )
            reporte = detector.analizar()
            self.root.after(0, self._display_dup_results_text, reporte, detector)
        except Exception as e:
            self.root.after(0, lambda: self._show_analysis_error(str(e)))

    def _show_analysis_error(self, error_msg):
        messagebox.showerror("Error en el análisis", error_msg)
        self.status_text.set("Error en el análisis")

    def _display_dup_results_text(self, reporte, detector):
        self.current_detector = detector
        self.current_reporte = reporte
        total_duplicados = reporte['duplicados_por_contenido']['archivos_duplicados']
        espacio_recuperable = reporte['duplicados_por_contenido']['espacio_recuperable_human']
        grupos = len(detector.grupos_contenido)
        if total_duplicados > 0:
            self.dup_summary_label.config(
                text=f"📊 Se encontraron {grupos} grupos con {total_duplicados} archivos duplicados | Espacio recuperable: {espacio_recuperable}",
                bootstyle="warning"
            )
        else:
            self.dup_summary_label.config(
                text="✅ No se encontraron archivos duplicados",
                bootstyle="success"
            )
        self.dup_text.config(state=tk.NORMAL)
        self.dup_text.delete(1.0, tk.END)
        if detector.grupos_contenido:
            self.dup_text.insert(tk.END, "🔐 DUPLICADOS POR CONTENIDO\n\n", 'header')
            self.dup_text.insert(tk.END, "💡 Doble clic en CUALQUIER archivo para marcarlo para eliminación\n\n", 'header')
            for i, grupo in enumerate(detector.grupos_contenido, 1):
                original = grupo.archivo_original
                self.dup_text.insert(tk.END, f"\nGrupo {i} - Tamaño: {grupo.archivos[0]._tamano_human()}\n", 'header')
                self.dup_text.insert(tk.END, f"{'='*60}\n")
                for archivo in grupo.archivos:
                    es_original = (archivo == original)
                    file_path = str(archivo.ruta)
                    file_size = archivo._tamano_human()
                    file_date = archivo.fecha_modificacion.strftime('%Y-%m-%d %H:%M')
                    if es_original:
                        self.dup_text.insert(tk.END, f"⭐ [ ] {file_path} ({file_size}) - {file_date}\n", 'original')
                    else:
                        self.dup_text.insert(tk.END, f"   [ ] {file_path} ({file_size}) - {file_date}\n", 'duplicate')
                self.dup_text.insert(tk.END, "\n")
        self.dup_text.config(state=tk.DISABLED)
        self.status_text.set(f"Análisis completado: {total_duplicados} duplicados encontrados")
        if total_duplicados > 0:
            messagebox.showinfo("Análisis completado",
                              f"Se encontraron {total_duplicados} archivos duplicados.\n"
                              f"Espacio recuperable: {espacio_recuperable}\n\n"
                              f"Los archivos marcados con ⭐ son los más recientes.\n"
                              f"⚠️ AHORA PUEDES MARCAR CUALQUIER ARCHIVO (incluido el más reciente)\n"
                              f"Haz doble clic en una línea para marcarla para eliminación.")

    def _get_selected_files(self):
        return list(self.dup_selected_files)

    def _delete_selected_duplicates(self):
        if not GrupoDuplicados:
            messagebox.showerror("Error", "El módulo detector_duplicados no está disponible.")
            return
        selected_files = self._get_selected_files()
        if not selected_files:
            messagebox.showwarning("Sin selección",
                                   "No has seleccionado ningún archivo para eliminar.\n\n"
                                   "Haz doble clic en las líneas que deseas eliminar para marcarlas con [✓].")
            return
        modo = "SIMULACIÓN" if self.dup_simulate.get() else "REAL"
        mensaje = (f"Se eliminarán {len(selected_files)} archivo(s) en modo {modo}:\n\n"
                   f"{chr(10).join(['  • ' + f for f in selected_files[:10]])}")
        if len(selected_files) > 10:
            mensaje += f"\n  ... y {len(selected_files) - 10} más"
        if not messagebox.askyesno("Confirmar eliminación", mensaje):
            return
        self.status_text.set(f"Eliminando {len(selected_files)} archivos...")
        self.last_delete_was_simulation = self.dup_simulate.get()
        thread = threading.Thread(target=self._run_delete_selected, args=(selected_files,))
        thread.daemon = True
        thread.start()

    def _run_delete_selected(self, selected_files):
        resultados = {'eliminados': [], 'errores': [], 'espacio_liberado': 0}
        modo_simulacion = self.dup_simulate.get()
        for ruta_str in selected_files:
            ruta = Path(ruta_str)
            try:
                if modo_simulacion:
                    print(f"  🧪 [SIMULACIÓN] Se eliminaría: {ruta}")
                    resultados['eliminados'].append(str(ruta))
                    try:
                        resultados['espacio_liberado'] += ruta.stat().st_size
                    except:
                        pass
                else:
                    if self.undo_manager:
                        temp_path = Path.home() / f".deleted_files_{int(ruta.stat().st_mtime)}"
                        try:
                            import shutil
                            shutil.move(str(ruta), str(temp_path))
                            self.undo_manager.record_action('delete', str(ruta), str(temp_path))
                            resultados['eliminados'].append(str(ruta))
                            try:
                                resultados['espacio_liberado'] += ruta.stat().st_size
                            except:
                                pass
                        except Exception as move_error:
                            error_msg = f"Error al mover a temporal: {move_error}"
                            print(f"  ⚠️ {error_msg}")
                            resultados['errores'].append(error_msg)
                    else:
                        try:
                            from send2trash import send2trash
                            send2trash(str(ruta))
                            print(f"  🗑️ Movido a papelera: {ruta}")
                        except ImportError:
                            ruta.unlink()
                            print(f"  ❌ Eliminado: {ruta}")
                        resultados['eliminados'].append(str(ruta))
                        try:
                            resultados['espacio_liberado'] += ruta.stat().st_size
                        except:
                            pass
            except Exception as e:
                error_msg = f"Error al eliminar {ruta}: {e}"
                print(f"  ⚠️ {error_msg}")
                resultados['errores'].append(error_msg)
        espacio_human = GrupoDuplicados._tamano_human(resultados['espacio_liberado'])
        modo_str = "SIMULACIÓN" if modo_simulacion else "REAL"
        mensaje = (f"Operación completada en modo {modo_str}\n\n"
                   f"✅ Archivos procesados: {len(resultados['eliminados'])}\n"
                   f"💾 Espacio liberado: {espacio_human}")
        if resultados['errores']:
            mensaje += f"\n\n⚠️ Errores: {len(resultados['errores'])}"
        self.root.after(0, lambda: messagebox.showinfo("Resultado", mensaje))
        self.root.after(0, lambda: self.status_text.set(f"Eliminación completada: {len(resultados['eliminados'])} archivos"))
        self.root.after(500, self._activate_undo_after_delete)
        if not modo_simulacion:
            self.root.after(1000, lambda: self._refresh_after_deletion())

    def _activate_undo_after_delete(self):
        if self.undo_manager:
            try:
                history = self.undo_manager.get_history()
                undo_count = history['undo_count']
                if self.last_delete_was_simulation:
                    self.undo_redo_label.config(
                        text=f"↩️ Deshacer: 0 disponibles (simulación)  |  ↪️ Rehacer: 0 disponibles"
                    )
                    self.undo_button.config(state=tk.NORMAL)
                    self.status_text.set("🧪 Simulación completada. Puedes probar Deshacer (no hay cambios reales).")
                    self.redo_button.config(state=tk.DISABLED)
                else:
                    if undo_count > 0:
                        self.undo_button.config(state=tk.NORMAL)
                        self.status_text.set("✅ Eliminación completada. Usa 'Deshacer' para recuperar los archivos.")
                    else:
                        self.undo_button.config(state=tk.DISABLED)
                    self.redo_button.config(state=tk.DISABLED)
                    self.undo_redo_label.config(
                        text=f"↩️ Deshacer: {undo_count} disponibles  |  ↪️ Rehacer: 0 disponibles"
                    )
            except Exception as e:
                print(f"   ⚠️ Error al activar Deshacer: {e}")

    def _refresh_after_deletion(self):
        self.dup_text.config(state=tk.NORMAL)
        self.dup_text.delete(1.0, tk.END)
        self.dup_text.config(state=tk.DISABLED)
        self.dup_selected_files.clear()
        self.current_detector = None
        self.current_reporte = None
        self.dup_summary_label.config(text="")
        if hasattr(self, 'dup_placeholder'):
            self.dup_placeholder.pack(pady=50)

    def _clear_dup_results(self):
        self.dup_text.config(state=tk.NORMAL)
        self.dup_text.delete(1.0, tk.END)
        self.dup_text.config(state=tk.DISABLED)
        self.dup_selected_files.clear()
        self.current_detector = None
        self.current_reporte = None
        self.dup_summary_label.config(text="")
        if hasattr(self, 'dup_placeholder'):
            self.dup_placeholder.pack(pady=50)
        self.status_text.set("Resultados limpiados")
        self.last_delete_was_simulation = False
        self._update_undo_redo_panel()

    def _update_undo_redo_panel(self):
        if self.undo_manager:
            try:
                history = self.undo_manager.get_history()
                undo_count = history['undo_count']
                redo_count = history['redo_count']
                self.undo_redo_label.config(
                    text=f"↩️ Deshacer: {undo_count} disponibles  |  ↪️ Rehacer: {redo_count} disponibles"
                )
                if self.last_delete_was_simulation:
                    self.undo_button.config(state=tk.NORMAL)
                else:
                    self.undo_button.config(state=tk.NORMAL if undo_count > 0 else tk.DISABLED)
                self.redo_button.config(state=tk.NORMAL if redo_count > 0 else tk.DISABLED)
            except Exception as e:
                print(f"Error al actualizar panel: {e}")
        else:
            self.undo_redo_label.config(text="⚠️ Sistema Undo/Redo no disponible")
            self.undo_button.config(state=tk.DISABLED)
            self.redo_button.config(state=tk.DISABLED)

    def _do_undo(self):
        if self.last_delete_was_simulation:
            messagebox.showinfo("Modo simulación", "Esta operación fue una simulación, no se realizaron cambios reales.\nNo hay nada que deshacer.")
            return
        if not self.undo_manager:
            messagebox.showwarning("No disponible", "El sistema Undo/Redo no está disponible.")
            return
        try:
            history = self.undo_manager.get_history()
            if history['undo_count'] == 0:
                messagebox.showinfo("Sin acciones", "No hay acciones para deshacer.")
                return
            if not messagebox.askyesno("Confirmar Deshacer", "¿Estás seguro de que deseas deshacer la última operación?\n\nLos archivos volverán a su ubicación original."):
                return
            self.status_text.set("Deshaciendo última operación...")
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, "🔄 Ejecutando operación de deshacer...\n\n")
            thread = threading.Thread(target=self._run_undo)
            thread.daemon = True
            thread.start()
        except Exception as e:
            messagebox.showerror("Error", f"Error al deshacer: {str(e)}")

    def _run_undo(self):
        try:
            history = self.undo_manager.get_history()
            if history['undo_stack']:
                last_action = history['undo_stack'][-1]
                action_info = f"Archivo: {last_action.get('source', 'desconocido')}"
            else:
                action_info = ""
            success, msg = self.undo_manager.undo()
            self.root.after(0, lambda: self._handle_undo_result_with_feedback(success, msg, "Deshacer", action_info))
        except Exception as e:
            self.root.after(0, lambda: self.output_text.insert(tk.END, f"❌ Error: {str(e)}\n"))
            self.root.after(0, lambda: self.status_text.set("Error al deshacer"))

    def _handle_undo_result_with_feedback(self, success, msg, operation, action_info):
        icon = "✅" if success else "❌"
        self.output_text.insert(tk.END, f"{icon} {operation}: {msg}\n")
        if action_info:
            self.output_text.insert(tk.END, f"   📄 {action_info}\n")
        self.output_text.insert(tk.END, f"   🔄 Los archivos han vuelto a su ubicación original\n\n")
        self.output_text.see(tk.END)
        self.status_text.set("Operación exitosa - Archivos recuperados")
        self.last_delete_was_simulation = False
        if self.undo_manager:
            try:
                history = self.undo_manager.get_history()
                redo_count = history['redo_count']
                undo_count = history['undo_count']
                self.undo_redo_label.config(
                    text=f"↩️ Deshacer: {undo_count} disponibles  |  ↪️ Rehacer: {redo_count} disponibles"
                )
                self.undo_button.config(state=tk.NORMAL if undo_count > 0 else tk.DISABLED)
                self.redo_button.config(state=tk.NORMAL if redo_count > 0 else tk.DISABLED)
                if redo_count > 0:
                    self.status_text.set("Archivos recuperados. Usa 'Rehacer' para eliminar permanentemente.")
            except Exception as e:
                print(f"Error al actualizar panel: {e}")
        self._show_restored_files_feedback()

    def _show_restored_files_feedback(self):
        self.dup_text.config(state=tk.NORMAL)
        self.dup_text.insert(tk.END, "\n" + "="*60 + "\n")
        self.dup_text.insert(tk.END, "✅ ARCHIVOS RECUPERADOS EXITOSAMENTE\n", 'restored')
        self.dup_text.insert(tk.END, "="*60 + "\n")
        self.dup_text.insert(tk.END, "📍 Los archivos eliminados han vuelto a su ubicación original.\n")
        self.dup_text.insert(tk.END, "🔄 Puedes usar 'Rehacer' si deseas volver a eliminarlos.\n\n")
        self.dup_text.config(state=tk.DISABLED)
        self.dup_text.see(tk.END)
        messagebox.showinfo("✅ Archivos Recuperados", "Los archivos han sido recuperados exitosamente.\n\nLos archivos están ahora en su ubicación original.\n\nUsa 'Rehacer' si deseas volver a eliminarlos.")

    def _do_redo(self):
        if not self.undo_manager:
            messagebox.showwarning("No disponible", "El sistema Undo/Redo no está disponible.")
            return
        try:
            history = self.undo_manager.get_history()
            if history['redo_count'] == 0:
                messagebox.showinfo("Sin acciones", "No hay acciones para rehacer.")
                return
            if not messagebox.askyesno("Confirmar Rehacer", "¿Estás seguro de que deseas rehacer la última operación?\n\nLos archivos volverán a ser eliminados permanentemente."):
                return
            self.status_text.set("Rehaciendo última operación...")
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, "🔄 Ejecutando operación de rehacer...\n\n")
            thread = threading.Thread(target=self._run_redo)
            thread.daemon = True
            thread.start()
        except Exception as e:
            messagebox.showerror("Error", f"Error al rehacer: {str(e)}")

    def _run_redo(self):
        try:
            success, msg = self.undo_manager.redo()
            self.root.after(0, lambda: self._handle_redo_result(success, msg, "Rehacer"))
        except Exception as e:
            self.root.after(0, lambda: self.output_text.insert(tk.END, f"❌ Error: {str(e)}\n"))
            self.root.after(0, lambda: self.status_text.set("Error al rehacer"))

    def _handle_redo_result(self, success, msg, operation):
        icon = "✅" if success else "❌"
        self.output_text.insert(tk.END, f"{icon} {operation}: {msg}\n")
        self.output_text.insert(tk.END, f"   ⚠️ Los archivos han sido eliminados nuevamente\n\n")
        self.output_text.see(tk.END)
        self.status_text.set("Rehacer exitoso - Archivos eliminados permanentemente")
        if self.undo_manager:
            try:
                history = self.undo_manager.get_history()
                undo_count = history['undo_count']
                redo_count = history['redo_count']
                self.undo_redo_label.config(
                    text=f"↩️ Deshacer: {undo_count} disponibles  |  ↪️ Rehacer: {redo_count} disponibles"
                )
                self.undo_button.config(state=tk.NORMAL if undo_count > 0 else tk.DISABLED)
                self.redo_button.config(state=tk.NORMAL if redo_count > 0 else tk.DISABLED)
                if undo_count > 0:
                    self.status_text.set("Archivos eliminados. Usa 'Deshacer' para recuperarlos.")
            except Exception as e:
                print(f"Error al actualizar panel: {e}")

    def _create_progress_and_status(self):
        progress_frame = ttk.Frame(self.root, padding=(15, 0, 15, 10))
        progress_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                            style="ios.Horizontal.TProgressbar", maximum=100)
        self.progress_bar.pack(fill=tk.X)
        status_bar = ttk.Label(self.root, textvariable=self.status_text,
                               bootstyle="secondary", padding=10, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _apply_theme(self):
        theme = "darkly" if self.dark_mode.get() else "cosmo"
        self.style.theme_use(theme)
        self._setup_ios_styles()
        if hasattr(self, 'theme_toggle'):
            self.theme_toggle.is_dark_mode = self.dark_mode.get()
            self.theme_toggle._update()

    def _toggle_theme(self):
        self._apply_theme()
        self.status_text.set("Modo oscuro activado" if self.dark_mode.get() else "Modo claro activado")
        self._save_preferences()

    def _on_simulate_change(self):
        self.status_text.set("Modo simulación: ACTIVADO" if self.simulate_mode.get() else "Modo simulación: DESACTIVADO")

    def _on_interactive_change(self):
        self.status_text.set("Modo interactivo: ACTIVADO" if self.interactive_mode.get() else "Modo interactivo: DESACTIVADO")
        self._save_preferences()

    def _on_profile_change(self):
        profile = self.selected_profile.get()
        if profile not in PERFILES:
            return
        info = PERFILES[profile]
        self.profile_desc_var.set(f"{info['icono']} {info['descripcion']}")
        if profile == "Personalizado":
            return
        config_path = os.path.join("configs", info["archivo"])
        if os.path.exists(config_path):
            self.config_file.set(config_path)
        else:
            self.config_file.set("")
        self.status_text.set(f"Perfil '{profile}' cargado")
        self._save_preferences()

    def _browse_downloads(self):
        d = filedialog.askdirectory(initialdir=self.downloads_dir.get())
        if d:
            self.downloads_dir.set(d)
            self.status_text.set(f"Origen: {d}")

    def _browse_organized(self):
        d = filedialog.askdirectory(initialdir=self.organized_dir.get())
        if d:
            self.organized_dir.set(d)
            self.status_text.set(f"Destino: {d}")

    def _browse_config(self):
        f = filedialog.askopenfilename(filetypes=[("JSON", "*.json")], initialdir="configs")
        if f:
            self.config_file.set(f)
            self.selected_profile.set("Personalizado")
            self.profile_desc_var.set("Configuración personalizada")
            self.status_text.set(f"Config: {os.path.basename(f)}")

    def _run_organizer(self):
        organizer_path = Path(__file__).parent.parent / "organizer.py"
        cmd = [sys.executable, str(organizer_path)]
        if self.config_file.get():
            cmd.extend(["--config", self.config_file.get()])
        if self.simulate_mode.get():
            cmd.append("--simulate")
        if self.interactive_mode.get():
            cmd.append("--interactive")

        self.output_text.delete(1.0, tk.END)
        self.status_text.set("Ejecutando...")
        self.run_button.config(state=tk.DISABLED)
        self.progress_var.set(0)

        if self.interactive_mode.get():
            self.interactive_info_label.config(
                text="⚠️ Modo interactivo activo. Se abrirán ventanas para tomar decisiones.",
                bootstyle="warning"
            )
            self.interactive_info_label.pack(fill=tk.X, pady=5)
        else:
            self.interactive_info_label.pack_forget()

        if self.current_process and self.process_alive:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=1)
            except:
                pass

        thread = threading.Thread(target=self._run_subprocess, args=(cmd,))
        thread.daemon = True
        thread.start()

    def _run_subprocess(self, cmd):
        try:
            use_stdin = self.interactive_mode.get()
            stdin_arg = subprocess.PIPE if use_stdin else None

            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=stdin_arg,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self.process_alive = True

            prompt_lines = []
            capturing = False
            lines = 0

            for line in self.current_process.stdout:
                self.root.after(0, self._append_output, line)

                if "¿Qué deseas hacer" in line or "Qué deseas hacer" in line:
                    capturing = True
                    prompt_lines = [line]
                    continue

                if capturing:
                    prompt_lines.append(line)
                    if "Tu selección (número):" in line:
                        full_prompt = "".join(prompt_lines)
                        print(f"🎯 Mostrando diálogo interactivo")
                        self.root.after(0, self._show_interactive_dialog, full_prompt)
                        capturing = False
                        prompt_lines = []
                        continue

                if "¿Recordar esta decisión" in line or "Recordar esta decisión" in line:
                    print(f"💾 Mostrando diálogo de recordar")
                    self.root.after(0, self._show_remember_dialog, line)

                lines += 1
                progress = min(lines / 50 * 100, 90)
                self.root.after(0, lambda p=progress: self.progress_var.set(p))

            self.current_process.wait()
            self.process_alive = False
            if self.current_process.returncode == 0:
                self.root.after(0, lambda: self.progress_var.set(100))
                self.root.after(0, lambda: self.status_text.set("Completado exitosamente"))
                self.root.after(500, self._update_undo_redo_panel)
            else:
                self.root.after(0, lambda: self.status_text.set("Error en la ejecución"))
        except Exception as e:
            self.root.after(0, lambda: self._append_output(f"Error: {str(e)}\n"))
            self.root.after(0, lambda: self.status_text.set("Error interno"))
        finally:
            self.root.after(0, lambda: self.run_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.interactive_info_label.pack_forget())
            self.process_alive = False

    def _show_interactive_dialog(self, prompt_text):
        print(f"📋 Prompt recibido:\n{prompt_text}")
        options = []
        for line in prompt_text.splitlines():
            match = re.match(r'\s*\[(\d+)\]\s*(.+)', line)
            if match:
                num = int(match.group(1))
                desc = match.group(2).strip()
                options.append((num, desc))
        
        print(f"✅ Opciones parseadas: {options}")
        
        if options and self.current_process and self.current_process.stdin:
            dialog = InteractiveDialog(self.root, prompt_text, options, self.current_process.stdin,
                                       title="Selecciona una categoría")
            print("✅ Diálogo mostrado")
        else:
            print(f"❌ No se puede mostrar diálogo:")
            print(f"   - Opciones: {len(options)}")
            print(f"   - Proceso: {self.current_process is not None}")
            print(f"   - Stdin: {self.current_process.stdin if self.current_process else None}")

    def _show_remember_dialog(self, prompt_text):
        if self.current_process and self.current_process.stdin:
            dialog = RememberDialog(self.root, prompt_text, self.current_process.stdin)

    def _append_output(self, text):
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)

    def _clear_output(self):
        self.output_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        self.status_text.set("Salida limpiada")

    def _load_stats(self):
        organizer_path = Path(__file__).parent.parent / "organizer.py"
        cmd = [sys.executable, str(organizer_path), "--stats"]
        self.stats_text.delete(1.0, tk.END)
        self.status_text.set("Cargando estadísticas...")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self.stats_text.insert(tk.END, result.stdout)
                self.status_text.set("Estadísticas cargadas")
            else:
                self.stats_text.insert(tk.END, result.stderr)
                self.status_text.set("No se pudieron cargar estadísticas")
        except Exception as e:
            self.stats_text.insert(tk.END, f"Error: {str(e)}\n")
            self.status_text.set("Error al cargar")


def main():
    prefs = {}
    try:
        if PREFS_FILE.exists():
            with open(PREFS_FILE, 'r', encoding='utf-8') as f:
                prefs = json.load(f)
    except:
        pass
    dark_mode = prefs.get("dark_mode", False)
    initial_theme = "darkly" if dark_mode else "cosmo"

    root = ttk.Window(themename=initial_theme)
    app = DownloadsOrganizerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()