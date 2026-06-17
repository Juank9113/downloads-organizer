#!/usr/bin/env python3
"""
Downloads Organizer Pro - GUI con estilo iOS
- Toggle switch tipo píldora con animación spring
- Segmented control en lugar de pestañas
- Header fijo que no se mueve al cambiar de página
- Tooltip genérico compatible con cualquier widget
- Entradas y botones redondeados
- Barra de progreso estilo iOS
- Detector de duplicados con Treeview (estable, sin segfaults)
- Paleta de colores: Azul (claro) / Gris (oscuro)
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import sys
import os
import threading
import json
from pathlib import Path
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# Corregir ruta de importación para encontrar detector_duplicados.py en src/
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

try:
    from detector_duplicados import DetectorDuplicados, GrupoDuplicados
except ImportError:
    print("⚠️ No se pudo importar detector_duplicados.py. Asegúrate de que esté en src/")
    sys.exit(1)


# ----------------------------------------------------------------------
# Tooltip flotante
# ----------------------------------------------------------------------
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


# ----------------------------------------------------------------------
# Toggle Switch estilo iOS
# ----------------------------------------------------------------------
class ToggleSwitch(ttk.Frame):
    def __init__(self, master, variable, command=None, tooltip_text=None, **kwargs):
        super().__init__(master, **kwargs)
        self.variable = variable
        self.command = command
        self.width = 52
        self.height = 28
        self.anim_pos = 0 if variable.get() else 26
        self.target_pos = 0 if variable.get() else 26
        self.anim_speed = 0.18

        container = ttk.Frame(self)
        container.pack(fill=tk.X, pady=5)

        self.label_left = ttk.Label(container, text="Simulado", font=("Segoe UI", 9, "bold"))
        self.label_left.pack(side=tk.LEFT, padx=(0, 10))

        self.canvas = tk.Canvas(container, width=self.width, height=self.height,
                                highlightthickness=0, bg="white")
        self.canvas.pack(side=tk.LEFT, padx=5)

        self.label_right = ttk.Label(container, text="Real", font=("Segoe UI", 9))
        self.label_right.pack(side=tk.LEFT, padx=(10, 0))

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
        self.target_pos = 0 if self.variable.get() else 26
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
        off_color = "#34c759"
        on_color = "#e5e5ea"
        progress = 1 - (self.anim_pos / 26)
        current_color = self._interpolate_color(on_color, off_color, progress)

        r = self.height / 2
        self.canvas.create_arc(0, 0, self.height, self.height,
                               start=90, extent=180,
                               fill=current_color, outline=current_color)
        self.canvas.create_arc(self.width - self.height, 0, self.width, self.height,
                               start=270, extent=180,
                               fill=current_color, outline=current_color)
        self.canvas.create_rectangle(r, 0, self.width - r, self.height,
                                     fill=current_color, outline=current_color)

        margin = 2
        circle_size = self.height - 2 * margin
        circle_x = margin + self.anim_pos
        circle_y = margin
        
        self.canvas.create_oval(circle_x + 1, circle_y + 2,
                                circle_x + circle_size + 1, circle_y + circle_size + 2,
                                fill="#c0c0c0", outline="")
        self.canvas.create_oval(circle_x, circle_y,
                                circle_x + circle_size, circle_y + circle_size,
                                fill="white", outline="#d1d1d6", width=1)

        if self.variable.get():
            self.label_left.config(font=("Segoe UI", 9, "bold"))
            self.label_right.config(font=("Segoe UI", 9))
        else:
            self.label_left.config(font=("Segoe UI", 9))
            self.label_right.config(font=("Segoe UI", 9, "bold"))

    @staticmethod
    def _interpolate_color(color1, color2, factor):
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        r = int(r1 + (r2 - r1) * factor)
        g = int(g1 + (g2 - g1) * factor)
        b = int(b1 + (b2 - b1) * factor)
        return f"#{r:02x}{g:02x}{b:02x}"


class ToggleSwitchIcon(ToggleSwitch):
    def __init__(self, master, variable, command=None,
                 icon_left="", text_left="", icon_right="", text_right="",
                 tooltip_text=None):
        super().__init__(master, variable, command, tooltip_text)
        self.label_left.config(text=f"{icon_left} {text_left}" if icon_left else text_left)
        self.label_right.config(text=f"{icon_right} {text_right}" if icon_right else text_right)


# ----------------------------------------------------------------------
# Perfiles y preferencias
# ----------------------------------------------------------------------
PERFILES = {
    "General": {"archivo": "config_default.json", "descripcion": "Organización estándar", "icono": "📁"},
    "Desarrollador": {"archivo": "config_dev.json", "descripcion": "Código y proyectos", "icono": "💻"},
    "Estudiante": {"archivo": "estudiante.json", "descripcion": "Apuntes y tareas", "icono": ""},
    "Diseñador": {"archivo": "disenador.json", "descripcion": "Fuentes e imágenes", "icono": "🎨"},
    "Profesional": {"archivo": "profesional.json", "descripcion": "Documentos laborales", "icono": "💼"},
    "Limpieza": {"archivo": "config_limpieza.json", "descripcion": "Limpieza profunda", "icono": "🧹"},
    "Backup": {"archivo": "config_backup.json", "descripcion": "Respaldos", "icono": "💾"},
    "Multimedia": {"archivo": "config_multimedia.json", "descripcion": "Vídeos y música", "icono": "🎬"},
    "Personalizado": {"archivo": "", "descripcion": "Configuración propia", "icono": "️"}
}

PREFS_FILE = Path.home() / ".downloads_organizer_prefs.json"


# ----------------------------------------------------------------------
# Aplicación principal
# ----------------------------------------------------------------------
class DownloadsOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Downloads Organizer Pro")
        self.root.geometry("1100x850")
        self.root.minsize(850, 700)

        self.style = ttk.Style()
        self.preferences = self._load_preferences()

        # Variables
        self.downloads_dir = tk.StringVar(value=self.preferences.get("downloads_dir", str(Path.home() / "Downloads")))
        self.organized_dir = tk.StringVar(value=self.preferences.get("organized_dir", str(Path.home() / "Downloads_Organized")))
        self.simulate_mode = tk.BooleanVar(value=self.preferences.get("simulate_mode", True))
        self.config_file = tk.StringVar(value="")
        self.selected_profile = tk.StringVar(value=self.preferences.get("selected_profile", "General"))
        self.dark_mode = tk.BooleanVar(value=self.preferences.get("dark_mode", False))
        self.progress_var = tk.DoubleVar(value=0)
        self.status_text = tk.StringVar(value="Listo para organizar")

        # Variables para detector de duplicados
        self.dup_folder = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.dup_min_size = tk.IntVar(value=1024)
        self.dup_recursive = tk.BooleanVar(value=True)
        self.dup_simulate = tk.BooleanVar(value=True)
        
        # Estado del detector
        self.current_detector = None
        self.current_reporte = None
        self.dup_tree_items = {}  # {item_id: ruta_archivo}
        
        self._setup_ios_styles()
        self._create_header()
        self._create_segmented_control()
        self._create_pages()
        self._create_progress_and_status()

        self._on_profile_change()
        self._on_simulate_change()
        self._apply_theme()

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
                "selected_profile": self.selected_profile.get()
            }
            with open(PREFS_FILE, 'w', encoding='utf-8') as f:
                json.dump(prefs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando preferencias: {e}")

    def _setup_ios_styles(self):
        font_family = "Segoe UI"
        for f in ["SF Pro Text", "Helvetica Neue", "Inter"]:
            if f in tk.font.families():
                font_family = f
                break

        self.style.configure(".", font=(font_family, 10))
        self.style.configure("TLabel", font=(font_family, 10))
        self.style.configure("TLabelframe.Label", font=(font_family, 10, "bold"))

        # Colores según modo
        if self.dark_mode.get():
            # Modo oscuro: gris
            primary_color = "#6c757d"
            accent_color = "#adb5bd"
            bg_color = "#212529"
        else:
            # Modo claro: azul
            primary_color = "#0d6efd"
            accent_color = "#0dcaf0"
            bg_color = "#ffffff"

        self.style.configure("ios.TEntry", fieldbackground=bg_color, bordercolor="#c6c6c8",
                             lightcolor="#c6c6c8", borderwidth=1, focusthickness=0, padding=8)
        self.style.map("ios.TEntry", fieldbackground=[("focus", bg_color)])

        self.style.configure("ios.TButton", font=(font_family, 10, "bold"), padding=8,
                             borderwidth=0, focusthickness=0, relief="flat",
                             background=primary_color, foreground="white")
        self.style.map("ios.TButton",
                       background=[("active", accent_color), ("pressed", primary_color)],
                       foreground=[("active", "white"), ("pressed", "white")])

        self.style.configure("iosAccent.TButton", font=(font_family, 10, "bold"), padding=8,
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
        ttk.Label(header, text="Organiza tus descargas automaticamente", font=("Segoe UI", 11),
                  bootstyle="inverse-primary").pack(pady=(5, 0))

    def _create_segmented_control(self):
        seg_frame = ttk.Frame(self.root)
        seg_frame.pack(fill=tk.X, padx=15, pady=(10, 5), side=tk.TOP)

        self.btn_config = ttk.Button(seg_frame, text="Configuracion",
                                     command=lambda: self._show_page(0), style="ios.TButton")
        self.btn_run = ttk.Button(seg_frame, text="Ejecutar",
                                  command=lambda: self._show_page(1), style="ios.TButton")
        self.btn_stats = ttk.Button(seg_frame, text="Estadisticas",
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
        theme_frame = ttk.Labelframe(parent, text="  Tema visual  ",
                                     bootstyle="secondary", padding=15)
        theme_frame.pack(fill=tk.X, pady=(0, 15))

        inner = ttk.Frame(theme_frame)
        inner.pack(fill=tk.X, pady=5)
        ttk.Label(inner, text="Modo Claro/Oscuro:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 20))

        self.theme_toggle = ToggleSwitchIcon(
            inner, variable=self.dark_mode, command=self._toggle_theme,
            icon_left="☀️", text_left="Claro", icon_right="🌙", text_right="Oscuro",
            tooltip_text="Alterna entre tema claro (Cosmo) y oscuro (Darkly)"
        )
        self.theme_toggle.pack(side=tk.LEFT, padx=10)
        ttk.Label(theme_frame, text="Cambia el aspecto completo de la aplicacion entre claro y oscuro.",
                  font=("Segoe UI", 9), bootstyle="secondary").pack(anchor=tk.W, pady=(5, 0))

        profile_frame = ttk.Labelframe(parent, text="  Selector de Perfiles  ",
                                       bootstyle="info", padding=15)
        profile_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(profile_frame, text="Selecciona un perfil:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))
        combo_prof = ttk.Frame(profile_frame)
        combo_prof.pack(fill=tk.X, pady=(0, 10))
        self.profile_combo = ttk.Combobox(combo_prof, textvariable=self.selected_profile,
                                          values=list(PERFILES.keys()), state="readonly",
                                          bootstyle="info", font=("Segoe UI", 10))
        self.profile_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.profile_combo.bind("<<ComboboxSelected>>", lambda e: self._on_profile_change())
        ttk.Button(combo_prof, text="Aplicar Perfil", command=self._on_profile_change,
                   bootstyle="info", style="ios.TButton").pack(side=tk.RIGHT)

        self.profile_desc_var = tk.StringVar()
        ttk.Label(profile_frame, textvariable=self.profile_desc_var,
                  font=("Segoe UI", 9), bootstyle="secondary").pack(anchor=tk.W)

        folders_frame = ttk.Labelframe(parent, text="  Carpetas  ",
                                       bootstyle="primary", padding=15)
        folders_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(folders_frame, text="Carpeta de origen:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        src_f = ttk.Frame(folders_frame)
        src_f.pack(fill=tk.X, pady=(0, 10))
        ttk.Entry(src_f, textvariable=self.downloads_dir, style="ios.TEntry").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(src_f, text="Seleccionar...", command=self._browse_downloads, style="ios.TButton").pack(side=tk.RIGHT)

        ttk.Label(folders_frame, text="Carpeta de destino:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        dst_f = ttk.Frame(folders_frame)
        dst_f.pack(fill=tk.X)
        ttk.Entry(dst_f, textvariable=self.organized_dir, style="ios.TEntry").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(dst_f, text="Seleccionar...", command=self._browse_organized, style="ios.TButton").pack(side=tk.RIGHT)

        sim_frame = ttk.Labelframe(parent, text="  Modo de Ejecucion  ",
                                   bootstyle="warning", padding=15)
        sim_frame.pack(fill=tk.X, pady=(0, 15))

        sim_container = ttk.Frame(sim_frame)
        sim_container.pack(fill=tk.X, pady=5)
        ttk.Label(sim_container, text="Modo simulacion:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 20))

        self.simulate_toggle = ToggleSwitch(
            sim_container, variable=self.simulate_mode, command=self._on_simulate_change,
            tooltip_text="Simulado: solo previsualiza los cambios.\nReal: mueve/renombra archivos realmente."
        )
        self.simulate_toggle.pack(side=tk.LEFT, padx=10)

        ttk.Label(sim_frame,
                  text="Simulado: previsualiza sin mover archivos.\nReal: ejecuta la organizacion real.",
                  wraplength=700, bootstyle="info", font=("Segoe UI", 9), justify=tk.LEFT).pack(anchor=tk.W, pady=(5, 0))

        extra_frame = ttk.Labelframe(parent, text="  Opciones avanzadas  ",
                                     bootstyle="success", padding=15)
        extra_frame.pack(fill=tk.X)

        ttk.Label(extra_frame, text="Archivo de configuracion (JSON):", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        cfg_f = ttk.Frame(extra_frame)
        cfg_f.pack(fill=tk.X)
        ttk.Entry(cfg_f, textvariable=self.config_file, style="ios.TEntry").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(cfg_f, text="Examinar...", command=self._browse_config, style="ios.TButton").pack(side=tk.RIGHT)

    def _create_run_page(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 15))

        center_frame = ttk.Frame(button_frame)
        center_frame.pack(anchor=tk.CENTER)

        self.run_button = ttk.Button(center_frame, text="Ejecutar Organizador", command=self._run_organizer,
                                     bootstyle="success", style="iosAccent.TButton", width=22)
        self.run_button.pack(side=tk.LEFT, padx=10)

        ttk.Button(center_frame, text="Limpiar Salida", command=self._clear_output,
                   bootstyle="warning", style="ios.TButton", width=22).pack(side=tk.LEFT, padx=10)

        out_group = ttk.Labelframe(parent, text="  Salida del programa  ",
                                   bootstyle="dark", padding=10)
        out_group.pack(fill=tk.BOTH, expand=True)

        self.output_text = tk.Text(out_group, wrap=tk.WORD, font=("Consolas", 10),
                                   bg="#1e1e1e", fg="#d4d4d4", insertbackground="#ffffff",
                                   relief=tk.FLAT, bd=0)
        scroll = ttk.Scrollbar(out_group, orient=tk.VERTICAL, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=scroll.set)
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_stats_page(self, parent):
        ttk.Button(parent, text="Cargar Estadisticas", command=self._load_stats,
                   bootstyle="primary", style="iosAccent.TButton", width=25).pack(pady=(0, 15))

        stats_group = ttk.Labelframe(parent, text="  Informacion  ",
                                     bootstyle="dark", padding=10)
        stats_group.pack(fill=tk.BOTH, expand=True)

        self.stats_text = tk.Text(stats_group, wrap=tk.WORD, font=("Consolas", 10),
                                  bg="#1e1e1e", fg="#d4d4d4", insertbackground="#ffffff",
                                  relief=tk.FLAT, bd=0)
        scroll = ttk.Scrollbar(stats_group, orient=tk.VERTICAL, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=scroll.set)
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_duplicates_page(self, parent):
        # Configuración del detector
        config_frame = ttk.Labelframe(parent, text="  Configuracion del Detector  ",
                                      bootstyle="info", padding=15)
        config_frame.pack(fill=tk.X, pady=(0, 15))

        # Carpeta a analizar
        ttk.Label(config_frame, text="Carpeta a analizar:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        folder_frame = ttk.Frame(config_frame)
        folder_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Entry(folder_frame, textvariable=self.dup_folder, style="ios.TEntry").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(folder_frame, text="Examinar...", command=self._browse_dup_folder, style="ios.TButton").pack(side=tk.RIGHT)

        # Opciones en grid
        options_frame = ttk.Frame(config_frame)
        options_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(options_frame, text="Tamaño mínimo (bytes):", font=("Segoe UI", 9)).grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(options_frame, from_=0, to=10485760, textvariable=self.dup_min_size, width=15).grid(row=0, column=1, sticky=tk.W, padx=10)

        ttk.Label(options_frame, text="Búsqueda recursiva:", font=("Segoe UI", 9)).grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Checkbutton(options_frame, variable=self.dup_recursive).grid(row=1, column=1, sticky=tk.W, padx=10)

        ttk.Label(options_frame, text="Modo simulación:", font=("Segoe UI", 9)).grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Checkbutton(options_frame, variable=self.dup_simulate).grid(row=2, column=1, sticky=tk.W, padx=10)

        # Botones de acción
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Button(button_frame, text="🔍 Analizar Duplicados", command=self._analyze_duplicates,
                   bootstyle="success", style="iosAccent.TButton", width=20).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="️ Eliminar Seleccionados", command=self._delete_selected_duplicates,
                   bootstyle="danger", style="iosAccent.TButton", width=20).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="🧹 Limpiar", command=self._clear_dup_results,
                   bootstyle="warning", style="ios.TButton", width=15).pack(side=tk.RIGHT, padx=5)

        # Frame de resumen
        self.dup_summary_frame = ttk.Frame(parent)
        self.dup_summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.dup_summary_label = ttk.Label(self.dup_summary_frame, text="", font=("Segoe UI", 10, "bold"))
        self.dup_summary_label.pack()

        # Área de resultados con Treeview (más estable que widgets dinámicos)
        results_frame = ttk.Labelframe(parent, text="  Duplicados encontrados (marca los que deseas eliminar)  ",
                                       bootstyle="dark", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview con checkboxes
        columns = ("select", "file", "size", "date", "group")
        self.dup_tree = ttk.Treeview(results_frame, columns=columns, show="headings", selectmode="extended")
        
        self.dup_tree.heading("select", text="Eliminar")
        self.dup_tree.heading("file", text="Archivo")
        self.dup_tree.heading("size", text="Tamaño")
        self.dup_tree.heading("date", text="Fecha")
        self.dup_tree.heading("group", text="Grupo")
        
        self.dup_tree.column("select", width=80, anchor=tk.CENTER)
        self.dup_tree.column("file", width=400, anchor=tk.W)
        self.dup_tree.column("size", width=100, anchor=tk.E)
        self.dup_tree.column("date", width=150, anchor=tk.CENTER)
        self.dup_tree.column("group", width=80, anchor=tk.CENTER)
        
        scroll_y = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.dup_tree.yview)
        scroll_x = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.dup_tree.xview)
        self.dup_tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        self.dup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind para toggle de selección con doble clic
        self.dup_tree.bind("<Double-1>", self._on_tree_double_click)
        
        # Mensaje inicial
        self.dup_placeholder = ttk.Label(results_frame, 
                                         text="Haz clic en 'Analizar Duplicados' para comenzar",
                                         font=("Segoe UI", 11), bootstyle="secondary")
        self.dup_placeholder.pack(pady=50)

    def _on_tree_double_click(self, event):
        """Toggle selección al hacer doble clic en una fila."""
        item = self.dup_tree.identify_row(event.y)
        if item:
            current_values = self.dup_tree.item(item, "values")
            if current_values:
                new_select = "✓" if current_values[0] == "" else ""
                self.dup_tree.item(item, values=(new_select, current_values[1], current_values[2], current_values[3], current_values[4]))

    def _browse_dup_folder(self):
        folder = filedialog.askdirectory(initialdir=self.dup_folder.get())
        if folder:
            self.dup_folder.set(folder)

    def _analyze_duplicates(self):
        folder = Path(self.dup_folder.get())
        
        if not folder.exists():
            messagebox.showerror("Error", f"La carpeta '{folder}' no existe")
            return
        
        self.status_text.set("Analizando duplicados...")
        
        # Limpiar resultados anteriores
        for item in self.dup_tree.get_children():
            self.dup_tree.delete(item)
        self.dup_tree_items = {}
        self.current_detector = None
        self.current_reporte = None
        
        # Ocultar placeholder
        if hasattr(self, 'dup_placeholder'):
            self.dup_placeholder.pack_forget()
        
        thread = threading.Thread(target=self._run_duplicate_analysis, args=(folder,))
        thread.start()

    def _run_duplicate_analysis(self, folder):
        try:
            detector = DetectorDuplicados(
                carpeta=folder,
                tamano_minimo=self.dup_min_size.get(),
                recursivo=self.dup_recursive.get(),
                modo_simulacion=self.dup_simulate.get()
            )
            
            reporte = detector.analizar()
            
            self.root.after(0, self._display_dup_results_treeview, reporte, detector)
            
        except Exception as e:
            self.root.after(0, lambda: self._show_analysis_error(str(e)))

    def _show_analysis_error(self, error_msg):
        messagebox.showerror("Error en el análisis", error_msg)
        self.status_text.set("Error en el análisis")

    def _display_dup_results_treeview(self, reporte, detector):
        """Muestra los resultados en el Treeview."""
        self.current_detector = detector
        self.current_reporte = reporte
        
        total_duplicados = reporte['duplicados_por_contenido']['archivos_duplicados']
        espacio_recuperable = reporte['duplicados_por_contenido']['espacio_recuperable_human']
        grupos = len(detector.grupos_contenido)
        
        # Actualizar resumen
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
        
        # Insertar grupos de duplicados por contenido
        group_num = 0
        for grupo in detector.grupos_contenido:
            group_num += 1
            original = grupo.archivo_original
            
            for archivo in grupo.archivos:
                es_original = (archivo == original)
                select_mark = "" if es_original else ""  # No marcar el original por defecto
                file_path = str(archivo.ruta)
                file_size = archivo._tamano_human()
                file_date = archivo.fecha_modificacion.strftime('%Y-%m-%d %H:%M')
                
                item_id = self.dup_tree.insert("", tk.END, values=(
                    select_mark,
                    file_path,
                    file_size,
                    file_date,
                    f"G{group_num}"
                ))
                
                # Marcar visualmente el archivo original
                if es_original:
                    self.dup_tree.item(item_id, tags=('original',))
                
                self.dup_tree_items[item_id] = file_path
        
        # Configurar tags para colorear el original
        self.dup_tree.tag_configure('original', background='#d4edda')
        
        self.status_text.set(f"Análisis completado: {total_duplicados} duplicados encontrados")
        
        if total_duplicados > 0:
            messagebox.showinfo("Análisis completado", 
                              f"Se encontraron {total_duplicados} archivos duplicados.\n"
                              f"Espacio recuperable: {espacio_recuperable}\n\n"
                              f"Los archivos marcados con fondo verde son los más recientes.\n"
                              f"Haz doble clic en una fila para marcarla para eliminación.")

    def _get_selected_files(self):
        """Obtiene todos los archivos marcados para eliminar."""
        selected = []
        for item_id in self.dup_tree.get_children():
            values = self.dup_tree.item(item_id, "values")
            if values and values[0] == "✓":
                if item_id in self.dup_tree_items:
                    selected.append(self.dup_tree_items[item_id])
        return selected

    def _delete_selected_duplicates(self):
        """Elimina los archivos seleccionados por el usuario."""
        selected_files = self._get_selected_files()
        
        if not selected_files:
            messagebox.showwarning("Sin selección", 
                                   "No has seleccionado ningún archivo para eliminar.\n\n"
                                   "Haz doble clic en las filas que deseas eliminar para marcarlas con ✓.")
            return
        
        # Confirmación
        modo = "SIMULACIÓN" if self.dup_simulate.get() else "REAL"
        mensaje = (f"Se eliminarán {len(selected_files)} archivo(s) en modo {modo}:\n\n"
                   f"{chr(10).join(['  • ' + f for f in selected_files[:10]])}")
        
        if len(selected_files) > 10:
            mensaje += f"\n  ... y {len(selected_files) - 10} más"
        
        if not messagebox.askyesno("Confirmar eliminación", mensaje):
            return
        
        self.status_text.set(f"Eliminando {len(selected_files)} archivos...")
        
        thread = threading.Thread(target=self._run_delete_selected, args=(selected_files,))
        thread.start()

    def _run_delete_selected(self, selected_files):
        """Ejecuta la eliminación de los archivos seleccionados."""
        resultados = {
            'eliminados': [],
            'errores': [],
            'espacio_liberado': 0
        }
        
        modo_simulacion = self.dup_simulate.get()
        
        for ruta_str in selected_files:
            ruta = Path(ruta_str)
            try:
                if modo_simulacion:
                    print(f"   [SIMULACIÓN] Se eliminaría: {ruta}")
                    resultados['eliminados'].append(str(ruta))
                    try:
                        resultados['espacio_liberado'] += ruta.stat().st_size
                    except:
                        pass
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
        
        # Mostrar resultados
        espacio_human = GrupoDuplicados._tamano_human(resultados['espacio_liberado'])
        modo_str = "SIMULACIÓN" if modo_simulacion else "REAL"
        
        mensaje = (f"Operación completada en modo {modo_str}\n\n"
                   f"✅ Archivos procesados: {len(resultados['eliminados'])}\n"
                   f"💾 Espacio liberado: {espacio_human}")
        
        if resultados['errores']:
            mensaje += f"\n\n️ Errores: {len(resultados['errores'])}"
        
        self.root.after(0, lambda: messagebox.showinfo("Resultado", mensaje))
        self.root.after(0, lambda: self.status_text.set(f"Eliminación completada: {len(resultados['eliminados'])} archivos"))
        
        # Refrescar la vista
        if not modo_simulacion:
            self.root.after(1000, lambda: self._refresh_after_deletion())

    def _refresh_after_deletion(self):
        """Refresca la vista después de una eliminación real."""
        for item in self.dup_tree.get_children():
            self.dup_tree.delete(item)
        self.dup_tree_items = {}
        self.current_detector = None
        self.current_reporte = None
        
        self.dup_summary_label.config(text="")
        if hasattr(self, 'dup_placeholder'):
            self.dup_placeholder.pack(pady=50)

    def _clear_dup_results(self):
        """Limpia todos los resultados."""
        for item in self.dup_tree.get_children():
            self.dup_tree.delete(item)
        self.dup_tree_items = {}
        self.current_detector = None
        self.current_reporte = None
        
        self.dup_summary_label.config(text="")
        if hasattr(self, 'dup_placeholder'):
            self.dup_placeholder.pack(pady=50)
        
        self.status_text.set("Resultados limpiados")

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
        # Reconfigurar estilos con nuevos colores
        self._setup_ios_styles()

    def _toggle_theme(self):
        self._apply_theme()
        self.status_text.set("Modo oscuro activado" if self.dark_mode.get() else "Modo claro activado")
        self._save_preferences()

    def _on_simulate_change(self):
        self.status_text.set("Modo simulacion: ACTIVADO" if self.simulate_mode.get() else "Modo simulacion: DESACTIVADO")

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
            self.profile_desc_var.set("Configuracion personalizada")
            self.status_text.set(f"Config: {os.path.basename(f)}")

    def _run_organizer(self):
        cmd = [sys.executable, "src/organizer.py"]
        if self.config_file.get():
            cmd.extend(["--config", self.config_file.get()])
        if self.simulate_mode.get():
            cmd.append("--simulate")

        self.output_text.delete(1.0, tk.END)
        self.status_text.set("Ejecutando...")
        self.run_button.config(state=tk.DISABLED)
        self.progress_var.set(0)

        thread = threading.Thread(target=self._run_subprocess, args=(cmd,))
        thread.start()

    def _run_subprocess(self, cmd):
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, bufsize=1)
            lines = 0
            for line in process.stdout:
                self.root.after(0, self._append_output, line)
                lines += 1
                progress = min(lines / 50 * 100, 90)
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
            process.wait()
            if process.returncode == 0:
                self.root.after(0, lambda: self.progress_var.set(100))
                self.root.after(0, lambda: self.status_text.set("Completado exitosamente"))
            else:
                self.root.after(0, lambda: self.status_text.set("Error en la ejecucion"))
        except Exception as e:
            self.root.after(0, lambda: self._append_output(f"Error: {str(e)}\n"))
            self.root.after(0, lambda: self.status_text.set("Error interno"))
        finally:
            self.root.after(0, lambda: self.run_button.config(state=tk.NORMAL))

    def _append_output(self, text):
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)

    def _clear_output(self):
        self.output_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        self.status_text.set("Salida limpiada")

    def _load_stats(self):
        cmd = [sys.executable, "src/organizer.py", "--stats"]
        self.stats_text.delete(1.0, tk.END)
        self.status_text.set("Cargando estadisticas...")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self.stats_text.insert(tk.END, result.stdout)
                self.status_text.set("Estadisticas cargadas")
            else:
                self.stats_text.insert(tk.END, result.stderr)
                self.status_text.set("No se pudieron cargar estadisticas")
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