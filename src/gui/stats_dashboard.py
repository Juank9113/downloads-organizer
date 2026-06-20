#!/usr/bin/env python3
"""
stats_dashboard.py - Dashboard de Estadísticas Profesional
Downloads Organizer Pro
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import sys
from pathlib import Path
from datetime import datetime

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class StatsDashboard(tk.Toplevel):
    """Dashboard profesional de estadísticas."""

    COLORS_LIGHT = ['#007AFF', '#34C759', '#FF9500', '#FF3B30', '#AF52DE', '#5856D6', '#FF2D55', '#5AC8FA']
    COLORS_DARK = ['#0A84FF', '#30D158', '#FF9F0A', '#FF453A', '#BF5AF2', '#5E5CE6', '#FF375F', '#64D2FF']
    
    BG_LIGHT = '#F5F5F7'
    BG_DARK = '#1C1C1E'
    CARD_LIGHT = '#FFFFFF'
    CARD_DARK = '#2C2C2E'
    TEXT_LIGHT = '#1D1D1F'
    TEXT_DARK = '#F5F5F7'
    ACCENT_LIGHT = '#007AFF'
    ACCENT_DARK = '#0A84FF'

    def __init__(self, parent, db_manager=None, is_dark_mode=False):
        super().__init__(parent)
        self.parent = parent
        self.is_dark_mode = is_dark_mode
        self.current_days = None
        self.loading = True
        
        self.bg_color = self.BG_DARK if is_dark_mode else self.BG_LIGHT
        self.card_color = self.CARD_DARK if is_dark_mode else self.CARD_LIGHT
        self.text_color = self.TEXT_DARK if is_dark_mode else self.TEXT_LIGHT
        self.accent_color = self.ACCENT_DARK if is_dark_mode else self.ACCENT_LIGHT
        
        print(" Inicializando StatsManager...")
        try:
            from stats_manager import StatsManager
            self.stats = StatsManager(db_manager)
            print("✅ StatsManager OK")
        except Exception as e:
            print(f"❌ Error StatsManager: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"No se pudo cargar estadísticas:\n{e}")
            self.destroy()
            return
        
        self.title("📊 Downloads Organizer Pro - Dashboard")
        self.geometry("1400x900")
        self.minsize(1200, 800)
        self.configure(bg=self.bg_color)
        
        print("🎨 Creando interfaz...")
        try:
            self._create_header()
            self._create_toolbar()
            self._create_kpi_section()
            self._create_loading_section()
            
            print("✅ Interfaz creada")
            self.update()
            
            self.after(300, self._load_charts_async)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Error al crear interfaz:\n{e}")

    def _create_header(self):
        """Header con título."""
        header_frame = tk.Frame(self, bg=self.accent_color, height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame, 
            text="📊 Dashboard de Estadísticas",
            bg=self.accent_color,
            fg="white",
            font=("Segoe UI", 24, "bold")
        ).pack(pady=15)

    def _create_toolbar(self):
        """Barra de herramientas."""
        toolbar = tk.Frame(self, bg=self.bg_color, height=60)
        toolbar.pack(fill=tk.X, padx=20, pady=(15, 10))
        toolbar.pack_propagate(False)
        
        tk.Label(
            toolbar,
            text="📅 Período:",
            bg=self.bg_color,
            fg=self.text_color,
            font=("Segoe UI", 11, "bold")
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.range_var = tk.StringVar(value="Últimos 30 días")
        ranges = ["Últimos 7 días", "Últimos 30 días", "Últimos 90 días", "Todo el historial"]
        self.range_map = {
            "Últimos 7 días": 7,
            "Últimos 30 días": 30,
            "Últimos 90 días": 90,
            "Todo el historial": None
        }
        
        range_menu = tk.OptionMenu(
            toolbar,
            self.range_var,
            *ranges,
            command=lambda x: self._on_range_change()
        )
        range_menu.config(
            bg=self.card_color,
            fg=self.text_color,
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            bd=0
        )
        range_menu.pack(side=tk.LEFT, padx=10)
        
        btn_frame = tk.Frame(toolbar, bg=self.bg_color)
        btn_frame.pack(side=tk.RIGHT)
        
        self._create_button(btn_frame, "🔄 Actualizar", self.refresh_charts, primary=True)
        self._create_button(btn_frame, " Exportar", self._export_png)
        self._create_button(btn_frame, "✕ Cerrar", self._safe_close)

    def _create_button(self, parent, text, command, primary=False):
        """Crea botón moderno."""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=self.accent_color if primary else self.card_color,
            fg="white" if primary else self.text_color,
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2"
        )
        btn.pack(side=tk.LEFT, padx=5)

    def _create_kpi_section(self):
        """Sección de KPIs."""
        kpi_container = tk.Frame(self, bg=self.bg_color)
        kpi_container.pack(fill=tk.X, padx=20, pady=10)
        
        self.kpi_cards = {}
        kpis = [
            ('total', '📦 Total Acciones', '0'),
            ('moves', '➡️ Movimientos', '0'),
            ('deletes', '️ Eliminaciones', '0'),
            ('size', '💾 Espacio', '0 MB'),
            ('sessions', '📋 Sesiones', '0')
        ]
        
        for key, title, default in kpis:
            card_frame = tk.Frame(kpi_container, bg=self.card_color)
            card_frame.configure(highlightbackground="#3A3A3C" if self.is_dark_mode else "#E5E5EA", 
                                highlightthickness=1)
            card_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
            
            tk.Label(
                card_frame,
                text=title,
                bg=self.card_color,
                fg=self.text_color,
                font=("Segoe UI", 10)
            ).pack(fill=tk.X, padx=15, pady=(15, 5))
            
            value_label = tk.Label(
                card_frame,
                text=default,
                bg=self.card_color,
                fg=self.accent_color,
                font=("Segoe UI", 28, "bold")
            )
            value_label.pack(fill=tk.X, padx=15, pady=(0, 15))
            
            self.kpi_cards[key] = value_label

    def _create_loading_section(self):
        """Sección de carga."""
        self.loading_frame = tk.Frame(self, bg=self.bg_color)
        self.loading_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(
            self.loading_frame,
            text=" Cargando dashboard...",
            bg=self.bg_color,
            fg=self.text_color,
            font=("Segoe UI", 16)
        ).pack(expand=True)

    def _load_charts_async(self):
        """Carga gráficos asíncronamente."""
        try:
            print("📊 Cargando gráficos...")
            
            if hasattr(self, 'loading_frame'):
                self.loading_frame.destroy()
            
            self.charts_container = tk.Frame(self, bg=self.bg_color)
            self.charts_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            self.charts_frame = tk.Frame(self.charts_container, bg=self.bg_color)
            self.charts_frame.pack(fill=tk.BOTH, expand=True)
            
            for i in range(2):
                self.charts_frame.grid_rowconfigure(i, weight=1)
                self.charts_frame.grid_columnconfigure(i, weight=1)
            
            self.figures = {}
            self.canvases = {}
            self.axes = {}
            
            # Crear los 4 gráficos con keys consistentes
            self._create_chart_card('category', '📊 Archivos por Categoría', 0, 0)
            self._create_chart_card('space', '💾 Espacio por Categoría', 0, 1)
            self._create_chart_card('timeline', '📈 Actividad Temporal', 1, 0)
            self._create_chart_card('extensions', '🏆 Top Extensiones', 1, 1)
            
            print(f"✅ Gráficos creados: {list(self.axes.keys())}")
            self.refresh_charts()
            self.loading = False
            print("✅ Dashboard completo")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Error al cargar gráficos:\n{e}")

    def _create_chart_card(self, chart_id, title, row, col):
        """Crea tarjeta de gráfico."""
        card = tk.Frame(self.charts_frame, bg=self.card_color)
        card.grid(row=row, column=col, sticky='nsew', padx=10, pady=10)
        card.configure(highlightbackground="#3A3A3C" if self.is_dark_mode else "#E5E5EA", 
                      highlightthickness=1)
        
        tk.Label(
            card,
            text=title,
            bg=self.card_color,
            fg=self.text_color,
            font=("Segoe UI", 12, "bold"),
            anchor=tk.W
        ).pack(fill=tk.X, padx=15, pady=(15, 10))
        
        chart_frame = tk.Frame(card, bg=self.card_color)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 15))
        
        fig = Figure(figsize=(6, 4), dpi=100, facecolor=self.card_color)
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.card_color)
        
        text_color = self.text_color
        ax.tick_params(colors=text_color, labelsize=9)
        
        for spine in ax.spines.values():
            spine.set_color("#8E8E93")
            spine.set_linewidth(0.5)
        
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Guardar referencias con keys consistentes
        self.figures[chart_id] = fig
        self.canvases[chart_id] = canvas
        self.axes[chart_id] = ax
        
        print(f"✅ Gráfico creado: {chart_id}")

    def _on_range_change(self):
        selected = self.range_var.get()
        self.current_days = self.range_map.get(selected)
        self.refresh_charts()

    def refresh_charts(self):
        if self.loading:
            return
        
        try:
            print("🔄 Refrescando gráficos...")
            
            totals = self.stats.get_total_stats(days=self.current_days)
            self.kpi_cards['total'].config(text=f"{totals['total_actions']:,}")
            self.kpi_cards['moves'].config(text=f"{totals['total_moves']:,}")
            self.kpi_cards['deletes'].config(text=f"{totals['total_deletes']:,}")
            size_mb = totals['total_size_bytes'] / (1024 * 1024)
            self.kpi_cards['size'].config(text=f"{size_mb:.2f} MB")
            self.kpi_cards['sessions'].config(text=f"{totals['sessions']:,}")
            
            self._draw_category_pie()
            self._draw_space_bar()
            self._draw_timeline()
            self._draw_extensions()
            
            print("✅ Gráficos refrescados")
            
        except Exception as e:
            print(f" Error refrescando: {e}")
            import traceback
            traceback.print_exc()

    def _draw_category_pie(self):
        try:
            print("🥧 Dibujando pie...")
            ax = self.axes.get('category')
            if ax is None:
                print(f"❌ No se encontró axis 'category'. Disponibles: {list(self.axes.keys())}")
                return
            
            ax.clear()
            data = self.stats.get_files_by_category(days=self.current_days)
            print(f"   Datos: {data}")
            
            if not data:
                ax.text(0.5, 0.5, 'Sin datos disponibles', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=12, color="#8E8E93")
                ax.axis('off')
            else:
                labels = [item[0] for item in data]
                values = [item[1] for item in data]
                colors = (self.COLORS_DARK if self.is_dark_mode else self.COLORS_LIGHT)[:len(labels)]
                
                wedges, texts, autotexts = ax.pie(
                    values, 
                    labels=labels, 
                    autopct='%1.1f%%',
                    colors=colors, 
                    startangle=90,
                    textprops={'fontsize': 9},
                    pctdistance=0.85
                )
                
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                
                ax.axis('equal')
                ax.set_title("Distribución", fontsize=10, pad=10)
            
            self.figures['category'].tight_layout()
            self.canvases['category'].draw()
            print("✅ Pie dibujado")
        except Exception as e:
            print(f"❌ Error en pie: {e}")
            import traceback
            traceback.print_exc()

    def _draw_space_bar(self):
        try:
            print("📊 Dibujando barras...")
            ax = self.axes.get('space')
            if ax is None:
                print(f"❌ No se encontró axis 'space'. Disponibles: {list(self.axes.keys())}")
                return
            
            ax.clear()
            data = self.stats.get_space_by_category(days=self.current_days)
            print(f"   Datos: {data}")
            
            if not data:
                ax.text(0.5, 0.5, 'Sin datos', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=12, color="#8E8E93")
                ax.axis('off')
            else:
                labels = [item[0] for item in data]
                values = [item[1] / (1024 * 1024) for item in data]
                colors = (self.COLORS_DARK if self.is_dark_mode else self.COLORS_LIGHT)[:len(labels)]
                
                bars = ax.bar(labels, values, color=colors)
                ax.tick_params(axis='x', rotation=45, labelsize=8)
                ax.set_ylabel('MB', fontsize=9)
                
                for bar, value in zip(bars, values):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{value:.2f}', ha='center', va='bottom', fontsize=7)
            
            self.figures['space'].tight_layout()
            self.canvases['space'].draw()
            print("✅ Barras dibujadas")
        except Exception as e:
            print(f"❌ Error en bar: {e}")
            import traceback
            traceback.print_exc()

    def _draw_timeline(self):
        try:
            print("📈 Dibujando timeline...")
            ax = self.axes.get('timeline')
            if ax is None:
                print(f"❌ No se encontró axis 'timeline'. Disponibles: {list(self.axes.keys())}")
                return
            
            ax.clear()
            days = self.current_days if self.current_days else 30
            data = self.stats.get_activity_over_time(days=days)
            print(f"   Datos: {len(data) if data else 0} puntos")
            
            if not data or all(d[1] == 0 for d in data):
                ax.text(0.5, 0.5, 'Sin actividad', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=12, color="#8E8E93")
                ax.axis('off')
            else:
                dates = [d[0][5:] for d in data]
                values = [d[1] for d in data]
                color = self.COLORS_DARK[0] if self.is_dark_mode else self.COLORS_LIGHT[0]
                
                ax.plot(dates, values, marker='o', color=color, linewidth=2, markersize=5)
                ax.fill_between(range(len(dates)), values, alpha=0.2, color=color)
                ax.tick_params(axis='x', rotation=45, labelsize=7)
                ax.set_ylabel('Acciones', fontsize=9)
                ax.grid(True, alpha=0.3)
            
            self.figures['timeline'].tight_layout()
            self.canvases['timeline'].draw()
            print("✅ Timeline dibujado")
        except Exception as e:
            print(f" Error en timeline: {e}")
            import traceback
            traceback.print_exc()

    def _draw_extensions(self):
        try:
            print("🏆 Dibujando extensiones...")
            ax = self.axes.get('extensions')
            if ax is None:
                print(f"❌ No se encontró axis 'extensions'. Disponibles: {list(self.axes.keys())}")
                return
            
            ax.clear()
            data = self.stats.get_top_extensions(limit=10, days=self.current_days)
            print(f"   Datos: {len(data) if data else 0} extensiones")
            
            if not data:
                ax.text(0.5, 0.5, 'Sin datos', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=12, color="#8E8E93")
                ax.axis('off')
            else:
                data = list(reversed(data))
                labels = [item[0] for item in data]
                values = [item[1] for item in data]
                colors = (self.COLORS_DARK if self.is_dark_mode else self.COLORS_LIGHT)[:len(labels)]
                
                bars = ax.barh(labels, values, color=colors, height=0.6)
                ax.set_xlabel('Cantidad', fontsize=9)
                
                for bar, value in zip(bars, values):
                    width = bar.get_width()
                    ax.text(width, bar.get_y() + bar.get_height()/2.,
                           f' {value}', ha='left', va='center', fontsize=8)
            
            self.figures['extensions'].tight_layout()
            self.canvases['extensions'].draw()
            print("✅ Extensiones dibujadas")
        except Exception as e:
            print(f"❌ Error en extensions: {e}")
            import traceback
            traceback.print_exc()

    def _export_png(self):
        if self.loading:
            messagebox.showwarning("Cargando", "Espere a que carguen los gráficos.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png")],
            initialfile=f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        
        if not file_path:
            return
        
        try:
            fig_combined = Figure(figsize=(16, 12), dpi=150, facecolor='white')
            
            chart_ids = ['category', 'space', 'timeline', 'extensions']
            titles = ['Distribución por Categoría', 'Espacio por Categoría (MB)',
                      'Actividad Temporal', 'Top Extensiones']
            
            for i, (chart_id, title) in enumerate(zip(chart_ids, titles)):
                ax_dst = fig_combined.add_subplot(2, 2, i + 1)
                
                if chart_id == 'category':
                    data = self.stats.get_files_by_category(days=self.current_days)
                    if data:
                        labels = [d[0] for d in data]
                        values = [d[1] for d in data]
                        colors = self.COLORS_LIGHT[:len(labels)]
                        ax_dst.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, 
                                  startangle=90, wedgeprops={'edgecolor': 'white', 'linewidth': 2})
                        ax_dst.axis('equal')
                elif chart_id == 'space':
                    data = self.stats.get_space_by_category(days=self.current_days)
                    if data:
                        labels = [d[0] for d in data]
                        values = [d[1] / (1024*1024) for d in data]
                        colors = self.COLORS_LIGHT[:len(labels)]
                        ax_dst.bar(labels, values, color=colors)
                        ax_dst.tick_params(axis='x', rotation=45)
                        ax_dst.set_ylabel('MB')
                elif chart_id == 'timeline':
                    days = self.current_days if self.current_days else 30
                    data = self.stats.get_activity_over_time(days=days)
                    if data:
                        dates = [d[0][5:] for d in data]
                        values = [d[1] for d in data]
                        ax_dst.plot(dates, values, marker='o', color=self.COLORS_LIGHT[0], linewidth=2)
                        ax_dst.fill_between(range(len(dates)), values, alpha=0.2, color=self.COLORS_LIGHT[0])
                        ax_dst.tick_params(axis='x', rotation=45)
                        ax_dst.set_ylabel('Acciones')
                elif chart_id == 'extensions':
                    data = list(reversed(self.stats.get_top_extensions(limit=10, days=self.current_days)))
                    if data:
                        labels = [d[0] for d in data]
                        values = [d[1] for d in data]
                        colors = self.COLORS_LIGHT[:len(labels)]
                        ax_dst.barh(labels, values, color=colors)
                        ax_dst.set_xlabel('Cantidad')
                
                ax_dst.set_title(title, fontsize=14, fontweight='bold', pad=15)
                ax_dst.grid(True, alpha=0.3)
            
            fig_combined.tight_layout(pad=3.0)
            fig_combined.savefig(file_path, bbox_inches='tight', facecolor='white', edgecolor='none')
            plt.close(fig_combined)
            
            messagebox.showinfo("✅ Exportación Exitosa", 
                               f"Dashboard exportado a:\n\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar:\n{e}")

    def _safe_close(self):
        """Cierra dashboard."""
        print("🛑 Cerrando...")
        try:
            if hasattr(self, 'figures'):
                for fig in self.figures.values():
                    plt.close(fig)
            self.destroy()
            print("✅ Dashboard cerrado")
        except Exception as e:
            print(f"⚠️ Error: {e}")
            self.destroy()


def main():
    from db_manager import DatabaseManager
    root = tk.Tk()
    root.withdraw()
    db = DatabaseManager()
    dashboard = StatsDashboard(root, db_manager=db, is_dark_mode=False)
    dashboard.mainloop()


if __name__ == "__main__":
    main()