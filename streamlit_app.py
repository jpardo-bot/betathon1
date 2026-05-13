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
    "Tipo de asignación de pares",
    ["Área", "Cargo"]
)

cantidad_pares = st.sidebar.number_input(
    "Cantidad de pares por colaborador",
    min_value=1,
    max_value=20,
    value=2
)

excluir_mismo_jefe = st.sidebar.checkbox(
    "Excluir personas del mismo supervisor",
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

        # ----------------------------------------
        # LEER EXCEL
        # ----------------------------------------

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

                # Filtrar por tipo
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

                # Seleccionar cantidad requerida
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

                # Crear fila base
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

            # ----------------------------------------
            # IDENTIFICAR SUPERVISORES
            # ----------------------------------------

            supervisores = df_original[
                "Cedula Supervisor"
            ].dropna().unique()

            resultados_ascendentes = []

            # ----------------------------------------
            # RECORRER SUPERVISORES
            # ----------------------------------------

            for supervisor in supervisores:

                # Buscar información supervisor
                info_supervisor = df_original[
                    df_original["Cedula"] == supervisor
                ]

                if info_supervisor.empty:
                    continue

                nombre_supervisor = info_supervisor[
                    "Nombre Completo"
                ].values[0]

                # Buscar equipo
                equipo = df_original[
                    df_original["Cedula Supervisor"] == supervisor
                ]

                evaluadores_ids = equipo[
                    "Cedula"
                ].tolist()

                evaluadores_nombres = equipo[
                    "Nombre Completo"
                ].tolist()

                fila = {
                    "Cedula Supervisor": supervisor,
                    "Nombre Supervisor": nombre_supervisor
                }

                # Crear columnas dinámicas
                for i in range(len(evaluadores_ids)):

                    fila[f"Ascendente_{i+1}_Cedula"] = \
                        evaluadores_ids[i]

                    fila[f"Ascendente_{i+1}_Nombre"] = \
                        evaluadores_nombres[i]

                resultados_ascendentes.append(fila)

            # Crear dataframe
            df_ascendentes = pd.DataFrame(
                resultados_ascendentes
            )

            # Unir resultado
            df_final = df_resultado.merge(
                df_ascendentes,
                on="Cedula Supervisor",
                how="left"
            )

            return df_final

        # ----------------------------------------
        # BOTÓN GENERAR
        # ----------------------------------------

        if st.button("✨ Generar Evaluaciones"):

            with st.spinner(
                "Generando evaluaciones..."
            ):

                # Generar pares
                df_pares = asignar_pares(df)

                # Generar ascendente
                df_final = asignar_ascendente(
                    df_pares,
                    df
                )

            st.success(
                "Evaluaciones generadas correctamente 🚀"
            )

            st.subheader("📋 Resultado Final")

            st.dataframe(df_final)

            # ------------------------------------
            # EXPORTAR EXCEL
            # ------------------------------------

            excel_buffer = BytesIO()

            df_final.to_excel(
                excel_buffer,
                index=False,
                engine="openpyxl"
            )

            excel_buffer.seek(0)

            st.download_button(
                label="📥 Descargar Excel",
                data=excel_buffer,
                file_name="evaluaciones_desempeno.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:

        st.error("Ocurrió un error ❌")

        st.code(str(e))
