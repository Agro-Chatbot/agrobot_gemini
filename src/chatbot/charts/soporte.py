from .errors import ChartError
from .filters import _FILTER_PROPERTIES, _apply_filters, _require_column
from .aggregate import _require_numeric
from .style import CHART_PALETTE, _new_figure


_GRUPOS_VALIDOS = ("Lote", "Campo", "Recurso")


def soporte_animal(df, filter_col=None, filter_val=None,
                   date_from=None, date_to=None, racion_kg_dia=8.0, filters=None,
                   group_by="Lote", n_ev=None):
    if racion_kg_dia <= 0:
        raise ChartError("racion_kg_dia debe ser mayor que cero.")
    if group_by not in _GRUPOS_VALIDOS:
        raise ChartError(
            f"group_by inválido: '{group_by}'. Valores admitidos: {', '.join(_GRUPOS_VALIDOS)}."
        )
    if n_ev is not None and n_ev <= 0:
        raise ChartError("n_ev debe ser mayor que cero.")

    df = _apply_filters(df, filter_col, filter_val, date_from, date_to, filters)
    _require_column(df, "Kg MS ha/día")
    _require_column(df, "Superficie ha")
    _require_numeric(df, "Kg MS ha/día")
    _require_numeric(df, "Superficie ha")
    _require_column(df, "Lote")
    if group_by != "Lote":
        _require_column(df, group_by)

    # Paso 1: agregar por (Lote, group_by) (media de tasa, max de superficie) para no
    # duplicar hectáreas de lotes con más de un registro de Superficie ha. El nombre de
    # Lote no es único entre Campo/Recurso en el dataset real, así que la clave de
    # agrupación debe incluir group_by cuando no es "Lote" — de lo contrario filas de
    # campos/recursos distintos con el mismo nombre de Lote se funden entre sí.
    group_keys = ["Lote"] if group_by == "Lote" else ["Lote", group_by]
    agg_kwargs = {
        "tasa_media": ("Kg MS ha/día", lambda s: s.mean(skipna=True)),
        "superficie": ("Superficie ha", "max"),
    }

    por_lote = df.groupby(group_keys).agg(**agg_kwargs)
    if len(por_lote) == 0:
        raise ChartError("El subconjunto resultante está vacío. Verificá los filtros aplicados.")

    por_lote["ms_disponible"] = por_lote["tasa_media"] * por_lote["superficie"]

    # Paso 2: sumar por el group_by pedido (Lote = sin cambios; Campo/Recurso = sumar
    # superficie y ms_disponible de los lotes agregados y recalcular la tasa media ponderada).
    if group_by == "Lote":
        grouped = por_lote[["tasa_media", "superficie", "ms_disponible"]].copy()
    else:
        grouped = por_lote.groupby(level=group_by).agg(
            superficie=("superficie", "sum"),
            ms_disponible=("ms_disponible", "sum"),
        )
        grouped["tasa_media"] = grouped["ms_disponible"] / grouped["superficie"]
        grouped = grouped[["tasa_media", "superficie", "ms_disponible"]]

    grouped["ev_soportados"] = grouped["ms_disponible"] / racion_kg_dia
    grouped["ev_por_ha"] = grouped["ev_soportados"] / grouped["superficie"]
    if n_ev is not None:
        grouped["ha_requeridas"] = n_ev * racion_kg_dia / grouped["tasa_media"]

    fig, ax = _new_figure((8, 5))
    grouped["ev_soportados"].plot.bar(ax=ax, color=CHART_PALETTE)
    ax.set_xlabel(group_by)
    ax.set_ylabel("EV soportados")
    ax.set_title(f"Capacidad de carga (EV soportados) por {group_by}")
    fig.tight_layout()

    ev_total = grouped["ev_soportados"].sum()
    sup_total = grouped["superficie"].sum()
    ms_total = grouped["ms_disponible"].sum()
    tasa_media_pond = ms_total / sup_total if sup_total > 0 else float("nan")
    ev_ha_pond = ev_total / sup_total if sup_total > 0 else float("nan")

    resumen_lineas = [
        f"Ración usada: {racion_kg_dia} kg MS/día por EV",
        f"Agrupado por: {group_by}",
        f"Tasa media ponderada del conjunto: {tasa_media_pond:.2f} kg MS/ha/día",
        f"Superficie total: {sup_total:.1f} ha",
        f"MS disponible total: {ms_total:.1f} kg MS/día",
        f"EV total del conjunto: {ev_total:.1f}",
        f"EV/ha promedio ponderado: {ev_ha_pond:.2f}",
    ]

    columnas_detalle = ["tasa_media", "superficie", "ms_disponible", "ev_soportados", "ev_por_ha"]
    if n_ev is not None:
        ha_requeridas_total = (
            n_ev * racion_kg_dia / tasa_media_pond if tasa_media_pond > 0 else float("nan")
        )
        resumen_lineas.append(
            f"Hectáreas requeridas para {n_ev} EV: {ha_requeridas_total:.1f} ha"
        )
        columnas_detalle.append("ha_requeridas")

    resumen = (
        "\n".join(resumen_lineas) + "\n\n"
        f"Detalle por {group_by.lower()}:\n{grouped[columnas_detalle].to_string()}\n\n"
        "NOTA: Estimación de capacidad potencial máxima. "
        "No descuenta pérdidas por pisoteo ni calidad nutritiva."
    )
    return fig, resumen


SOPORTE_ANIMAL_SCHEMA = {
    "name": "soporte_animal",
    "description": (
        "Estima la capacidad de carga (EV soportados y EV/ha) para un subconjunto "
        "de lotes en un período, usando tasa de crecimiento de MS y superficie del CSV. "
        "Ración default: 8 kg MS/día por EV (vaca 400 kg). "
        "Resultado: estimación de capacidad potencial máxima "
        "(no descuenta pérdidas por pisoteo ni calidad nutritiva)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            **_FILTER_PROPERTIES,
            "racion_kg_dia": {
                "type": "number",
                "description": "Consumo diario por EV en kg MS/día (default 8.0).",
                "exclusiveMinimum": 0,
            },
            "group_by": {
                "type": "string",
                "enum": ["Lote", "Campo", "Recurso"],
                "description": (
                    "Columna por la que agrupar el resultado (default 'Lote'). Para "
                    "'Campo' o 'Recurso' primero se agrega por Lote (media de tasa, max de "
                    "Superficie ha) para no duplicar hectáreas de lotes con más de un "
                    "registro de superficie, y luego se suma por el grupo pedido."
                ),
            },
            "n_ev": {
                "type": "number",
                "description": (
                    "Cantidad de EV (equivalente vaca) para calcular la superficie "
                    "requerida: ha_requeridas = n_ev × racion_kg_dia / tasa_media, por "
                    "grupo y para el conjunto. Solo afecta el resumen de texto: el gráfico "
                    "sigue mostrando EV soportados."
                ),
                "exclusiveMinimum": 0,
            },
        },
        "required": [],
    },
}
