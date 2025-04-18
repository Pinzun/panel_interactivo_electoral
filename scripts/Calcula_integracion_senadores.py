#importa pandas para el manejo de df
import pandas as pd
import numpy as np
#import plotly.express as px
import gdown
import os
from pathlib import Path
# Función para agregar una fila de totales a un DataFrame
def agregar_totales(df):
    if df.empty:
        return df
    # Sumar solo columnas numéricas
    totales = df.select_dtypes(include='number').sum()
    totales_df = pd.DataFrame(totales).T
    totales_df.index = ['Total']
    return pd.concat([df, totales_df])


def calcula_dhont(numero_concejales, numero_pactos, votos_por_pacto):
    # Crear una lista para almacenar los resultados de la distribución de escaños por pacto
    escaños_por_pacto = []
    
    # Inicializar una lista con el número de escaños ganados por cada pacto a cero
    for _ in range(numero_pactos):
        escaños_por_pacto.append(0)
    
    # Iterar para asignar los escaños a cada pacto
    for i in range(numero_concejales):
        # Crear una lista para almacenar los cocientes electorales
        cocientes_electorales = []
        
        # Calcular el cociente electoral para cada pacto
        for j in range(numero_pactos):
            cociente = votos_por_pacto[j] / (escaños_por_pacto[j] + 1)
            cocientes_electorales.append((cociente, j))
        
        # Encontrar el pacto con el mayor cociente electoral
        max_cociente, index_pacto_ganador = max(cocientes_electorales)
        
        # Incrementar el número de escaños del pacto ganador
        escaños_por_pacto[index_pacto_ganador] += 1
    
    return escaños_por_pacto


def calcula_integracion(df_edited):    
    ruta_escaños = Path(__file__).parent.parent / "data" / "escaños_circunscripcion.json" 
    escaños=pd.read_json(str(ruta_escaños))
    ruta_circun = Path(__file__).parent.parent / "data" / "comunas_circunscripcion.json"
    comunas_circun=pd.read_json(str(ruta_circun))
    ruta_proyectados = Path(__file__).parent.parent / "data" / "resultados_proyectados_senadores.json"    
    resultados_proyectados=pd.read_json(str(ruta_proyectados))
    resultados_proyectados = resultados_proyectados.loc[:, ~resultados_proyectados.columns.str.contains('^Unnamed')]
    resultados_proyectados=resultados_proyectados.drop(columns=['Votos Blancos', 'Votos Nulos'])
    #Se calculan los votos de cada partido por distriro
    # Asegurarnos de que 'comunas_distrito' tiene 'comuna' como índice
    comunas_circun = comunas_circun.set_index('comuna')
    resultados_proyectados = resultados_proyectados.set_index('Comuna')

    # Paso 2: Ahora unimos 'resultados_proyectados_transpuesto' con la columna 'Circunscripcion' de 'comunas_circun'
    resultados_proyectados['Circunscripcion'] = resultados_proyectados.index.map(comunas_circun['Circunscripcion'])

    # Paso 3: Agrupar por 'Circunscripcion' y sumar los votos de cada partido
    resultados_proyectados_circun = resultados_proyectados.groupby('Circunscripcion').sum()
    resultados_proyectados_circun.index = resultados_proyectados_circun.index.astype(int)


    #se procede a calcular el dhont para diputados

 
    #Se agrupan los votos por pacto
    # Paso 1: Transponer el DataFrame 'resultados_proyectados_circun' para que los partidos sean las filas
    resultados_proyectados_transpuesto = resultados_proyectados_circun.T
    resultados_proyectados_transpuesto = resultados_proyectados_transpuesto.rename_axis('partido', axis=1)
    # Paso 2: Unir el DataFrame 'resultados_proyectados_transpuesto' con el DataFrame 'pactos' para agregar la columna 'pacto'
    resultados_proyectados_transpuesto = resultados_proyectados_transpuesto.merge(df_edited, how='left', left_index=True, right_on='partido')
    # Paso 3: Agrupar por 'pacto' y sumar los votos de los partidos dentro de cada pacto
    resultados_proyectados_por_pacto = resultados_proyectados_transpuesto.groupby('pacto').sum()
    resultados_proyectados_por_partido = resultados_proyectados_transpuesto.groupby(['pacto','partido']).sum()
    # Paso 4: Volver a transponer para tener las comunas como índice y los pactos como columnas
    resultados_proyectados_por_pacto = resultados_proyectados_por_pacto.T
    resultados_proyectados_por_pacto = resultados_proyectados_por_pacto.drop("partido", axis=0)


    # Crear DataFrame para guardar los resultados, usando pactos como columnas
    pactos_unicos = resultados_proyectados_por_pacto.columns  # Extraer los pactos únicos
    partidos_unicos = resultados_proyectados_circun.columns
    integracion_pacto = pd.DataFrame(index=resultados_proyectados_circun.index, columns=pactos_unicos)
    integracion_pacto=integracion_pacto.fillna(0)
    integracion_partido = pd.DataFrame(index=resultados_proyectados_circun.index, columns=partidos_unicos)
    integracion_partido=integracion_partido.fillna(0)
    # Asegurarse de que la columna 'Circunscripcion' sea el índice de 'escaños'
    escaños = escaños.set_index('Circunscripcion')

    # Aplica D'Hondt en cada circunscripcion
    for d in resultados_proyectados_circun.index:    
        # Obtener el número de escaños asignados para esta circunscripcion
        n_escaños = escaños.loc[d, 'Senadores']    
        # Seleccionar la fila correspondiente a la circunscripcion en 'resultados_proyectados_por_pacto'
        fila = resultados_proyectados_por_pacto.loc[d]    
        # Crear la lista omitiendo los valores iguales a 0
        votos_por_pacto = fila[fila != 0].tolist()      
        # Calcular la distribución de escaños con D'Hondt
        numero_pactos = len(votos_por_pacto)
        integracion = calcula_dhont(n_escaños, numero_pactos, votos_por_pacto)    
        # Asignar los resultados al DataFrame
        # Mapear los resultados de integración al índice de pactos con votos
        pactos_no_cero = fila[fila != 0].index  # Índices (pactos) con votos
        for pacto, escaños_asignados in zip(pactos_no_cero, integracion):
            integracion_pacto.loc[d, pacto] = escaños_asignados
    for indice, row in integracion_pacto.iterrows():
        for pacto in pactos_unicos:
            n_electos=row[pacto]
            partidos=df_edited.loc[df_edited['pacto']==pacto,'partido'].tolist()
            n_partidos=len(partidos)
            votos_partido=resultados_proyectados_circun.loc[indice,partidos].tolist()
            integracion_partidos=calcula_dhont(n_electos, n_partidos, votos_partido)
            for partido, escaños_partido in zip(partidos,integracion_partidos):
                integracion_partido.loc[indice,partido] = escaños_partido
                            

    integracion_partido = integracion_partido.rename(columns={
        'IND - CANDIDATURAS INDEPENDIENTES': 'IND',
        'AMARILLOS': 'AMA',
        'EVOPOLI': 'EVO',
        'IGUALDAD': 'IGU',
        'POPULAR': 'POP',
        'DEMOCRATAS': 'DEM',
        'REPUBLICANO': 'REP'})
    # Lista de circunscripciones a eliminar
    drop_circuns = [2, 4, 6, 8, 10, 12, 13, 14, 16]

    # Eliminar las filas correspondientes en integracion_pacto e integracion_partido
    integracion_pacto = integracion_pacto.drop(drop_circuns, errors='ignore')
    integracion_partido = integracion_partido.drop(drop_circuns, errors='ignore')
    integracion_pacto = agregar_totales(integracion_pacto)
    integracion_partido = agregar_totales(integracion_partido)
    return integracion_pacto, integracion_partido

#resultados_proyectados_por_pacto.to_csv("resultados_proyectados_por_pacto.csv", encoding= 'utf-8',sep=';')
#integracion_pacto.to_csv("resultados_integracion_pacto.csv", encoding= 'utf-8-sig',sep=';')
#integracion_partido.to_csv("resultados_integracion_partido.csv", encoding= 'utf-8-sig',sep=';')
#integracion_partido.csv("resultados_url_integracion_partido.csv", encoding= 'utf-8',sep=';')
