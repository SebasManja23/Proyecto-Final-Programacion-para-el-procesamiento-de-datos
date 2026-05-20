# Proyecto de Procesamiento de Datos para Retail

## Descripción

Este proyecto implementa un pipeline completo de procesamiento de datos para un sistema de retail. El objetivo principal es extraer datos de múltiples fuentes heterogéneas, limpiarlos, transformarlos, enriquecerlos y analizarlos para obtener insights valiosos sobre el comportamiento de los clientes, segmentación mediante PCA y visualizaciones interactivas.

El pipeline incluye extracción de datos desde bases de datos SQL (SQLite), NoSQL (MongoDB), archivos CSV/JSON, web scraping de precios de competencia, APIs externas para tipo de cambio, y parsing de logs de servidor. Posteriormente, aplica reglas de negocio, análisis de componentes principales (PCA) para segmentación de clientes en arquetipos, y genera reportes visuales estáticos e interactivos.

## Características Principales

- **Extracción Multifuente**: Integración de datos desde CSV, JSON, SQLite, MongoDB, web scraping y APIs REST.
- **Limpieza y Normalización**: Manejo de datos sucios, normalización de fechas y estados, eliminación de duplicados.
- **Enriquecimiento de Datos**: Merging de datasets para crear una base de datos maestra.
- **Análisis Avanzado**: Aplicación de PCA para reducción dimensional y segmentación de clientes en 3 arquetipos.
- **Reglas de Negocio**: Segmentación basada en monto de compra y edad.
- **Visualizaciones**: Gráficos 3D interactivos con Plotly, diagramas de Sankey para embudos de conversión, comparativas de precios vs competencia, y reportes de cumplimiento de metas.
- **Persistencia**: Guardado de datos procesados en CSV y generación de archivos HTML/PNG para reportes.

## Instalación

### Prerrequisitos

- Python 3.8 o superior
- MongoDB (opcional, para perfiles de usuarios; usa respaldo JSON si no está disponible)
- SQLite (para base de datos de ventas)
- XAMPP o servidor local para web scraping de competencia (opcional)

### Pasos de Instalación

1. Clona o descarga el repositorio en tu máquina local.

2. Navega al directorio del proyecto:
   ```
   cd "proyecto programacion para el procesamiento de datos"
   ```

3. Instala las dependencias usando pip:
   ```
   pip install -r Apoyos/requirements.txt
   ```

4. Asegúrate de que los archivos de datos estén en el directorio raíz:
   - `inventario.csv`
   - `perfiles_usuarios.json` (respaldo si MongoDB no está disponible)
   - `ventas_historicas.db` (base de datos SQLite)
   - `logs_servidor.txt`
   - `metas_anuales.xlsx` (para metas anuales)

5. (Opcional) Configura MongoDB en `localhost:27017` con una base de datos `proyecto_retail` y colección `perfiles` para datos de perfiles de usuarios.

6. (Opcional) Inicia XAMPP y coloca un archivo `competencia.html` en `htdocs/proyecto_retail/` con una tabla de precios para web scraping. También se incluye la carpeta `proyecto_retail/` en el proyecto con el archivo `competencia.html` como ejemplo.

## Uso

### Ejecución del Pipeline

Ejecuta el script principal para procesar todos los datos y generar reportes:

```bash
python main_proyecto.py
```

Esto realizará las siguientes operaciones:
1. Extracción de datos de todas las fuentes.
2. Limpieza y transformación inicial.
3. Enriquecimiento mediante merging.
4. Cálculo de montos en USD usando API de tipo de cambio.
5. Aplicación de reglas de negocio y PCA para segmentación.
6. Generación de visualizaciones y guardado de archivos de salida.

### Archivos de Salida

- `data_master_clean.csv`: Base de datos maestra procesada.
- `flujo_sankey.html`: Diagrama de Sankey interactivo mostrando el embudo de conversión.
- `reporte_visual_retail.png`: Gráficos estáticos de segmentación PCA y distribución de ingresos.
- `grafico_competencia_html.png`: Comparativa de precios vs competencia.
- `grafico_metas.png`: Gráfico de cumplimiento de metas anuales por estado.
- `pca_3d.html`: Gráfico 3D interactivo de segmentación PCA con arquetipos de clientes.

### Funciones Adicionales

Puedes importar y usar funciones individuales desde `funciones.py` para análisis específicos:

```python
import funciones

# Extraer inventario
inv = funciones.extraer_inventario('inventario.csv')

# Generar visualizaciones
funciones.generar_visualizaciones(df_final)
```

## Estructura del Proyecto

```
proyecto programacion para el procesamiento de datos/
├── main_proyecto.py          # Script principal que ejecuta el pipeline
├── funciones.py               # Módulo con todas las funciones auxiliares
├── inventario.csv             # Datos de inventario
├── perfiles_usuarios.json     # Perfiles de usuarios (respaldo)
├── perfiles_usuarios_viejos.json  # Versión anterior de perfiles
├── logs_servidor.txt          # Logs del servidor para análisis
├── ventas_historicas.db       # Base de datos SQLite de ventas (no incluida en repo)
├── metas_anuales.xlsx         # Metas anuales por región (no incluida en repo)
├── data_master_clean.csv      # Salida: datos procesados
├── flujo_sankey.html          # Salida: diagrama de Sankey
├── reporte_visual_retail.png  # Salida: gráficos estáticos
├── grafico_competencia_html.png  # Salida: comparativa de precios
├── proyecto_retail/
│   └── competencia.html       # Ejemplo de página de competencia para web scraping
└── Apoyos/
    └── requirements.txt       # Dependencias de Python

```

## Dependencias

Las dependencias principales están listadas en `Apoyos/requirements.txt`:

- `requests`: Para llamadas a APIs y web scraping
- `beautifulsoup4`: Para parsing HTML en web scraping
- `numpy`: Para operaciones numéricas
- `pandas`: Para manipulación de datos
- `scikit-learn`: Para PCA y clustering
- `matplotlib`: Para gráficos estáticos
- `seaborn`: Para visualizaciones estadísticas
- `plotly`: Para gráficos interactivos
- `pymongo`: Para conexión a MongoDB

## Tecnologías Utilizadas

- **Lenguaje**: Python
- **Bases de Datos**: SQLite, MongoDB (NoSQL)
- **APIs**: exchangerate-api.com para tipo de cambio
- **Web Scraping**: BeautifulSoup para extracción de precios de competencia
- **Análisis**: PCA con scikit-learn para segmentación
- **Visualización**: Matplotlib, Seaborn, Plotly

## Contribución

Si deseas contribuir al proyecto:

1. Haz un fork del repositorio.
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`).
3. Realiza tus cambios y commits.
4. Envía un pull request.

## Licencia

Este proyecto es para fines educativos y no tiene una licencia específica asignada.

## Notas Adicionales

- El proyecto asume que las bases de datos externas (MongoDB, SQLite) están configuradas correctamente.
- Si alguna fuente de datos externa no está disponible, el código usa valores de respaldo o archivos locales.
- Los gráficos interactivos requieren un navegador web para visualizarse completamente.
- Para el web scraping de competencia, se requiere un servidor local (XAMPP) con la página HTML correspondiente.