# 📊 Estadísticas

## Descripción General

El sistema de **estadísticas** de Downloads Organizer te proporciona información detallada sobre:
- Archivos organizados
- Espacio utilizado
- Distribución por categorías
- Actividad histórica
- Rendimiento del sistema

##  ¿Qué Información Proporciona?

### Métricas Disponibles

1. **Total de Archivos**
   - Número total de archivos en la carpeta de descargas
   - Número de archivos organizados
   - Porcentaje de organización

2. **Distribución por Categoría**
   - Cantidad de archivos por tipo
   - Porcentaje del total
   - Espacio ocupado por categoría

3. **Espacio en Disco**
   - Tamaño total de archivos
   - Espacio liberado/organizado
   - Promedio por archivo

4. **Actividad Reciente**
   - Última ejecución
   - Archivos procesados hoy/esta semana/este mes
   - Tendencias de descarga

5. **Rendimiento**
   - Tiempo promedio de organización
   - Velocidad de procesamiento
   - Archivos por segundo

## 📱 Cómo Ver Estadísticas

### Desde la GUI

1. **Abre la aplicación:**
   ```bash
   python3 src/gui/organizer_gui.py
   ```

2. **Navega a la pestaña "Estadísticas"** (tercera pestaña)

3. **Haz clic en "🔄 Cargar Estadísticas"**

4. **Visualiza la información:**
   - Se muestra en el área de texto con formato
   - Fondo oscuro para mejor legibilidad
   - Actualización en tiempo real

### Desde la Línea de Comandos

**Comando básico:**
```bash
python3 src/organizer.py --stats
```

**Con configuración específica:**
```bash
python3 src/organizer.py --config configs/config_dev.json --stats
```

**Con salida detallada:**
```bash
python3 src/organizer.py --stats --verbose
```

**Guardar en archivo:**
```bash
python3 src/organizer.py --stats > estadisticas.txt
```

## 📋 Formato de Salida

### Ejemplo de Estadísticas en Consola

```
╔═══════════════════════════════════════════════════════╗
║         ESTADÍSTICAS - DOWNLOADS ORGANIZER            ║
╚═══════════════════════════════════════════════════════╝

📊 RESUMEN GENERAL
─────────────────────────────────────────────────────────
Total de archivos:          1,247
Archivos organizados:         892
Archivos pendientes:          355
Porcentaje organizado:       71.5%

💾 ESPACIO EN DISCO
─────────────────────────────────────────────────────────
Tamaño total:               15.3 GB
Espacio organizado:         12.1 GB
Espacio pendiente:           3.2 GB
Promedio por archivo:        12.5 MB

📁 DISTRIBUCIÓN POR CATEGORÍA
─────────────────────────────────────────────────────────
Categoría           Archivos     Espacio      % Total
─────────────────────────────────────────────────────────
📷 Imágenes            342        4.2 GB       27.4%
📄 Documentos          289        2.8 GB       23.2%
🎬 Videos              156        6.1 GB       12.5%
🎵 Audio              198        1.5 GB       15.9%
💻 Código              89         245 MB        7.1%
📦 Comprimidos         67         380 MB        5.4%
🔧 Otros              106         78 MB         8.5%

📈 ACTIVIDAD RECIENTE
─────────────────────────────────────────────────────────
Última organización:    2024-01-15 14:32:18
Archivos hoy:            23
Archivos esta semana:    87
Archivos este mes:      342

⏱️ RENDIMIENTO
─────────────────────────────────────────────────────────
Tiempo promedio:         2.3 segundos
Velocidad:               43 archivos/segundo
Última ejecución:        1.8 segundos

✅ Estadísticas generadas exitosamente
```

### Ejemplo en la GUI

En la interfaz gráfica, verás un formato similar pero con:
- **Colores** para mejor legibilidad
- **Scroll** si hay mucha información
- **Botón de copiar** para portapapeles
- **Actualización automática** al cargar

## 📊 Tipos de Estadísticas

### 1. Estadísticas Generales

Información básica del sistema:

```json
{
  "total_archivos": 1247,
  "archivos_organizados": 892,
  "archivos_pendientes": 355,
  "porcentaje_organizado": 71.5,
  "ultima_ejecucion": "2024-01-15T14:32:18"
}
```

### 2. Estadísticas por Categoría

Desglose detallado por tipo de archivo:

```json
{
  "categorias": {
    "Imagenes": {
      "cantidad": 342,
      "espacio_bytes": 4509715660,
      "porcentaje": 27.4,
      "extensiones": {
        ".jpg": 156,
        ".png": 98,
        ".gif": 45,
        ".bmp": 43
      }
    },
    "Documentos": {
      "cantidad": 289,
      "espacio_bytes": 3006477107,
      "porcentaje": 23.2
    }
  }
}
```

### 3. Estadísticas Temporales

Actividad a lo largo del tiempo:

```json
{
  "actividad": {
    "hoy": 23,
    "esta_semana": 87,
    "este_mes": 342,
    "total": 1247
  },
  "tendencia": {
    "promedio_diario": 12.5,
    "dia_mas_activo": "Lunes",
    "hora_pico": "14:00-15:00"
  }
}
```

### 4. Estadísticas de Rendimiento

Métricas de performance:

```json
{
  "rendimiento": {
    "tiempo_promedio_segundos": 2.3,
    "velocidad_archivos_por_segundo": 43,
    "ultima_ejecucion_segundos": 1.8,
    "mejor_tiempo": 1.2,
    "peor_tiempo": 5.7
  }
}
```

## 🎯 Casos de Uso

### 1. Monitoreo de Espacio

**Problema:** Quieres saber cuánto espacio ocupan tus descargas

**Solución:**
```bash
python3 src/organizer.py --stats | grep "Tamaño total"
```

**Resultado:**
```
Tamaño total: 15.3 GB
```

### 2. Identificar Categorías Dominantes

**Problema:** Quieres saber qué tipo de archivos ocupan más espacio

**Solución:**
```bash
python3 src/organizer.py --stats | grep -A 10 "DISTRIBUCIÓN"
```

**Resultado:**
```
📁 DISTRIBUCIÓN POR CATEGORÍA
Videos: 6.1 GB (40%)
Imágenes: 4.2 GB (27%)
Documentos: 2.8 GB (18%)
```

### 3. Seguimiento de Actividad

**Problema:** Quieres ver tu actividad de descargas esta semana

**Solución:**
```bash
python3 src/organizer.py --stats | grep "esta semana"
```

**Resultado:**
```
Archivos esta semana: 87
```

### 4. Optimización de Rendimiento

**Problema:** El organizador está lento

**Solución:**
```bash
python3 src/organizer.py --stats | grep "Rendimiento"
```

**Resultado:**
```
Tiempo promedio: 2.3 segundos
Velocidad: 43 archivos/segundo
```

**Análisis:** Si el tiempo es > 5 segundos, considera:
- Reducir el número de categorías
- Excluir más extensiones
- Usar un SSD en lugar de HDD

## 📈 Gráficos y Visualización

### Exportar para Gráficos

Puedes exportar las estadísticas a JSON para crear gráficos:

```bash
python3 src/organizer.py --stats --format json > stats.json
```

**Ejemplo de uso con Python:**

```python
import json
import matplotlib.pyplot as plt

# Cargar estadísticas
with open('stats.json', 'r') as f:
    stats = json.load(f)

# Crear gráfico de barras
categorias = list(stats['categorias'].keys())
cantidades = [stats['categorias'][c]['cantidad'] for c in categorias]

plt.bar(categorias, cantidades)
plt.title('Archivos por Categoría')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('grafico_categorias.png')
plt.show()
```

## 🔧 Configuración Avanzada

### Estadísticas en Tiempo Real

Para ver estadísticas después de cada ejecución:

```bash
python3 src/organizer.py --stats --auto
```

### Estadísticas Históricas

Guardar historial de estadísticas:

```bash
# Ejecutar y guardar con timestamp
python3 src/organizer.py --stats > "stats_$(date +%Y%m%d_%H%M%S).txt"
```

### Comparación de Períodos

Comparar estadísticas de diferentes períodos:

```bash
# Semana 1
python3 src/organizer.py --stats > stats_week1.txt

# Semana 2
python3 src/organizer.py --stats > stats_week2.txt

# Comparar
diff stats_week1.txt stats_week2.txt
```

## 💡 Consejos y Mejores Prácticas

### 1. Revisión Periódica

**Recomendación:** Revisa estadísticas semanalmente

```bash
# Añadir a crontab (cada lunes a las 9 AM)
0 9 * * 1 python3 /path/to/organizer.py --stats >> ~/stats_weekly.log
```

### 2. Alertas de Espacio

Configurar alertas cuando el espacio supere un límite:

```python
#!/usr/bin/env python3
import subprocess
import json

# Obtener estadísticas
result = subprocess.run(
    ['python3', 'src/organizer.py', '--stats', '--format', 'json'],
    capture_output=True, text=True
)

stats = json.loads(result.stdout)
total_gb = stats['espacio_total_gb']

if total_gb > 20:  # Alerta si supera 20 GB
    print(f"⚠️ ALERTA: Espacio de descargas: {total_gb} GB")
    # Enviar email/notificación aquí
```

### 3. Optimización Basada en Estadísticas

**Si ves que:**
- **Muchos archivos "Otros"**: Añade más categorías
- **Poco espacio liberado**: Revisa tus reglas de organización
- **Rendimiento lento**: Reduce categorías o usa SSD

## 📊 Métricas Clave a Monitorear

### KPIs Recomendados

| Métrica | Valor Óptimo | Acción si no se cumple |
|---------|--------------|------------------------|
| **% Organizado** | > 80% | Revisar categorías |
| **Tiempo promedio** | < 3 seg | Optimizar configuración |
| **Archivos "Otros"** | < 10% | Añadir más categorías |
| **Espacio liberado** | > 50% | Revisar reglas de organización |

## 🚨 Solución de Problemas

### Problema: Las estadísticas no se actualizan

**Causa:** Cache de estadísticas

**Solución:**
```bash
# Forzar actualización
python3 src/organizer.py --stats --force
```

### Problema: Las estadísticas muestran 0 archivos

**Causa:** Carpeta de destino incorrecta

**Solución:**
```bash
# Verificar configuración
python3 src/organizer.py --config configs/tu_config.json --stats
```

### Problema: Las estadísticas tardan mucho

**Causa:** Muchos archivos o disco lento

**Solución:**
- Usar `--fast-stats` para estadísticas rápidas
- Excluir más extensiones
- Usar SSD

## 🔗 Enlaces Relacionados

- [Interfaz Gráfica](gui.md) - Ver estadísticas en la GUI
- [Uso](usage.md) - Comandos disponibles
- [Personalización](customization.md) - Configurar categorías
- [Modo Simulación](simulation.md) - Previsualizar cambios
