import streamlit as st
import pandas as pd
import random
from io import BytesIO

st.set_page_config(
    page_title="Lia by Buk",
    layout="wide"
)

st.title("🤖 Lia by Buk, tu asignador Inteligente de Evaluadores")

# ------------------------------------------------
# CONFIGURACIÓN
# ------------------------------------------------

st.sidebar.header("⚙️ Configuración")

tipo_cruce = st.sidebar.selectbox(
    "Tipo de asignación de pares",
    ["Area", "Cargo"]
)

cantidad_pares = st.sidebar.number_input(
    "Cantidad de pares por colaborador",
    min_value=1,
    max_value=100,
    value=2
)

excluir_mismo_jefe = st.sidebar.checkbox(
    "Excluir personas del mismo jefe",
    value=True
)

# ------------------------------------------------
# SUBIR ARCHIVO
# ------------------------------------------------

archivo = st.file_uploader(
    "📂 Sube archivo Excel",
    type=["xlsx"]
)

if archivo:

    df = pd.read_excel(
    archivo,
    engine="openpyxl"
)

    st.subheader("📊 Vista previa")
    st.dataframe(df)

    columnas_necesarias = [
        "Cedula",
        "Nombre Completo",
        "Cargo",
        "Área",
        "Cedula Supervisor"
    ]

    faltantes = [
        col for col in columnas_necesarias
        if col not in df.columns
    ]

    if faltantes:
        st.error(
            f"Faltan columnas: {faltantes}"
        )
        st.stop()

    # --------------------------------------------
    # FUNCIÓN PARES
    # --------------------------------------------

    def asignar_pares(df):

        resultados = []

        for _, persona in df.iterrows():

            Cedula = persona["Cedula"]
            Nombre Completo = persona["Nombre"]
            Área = persona["Area"]
            Cargo = persona["Cargo"]
            Cedula Supervisor = persona["Cedula_Jefe"]
            

            candidatos = df.copy()

            # Evitar autoevaluación
            candidatos = candidatos[
                candidatos["Cedula"] != cedula
            ]

            # Filtro principal
            if tipo_cruce == "Area":

                candidatos = candidatos[
                    candidatos["Area"] == area
                ]

            else:

                candidatos = candidatos[
                    candidatos["Cargo"] == cargo
                ]

            # Excluir mismo jefe
            if excluir_mismo_jefe:

                candidatos = candidatos[
                    candidatos["Cedula_Jefe"] != jefe
                ]

            # Mezclar aleatoriamente
            candidatos = candidatos.sample(
                frac=1,
                random_state=random.randint(1, 100000)
            )

            seleccionados = candidatos.head(
                cantidad_pares
            )

            evaluadores = seleccionados[
                "Cedula"
            ].tolist()

            nombres = seleccionados[
                "Nombre"
            ].tolist()

            # Completar espacios vacíos
            while len(evaluadores) < cantidad_pares:
                evaluadores.append("")
                nombres.append("")

            fila = {
                "Cedula": cedula,
                "Nombre": persona["Nombre"],
                "Cargo": cargo,
                "Area": area,
                "Cedula_Jefe": jefe
            }

            # Crear columnas dinámicas
            for i in range(cantidad_pares):

                fila[f"Par_{i+1}_Cedula"] = evaluadores[i]
                fila[f"Par_{i+1}_Nombre"] = nombres[i]

            resultados.append(fila)

        return pd.DataFrame(resultados)

    # --------------------------------------------
    # FUNCIÓN ASCENDENTE
    # --------------------------------------------

    def asignar_ascendente(df_resultado, df_original):

        mapa_jefes = df_original[
            [
                "Cedula",
                "Nombre"
            ]
        ].rename(
            columns={
                "Cedula": "Cedula_Jefe",
                "Nombre": "Nombre_Jefe"
            }
        )

        df_resultado = df_resultado.merge(
            mapa_jefes,
            on="Cedula_Jefe",
            how="left"
        )

        df_resultado["Evaluador_Ascendente"] = \
            df_resultado["Cedula_Jefe"]

        df_resultado["Nombre_Ascendente"] = \
            df_resultado["Nombre_Jefe"]

        return df_resultado

    # --------------------------------------------
    # GENERAR TODO
    # --------------------------------------------

    if st.button("✨ Generar Evaluaciones"):

        with st.spinner("Generando evaluadores..."):

            df_pares = asignar_pares(df)

            df_final = asignar_ascendente(
                df_pares,
                df
            )

        st.success("La estructura de tu evaluación está lista 🚀")

        st.dataframe(df_final)

        # ----------------------------------------
        # EXPORTAR EXCEL
        # ----------------------------------------

        output = BytesIO()

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            df_final.to_excel(
                writer,
                index=False,
                sheet_name="Estrucutra evaluación"
            )

        output.seek(0)

        st.download_button(
            label="📥 Descargar Excel",
            data=output,
            file_name="evaluaciones_desempeno.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
