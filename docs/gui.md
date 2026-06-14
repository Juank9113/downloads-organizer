# 🎨 Interfaz Gráfica (GUI)

## Descripción General

Downloads Organizer Pro incluye una **interfaz gráfica profesional** desarrollada con `ttkbootstrap` que combina el estilo moderno de iOS con la funcionalidad completa del organizador de archivos.

## 🚀 Características Principales

### 1. **Diseño iOS Moderno**

- **Toggle Switch estilo píldora** con animación spring
- **Segmented Control** para navegación entre pestañas
- **Fuente SF Pro / Helvetica Neue** (con fallback a Segoe UI)
- **Entradas y botones redondeados**
- **Barra de progreso delgada** estilo iOS (6px)
- **Paleta de colores iOS**: Verde (#34c759), Azul (#007aff), Gris (#e5e5ea)

### 2. **Navegación Intuitiva**

La interfaz utiliza un **Segmented Control** con tres secciones principales:

#### 📋 **Configuración**
- Selector de tema claro/oscuro (☀️/🌙)
- Selector de perfiles predefinidos
- Configuración de carpetas (origen y destino)
- Toggle de modo simulación/real
- Archivo de configuración personalizado

#### ▶️ **Ejecutar**
- Botón principal "Ejecutar Organizador"
- Área de salida en tiempo real (tema oscuro)
- Botón "Limpiar Salida"
- Barra de progreso animada

#### 📈 **Estadísticas**
- Visualización de estadísticas del sistema
- Información detallada de archivos organizados
- Botón "Cargar Estadísticas"

### 3. **Temas Claro y Oscuro**

**Toggle Switch Inteligente:**
- ☀️ **Modo Claro (Cosmo)**: Interfaz brillante y profesional
- 🌙 **Modo Oscuro (Darkly)**: Interfaz oscura para reducir fatiga visual
- **Cambio instantáneo** sin reiniciar la aplicación
- **Preferencia guardada** automáticamente

### 4. **Toggle Switch de Modo Simulación**

**Características del Toggle:**
- **Animación spring** con efecto rebote
- **Posición izquierda** = Simulado (verde #34c759)
- **Posición derecha** = Real (gris #e5e5ea)
- **Labels dinámicos**: "Simulado" y "Real" se resaltan según el estado
- **Círculo deslizador** con sombra sutil
- **Tooltip informativo** al pasar el mouse

## 📖 Uso de la GUI

### Primer Inicio

1. **Ejecutar la GUI:**
   ```bash
   python3 src/gui/organizer_gui.py
   ```

2. **Seleccionar tema visual** (opcional):
   - Usa el toggle ☀️/🌙 en la pestaña Configuración
   - El cambio es instantáneo

3. **Configurar carpetas:**
   - Haz clic en "Seleccionar..." para elegir la carpeta de origen
   - Selecciona la carpeta de destino

4. **Elegir modo de ejecución:**
   - **Simulado**: Previsualiza sin mover archivos (recomendado)
   - **Real**: Ejecuta la organización realmente

5. **Ejecutar:**
   - Ve a la pestaña "Ejecutar"
   - Haz clic en "🚀 Ejecutar Organizador"

### Perfiles Predefinidos

La GUI incluye **9 perfiles optimizados**:

| Perfil | Icono | Descripción |
|--------|-------|-------------|
| **General** | 📁 | Organización estándar para uso diario |
| **Desarrollador** | 💻 | Código, configuraciones y proyectos |
| **Estudiante** | 📚 | Apuntes, documentos y tareas |
| **Diseñador** | 🎨 | Fuentes, imágenes y vectores |
| **Profesional** | 💼 | Documentos laborales y facturas |
| **Limpieza** | 🧹 | Limpieza profunda de temporales |
| **Backup** | 💾 | Respaldos y archivos comprimidos |
| **Multimedia** | 🎬 | Videos, música e imágenes |
| **Personalizado** | ⚙️ | Tu propia configuración JSON |

## 🎯 Elementos de la Interfaz

### Header Fijo
- **Título**: "Downloads Organizer Pro"
- **Subtítulo**: "Organiza tus descargas automáticamente"
- **Posición**: Siempre visible en la parte superior

### Segmented Control
- **Botones**: Configuración | Ejecutar | Estadísticas
- **Estilo**: Botón activo en azul (#007aff), inactivos en gris
- **Comportamiento**: Cambio instantáneo entre páginas

### Barra de Progreso
- **Estilo**: Delgada (6px), verde (#34c759)
- **Animación**: Progreso suave durante la ejecución
- **Ubicación**: Parte inferior, antes del status bar

### Status Bar
- **Información**: Estado actual de la aplicación
- **Ejemplos**: 
  - "✅ Listo para organizar"
  - "🔄 Ejecutando..."
  - "Modo simulación: ACTIVADO"

## 🎨 Personalización Avanzada

### Cambiar Colores del Tema

Edita el archivo `src/gui/organizer_gui.py`:

```python
# Colores iOS personalizados
off_color = "#e5e5ea"  # Gris (modo desactivado)
on_color = "#34c759"   # Verde (modo activado)
accent_color = "#007aff"  # Azul (botones principales)
```

### Modificar Animación del Toggle

```python
# Velocidad de animación (0.0 - 1.0)
self.anim_speed = 0.18  # Más alto = más rápido

# Efecto rebote
if bounce and abs(diff) < 2:
    self.anim_pos = self.target_pos + (diff * 0.3)
```

### Agregar Nuevos Perfiles

Añade al diccionario `PERFILES`:

```python
PERFILES = {
    # ... perfiles existentes ...
    "Nuevo Perfil": {
        "archivo": "nuevo_config.json",
        "descripcion": "Descripción del perfil",
        "icono": "🎯"
    }
}
```

## 💡 Consejos de Uso

### ✅ Mejores Prácticas

1. **Siempre usa el modo simulación** la primera vez con una nueva configuración
2. **Verifica la salida** antes de ejecutar en modo real
3. **Guarda perfiles personalizados** para diferentes escenarios
4. **Usa el tema oscuro** en entornos con poca luz

### ⚠️ Consideraciones

- **Resolución mínima**: 800x650 píxeles
- **Requiere**: Python 3.8+, ttkbootstrap 1.20.3+
- **Fuentes**: SF Pro Text (macOS), Helvetica Neue (Linux), Segoe UI (Windows)

## 🐛 Solución de Problemas

### La GUI no se abre
```bash
# Verificar dependencias
pip3 install ttkbootstrap

# Ejecutar con detalles de error
python3 src/gui/organizer_gui.py 2>&1
```

### Los toggle switches no responden
- **Causa**: Problema con el event loop de Tkinter
- **Solución**: Reiniciar la aplicación

### Los colores no se ven correctamente
- **Causa**: Tema de ttkbootstrap no cargado
- **Solución**: Verificar que `theme="cosmo"` o `"darkly"` esté disponible

## 📚 Referencias Técnicas

### Librerías Utilizadas

- **ttkbootstrap**: Temas modernos para Tkinter
- **tkinter**: GUI estándar de Python
- **subprocess**: Ejecución de comandos en segundo plano
- **threading**: Ejecución asíncrona para no bloquear la GUI

### Arquitectura

```
DownloadsOrganizerGUI
├── Header (fijo arriba)
├── Segmented Control (fijo)
├── Pages Container (dinámico)
│   ├── Configuración
│   ├── Ejecutar
│   └── Estadísticas
├── Progress Bar (fijo abajo)
└── Status Bar (fijo abajo)
```

## 🔗 Enlaces Relacionados

- [Instalación](installation.md) - Cómo instalar el proyecto
- [Uso](usage.md) - Guía de uso de la CLI
- [Personalización](customization.md) - Configuración avanzada
