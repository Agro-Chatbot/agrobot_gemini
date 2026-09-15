import io
import sys
import traceback

import matplotlib.pyplot as plt
import streamlit as st

from chatbot import config, ui_theme
from chatbot.agent import answer
from chatbot.charts import ChartError
from chatbot.data import load_csv, schema_summary

st.set_page_config(page_title="Chatbot de datos", page_icon="🌾", layout="centered")
st.markdown(ui_theme.THEME_CSS, unsafe_allow_html=True)
st.title("Chatbot de datos")


@st.cache_data
def _load():
    df = load_csv(config.CSV_PATH)
    return df, schema_summary(df)


try:
    df, schema = _load()
except FileNotFoundError:
    print(f"ERROR: CSV no encontrado: {config.CSV_PATH}", file=sys.stderr)
    st.error("No se pudo cargar el dataset. Verificá la configuración del servidor.")
    st.stop()
except Exception:
    traceback.print_exc(file=sys.stderr)
    st.error("Error al cargar el dataset. Contactá al administrador.")
    st.stop()

st.caption(f"Dataset: {config.CSV_PATH.name} — {len(df)} filas, {len(df.columns)} columnas")

if "history" not in st.session_state:
    st.session_state.history = []

for item in st.session_state.history:
    with st.chat_message("user"):
        st.write(item["query"])
    with st.chat_message("assistant"):
        if item["img_bytes"] is not None:
            st.image(item["img_bytes"], use_container_width=True)
        st.write(item["text"])

MAX_QUERY_LEN = 2000

if not st.session_state.history:
    with st.expander("Ejemplos de preguntas que podés hacer", expanded=True):
        st.markdown(
            "- ¿Cuál es la tasa de crecimiento promedio por tipo de recurso forrajero?\n"
            "- ¿Qué lotes tienen las mayores tasas de crecimiento promedio?\n"
            "- ¿Cómo se distribuyen las tasas de crecimiento en todo el establecimiento?\n"
            "- ¿Qué proporción de la superficie total corresponde a cada tipo de recurso?"
        )

query = st.chat_input("Preguntá algo sobre los datos...")
if query:
    query = query.strip()
    if not query:
        st.warning("El mensaje no puede estar vacío.")
    elif len(query) > MAX_QUERY_LEN:
        st.warning(f"El mensaje es demasiado largo ({len(query)} caracteres). El máximo es {MAX_QUERY_LEN}.")
    else:
        with st.chat_message("user"):
            st.write(query)
        with st.chat_message("assistant"):
            with st.spinner("Analizando..."):
                try:
                    fig, text = answer(query, df, schema)
                except ChartError:
                    traceback.print_exc(file=sys.stderr)
                    st.error("No se pudo generar el gráfico con los parámetros solicitados. Intentá reformular la pregunta.")
                except RuntimeError:
                    traceback.print_exc(file=sys.stderr)
                    st.error("Ocurrió un error al procesar tu consulta. Intentá de nuevo.")
                except Exception:
                    traceback.print_exc(file=sys.stderr)
                    st.error("Ocurrió un error inesperado. Intentá de nuevo.")
                else:
                    if fig is None:
                        st.write(text)
                        st.session_state.history.append({"query": query, "img_bytes": None, "text": text})
                    else:
                        try:
                            config.OUTPUT_DIR.mkdir(exist_ok=True)
                            fig.savefig(config.OUTPUT_DIR / "ultimo_grafico.png")
                            buf = io.BytesIO()
                            fig.savefig(buf, format="png")
                            img_bytes = buf.getvalue()
                            st.image(img_bytes, use_container_width=True)
                            st.write(text)
                            st.session_state.history.append({"query": query, "img_bytes": img_bytes, "text": text})
                        except Exception:
                            traceback.print_exc(file=sys.stderr)
                            st.error("Ocurrió un error inesperado. Intentá de nuevo.")
                        finally:
                            plt.close(fig)
