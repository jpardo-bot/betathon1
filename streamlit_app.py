import streamlit as st
import pandas as pd
import random
from io import BytesIO

# ------------------------------------------------
# CONFIGURACIÓN PÁGINA
# ------------------------------------------------
st.set_page_config(
    page_title="Lia by Buk",
    layout="wide"
)

# ------------------------------------------------
# LOGO (Manteniendo tu estructura original)
# ------------------------------------------------
try:
    st.sidebar.image("logo.png", width=180)
except:
    pass

# ------------------------------------------------
# TÍTULOS
# ------------------------------------------------
st.title("🤖 Lia by Buk")
st.subheader("Asignador Inteligente de Evaluadores")

# ------------------------------------------------
# SIDEBAR - CONFIGURACIÓN CONDICIONAL
# ------------------------------------------------
st.sidebar.header("⚙️ Configuración")

st.sidebar.divider()

# 1. Configuración de Pares
incluir_pares = st.sidebar.toggle("👥 Incluir Evaluadores Pares", value=True)
if incluir_pares:
    tipo_cruce = st.sidebar.selectbox(
        "Tipo de asignación de pares",
        ["Área", "Cargo"]
    )
    cantidad_pares = st.sidebar.number_input(
        "Cantidad de pares",
        min_value=1, max_value=10, value=2
    )
    excluir_mismo_jefe = st.sidebar.checkbox(
        "Excluir personas del mismo supervisor",
        value=True
    )

st.sidebar.divider()

# 2. Configuración de Ascendentes
incluir_ascendentes = st.sidebar.toggle("⬆️ Incluir Evaluadores Ascendentes", value=False)
if incluir_ascendentes:
    cantidad_ascendentes = st.sidebar.number_input(
        "Cantidad de ascendentes",
        min_value=1, max_value=10, value=2
    )

# ------------------------------------------------
# SUBIR ARCHIVO
# ------------------------------------------------
archivo = st.file_uploader("📂 Sube tu archivo Excel", type=["xlsx"])

if archivo is not None:
    try:
        df = pd.read_excel(archivo, engine="openpyxl")
        st.success("Archivo cargado correctamente ✅")
        
        # Validar columnas necesarias
        columnas_req = ["Cedula", "Nombre Completo", "Cargo", "Área", "Cedula Supervisor"]
        faltantes = [col for col in columnas_req if col not in df.columns]

        if faltantes:
            st.error(f"Faltan columnas obligatorias: {faltantes}")
            st.stop()

        st.subheader("📊 Vista previa de datos")
        st.dataframe(df.head(5))

        if st.button("✨ Generar Evaluaciones"):
            with st.spinner("Lia está trabajando en las asignaciones..."):
                
                # Base del DataFrame final
                df_final = df[["Cedula", "Nombre Completo", "Cedula Supervisor"]].copy()


                # --- LÓGICA PARES ---
                if incluir_pares:
                    pares_data = []
                    for _, persona in df.iterrows():
                        candidatos = df[df["Cedula"] != persona["Cedula"]].copy()
                        
                        if tipo_cruce == "Área":
                            candidatos = candidatos[candidatos["Área"] == persona["Área"]]
                        else:
                            candidatos = candidatos[candidatos["Cargo"] == persona["Cargo"]]
                        
                        if excluir_mismo_jefe:
                            candidatos = candidatos[candidatos["Cedula Supervisor"] != persona["Cedula Supervisor"]]
                        
                        # Aleatorizar y seleccionar
                        ids_pares = candidatos.sample(n=min(len(candidatos), cantidad_pares))["Cedula"].tolist()
                        while len(ids_pares) < cantidad_pares:
                            ids_pares.append("")
                        
                        fila = {"Cedula": persona["Cedula"]}
                        for i in range(cantidad_pares):
                            fila[f"Par_{i+1}"] = ids_pares[i]
                        pares_data.append(fila)
                    
                    df_pares = pd.DataFrame(pares_data)
                    df_final = df_final.merge(df_pares, on="Cedula", how="left")

                # --- LÓGICA ASCENDENTES ---
                if incluir_ascendentes:
                    # Crear columnas vacías primero
                    for i in range(cantidad_ascendentes):
                        df_final[f"Asc_{i+1}"] = ""
                    
                    supervisores = df["Cedula Supervisor"].dropna().unique()
                    for sup in supervisores:
                        equipo = df[df["Cedula Supervisor"] == sup]
                        if not equipo.empty:
                            ids_asc = equipo.sample(n=min(len(equipo), cantidad_ascendentes))["Cedula"].tolist()
                            for idx, val in enumerate(ids_asc):
                                df_final.loc[df_final["Cedula"] == sup, f"Asc_{idx+1}"] = val

            # ------------------------------------
            # RENOMBRAR Y FILTRAR COLUMNAS FINALES
            # ------------------------------------
            
            # Diccionario base de renombramiento
            rename_dict = {
                "Cedula": "Número de Documento",
                "Nombre Completo": "Nombre Colaborador",
                "Cedula Supervisor": "Evaluador Descendente"
            }


            if incluir_pares:
                for i in range(cantidad_pares):
                    rename_dict[f"Par_{i+1}"] = f"Evaluador Paralelo {i+1}"

            if incluir_ascendentes:
                for i in range(cantidad_ascendentes):
                    rename_dict[f"Asc_{i+1}"] = f"Evaluador Ascendente {i+1}"

            # Aplicar cambios
            df_export = df_final.rename(columns=rename_dict)
            
            # Seleccionar solo las columnas que fueron renombradas (las que el usuario eligió)
            columnas_finales = list(rename_dict.values())
            df_export = df_export[columnas_finales]

            st.success("¡Evaluaciones generadas! 🚀")
            st.subheader("📋 Resultado Final")
            st.dataframe(df_export)

            # EXPORTACIÓN
            excel_buffer = BytesIO()
            df_export.to_excel(excel_buffer, index=False, engine="openpyxl")
            excel_buffer.seek(0)

            st.download_button(
                label="📥 Descargar Excel Final",
                data=excel_buffer,
                file_name="matriz_evaluaciones_buk.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Hubo un problema técnico: {e}")
