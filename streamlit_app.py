def asignar_pares(df):

    resultados = []

    for _, persona in df.iterrows():

        cedula = persona["Cedula"]
        nombre_completo = persona["Nombre Completo"]
        area = persona["Área"]
        cargo = persona["Cargo"]
        cedula_supervisor = persona["Cedula Supervisor"]

        candidatos = df.copy()

        # Evitar autoevaluación
        candidatos = candidatos[
            candidatos["Cedula"] != cedula
        ]

        # Filtro principal
        if tipo_cruce == "Area":

            candidatos = candidatos[
                candidatos["Área"] == area
            ]

        else:

            candidatos = candidatos[
                candidatos["Cargo"] == cargo
            ]

        # Excluir mismo jefe
        if excluir_mismo_jefe:

            candidatos = candidatos[
                candidatos["Cedula Supervisor"] != cedula_supervisor
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
            "Nombre Completo"
        ].tolist()

        # Completar vacíos
        while len(evaluadores) < cantidad_pares:

            evaluadores.append("")
            nombres.append("")

        fila = {
            "Cedula": cedula,
            "Nombre Completo": nombre_completo,
            "Cargo": cargo,
            "Área": area,
            "Cedula Supervisor": cedula_supervisor
        }

        # Crear columnas dinámicas
        for i in range(cantidad_pares):

            fila[f"Par_{i+1}_Cedula"] = evaluadores[i]
            fila[f"Par_{i+1}_Nombre"] = nombres[i]

        resultados.append(fila)

    return pd.DataFrame(resultados)

def asignar_ascendente(df_resultado, df_original):

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

    df_resultado["Evaluador_Ascendente"] = \
        df_resultado["Cedula Supervisor"]

    df_resultado["Nombre_Ascendente"] = \
        df_resultado["Nombre Supervisor"]

    return df_resultado
