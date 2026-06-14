
# 🧪 Modo Simulación

## ¿Qué es el Modo Simulación?

El **Modo Simulación** es una característica de seguridad que te permite **previsualizar** qué archivos se moverían y a qué carpetas irían, **sin realizar ningún cambio real** en tu sistema de archivos.

## 🎯 ¿Por qué Usarlo?

### ✅ Ventajas del Modo Simulación

1. **Sin Riesgos**: No mueve, renombra ni elimina archivos reales
2. **Previsualización**: Ves exactamente qué pasaría antes de ejecutar
3. **Validación**: Verifica que tu configuración es correcta
4. **Aprendizaje**: Entiende cómo funciona el organizador sin compromiso
5. **Debugging**: Identifica problemas en tu configuración

### ⚠️ Modo Real vs Simulación

| Característica | Simulación | Real |
|----------------|------------|------|
| **Mueve archivos** | ❌ No | ✅ Sí |
| **Renombra** | ❌ No | ✅ Sí |
| **Elimina** | ❌ No | ✅ Sí |
| **Crea carpetas** | ❌ No | ✅ Sí |
| **Modifica sistema** | ❌ No | ✅ Sí |
| **Seguro** | ✅ 100% | ⚠️ Requiere precaución |

## 🎛️ Cómo Activar/Desactivar

### Desde la GUI

1. Abre la aplicación:
   ```bash
   python3 src/gui/organizer_gui.py
   ```

2. Ve a la pestaña **Configuración**

3. Busca la sección **"Modo de Ejecución"**

4. **Toggle Switch:**
   - **Posición izquierda** (verde) = **Simulado** ✅
   - **Posición derecha** (gris) = **Real** ⚠️

5. El estado se muestra en la barra inferior:
   - `"Modo simulación: ACTIVADO (Simulado)"`
   - `"Modo simulación: DESACTIVADO (Real)"`

### Desde la Línea de Comandos

**Modo Simulación (por defecto):**
```bash
python3 src/organizer.py --simulate
```

**Modo Real (sin flag):**
```bash
python3 src/organizer.py
```

**Con configuración personalizada:**
```bash
# Simulación
python3 src/organizer.py --config configs/config_dev.json --simulate

# Real
python3 src/organizer.py --config configs/config_dev.json
```

## 📋 Qué Muestra el Modo Simulación

### Información en Consola/GUI

Cuando ejecutas en modo simulación, verás:

```
═══════════════════════════════════════════════════════
MODO SIMULACIÓN - No se realizarán cambios reales
═══════════════════════════════════════════════════════

Archivos que se moverían:
─────────────────────────────────────────────────────

📄 ~/Downloads/proyecto.py
   → ~/Downloads_Organized/Codigo/proyecto.py

📄 ~/Downloads/foto_vacaciones.jpg
   → ~/Downloads_Organized/Imagenes/foto_vacaciones.jpg

📄 ~/Downloads/presentacion.pdf
   → ~/Downloads_Organized/Documentos/presentacion.pdf

📄 ~/Downloads/cancion.mp3
   → ~/Downloads_Organized/Audio/cancion.mp3

─────────────────────────────────────────────────────
Resumen:
  Total archivos: 4
  Imágenes: 1
  Documentos: 1
  Código: 1
  Audio: 1

✅ Simulación completada exitosamente
```

### Detalles que se Muestran

1. **Ruta original** del archivo
2. **Ruta destino** calculada
3. **Categoría** asignada
4. **Resumen estadístico** por categoría
5. **Advertencia clara** de que es simulación

## 🔍 Casos de Uso Recomendados

### ✅ Siempre Usa Simulación Cuando:

1. **Primera ejecución** del organizador
2. **Cambiaste la configuración** (nuevo archivo JSON)
3. **Añadiste nuevas categorías** o extensiones
4. **Modificaste las rutas** de origen/destino
5. **Probando un perfil nuevo** (Desarrollador, Estudiante, etc.)
6. **No estás seguro** de qué archivos se verán afectados

### ⚡ Puedes Usar Modo Real Cuando:

1. Ya **probaste en simulación** y todo se ve correcto
2. **Confías en tu configuración**
3. Tienes **backup** de tus archivos importantes
4. Es una **ejecución rutinaria** (ya has usado el organizador antes)

## 🛡️ Flujo de Trabajo Recomendado

### Paso 1: Configuración Inicial
```bash
# 1. Selecciona o crea tu configuración
python3 src/organizer.py --config configs/config_dev.json --simulate
```

### Paso 2: Revisa la Salida
- Verifica que las rutas destino sean correctas
- Confirma que las categorías son las esperadas
- Busca archivos que NO quieras mover

### Paso 3: Ajusta si es Necesario
```bash
# Edita tu configuración si algo no está bien
nano configs/config_dev.json
```

### Paso 4: Ejecuta Simulación de Nuevo
```bash
# Repite hasta que estés satisfecho
python3 src/organizer.py --config configs/config_dev.json --simulate
```

### Paso 5: Ejecución Real
```bash
# ¡Solo cuando estés 100% seguro!
python3 src/organizer.py --config configs/config_dev.json
```

## 🎓 Ejemplos Prácticos

### Ejemplo 1: Perfil Estudiante

**Configuración:**
```json
{
  "downloads_dir": "~/Downloads",
  "organized_dir": "~/Universidad",
  "categories": {
    "PDFs": [".pdf"],
    "Word": [".docx", ".doc"],
    "Presentaciones": [".pptx", ".ppt"]
  }
}
```

**Simulación:**
```bash
python3 src/organizer.py --config configs/estudiante.json --simulate
```

**Resultado esperado:**
```
📄 ~/Downloads/tesis_final.pdf
   → ~/Universidad/PDFs/tesis_final.pdf

📄 ~/Downloads/trabajo_grupo.docx
   → ~/Universidad/Word/trabajo_grupo.docx
```

### Ejemplo 2: Perfil Desarrollador

**Configuración:**
```json
{
  "categories": {
    "Python": [".py"],
    "JavaScript": [".js", ".jsx", ".ts", ".tsx"],
    "Configuraciones": [".json", ".yaml", ".yml", ".toml"]
  }
}
```

**Simulación:**
```bash
python3 src/organizer.py --config configs/dev.json --simulate
```

**Verifica:**
- ¿Los `.py` van a la carpeta Python?
- ¿Los `.json` van a Configuraciones?
- ¿Hay archivos que NO deberían moverse?

## ⚙️ Configuración Avanzada

### Excluir Archivos en Simulación

Puedes excluir extensiones específicas:

```json
{
  "exclude_extensions": [".tmp", ".crdownload", ".part"],
  "exclude_patterns": ["*.log", "*.bak"]
}
```

### Logs Detallados

Para ver más información en simulación:

```bash
# Modo verbose
python3 src/organizer.py --simulate --verbose

# O con nivel de debug
python3 src/organizer.py --simulate --log-level DEBUG
```

## 📊 Comparación Detallada

### Modo Simulación

```
✅ Ventajas:
  - 100% seguro
  - Sin cambios en el sistema
  - Perfecto para aprender
  - Ideal para testing

❌ Desventajas:
  - No organiza realmente
  - Requiere ejecución adicional en modo real
```

### Modo Real

```
✅ Ventajas:
  - Organiza inmediatamente
  - Un solo paso

❌ Desventajas:
  - Cambios irreversibles (sin backup)
  - Requiere precaución
  - Riesgo de mover archivos incorrectos
```

## 🚨 Advertencias Importantes

### ⚠️ Antes de Usar Modo Real

1. **Siempre prueba primero en simulación**
2. **Haz backup** de tu carpeta de descargas
3. **Verifica las rutas** de origen y destino
4. **Revisa las extensiones** en tu configuración
5. **Asegúrate** de que no haya archivos importantes en proceso

### 🔒 Seguridad

- El modo simulación **NUNCA** modifica archivos
- El modo real **SÍ** modifica el sistema de archivos
- No hay "deshacer" en modo real (usa backup)
- Los logs se guardan para auditoría

## 📝 Mejores Prácticas

### Checklist Pre-Ejecución

```markdown
- [ ] Probé en modo simulación
- [ ] Revisé la salida cuidadosamente
- [ ] Las rutas destino son correctas
- [ ] No hay archivos que deban excluirse
- [ ] Tengo backup de archivos importantes
- [ ] Entiendo qué hará el organizador
- [ ] Estoy listo para ejecutar en modo real
```

### Frecuencia Recomendada

- **Primera vez**: Siempre simulación
- **Configuración nueva**: Siempre simulación
- **Uso rutinario**: Modo real (si ya confías)
- **Dudas**: Vuelve a simulación

## 🎯 Resumen

| Aspecto | Recomendación |
|---------|---------------|
| **Principiantes** | Siempre simulación |
| **Configuración nueva** | Siempre simulación |
| **Uso diario** | Modo real (con precaución) |
| **Dudas** | Simulación |
| **Backup** | Siempre recomendado |

## 🔗 Enlaces Relacionados

- [Interfaz Gráfica](gui.md) - Uso del toggle en la GUI
- [Personalización](customization.md) - Configuración de categorías
- [Uso](usage.md) - Comandos disponibles
