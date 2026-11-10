"""Tests de contrato para chatbot.prompt (TECH-159): el paquete de secciones debe producir
el mismo texto que el _system_prompt monolítico anterior, sin cambio de comportamiento.
"""

from chatbot import config, data, prompt
from chatbot.agent import _system_prompt


def test_system_prompt_contiene_los_bloques_esperados():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "MI_ESQUEMA" in texto
    assert "Columnas derivadas" in texto
    assert "Parámetros de filtrado" in texto
    assert "soporte_animal" in texto


def test_orden_de_secciones_no_vacias_coincide_con_secciones():
    texto = prompt.system_prompt("MI_ESQUEMA")

    marcador_por_seccion = {
        "base": "MI_ESQUEMA",
        "temporal": "Columnas derivadas",
        "valores": "Resolución de valores categóricos",
        "filtros": "Parámetros de filtrado",
        "recursos": None,
        "graficos": None,
        "soporte": "## Tool soporte_animal",
        "ganaderia": None,
        "clima": "Lluvia y variables climáticas",
        "limites": None,
    }

    posiciones = []
    for nombre in prompt.SECCIONES:
        marcador = marcador_por_seccion[nombre]
        if marcador is None:
            continue
        posiciones.append(texto.index(marcador))

    assert posiciones == sorted(posiciones)


def test_secciones_vacias_no_dejan_lineas_en_blanco_de_mas():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "\n\n\n" not in texto


def test_agent_system_prompt_delega_en_prompt_package():
    schema = "Columna1: int64\nColumna2: object"

    assert _system_prompt(schema) == prompt.system_prompt(schema)


def test_temporal_resuelve_expresiones_relativas_contra_ultima_fecha_con_datos():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "última fecha con datos" in texto
    assert "NUNCA contra la fecha real del sistema" in texto


def test_temporal_declara_periodo_efectivamente_usado():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "date_from" in texto and "date_to" in texto
    assert "efectivamente usado" in texto


def test_temporal_nombra_campana_parcial():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "campaña parcial" in texto
    assert "Cobertura" in texto


def test_temporal_ultimos_n_anios_usa_rango_explicito():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "últimos N años" in texto
    assert "rango explícito" in texto


def test_temporal_salida_del_invierno_no_es_sinonimo_de_primavera():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "salida del invierno" in texto
    assert "08-01" in texto and "09-30" in texto
    assert "Estacion=Primavera" in texto


def test_ganaderia_contiene_equivalencias_ev_por_categoria():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "1,0 EV" in texto
    assert "0,7 EV" in texto
    assert "0,8 EV" in texto
    assert "0,5 EV" in texto
    assert "1,3 EV" in texto


def test_ganaderia_contiene_regla_de_raciones_acumuladas():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "EV soportados × N días" in texto
    assert "No vuelvas a dividir por la ración diaria" in texto


def test_ganaderia_contiene_las_salvedades_de_dominio():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "capacidad potencial máxima" in texto
    assert "no descuenta pisoteo, rechazo ni" in texto
    assert "no decide descanso ni reserva/reparto a heno o silaje" in texto
    assert "no es representativo del comportamiento típico del lote" in texto
    assert "Perennes y verdeos anuales no son comparables" in texto


def test_valores_no_negar_existencia_sin_chart_error():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "No negar la existencia de un valor sin haberlo intentado" in texto
    assert "ChartError" in texto


def test_valores_mapea_coloquialismos_y_desambigua_candidatos():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "Mapeá coloquialismos al valor real" in texto
    assert "alfalfa" in texto and "Pastura base alfalfa" in texto
    assert "festuca" in texto
    assert "Pastura de festuca" in texto and "Pastura de agropiro y festuca" in texto
    assert "listá los candidatos y pedí cuál usar" in texto


def test_valores_sugiere_hasta_tres_similares_ante_valor_inexistente():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "sugerí hasta 3 valores similares" in texto


def test_valores_muestra_no_exhaustiva_no_es_lista_completa():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "no exhaustivas" in texto
    assert "no son la lista completa de valores" in texto


def test_seccion_limites_cubre_reglas():
    texto = prompt.system_prompt("MI_ESQUEMA")

    # Regla 1: nunca presentar un resultado parcial/sustituto como si respondiera lo pedido.
    assert "Nunca presentes un resultado parcial o un sustituto" in texto
    # Regla 2: filtro no aplicado (o aplicado solo en parte) se declara antes de interpretar.
    assert "Si un filtro pedido no se aplicó" in texto
    # Regla 3: no prometer análisis que las tools no pueden ejecutar (criterio de aceptación
    # literal: "no prometas").
    assert "no prometas" in texto.lower()
    # Regla 4: placeholder sin valor concreto -> pedir el dato antes de graficar, sin tool call.
    assert "placeholder sin valor concreto" in texto
    assert "sin llamar a ninguna tool" in texto
    # Regla 5: date_from/date_to como intervalo continuo único (no mes recurrente ni ventanas
    # discontinuas).
    assert "un único intervalo continuo" in texto
    assert "nunca un mes recurrente ni dos ventanas discontinuas" in texto
    # Regla 6: declarar las dimensiones no cubiertas, no solo las cubiertas.
    assert "las dimensiones de la pregunta que NO se pudieron cubrir" in texto
    # Regla 7: no afirmar ni negar existencia de valores sin evidencia.
    assert "No afirmes ni niegues la existencia de valores del dataset sin evidencia" in texto


def test_clima_nombra_los_dos_datasets_y_la_lluvia_disponible():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "`tasas`" in texto and "`precipitaciones`" in texto
    assert "Precipitación mm" in texto
    assert "no tiene** columnas de lluvia" not in texto


def test_clima_lluvia_se_agrega_con_sum_y_2026_es_parcial():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert 'agg="sum"' in texto
    assert "2026 es un año parcial" in texto
    assert "2026-08-26" in texto


def test_clima_expresiones_relativas_contra_rango_del_dataset_elegido():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "contra el rango del dataset elegido" in texto


def test_clima_temperatura_ausente_sin_tool_call_ni_proxy():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "temperatura no existe" in texto
    assert "**sin tool call**" in texto
    assert "no uses un proxy" in texto


def test_clima_prohibe_atribucion_causal_y_cruce_en_una_tool_call():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "No atribuyas causalidad" in texto
    assert "dos gráficos" in texto


def test_clima_atribucion_de_terceros_no_es_hallazgo_de_datos():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "nunca la presentes" in texto
    assert "un hallazgo de los datos" in texto


def test_recursos_enumera_los_5_valores_de_pasturas_implantadas():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "pasturas implantadas" in texto
    for valor in (
        "Pastura consociada",
        "Pastura de festuca",
        "Pastura de agropiro",
        "Pastura de agropiro y festuca",
        "Pastura base alfalfa",
    ):
        assert valor in texto


def test_recursos_enumera_los_7_valores_de_verdeos():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "verdeos" in texto
    for valor in (
        "Verdeo de invierno",
        "Verdeo de avena",
        "Verdeo de maiz",
        "Verdeo de triticale",
        "Verdeo de sorgo",
        "Verdeo de raigras",
        "Verdeo de verano",
    ):
        assert valor in texto


def test_recursos_promociones_de_raigras_no_es_parte_de_verdeos():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "Promocion de raigras" in texto
    assert "Promocion intensiva de raigras" in texto

    inicio = texto.index('**"verdeos"**')
    fin = texto.index("**\"promociones de raigrás\"**")
    bloque_verdeos = texto[inicio:fin]

    assert "Promocion de raigras" not in bloque_verdeos
    assert "Promocion intensiva de raigras" not in bloque_verdeos
    assert "no forma parte de \"verdeos\"" in texto


def test_filtros_regla_de_comparacion_multivalor():
    texto = prompt.system_prompt("MI_ESQUEMA")

    assert "Regla de comparación multivalor" in texto
    assert "Nunca filtres por uno solo de los valores comparados" in texto


def test_esquema_real_incluye_todos_los_valores_de_recurso_y_campo():
    df = data.load_csv(config.CSV_PATH)
    schema = data.schema_summary(df)
    texto = prompt.system_prompt(schema)

    for valor in df["Recurso"].astype(str).unique():
        assert valor in texto, f"Valor de Recurso ausente en el prompt: {valor!r}"
    for valor in df["Campo"].astype(str).unique():
        assert valor in texto, f"Valor de Campo ausente en el prompt: {valor!r}"
