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
# LOGO 
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

# 1. Pares
incluir_pares = st.sidebar.toggle("👥 Incluir Evaluadores Pares", value=True)
if incluir_pares:
    tipo_cruce = st.sidebar.selectbox("Tipo de asignación de pares", ["Área", "Cargo"])
    cantidad_pares = st.sidebar.number_input("Cantidad de pares", 1, 10, 2)
    excluir_mismo_jefe = st.sidebar.checkbox("Excluir mismo supervisor", value=True)

st.sidebar.divider()

# 2. Ascendentes
incluir_ascendentes = st.sidebar.toggle("⬆️ Incluir Evaluadores Ascendentes", value=False)
if incluir_ascendentes:
    cantidad_ascendentes = st.sidebar.number_input("Cantidad de ascendentes", 1, 10, 2)

# ------------------------------------------------
# PROCESAMIENTO
# ------------------------------------------------
archivo = st.file_uploader("📂 Sube tu archivo Excel", type=["xlsx"])

if archivo is not None:
    try:
        # Cargamos el archivo
        df = pd.read_excel(archivo, engine="openpyxl")
        
        # Limpieza básica de datos (quitar espacios en blanco)
        df["Cedula"] = df["Cedula"].astype(str).str.strip()
        df["Cedula Supervisor"] = df["Cedula Supervisor"].astype(str).str.strip()

        st.success("Archivo cargado correctamente ✅")

        # --- SECCIÓN DE PREVISUALIZACIÓN (EL CAMBIO SOLICITADO) ---
        st.markdown("### 🔍 Previsualización de los datos cargados")
        st.info("Revisa que las columnas y los datos aparezcan correctamente abajo antes de generar las evaluaciones.")
        st.dataframe(df) # Aquí se muestra el archivo completo que acabas de subir
        st.divider()
        # ---------------------------------------------------------
        
        columnas_req = ["Cedula", "Nombre Completo", "Cargo", "Área", "Cedula Supervisor"]
        if not all(col in df.columns for col in columnas_req):
            st.error(f"Faltan columnas obligatorias. Asegúrate de que el archivo tenga: {columnas_req}")
            st.stop()

        if st.button("🎄 Generar árbol de relaciones"):
            with st.spinner("Lia está validando jerarquías y asignando..."):
                
                # --- TRATAMIENTO DE JEFE DIRECTO (DESCENDENTE) ---
                df["Evaluador Descendente Final"] = df.apply(
                    lambda x: "No Aplica" if x["Cedula"] == x["Cedula Supervisor"] else x["Cedula Supervisor"],
                    axis=1
                )

                df_final = df[["Cedula", "Nombre Completo", "Evaluador Descendente Final"]].copy()


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
                        
                        # Selección aleatoria segura
                        n_a_seleccionar = min(len(candidatos), cantidad_pares)
                        if n_a_seleccionar > 0:
                            ids_pares = candidatos.sample(n=n_a_seleccionar)["Cedula"].tolist()
                        else:
                            ids_pares = []
                            
                        while len(ids_pares) < cantidad_pares:
                            ids_pares.append("")
                        
                        fila = {"Cedula": persona["Cedula"]}
                        for i in range(cantidad_pares):
                            fila[f"Par_{i+1}"] = ids_pares[i]
                        pares_data.append(fila)
                    
                    df_final = df_final.merge(pd.DataFrame(pares_data), on="Cedula", how="left")

                # --- LÓGICA ASCENDENTES ---
                if incluir_ascendentes:
                    for i in range(cantidad_ascendentes):
                        df_final[f"Asc_{i+1}"] = ""
                    
                    supervisores = df["Cedula Supervisor"].unique()
                    for sup in supervisores:
                        equipo = df[(df["Cedula Supervisor"] == sup) & (df["Cedula"] != sup)]
                        if not equipo.empty:
                            n_asc = min(len(equipo), cantidad_ascendentes)
                            ids_asc = equipo.sample(n=n_asc)["Cedula"].tolist()
                            for idx, val in enumerate(ids_asc):
                                df_final.loc[df_final["Cedula"] == sup, f"Asc_{idx+1}"] = val

            # ------------------------------------
            # RENOMBRAR Y COLUMNAS FINALES
            # ------------------------------------
            rename_dict = {
                "Cedula": "Número de Documento",
                "Nombre Completo": "Nombre Colaborador",
                "Evaluador Descendente Final": "Evaluador Descendente"
            }

            if incluir_auto: rename_dict["Autoevaluacion_ID"] = "Autoevaluación"
            if incluir_pares:
                for i in range(cantidad_pares):
                    rename_dict[f"Par_{i+1}"] = f"Evaluador Paralelo {i+1}"
            if incluir_ascendentes:
                for i in range(cantidad_ascendentes):
                    rename_dict[f"Asc_{i+1}"] = f"Evaluador Ascendente {i+1}"

            df_export = df_final.rename(columns=rename_dict)
            df_export = df_export[list(rename_dict.values())]

            st.success("¡Estrucutra generada con éxito! 🚀")
            st.markdown("### 📊 Resultado Final")
            st.dataframe(df_export)

            excel_buffer = BytesIO()
            df_export.to_excel(excel_buffer, index=False, engine="openpyxl")
            st.download_button("📥 Descargar Excel", excel_buffer.getvalue(), "evaluaciones_desempeno.xlsx")

    except Exception as e:
        st.error(f"Se produjo un error al procesar el archivo: {e}")
