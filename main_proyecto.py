import funciones

def ejecutar_pipeline():
    print("\n--- INICIANDO PIPELINE DE DATOS ---")
    
    # 1. EXTRACCIÓN (Multifuente)
    inv = funciones.extraer_inventario('inventario.csv')
    perf = funciones.extraer_perfiles('perfiles_usuarios.json')
    vnt = funciones.extraer_ventas('ventas_historicas.db')
    df_competencia = funciones.extraer_precios_competencia_real()
    tasa_usd = funciones.extraer_tipo_cambio_api()
    
    # 2. LIMPIEZA Y TRANSFORMACIÓN INICIAL
    inv_limpio = funciones.limpiar_inventario(inv)
    vnt_limpio = funciones.normalizar_ventas(vnt)
    df_logs = funciones.parsear_logs('logs_servidor.txt')
    #metas = extraer_metas('metas_anuales.xlsx')
    
    # 3. ENRIQUECIMIENTO (Merging)
    base_maestra = funciones.enriquecer_datos(vnt_limpio, perf)
    
    # 4. CÁLCULO DE MONEDA (Uso de los datos de la API)
    # Creamos la columna en USD antes de normalizar
    base_maestra['monto_usd'] = base_maestra['monto'] * tasa_usd
    
    
    # 5. REGLAS DE NEGOCIO Y PCA
    base_maestra = funciones.aplicar_reglas_negocio(base_maestra)
    base_maestra = funciones.aplicar_pca_avanzado(base_maestra)
    
    print("\nPIPELINE COMPLETADO EXITOSAMENTE")
    return base_maestra, inv_limpio, df_logs, df_competencia,perf

###############

if __name__ == "__main__":
    try:
        # 1. Ejecutar el proceso
        df_final, inv_final, logs_final, comp_final,perf_originales = ejecutar_pipeline()
        
        # 2. Guardar CSV
        df_final.to_csv('data_master_clean.csv', index=False)
        print("\nArchivo 'data_master_clean.csv' guardado.")
        # Gráficos de Inteligencia Externa (HTML y Excel)
        funciones.generar_grafico_competencia(inv_final, comp_final)
        funciones.generar_grafico_metas(df_final)
        
        # 3. Gráficos estáticos (PNG)
        print("\nGenerando reportes visuales...")
        funciones.generar_visualizaciones(df_final)
        funciones.grafico_3d_interactivo(df_final) # Gráfico 3D interactivo con Plotly (se abre en el navegador)
        
        # 4. Gráfico interactivo (HTML) 
        print("\nGenerando Diagrama de Sankey...")
        funciones.generar_sankey_flujo(df_final, perf_originales, logs_final)
        
        print("\n" + "="*30)
        print("PROYECTO LISTO PARA PRESENTAR")
        print("="*30)
        
    except Exception as e:
        print(f"\n ERROR CRÍTICO: {e}")