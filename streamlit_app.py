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

        def asignar_ascendente(df_resultado, df_original):

            # Crear columnas vacías
            df_resultado["Evaluadores Ascendentes"] = ""
            df_resultado["Nombres Ascendentes"] = ""

            # Obtener supervisores únicos
            supervisores = df_original[
                "Cedula Supervisor"
            ].dropna().unique()

            for supervisor in supervisores:

                # Buscar colaboradores del supervisor
                equipo = df_original[
                    df_original["Cedula Supervisor"] == supervisor
                ]

                ids_equipo = equipo[
                    "Cedula"
                ].astype(str).tolist()

                nombres_equipo = equipo[
                    "Nombre Completo"
                ].tolist()

                # Convertir a texto separado por coma
                ids_texto = ", ".join(ids_equipo)

                nombres_texto = ", ".join(nombres_equipo)

                # Asignar SOLO al supervisor
                df_resultado.loc[
                    df_resultado["Cedula"] == supervisor,
                    "Evaluadores Ascendentes"
                ] = ids_texto

                df_resultado.loc[
                    df_resultado["Cedula"] == supervisor,
                    "Nombres Ascendentes"
                ] = nombres_texto

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
            # RENOMBRAR COLUMNAS FINALES
            # ------------------------------------

            df_final = df_final.rename(
                columns={

                    "Cedula": "Número de Documento",

                    "Nombre Completo": "Nombre Colaborador",

                    "Cedula Supervisor": "Evaluador descendente",

                    "Par_1_Cedula": "Evaluador paralelo 1",

                    "Par_2_Cedula": "Evaluador paralelo 2",

                    "Evaluadores Ascendentes": "Evaluador ascendente",

        
                }
            )
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
