#!/usr/bin/env python3
"""
Downloads Organizer Pro - GUI con estilo iOS
- Toggle switch tipo píldora con animación spring
- Segmented control en lugar de pestañas
- Header fijo que no se mueve al cambiar de página
- Tooltip genérico compatible con cualquier widget
- Entradas y botones redondeados
- Barra de progreso estilo iOS
- Lógica corregida: Simulado (izquierda) / Real (derecha)
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import sys
import os
import threading
import json
from pathlib import Path
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# ----------------------------------------------------------------------
# Tooltip flotante (genérico, compatible con cualquier widget)
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
        # Posición genérica: a la derecha del widget
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
# Toggle Switch estilo iOS (píldora + spring)
# CORREGIDO: Simulado = izquierda (posición 0), Real = derecha (posición 26)
# ----------------------------------------------------------------------
class ToggleSwitch(ttk.Frame):
    def __init__(self, master, variable, command=None, tooltip_text=None, **kwargs):
        super().__init__(master, **kwargs)
        self.variable = variable
        self.command = command
        self.width = 52
        self.height = 28
        # CORRECCIÓN: variable=True (Simulado) → posición 0 (izquierda)
        # variable=False (Real) → posición 26 (derecha)
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
        # CORRECCIÓN: variable=True → target_pos=0 (Simulado/izquierda)
        self.target_pos = 0 if self.variable.get() else 26
        self._animate_step(True)

    def _animate_step(self, bounce=False):
        diff = self.target_pos - self.anim_pos
        if abs(diff) < 0.5 and not bounce:
            self.anim_pos = self.target_pos
            self._update()
            return
        if bounce and abs(diff) < 2:
            # Efecto rebote: se pasa un poco y vuelve
            self.anim_pos = self.target_pos + (diff * 0.3)
            self._update()
            self.after(20, lambda: self._animate_step(False))
            return
        self.anim_pos += diff * self.anim_speed
        self._update()
        self.after(16, lambda: self._animate_step(True if abs(diff) > 2 else False))

    def _update(self):
        self.canvas.delete("all")
        off_color = "#34c759"  # Verde cuando está en Simulado (izquierda)
        on_color = "#e5e5ea"   # Gris cuando está en Real (derecha)
        # Invertimos la lógica: posición 0 = verde (Simulado), posición 26 = gris (Real)
        progress = 1 - (self.anim_pos / 26)
        current_color = self._interpolate_color(on_color, off_color, progress)

        # Fondo en forma de píldora
        r = self.height / 2
        self.canvas.create_arc(0, 0, self.height, self.height,
                               start=90, extent=180,
                               fill=current_color, outline=current_color)
        self.canvas.create_arc(self.width - self.height, 0, self.width, self.height,
                               start=270, extent=180,
                               fill=current_color, outline=current_color)
        self.canvas.create_rectangle(r, 0, self.width - r, self.height,
                                     fill=current_color, outline=current_color)

        # Círculo deslizador con sombra (color sólido, no transparencia)
        margin = 2
        circle_size = self.height - 2 * margin
        circle_x = margin + self.anim_pos
        circle_y = margin
        
        # Sombra sutil con color sólido
        self.canvas.create_oval(circle_x + 1, circle_y + 2,
                                circle_x + circle_size + 1, circle_y + circle_size + 2,
                                fill="#c0c0c0", outline="")
        self.canvas.create_oval(circle_x, circle_y,
                                circle_x + circle_size, circle_y + circle_size,
                                fill="white", outline="#d1d1d6", width=1)

        # Estilo de labels (el activo se pone en bold)
        if self.variable.get():
            # Simulado activo (izquierda)
            self.label_left.config(font=("Segoe UI", 9, "bold"))
            self.label_right.config(font=("Segoe UI", 9))
        else:
            # Real activo (derecha)
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


# ----------------------------------------------------------------------
# Toggle Switch con iconos para tema claro/oscuro
# ----------------------------------------------------------------------
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
        self.root.geometry("980x800")
        self.root.minsize(800, 650)

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

        # Configurar estilos iOS
        self._setup_ios_styles()

        # Crear interfaz en orden correcto para layout fijo
        self._create_header()
        self._create_segmented_control()
        self._create_pages()
        self._create_progress_and_status()

        # Cargar perfil y tema
        self._on_profile_change()
        self._on_simulate_change()
        self._apply_theme()

    # ------------------------------------------------------------------
    # Estilos iOS
    # ------------------------------------------------------------------
    def _setup_ios_styles(self):
        font_family = "Segoe UI"
        for f in ["SF Pro Text", "Helvetica Neue", "Inter"]:
            if f in tk.font.families():
                font_family = f
                break

        self.style.configure(".", font=(font_family, 10))
        self.style.configure("TLabel", font=(font_family, 10))
        self.style.configure("TLabelframe.Label", font=(font_family, 10, "bold"))

        # Entradas redondeadas
        self.style.configure("ios.TEntry", fieldbackground="white", bordercolor="#c6c6c8",
                             lightcolor="#c6c6c8", borderwidth=1, focusthickness=0, padding=8)
        self.style.map("ios.TEntry", fieldbackground=[("focus", "white")])

        # Botón secundario
        self.style.configure("ios.TButton", font=(font_family, 10, "bold"), padding=8,
                             borderwidth=0, focusthickness=0, relief="flat")
        self.style.map("ios.TButton",
                       background=[("active", "#e5e5ea"), ("pressed", "#d1d1d6")],
                       foreground=[("active", "#007aff")])

        # Botón primario (acento)
        self.style.configure("iosAccent.TButton", font=(font_family, 10, "bold"), padding=8,
                             borderwidth=0, foreground="white", background="#007aff")
        self.style.map("iosAccent.TButton",
                       background=[("active", "#0051d5"), ("pressed", "#0040a8")])

        # Progress bar delgada y redondeada
        self.style.configure("ios.Horizontal.TProgressbar", thickness=6, troughcolor="#e5e5ea",
                             background="#34c759", bordercolor="#34c759", lightcolor="#34c759",
                             darkcolor="#34c759")

    # ------------------------------------------------------------------
    # Cabecera (FIJA - siempre arriba)
    # ------------------------------------------------------------------
    def _create_header(self):
        header = ttk.Frame(self.root, bootstyle="primary", padding=20)
        header.pack(fill=tk.X, side=tk.TOP)
        ttk.Label(header, text="Downloads Organizer Pro", font=("Segoe UI", 22, "bold"),
                  bootstyle="inverse-primary").pack()
        ttk.Label(header, text="Organiza tus descargas automaticamente", font=("Segoe UI", 11),
                  bootstyle="inverse-primary").pack(pady=(5, 0))

    # ------------------------------------------------------------------
    # Segmented Control (FIJO - debajo del header)
    # ------------------------------------------------------------------
    def _create_segmented_control(self):
        seg_frame = ttk.Frame(self.root)
        seg_frame.pack(fill=tk.X, padx=15, pady=(10, 5), side=tk.TOP)

        self.btn_config = ttk.Button(seg_frame, text="Configuracion",
                                     command=lambda: self._show_page(0), style="ios.TButton")
        self.btn_run = ttk.Button(seg_frame, text="Ejecutar",
                                  command=lambda: self._show_page(1), style="ios.TButton")
        self.btn_stats = ttk.Button(seg_frame, text="Estadisticas",
                                    command=lambda: self._show_page(2), style="ios.TButton")

        for btn in (self.btn_config, self.btn_run, self.btn_stats):
            btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # Contenedor de páginas (este es el que cambia)
        self.pages_container = ttk.Frame(self.root)
        self.pages_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15, side=tk.TOP)

        # Crear las páginas dentro del contenedor
        self.pages = [ttk.Frame(self.pages_container),
                      ttk.Frame(self.pages_container),
                      ttk.Frame(self.pages_container)]

        # Inicialmente mostrar la primera página
        self.pages[0].pack(fill=tk.BOTH, expand=True)
        for page in self.pages[1:]:
            page.pack_forget()

    def _show_page(self, index):
        # Ocultar todas las páginas
        for page in self.pages:
            page.pack_forget()

        # Mostrar solo la página seleccionada
        self.pages[index].pack(fill=tk.BOTH, expand=True)

        # Actualizar estilos de botones
        buttons = [self.btn_config, self.btn_run, self.btn_stats]
        for i, btn in enumerate(buttons):
            if i == index:
                btn.config(style="iosAccent.TButton")
            else:
                btn.config(style="ios.TButton")

    # ------------------------------------------------------------------
    # Construcción de cada página
    # ------------------------------------------------------------------
    def _create_pages(self):
        self._create_config_page(self.pages[0])
        self._create_run_page(self.pages[1])
        self._create_stats_page(self.pages[2])

    def _create_config_page(self, parent):
        # Tema claro/oscuro
        theme_frame = ttk.Labelframe(parent, text="  Tema visual  ",
                                     bootstyle="secondary", padding=15)
        theme_frame.pack(fill=tk.X, pady=(0, 15))

        inner = ttk.Frame(theme_frame)
        inner.pack(fill=tk.X, pady=5)
        ttk.Label(inner, text="Modo Claro/Oscuro:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 20))

        self.theme_toggle = ToggleSwitchIcon(
            inner, variable=self.dark_mode, command=self._toggle_theme,
            icon_left="", text_left="Claro", icon_right="", text_right="Oscuro",
            tooltip_text="Alterna entre tema claro (Cosmo) y oscuro (Darkly)"
        )
        self.theme_toggle.pack(side=tk.LEFT, padx=10)
        ttk.Label(theme_frame, text="Cambia el aspecto completo de la aplicacion entre claro y oscuro.",
                  font=("Segoe UI", 9), bootstyle="secondary").pack(anchor=tk.W, pady=(5, 0))

        # Perfiles
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

        # Carpetas
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

        # Modo simulación
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

        # Opciones avanzadas
        extra_frame = ttk.Labelframe(parent, text="  Opciones avanzadas  ",
                                     bootstyle="success", padding=15)
        extra_frame.pack(fill=tk.X)

        ttk.Label(extra_frame, text="Archivo de configuracion (JSON):", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        cfg_f = ttk.Frame(extra_frame)
        cfg_f.pack(fill=tk.X)
        ttk.Entry(cfg_f, textvariable=self.config_file, style="ios.TEntry").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(cfg_f, text="Examinar...", command=self._browse_config, style="ios.TButton").pack(side=tk.RIGHT)

    def _create_run_page(self, parent):
        # Barra con dos botones: Ejecutar y Limpiar Salida
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 15))

        # Contenedor para centrar los botones
        center_frame = ttk.Frame(button_frame)
        center_frame.pack(anchor=tk.CENTER)

        self.run_button = ttk.Button(center_frame, text="Ejecutar Organizador", command=self._run_organizer,
                                     bootstyle="success", style="iosAccent.TButton", width=22)
        self.run_button.pack(side=tk.LEFT, padx=10)

        ttk.Button(center_frame, text="Limpiar Salida", command=self._clear_output,
                   bootstyle="warning", style="ios.TButton", width=22).pack(side=tk.LEFT, padx=10)

        # Área de salida del programa
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

    def _create_progress_and_status(self):
        progress_frame = ttk.Frame(self.root, padding=(15, 0, 15, 10))
        progress_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                            style="ios.Horizontal.TProgressbar", maximum=100)
        self.progress_bar.pack(fill=tk.X)

        status_bar = ttk.Label(self.root, textvariable=self.status_text,
                               bootstyle="secondary", padding=10, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # ------------------------------------------------------------------
    # Lógica
    # ------------------------------------------------------------------
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

    def _apply_theme(self):
        theme = "darkly" if self.dark_mode.get() else "cosmo"
        self.style.theme_use(theme)

    def _toggle_theme(self):
        self._apply_theme()
        self.status_text.set("Modo oscuro activado" if self.dark_mode.get() else "Modo claro activado")
        self._save_preferences()

    def _on_simulate_change(self):
        # CORREGIDO: Ahora muestra correctamente el estado
        if self.simulate_mode.get():
            self.status_text.set("Modo simulacion: ACTIVADO (Simulado)")
        else:
            self.status_text.set("Modo simulacion: DESACTIVADO (Real)")

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

        thread = threading.Thread(target=self._run_subprocess, args=(cmd,), daemon=True)
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


# ----------------------------------------------------------------------
# Punto de entrada
# ----------------------------------------------------------------------
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