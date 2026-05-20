import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import sqlite3
import json
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import re
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from sklearn.cluster import KMeans
from pymongo import MongoClient


#----------------------------------------------FUNCIONES DE EXTRACCION--------------------------------------------------------------------------------
def extraer_inventario(ruta_csv):
    """Carga el inventario desde CSV."""
    df=pd.read_csv(ruta_csv)
    return df

def extraer_perfiles(ruta_json):
    """Carga perfiles desde MongoDB (NoSQL). Si falla, usa el JSON de respaldo."""
    try:
        # Intentamos conectar al servidor que ves en tu imagen (localhost:27017)
        cliente = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        db = cliente['proyecto_retail']
        coleccion = db['perfiles']
        
        # Intentamos traer los datos
        datos_mongo = list(coleccion.find({}, {'_id': 0}))
        
        if len(datos_mongo) > 0:
            print(" ¡Conexión exitosa a MongoDB (NoSQL)! Datos extraídos.")
            return pd.DataFrame(datos_mongo)
        else:
            raise Exception("Colección vacía")

    except Exception as e:
        print(f"No se pudo conectar a MongoDB o está vacío. Usando JSON de respaldo. Motivo: {e}")
        with open(ruta_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return pd.DataFrame(data)

def extraer_ventas(ruta_db):
    """Conecta a SQLite y extrae ventas."""
    conn = sqlite3.connect(ruta_db)
    df = pd.read_sql_query("SELECT * FROM ventas", conn)
    conn.close()
    return df

def extraer_metas(ruta_excel):
    """Carga metas anuales desde Excel."""
    return pd.read_excel(ruta_excel, engine='openpyxl')

def extraer_precios_competencia_real():
    """
    PUNTO 1: Web Scraping Real desde Servidor Local (XAMPP).
    """
    url = "http://localhost/proyecto_retail/competencia.html"
    
    try:
        # Hacemos la petición al servidor XAMPP
        respuesta = requests.get(url)
        respuesta.encoding = 'utf-8' # Asegurar que lea bien acentos
        
        if respuesta.status_code == 200:
            soup = BeautifulSoup(respuesta.text, 'html.parser')
            tabla = soup.find('table', {'id': 'tabla-precios'})
            
            datos = []
            for row in tabla.find_all('tr')[1:]:
                cols = row.find_all('td')
                datos.append({
                    "producto": cols[0].text,
                    "precio_competencia": float(cols[1].text)
                })
            
            print("Web Scraping exitoso desde http://localhost!")
            return pd.DataFrame(datos)
        else:
            print("El servidor respondió, pero la página no existe.")
            return pd.DataFrame()

    except requests.exceptions.ConnectionError:
        print(" ERROR: El servidor XAMPP no está encendido.")
        return pd.DataFrame()

def extraer_tipo_cambio_api():
    """
    PUNTO 1: API REST. 
    Obtiene el tipo de cambio actual de MXN a USD.
    """
    url = "https://api.exchangerate-api.com/v4/latest/MXN"
    
    try:
        print("Consultando API de Tipo de Cambio...")
        respuesta = requests.get(url)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            tasa_usd = datos['rates']['USD']
            print(f"Tasa obtenida: 1 MXN = {tasa_usd} USD")
            return tasa_usd
        else:
            return 0.050  # Valor de respaldo (aprox 20 pesos por dólar)
    except:
        print("No se pudo conectar a la API. Usando valor estático.")
        return 0.050
#----------------------------------------------FUNCIONES DE LIMPIEZA--------------------------------------------------------------------------------

def limpiar_inventario(df):
    """Aplica reglas: eliminar duplicados y manejar nulos."""
    df = df.drop_duplicates()
    df['precio'] = df['precio'].fillna(df['precio'].median())
    df['stock'] = df['stock'].fillna(0)
    return df

def normalizar_ventas(df):
    """Arregla fechas y nombres de estados (Texto sucio)."""
    # 1. Normalizar Fechas
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce').ffill()
    
    # 2. Forzar todo a mayúsculas temporalmente para atrapar variantes raras
    df['estado'] = df['estado'].str.upper().str.strip()
    
    # 3. Mapeo a prueba de balas (Atrapa abreviaturas y mayúsculas)
    mapeo = {
        'MEX': 'México', 'MX': 'México', 'MÉXICO': 'México', 'MEXICO': 'México',
        'NL': 'Nuevo León','N.L.':'Nuevo León', 'NUEVO LEÓN': 'Nuevo León', 'NUEVO LEON': 'Nuevo León',
        'JAL': 'Jalisco', 'JALISCO': 'Jalisco',
        'PUE': 'Puebla', 'PUEBLA': 'Puebla'
    }
    df['estado'] = df['estado'].replace(mapeo)
    
    return df

def enriquecer_datos(df_ventas, df_perfiles):
    """PUNTO CLAVE: Une ventas con perfiles usando Customer_ID."""
    #hacemos el merge
    df_perfiles = df_perfiles.rename(columns={'Customer_ID': 'id_cliente'})
    df_final = pd.merge(df_ventas, df_perfiles, on='id_cliente', how='left')
    return df_final


def parsear_logs(ruta_txt):
    """Extrae datos de logs usando Expresiones Regulares (RegEx)."""
    patron = r'(?P<ip>\d+\.\d+\.\d+\.\d+) - \[(?P<fecha>.*?)\] "(?P<metodo>\w+) (?P<recurso>.*?)" (?P<status>\d+) (?P<tiempo>\d+)ms'
    
    logs_data = []
    with open(ruta_txt, 'r') as f:
        for linea in f:
            match = re.search(patron, linea)
            if match:
                logs_data.append(match.groupdict())
    
    df_logs = pd.DataFrame(logs_data)
    # Convertir el tiempo a número para poder analizarlo
    df_logs['tiempo'] = pd.to_numeric(df_logs['tiempo'])
    return df_logs

def aplicar_reglas_negocio(df):
    """
    Creamos segmento_cliente usando np.where.
    """
    #si gasto > 1000 y edad < 30, 'Premium Joven'
    df['segmento_cliente'] = np.where(
        (df['monto'] > 1000) & (df['edad'] < 30), 
        'Premium Joven', 
        np.where(df['monto'] > 3000, 'VIP', 'Regular')
    )
    return df
#----------------------------------------------FUNCION DE PCA--------------------------------------------------------------------------------

def aplicar_pca_avanzado(df):
    """
     PCA sobre 20 variables para identificar 3 componentes principales.
    """
    columnas_20 = [
        'edad', 'ingresos', 'puntos_lealtad', 'clics_productos', 'tiempo_sesion_min',
        'articulos_vistos', 'tasa_conversion', 'devoluciones_previas', 
        'dias_desde_ultima_compra', 'uso_cupones', 'quejas_soporte', 
        'puntuacion_app', 'interacciones_sociales', 'email_abiertos', 
        'compras_fin_semana', 'gasto_tecnologia', 'gasto_hogar', 
        'distancia_tienda_km', 'monto', 'id_tienda'
    ]
    
    # 1 Normalización
    scaler = StandardScaler()
    datos_escalados = scaler.fit_transform(df[columnas_20].fillna(0))
    
    # 2 Aplicar PCA
    pca = PCA(n_components=3)
    componentes = pca.fit_transform(datos_escalados)
    
    df['pca_1'] = componentes[:, 0]
    df['pca_2'] = componentes[:, 1]
    df['pca_3'] = componentes[:, 2]
    
    varianza = pca.explained_variance_ratio_.sum()
    print(f" PCA completado. Varianza explicada: {varianza:.2%}")

   #EXTRAER LOADINGS 
    print("\nGUION PARA EXPOSICIÓN (Variables con más peso por componente):")
    for i, component in enumerate(pca.components_):
        pesos = pd.DataFrame({'Variable': columnas_20, 'Peso': component})
        pesos['Absoluto'] = pesos['Peso'].abs()
        # Tomamos las 3 variables que más influyen en este componente
        top_variables = pesos.sort_values(by='Absoluto', ascending=False).head(3)
        
        print(f"  -> El Componente {i+1} está fuertemente marcado por:")
        for _, row in top_variables.iterrows():
            print(f"     * {row['Variable']} (Peso: {row['Peso']:.2f})")

    # Usamos KMeans para encontrar los 3 arquetipos que generamos en el JSON
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df['cluster_pca'] = kmeans.fit_predict(datos_escalados)
    
    # Le ponemos nombres para que la gráfica se vea profesional
    nombres_clusters = {0: 'Arquetipo A', 1: 'Arquetipo B', 2: 'Arquetipo C'}
    df['arquetipo'] = df['cluster_pca'].map(nombres_clusters)
    print("Clustering completado: Se asignaron colores a los 3 arquetipos.")
    
    return df

#----------------------------------------------FUNCIONES DE VISUALIZACION--------------------------------------------------------------------------------

    
def grafico_3d_interactivo(df):
    """Gráfico 3D Interactivo con Plotly mostrando los 3 arquetipos."""
    fig = px.scatter_3d(
        df, x='pca_1', y='pca_2', z='pca_3',
        color='arquetipo', # <--- AQUÍ CAMBIAMOS EL COLOR
        title='Segmentación en 3D (3 Arquetipos de Cliente)'
    )
    fig.show()



def generar_visualizaciones(df):
    """
    Genera los gráficos requeridos por la rúbrica usando los nuevos arquetipos.
    """
    
    # Configuramos el estilo
    sns.set_theme(style="whitegrid")
    # Aumentamos un poco el tamaño para que se vea mejor
    fig, axes = plt.subplots(1, 2, figsize=(18, 7))

    # GRÁFICO 1: PCA 2D (Para ver la separación clara que ya viste en 3D)
    sns.scatterplot(
        data=df, x='pca_1', y='pca_2', 
        hue='arquetipo', palette='viridis', alpha=0.8,
        ax=axes[0]
    )
    axes[0].set_title('Análisis de Segmentación (Vista 2D de Clusters)')
    axes[0].set_xlabel('Componente Principal 1 (Comportamiento)')
    axes[0].set_ylabel('Componente Principal 2 (Gasto)')

    # GRÁFICO 2: Distribución de Ingresos por ARQUETIPO
    # Usamos 'arquetipo' para que coincida con los colores del PCA
    sns.boxplot(
        data=df, x='arquetipo', y='ingresos', 
        hue='arquetipo', palette='viridis', legend=False,
        ax=axes[1]
    )
    axes[1].set_title('Nivel de Ingresos por Arquetipo de Cliente')
    axes[1].set_xlabel('Arquetipo Detectado')
    axes[1].set_ylabel('Ingresos')

    plt.tight_layout()
    
    # 1. Guardamos la imagen (revisa tu carpeta del proyecto)
    plt.savefig('reporte_visual_retail.png', dpi=300) 
    print("Imagen 'reporte_visual_retail.png' guardada en la carpeta.")
    

def generar_sankey_flujo(df_final, perf_originales, df_logs):
    """Genera un diagrama de Sankey mostrando el embudo completo, incluyendo la limpieza."""
    
    # 1. CONTAR LOS DATOS EN CADA ETAPA
    # A. Tráfico Crudo (Leemos el archivo TXT directamente)
    try:
        with open('logs_servidor.txt', 'r', encoding='utf-8') as f:
            n_logs_crudos = len(f.readlines())
    except:
        n_logs_crudos = 2500 # Valor por defecto si hay error al leer
        
    # B. Visitas de Éxito (Lo que el código filtró y dejó en el DataFrame)
    n_logs_limpios = len(df_logs)
    
    # C. Cuentas creadas (Total del JSON)
    n_cuentas = len(perf_originales)
    
    # D. Clientes con compra (Únicos en la base de datos SQL que coinciden con el json(mongoDB)
    n_compradores = df_final['id_cliente'].nunique()

    # 2. DEFINIR NODOS Y FLUJOS
    label = [
        f"Tráfico Crudo (TXT): {n_logs_crudos}", 
        f"Visitas Válidas (200 OK): {n_logs_limpios}",
        f"Usuarios Registrados: {n_cuentas}", 
        f"Clientes con Compra: {n_compradores}"
    ]
    
    source = [0, 1, 2] # De dónde viene el flujo
    target = [1, 2, 3] # A dónde va
    value = [n_logs_limpios, n_cuentas, n_compradores] # El tamaño del flujo

    # 3. CREAR LA FIGURA
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15, thickness=20, line=dict(color="black", width=0.5),
            label=label,
            color=["#dfe6e9", "#74b9ff", "#a29bfe", "#55efc4"] # Colores: Gris -> Azul -> Morado -> Verde
        ),
        link=dict(
            source=source, target=target, value=value,
            color="rgba(116, 185, 255, 0.4)" # Color del flujo semitransparente
        )
    )])
    print(f"\n ¡Diagrama Maestro generado! Abre 'flujo_sankey_completo.html'")
    fig.update_layout(title_text="Embudo de Conversión Real (Sin Sesgo de Merge)", font_size=12)
    fig.write_html("flujo_sankey.html")
    
def generar_grafico_competencia(inv_final, df_competencia):
    """Genera un gráfico comparativo de precios usando los datos del Web Scraping (HTML). """
    print("\nGenerando gráfico de Inteligencia de Precios (HTML)...")
    
    if df_competencia is not None and not df_competencia.empty:
        
        # 1. Sacamos nuestros precios
        nuestros_precios = inv_final[['id_producto', 'precio']].drop_duplicates()
        
        # 2. EL CRUCE MÁGICO: Unimos 'id_producto' con 'producto'
        df_precios = pd.merge(
            nuestros_precios, 
            df_competencia, 
            left_on='id_producto',  # El nombre en nuestro inventario
            right_on='producto',    # El nombre en el HTML de la competencia
            how='inner'
        )
        
        if not df_precios.empty:
            df_precios = df_precios.head(6) 
            
            plt.figure(figsize=(10, 6))
            x = np.arange(len(df_precios))
            width = 0.35  
            
            plt.bar(x - width/2, df_precios['precio'], width, label='Nuestro Precio', color='#2ca02c')
            plt.bar(x + width/2, df_precios['precio_competencia'], width, label='Precio Competencia', color='#d62728')
            
            plt.title('Comparativa de Precios vs Competencia (Web Scraping)', fontsize=14)
            plt.xticks(x, df_precios['id_producto'], rotation=45)
            plt.ylabel('Precio en MXN ($)')
            plt.legend()
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
            plt.tight_layout()
            plt.savefig('grafico_competencia_html.png', dpi=300)
            print("Gráfico guardado como 'grafico_competencia_html.png'")
            plt.close()
        else:
            print("No hubo coincidencias de productos entre ambas tablas.")
    else:
        print("Datos de competencia (HTML) no disponibles o vacíos.")
        
def generar_grafico_metas(df_final):
    """
    Genera un gráfico de ventas reales vs metas anuales usando el archivo Excel.
    """
    print("\nGenerando gráfico de Cumplimiento de Metas (Excel)...")
    try:
        # Extraemos el Excel usando tu función ya existente
        df_metas = extraer_metas('metas_anuales.xlsx') 
        
        # DEFINICIÓN DE COLUMNAS
        columna_ubicacion = 'estado'  # <--- Aquí ya pusimos 'estado' como me indicaste
        columna_meta_region = 'Region' # Es el nombre en tu Excel
        
        if columna_ubicacion in df_final.columns and columna_meta_region in df_metas.columns:
            # 1. Sumamos las ventas reales por estado
            ventas_reales = df_final.groupby(columna_ubicacion)['monto'].sum().reset_index()
            
            # 2. Cruzamos (Merge) las ventas con las metas del Excel
            # Esto une, por ejemplo, el 'estado' Sinaloa con la 'Region' Sinaloa
            df_comparativo = pd.merge(
                ventas_reales, 
                df_metas, 
                left_on=columna_ubicacion, 
                right_on=columna_meta_region, 
                how='inner'
            )
            
            if not df_comparativo.empty:
                plt.figure(figsize=(12, 7))
                x_m = np.arange(len(df_comparativo))
                width = 0.35
                
                # Barras de Ventas Reales vs Metas
                plt.bar(x_m - width/2, df_comparativo['monto'], width, label='Ventas Reales', color='#1f77b4')
                plt.bar(x_m + width/2, df_comparativo['Meta_Ventas_Anual'], width, label='Meta Anual (Excel)', color='#ff7f0e')
                
                # Configuración estética
                plt.title('Cumplimiento de Metas Anuales por Estado', fontsize=14)
                plt.xticks(x_m, df_comparativo[columna_ubicacion], rotation=45)
                plt.ylabel('Monto en MXN ($)')
                plt.legend()
                plt.grid(axis='y', linestyle='--', alpha=0.7)
                
                plt.tight_layout()
                plt.savefig('grafico_metas_excel.png', dpi=300)
                print(" Gráfico guardado como 'grafico_metas_excel.png'")
                plt.close()
            else:
                print(f"No hubo coincidencias entre los nombres en '{columna_ubicacion}' y '{columna_meta_region}'.")
        else:
             print(f"Error: No se encontró la columna '{columna_ubicacion}' en los datos.")
    except Exception as e:
        print(f"Error al generar gráfico de metas: {e}")
