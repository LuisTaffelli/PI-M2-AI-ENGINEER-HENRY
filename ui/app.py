"""Ejecutar con python -m streamlit run ui/app.py desde la raíz."""
from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nubbix_assist.bootstrap import make_retriever, language_model
from nubbix_assist.generation.prompts import load_prompt
from nubbix_assist.llm.service import CallBudget
from nubbix_assist.query.service import answer_retrieval
from nubbix_assist.ui.examples import load_examples
from nubbix_assist.ui.reader import render_result

VERSIONS = {
    "headings_v1": (
        "Secciones H2",
        "Cada subtítulo de nivel 2 (H2) inicia un fragmento. Así, una política y las condiciones "
        "que aparecen bajo el mismo subtítulo se pueden recuperar juntas.",
    ),
    "words_v1": (
        "Ventanas de 80 palabras",
        "Recorre el documento en bloques de hasta 80 palabras. Dos bloques consecutivos comparten "
        "20 palabras. Un bloque puede cruzar de una sección a la siguiente.",
    ),
    "section_words_v1": (
        "Ventanas dentro de secciones",
        "Es el corte híbrido. Primero separa por H2. Si una sección supera las 80 palabras, "
        "la divide en ventanas que comparten 20 palabras. Cada ventana conserva su subtítulo.",
    ),
    "pilot": (
        "Piloto H2",
        "Es la primera respuesta guardada sobre el crédito de capacitación. Usa el mismo corte "
        "por secciones H2 que después se evaluó con las 27 preguntas.",
    ),
}
TOPICS = {
    "q01": "Licencia por matrimonio", "q02": "Días de examen", "q03": "Licencia por adopción",
    "q04": "Solicitud de vacaciones", "q05": "Gastos de trabajo en casa", "q06": "Trabajo desde el exterior",
    "q07": "Certificado por enfermedad", "q08": "Prepaga del grupo familiar", "q09": "Crédito de capacitación",
    "q10": "Acceso a Producción", "q11": "Renovación de notebooks", "q12": "Aplicaciones para MFA",
    "q13": "Contraseñas de Google Workspace", "q14": "Wi-Fi de un café", "q15": "Copias de la base de producción",
    "q16": "Plazos de soporte", "q17": "Baja de accesos", "q18": "Equipo dañado durante un viaje",
    "q19": "Viáticos para comidas", "q20": "Reintegros después del día 25", "q21": "Compra de licencias",
    "q22": "Presupuestos de software", "q23": "Recibo de sueldo", "q24": "Cursos ajenos a la función",
    "q25": "Bono por desempeño", "q26": "Diferencias en una factura", "q27": "Cupos de guardería",
}


@st.cache_data
def examples():
    return load_examples(ROOT)


def chunking_guide():
    entries = "".join(f"<dt>{label}</dt><dd>{description}</dd>" for label, description in VERSIONS.values())
    st.html(f"""
    <details class="chunking-guide">
      <summary>¿Qué significa cada versión de chunking?</summary>
      <p>El <i>chunking</i> define cómo se divide un documento en los fragmentos que el buscador
         puede recuperar y que después ves en las citas.</p>
      <dl>{entries}</dl>
      <p>Los ejemplos guardados comparan H2 y ventanas corridas. En «Nueva consulta» también podés probar
         el híbrido de 80 palabras. Al ensayar el híbrido con <strong>160 palabras</strong>, cada una
         de las 18 secciones del corpus entró en un solo fragmento.</p>
    </details>
    """)


def index_label(build):
    strategy = build.partition("-")[0]
    name = VERSIONS[strategy][0] if strategy in VERSIONS else build
    return f"{name} · {build[-8:]}"


def live_result():
    builds = sorted(p.parent.name for p in (ROOT / "data/indexes").glob("*/manifest.json"))
    if not builds:
        st.info("Construí un índice con python ingest/run.py build --strategy headings_v1 para hacer consultas.")
        return
    with st.form("consultar"):
        question = st.text_area("Tu pregunta", placeholder="¿Qué beneficio cubre libros de tecnología?")
        with st.expander("Opciones de búsqueda"):
            build = st.selectbox("Índice", builds, format_func=index_label)
            multi = st.checkbox("Multi-query")
            rerank = st.checkbox("Re-ranking local")
        st.caption("Buscar pasajes funciona en tu máquina. Generar una respuesta usa hasta dos llamadas al modelo del .env.")
        with st.container(horizontal=True):
            local = st.form_submit_button("Buscar pasajes")
            generate = st.form_submit_button("Generar respuesta", type="primary")
    if local or generate:
        st.session_state.pop("result", None)
        if not question.strip():
            st.warning("Escribí una pregunta para consultar.")
            return
        key = (build, rerank, multi)
        with st.spinner("Consultando el índice…"):
            if st.session_state.get("engine_key") != key:
                st.session_state.engine = make_retriever(ROOT, build, rerank=rerank, multi_query=multi)
                st.session_state.engine_key = key
            engine = st.session_state.engine
            trace = engine.retrieve(question.strip())
            if generate:
                model = language_model(ROOT, "GENERATOR", CallBudget(2))
                answer = answer_retrieval(ROOT, trace, model, load_prompt(ROOT, "generation")).answer
                chunks = [engine.build.catalog[c.chunk_id] for c in answer.chunks_related]
                result = render_result(ROOT, answer.system_answer, chunks)
            else:
                chunks = [hit.chunk for hit in trace.selected]
                result = render_result(ROOT, trace.question, chunks, heading="Pasajes recuperados")
            st.session_state.result = (question.strip() if generate else None, result)
    if "result" in st.session_state:
        asked, html = st.session_state.result
        if asked:
            st.subheader(asked)
        st.html(html)


st.set_page_config(page_title="Nubbix Assist", page_icon="📖", layout="wide")
st.html(ROOT / "ui/reader.css")
st.html(ROOT / "ui/cover.html", unsafe_allow_javascript=True)
try:
    with st.container(key="archive_controls"):
        modes, selection, version_picker = st.columns([1.1, 1.2, .85], vertical_alignment="bottom")
        mode = modes.segmented_control("Modo", ["Ejemplos evaluados", "Nueva consulta"],
                                      default="Ejemplos evaluados", required=True, label_visibility="collapsed")
        if mode == "Ejemplos evaluados":
            saved = examples()
            ids = list(saved)
            qid = selection.selectbox("Respuesta guardada", ids, index=ids.index("q09"),
                                      format_func=lambda key: TOPICS.get(key, saved[key].question))
            question = saved[qid]
            versions = list(question.versions)
            version = version_picker.selectbox("Versión", versions,
                                               index=versions.index("pilot") if "pilot" in versions else 0,
                                               format_func=lambda key: VERSIONS[key][0])
        chunking_guide()
    if mode == "Ejemplos evaluados":
        text, chunks = question.versions[version]
        st.subheader(question.question)
        st.html(render_result(ROOT, text, chunks))
    else:
        live_result()
except (OSError, ValueError, RuntimeError, KeyError) as exc:
    st.error(str(exc))

st.html("""
<footer class="archive-garden">
  <button type="button" class="cherry-tree" aria-label="Hacer llover pétalos" title="Hacer llover pétalos">
    <img src="./app/static/cerezo.webp" alt="" draggable="false">
  </button>
</footer>
""")
