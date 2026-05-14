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

st.sidebar.image(
    "logo.png",
    width=180
)

st.title("🤖 Lia by Buk")

# ------------------------------------------------
# SIDEBAR
# ------------------------------------------------

st.sidebar.header("⚙️ Configuración")

tipo_cruce = st.sidebar.selectbox(
    "Tipo de asignación de pares",
    ["Área", "Cargo"]
)

cantidad_pares = st.sidebar.number_input(
    "Cantidad de evaluadores paralelos",
    min_value=1,
    max_value=10,
    value=2
)

cantidad_ascendentes = st.sidebar.number_input(
    "Cantidad de evaluadores ascendentes",
    min_value=1,
    max_value=10,
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
    "📂 Sube tu archivo Excel",
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

        st.subheader("📊 Vista previa del archivo")

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
                f"Faltan columnas obligatorias: {faltantes}"
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

                # Filtrar por área o cargo
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
                    frac=1,
                    random_state=random.randint(1, 100000)
                )

                # Seleccionar pares
                seleccionados = candidatos.head(
                    cantidad_pares
                )

                evaluadores = seleccionados[
                    "Cedula"
                ].tolist()

                # Completar vacíos
                while len(evaluadores) < cantidad_pares:

                    evaluadores.append("")

                # Crear fila
                fila = {
                    "Cedula": cedula,
                    "Nombre Completo": nombre,
                    "Cedula Supervisor": supervisor
                }

                # Crear columnas dinámicas
                for i in range(cantidad_pares):

                    fila[f"Par_{i+1}"] = evaluadores[i]

                resultados.append(fila)

            return pd.DataFrame(resultados)

        # ----------------------------------------
        # FUNCIÓN ASCENDENTE
        # ----------------------------------------

        def asignar_ascendente(
            df_resultado,
            df_original
        ):

            # Obtener supervisores únicos
            supervisores = df_original[
                "Cedula Supervisor"
            ].dropna().unique()

            # Recorrer supervisores
            for supervisor in supervisores:

                # Buscar equipo
                equipo = df_original[
                    df_original["Cedula Supervisor"] == supervisor
                ]

                # Aleatorizar equipo
                equipo = equipo.sample(
                    frac=1,
                    random_state=random.randint(1, 100000)
                )

                # Seleccionar cantidad requerida
                equipo = equipo.head(
                    cantidad_ascendentes
                )

                ids_equipo = equipo[
                    "Cedula"
                ].tolist()

                # Completar vacíos
                while len(ids_equipo) < cantidad_ascendentes:

                    ids_equipo.append("")

                # Crear columnas dinámicas
                for i in range(cantidad_ascendentes):

                    columna = f"Ascendente_{i+1}"

                    df_resultado.loc[
                        df_resultado["Cedula"] == supervisor,
                        columna
                    ] = ids_equipo[i]

            return df_resultado

        # ----------------------------------------
        # BOTÓN GENERAR
        # ----------------------------------------

        if st.button("✨ Generar Evaluaciones"):

            with st.spinner(
                "Generando evaluaciones..."
            ):

                # Generar pares
                df_pares = asignar_pares(df)

                # Generar ascendentes
                df_final = asignar_ascendente(
                    df_pares,
                    df
                )

            # ------------------------------------
            # RENOMBRAR COLUMNAS
            # ------------------------------------

            columnas_rename = {

                "Cedula": "Número de Documento",

                "Nombre Completo": "Nombre Colaborador",

                "Cedula Supervisor": "Evaluador Descendente"

            }

            # Pares
            for i in range(cantidad_pares):

                columnas_rename[
                    f"Par_{i+1}"
                ] = f"Evaluador Paralelo {i+1}"

            # Ascendentes
            for i in range(cantidad_ascendentes):

                columnas_rename[
                    f"Ascendente_{i+1}"
                ] = f"Evaluador Ascendente {i+1}"

            # Aplicar rename
            df_final = df_final.rename(
                columns=columnas_rename
            )

            # ------------------------------------
            # COLUMNAS FINALES
            # ------------------------------------

            columnas_finales = [

                "Número de Documento",

                "Nombre Colaborador",

                "Evaluador Descendente"
            ]

            # Agregar paralelos
            for i in range(cantidad_pares):

                columnas_finales.append(
                    f"Evaluador Paralelo {i+1}"
                )

            # Agregar ascendentes
            for i in range(cantidad_ascendentes):

                columnas_finales.append(
                    f"Evaluador Ascendente {i+1}"
                )

            # Filtrar columnas existentes
            columnas_finales = [
                col for col in columnas_finales
                if col in df_final.columns
            ]

            df_final = df_final[
                columnas_finales
            ]

            # ------------------------------------
            # MOSTRAR RESULTADO
            # ------------------------------------

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
