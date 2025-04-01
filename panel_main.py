import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from scripts.Calcula_integracion_dip import calcula_integracion as calcular_d
from scripts.Calcula_integracion_senadores import calcula_integracion as calcular_s
from pathlib import Path
import base64
import io
import plotly.express as px



#Define un CSS para centrar títulos
st.markdown(
    """
    <style>
        .centered-title {
            text-align: center;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Función para verificar si al menos un DataFrame en una lista no está vacío
def not_empty(df_list):
    return any(not df.empty for df in df_list)

# Función para exportar a Excel en memoria
def to_excel(df_edited, rp, rpart):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_edited.to_excel(writer, sheet_name='Pactos', index=False)
        rp.to_excel(writer, sheet_name='Resultados_Pacto', index=False)
        rpart.to_excel(writer, sheet_name='Resultados_Partido', index=False)
    writer.close()  # Asegura que se guarden los datos
    output.seek(0)  # Reinicia el puntero al inicio del archivo
    return output.getvalue()  # Devuelve los datos binarios correctamente

# Función para resaltar en negrita la fila de totales
def highlight_totals(row):
    if row.name == "Total":
        return ['font-weight: bold'] * len(row)
    else:
        return [''] * len(row)

# Crear una lista con los valores para la columna 'Partido'
partidos = [
    'FA', 'FREVS', 'AH', 'PL', 'PCCH', 'PR', 'PDC', 'PPD', 'PS', 'UDI', 'DEMOCRATAS', 
    'AMARILLOS', 'RN', 'EVOPOLI', 'PSC', 'REPUBLICANO', 'POPULAR', 'PAVP', 'IGUALDAD', 
    'PH', 'PTR', 'PDG', 'IND'
]

data = {
    'Partido': partidos,  # Lista de partidos
    'Escenario 1': [
        'seguimos', 'seguimos', 'seguimos', 'seguimos', 'seguimos',
        'seguimos', 'seguimos', 'seguimos', 'seguimos', 'chv',
        'chv', 'chv', 'chv', 'chv', 'rep',
        'rep', 'ultra', 'ultra', 'ultra', 'ultra',
        'ptr', 'rep', 'ind'
    ],
    'Escenario 2': [
        'izquierda', 'centro', 'izquierda', 'centro', 'izquierda',
        'centro', 'centro', 'izquierda', 'izquierda', 'chv',
        'chv', 'chv', 'chv', 'chv', 'rep',
        'rep', 'ultra', 'ultra', 'ultra', 'ultra',
        'ptr', 'rep', 'ind'
    ]
}


df = pd.DataFrame(data)
# Explicación de uso
st.markdown('<h1 class="centered-title">Calculadora de Integración Electoral</h1>', unsafe_allow_html=True)
st.write(
    "Esta herramienta permite simular los resultados electorales de los distintos partidos políticos de Chile en función de los pactos electorales que formen. "
    "Cada partido tiene una proyección de votos basada en los resultados de las elecciones de 2024 y en la presencia de candidaturas incumbentes."
    "\n\n"
    "**¿Cómo utilizar la herramienta?**\n"
    "1. Completa el **constructor de pactos** con las configuraciones deseadas.\n"
    "2. La tabla permite simular **dos escenarios de pactos distintos**, los cuales serán comparados gráficamente.\n"
    "3. Si un partido obtiene un resultado negativo, significa que en el segundo escenario pierde diputados ( o senadores) respecto al primero."
    "\n\n"
    "A continuación, se presenta la metodología utilizada para la proyección electoral:"
)

# Cargar y mostrar la imagen de la metodología
ruta_imagen = Path("images") / "diagrama_metodologia.drawio.svg"

with open(ruta_imagen, "rb") as f:
    svg_content = f.read()
    encoded_svg = base64.b64encode(svg_content).decode()

st.markdown("### ¿Diagrama de Metodología", unsafe_allow_html=True)

st.markdown(
    f"""
    <div style="display: flex; justify-content: center;">
        <img src="data:image/svg+xml;base64,{encoded_svg}" 
             style="max-width: 100%; height: auto;">
    </div>
    """,
    unsafe_allow_html=True
)

# Mostrar la tabla estilo Excel
# Aplica la clase al título
st.markdown('### Constructor de pactos', unsafe_allow_html=True)

# Configurar la tabla para permitir la edición
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_column("Escenario 1", editable=True)
gb.configure_column("Escenario 2", editable=True)

# Ajustar automáticamente el tamaño de todas las columnas
gb.configure_grid_options(autoSizeMode="fitAllColumnsToView")


gridOptions = gb.build()

# Mostrar la tabla estilo Excel
# Mostrar la tabla interactiva con edición habilitada
grid_response = AgGrid(df, gridOptions=gridOptions, enable_enterprise_modules=True)

# Obtener los datos actualizados después de la edición
df_edited = grid_response['data']

# Inicializar variables con DataFrames vacíos
if 'resultados_pacto' not in st.session_state:
    st.session_state['resultados_pacto'] = pd.DataFrame()
if 'resultados_partido' not in st.session_state:
    st.session_state['resultados_partido'] = pd.DataFrame()

if st.button('Calcular Diputados'):
    df1 = df_edited[["Partido", "Escenario 1"]]
    df1 = df1.rename(columns={
    'Partido': 'partido',
    'Escenario 1': 'pacto'
    })
    print(df1)
    rp1, rpart1 = calcular_d(df1)
    df2 = df_edited[["Partido", "Escenario 2"]]
    df2 = df2.rename(columns={
    'Partido': 'partido',
    'Escenario 2': 'pacto'
    })
    rp2, rpart2 = calcular_d(df2)
    
    #Guardar los resultados en listas
    st.session_state['resultados_pacto'] = [rp1, rp2]
    st.session_state['resultados_partido'] = [rpart1, rpart2]

    st.markdown('### Resultados', unsafe_allow_html=True)
    #delta_pacto = rp1 - rp2
    delta_partido = rpart2 - rpart1
    st.subheader("Diferencia entre escenario 1 y 2 por partido")
    #st.dataframe(delta_partido)
    #print(delta_partido.columns)
    # Suponiendo que delta_partido ya está calculado
    ultima_fila = delta_partido.iloc[-1]  # Obtener la última fila    
    # Crear gráfico de barras
    # Crear un nuevo DataFrame con las columnas como valores en X
    df_grafico = pd.DataFrame({
        'Partido': ultima_fila.index,  # Nombres de los partidos (X)
        'Diferencia': ultima_fila.values  # Valores de la última fila (Y)
    })
    # Crear gráfico de barras
    fig = px.bar(df_grafico, x="Partido", y="Diferencia", 
             labels={'Partido': 'Partido Político', 'Diferencia': 'Diferencia de escaños'},
             text_auto=True,
             color_discrete_sequence=["blue"])  # Personaliza el color
    # Ajustar tamaño de fuente para mejorar la visualización
    fig.update_traces(textfont_size=12, textposition="outside")
    st.plotly_chart(fig)


    st.subheader("Resultados por Pacto ")
    #st.dataframe(rp1)
    #st.dataframe(rp2)
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Resultados escenario 1")
        st.dataframe(rp1)

    with col2:
        st.subheader("Resultados escenario 2")
        st.dataframe(rp2)

    st.subheader("Resultados por partido ")
    st.subheader("Resultados escenario 1")
    st.dataframe(rpart1)
    st.subheader("Resultados escenario 2")
    st.dataframe(rpart2)   



if st.button('Calcular Senadores'):
    df1 = df_edited[["Partido", "Escenario 1"]]
    df1 = df1.rename(columns={
    'Partido': 'partido',
    'Escenario 1': 'pacto'
    })
    print(df1)
    rp1, rpart1 = calcular_s(df1)
    df2 = df_edited[["Partido", "Escenario 2"]]
    df2 = df2.rename(columns={
    'Partido': 'partido',
    'Escenario 2': 'pacto'
    })
    rp2, rpart2 = calcular_s(df2)
    
    #Guardar los resultados en listas
    st.session_state['resultados_pacto'] = [rp1, rp2]
    st.session_state['resultados_partido'] = [rpart1, rpart2]

    st.markdown('### Resultados', unsafe_allow_html=True)

    #delta_pacto = rp1 - rp2
    delta_partido = rpart2 - rpart1

    st.subheader("Diferencia entre escenario 1 y 2 por partido")    
    ultima_fila = delta_partido.iloc[-1]  # Obtener la última fila    
    # Crear gráfico de barras
    # Crear un nuevo DataFrame con las columnas como valores en X
    df_grafico = pd.DataFrame({
        'Partido': ultima_fila.index,  # Nombres de los partidos (X)
        'Diferencia': ultima_fila.values  # Valores de la última fila (Y)
    })
    # Crear gráfico de barras
    fig = px.bar(df_grafico, x="Partido", y="Diferencia", 
             labels={'Partido': 'Partido Político', 'Diferencia': 'Diferencia de escaños'},
             text_auto=True,
             color_discrete_sequence=["blue"])  # Personaliza el color
    # Ajustar tamaño de fuente para mejorar la visualización
    fig.update_traces(textfont_size=12, textposition="outside")
    st.plotly_chart(fig)

    st.subheader("Resultados por Pacto ")
    #st.dataframe(rp1)
    #st.dataframe(rp2)
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Resultados escenario 1")
        st.dataframe(rp1)

    with col2:
        st.subheader("Resultados escenario 2")
        st.dataframe(rp2)

    st.subheader("Resultados por partido ")
    st.subheader("Resultados escenario 1")
    st.dataframe(rpart1)
    st.subheader("Resultados escenario 2")
    st.dataframe(rpart2)



# Botón para descargar el archivo Excel
# Verificar si las listas no están vacías y si los DataFrames dentro de ellas no están vacíos
# Verificar que las listas no estén vacías
if not_empty(st.session_state['resultados_pacto']) and not_empty(st.session_state['resultados_partido']):
    # Crear un buffer en memoria para almacenar el archivo Excel
    output = io.BytesIO()
    
    # Usamos ExcelWriter para escribir en el buffer
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Opcional: escribir el DataFrame original en una hoja (por ejemplo, 'Datos Originales')
        #df_edited.to_excel(writer, sheet_name='Datos Originales', index=False)
        combined=df_edited
        sheet_name = "Pactos"
        combined.to_excel(writer, sheet_name=sheet_name, index=False)   
        
        # Iterar sobre los resultados y escribir cada par en una hoja separada
        for index, (resultado_pacto, resultado_partido) in enumerate(zip(st.session_state['resultados_pacto'],
                                                                          st.session_state['resultados_partido'])):
            # Combinar los dos DataFrames (por ejemplo, concatenándolos horizontalmente)
            combined = pd.concat([resultado_pacto, resultado_partido], axis=1)
            
            # Definir un nombre de hoja único para cada iteración
            sheet_name = f"Pacto escenario {index + 1}"
            combined.to_excel(writer, sheet_name=sheet_name, index=False)      
        
    output.seek(0)
    excel_data = output.getvalue()
    
    st.download_button(
        label="Descargar Resultados en Excel",
        data=excel_data,
        file_name="resultados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
