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

st.title("🤖 Lia by Buk")
st.subheader("Asignador Inteligente de Evaluadores")

# ------------------------------------------------
# SIDEBAR
# ------------------------------------------------

st.sidebar.header("⚙️ Configuración")

tipo_cruce = st.sidebar.selectbox(
    "Tipo de asignación",
    ["Área", "Cargo"]
)

cantidad_pares = st.sidebar.number_input(
    "Cantidad de pares",
    min_value=1,
    max_value=20,
    value=2
)

excluir_mismo_jefe = st.sidebar.checkbox(
    "Excluir mismo supervisor",
    value=True
)

# ------------------------------------------------
# SUBIR ARCHIVO
# ------------------------------------------------

archivo = st.file_uploader(
    "📂 Sube archivo Excel",
    type=["xlsx"]
)

# ------------------------------------------------
# PROCESAMIENTO
# ------------------------------------------------

if archivo is not None:

    try:

        df = pd.read_excel(
            archivo,
            engine="openpyxl"
        )

        st.success("Archivo cargado correctamente ✅")

        st.subheader("📊 Vista previa")
        st.dataframe(df)

        # ----------------------------------------
        # VALIDAR COLUMNAS
        # ----------------------------------------

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

        # ----------------------------------------
        # FUNCIÓN PARES
        # ----------------------------------------

        def asignar_pares(df):

            resultados = []

            for _, persona in df.iterrows():

                cedula = persona["Cedula"]
                nombre = persona["Nombre Completo"]
                cargo = persona["Cargo"]
                area = persona["Área"]
                supervisor = persona["Cedula Supervisor"]

                candidatos = df.copy()

                # Evitar autoevaluación
                candidatos = candidatos[
                    candidatos["Cedula"] != cedula
                ]

                # Filtro principal
                if tipo_cruce == "Área":

                    candidatos = candidatos[
                        candidatos["Área"] == area
                    ]

                else:

                    candidatos = candidatos[
                        candidatos["Cargo"] == cargo
                    ]

                # Excluir mismo supervisor
                if excluir_mismo_jefe:

                    candidatos = candidatos[
                        candidatos["Cedula Supervisor"] != supervisor
                    ]

                # Aleatorizar
                candidatos = candidatos.sample(
                    frac=1
                )

                seleccionados = candidatos.head(
                    cantidad_pares
                )

                evaluadores = seleccionados[
                    "Cedula"
                ].tolist()

                nombres = seleccionados[
                    "Nombre Completo"
                ].tolist()

                # Completar vacíos
                while len(evaluadores) < cantidad_pares:

                    evaluadores.append("")
                    nombres.append("")

                fila = {
                    "Cedula": cedula,
                    "Nombre Completo": nombre,
                    "Cargo": cargo,
                    "Área": area,
                    "Cedula Supervisor": supervisor
                }

                # Crear columnas dinámicas
                for i in range(cantidad_pares):

                    fila[f"Par_{i+1}_Cedula"] = evaluadores[i]

                    fila[f"Par_{i+1}_Nombre"] = nombres[i]

                resultados.append(fila)

            return pd.DataFrame(resultados)

        # ----------------------------------------
        # FUNCIÓN ASCENDENTE
        # ----------------------------------------

        def asignar_ascendente(
            df_resultado,
            df_original
        ):

            mapa_jefes = df_original[
                [
                    "Cedula",
                    "Nombre Completo"
                ]
            ].rename(
                columns={
                    "Cedula": "Cedula Supervisor",
                    "Nombre Completo": "Nombre Supervisor"
                }
            )

            df_resultado = df_resultado.merge(
                mapa_jefes,
                on="Cedula Supervisor",
                how="left"
            )

            df_resultado[
                "Evaluador_Ascendente"
            ] = df_resultado[
                "Cedula Supervisor"
            ]

            df_resultado[
                "Nombre_Ascendente"
            ] = df_resultado[
                "Nombre Supervisor"
            ]

            return df_resultado

        # ----------------------------------------
        # BOTÓN
        # ----------------------------------------

        if st.button("✨ Generar Evaluaciones"):

            with st.spinner(
                "Generando evaluaciones..."
            ):

                df_pares = asignar_pares(df)

                df_final = asignar_ascendente(
                    df_pares,
                    df
                )

            st.success(
                "Evaluaciones generadas 🚀"
            )

            st.dataframe(df_final)

            # ------------------------------------
            # EXPORTAR
            # ------------------------------------

            output = BytesIO()

            with pd.ExcelWriter(
                output,
                engine="openpyxl"
            ) as writer:

                df_final.to_excel(
                    writer,
                    index=False,
                    sheet_name="Evaluaciones"
                )

            output.seek(0)

            st.download_button(
                label="📥 Descargar Excel",
                data=output,
                file_name="evaluaciones.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:

        st.error("Ocurrió un error ❌")
        st.code(str(e))
