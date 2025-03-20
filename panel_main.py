import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from scripts.Calcula_integracion_dip import calcula_integracion as calcular_d
from scripts.Calcula_integracion_senadores import calcula_integracion as calcular_s

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

# Crear un dataframe de ejemplo con columnas 'Partido' y 'Pacto'
data = {
    'partido': partidos,
    'pacto': ['' for _ in partidos]  # Inicia la columna 'Pacto' vacía
}

df = pd.DataFrame(data)

with open("images\diagrama_metodologia.drawio.svg", encoding="utf-8") as f:
    svg_code = f.read()


st.title('Diagrama metodológico')
st.markdown(svg_code, unsafe_allow_html=True)


# Mostrar la tabla estilo Excel
st.title('Constructor de pactos')


# Configurar la tabla para permitir la edición
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_column("pacto", editable=True)  # Hacer que la columna 'Pacto' sea editable
gridOptions = gb.build()

# Mostrar la tabla estilo Excel
# Mostrar la tabla interactiva con edición habilitada
grid_response = AgGrid(df, gridOptions=gridOptions, enable_enterprise_modules=True)

# Obtener los datos actualizados después de la edición
df_edited = grid_response['data']
# Mostrar la tabla actualizada
#st.dataframe(df_edited)'

# Inicializar variables con DataFrames vacíos
if 'resultados_pacto' not in st.session_state:
    st.session_state['resultados_pacto'] = pd.DataFrame()
if 'resultados_partido' not in st.session_state:
    st.session_state['resultados_partido'] = pd.DataFrame()

if st.button('Calcular Diputados'):
    rp, rpart = calcular_d(df_edited)
    st.session_state['resultados_pacto'] = rp
    st.session_state['resultados_partido'] = rpart



    st.subheader("Resultados Pacto")
    st.dataframe(rp)


    st.subheader("Resultados Partido")
    st.dataframe(rpart)

if st.button('Calcular Senadores'):
    rp, rpart = calcular_s(df_edited)
    st.session_state['resultados_pacto'] = rp
    st.session_state['resultados_partido'] = rpart



    st.subheader("Resultados Pacto")
    st.dataframe(rp)


    st.subheader("Resultados Partido")
    st.dataframe(rpart)
