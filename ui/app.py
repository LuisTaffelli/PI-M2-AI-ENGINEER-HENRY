"""Ejecutar con python -m streamlit run ui/app.py desde la raíz."""
import csv
import json
from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nubbix_assist.bootstrap import inspect_heading_document, make_retriever, language_model
from nubbix_assist.generation.prompts import load_prompt
from nubbix_assist.llm.service import CallBudget
from nubbix_assist.query.service import answer_retrieval
from nubbix_assist.ui.reader import render_result


@st.cache_data
def examples():
    folder = ROOT / "evals/resultados"
    training = json.loads((folder / "2026-11-22-ejemplo-q09.json").read_text())
    with (folder / "2026-11-22-generacion-golden-revisado.csv").open(encoding="utf-8") as handle:
        refusal = next(row for row in csv.DictReader(handle)
                       if row["pregunta_id"] == "q27" and row["estrategia"] == "headings_v1")
    catalog = {}
    for citation in training["chunks_related"]:
        for chunk in inspect_heading_document(Path(citation["source"]), project_root=ROOT):
            catalog[chunk.chunk_id] = chunk
    return {
        "Crédito de capacitación": (training["user_question"], training["system_answer"],
                                   [catalog[c["chunk_id"]] for c in training["chunks_related"]]),
        "Cupos de guardería": (refusal["pregunta"], refusal["respuesta"], []),
    }


def live_result():
    names = {"headings_v1": "Secciones H2", "words_v1": "Ventanas de 80 palabras",
             "section_words_v1": "Ventanas dentro de secciones"}
    builds = sorted(p.parent.name for p in (ROOT / "data/indexes").glob("*/manifest.json"))
    if not builds:
        st.info("Construí un índice con python ingest/run.py build --strategy headings_v1 para hacer consultas.")
        return
    with st.form("consultar"):
        question = st.text_area("Tu pregunta", placeholder="¿Qué beneficio cubre libros de tecnología?")
        with st.expander("Opciones de búsqueda"):
            build = st.selectbox("Índice", builds, format_func=lambda b: names.get(b.split("-")[0], b) + " · " + b[-8:])
            multi = st.checkbox("Multi-query")
            rerank = st.checkbox("Re-ranking local")
        st.caption("Buscar pasajes funciona en tu máquina. Generar una respuesta usa hasta dos llamadas al modelo del .env.")
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


st.set_page_config(page_title="Nubbix Assist", page_icon="📖")
st.html((ROOT / "ui/reader.css"))
st.title("Nubbix Assist")
st.caption("Consultas sobre Recursos Humanos, Finanzas y Tecnología.")
mode = st.segmented_control("Modo", ["Ejemplos evaluados", "Nueva consulta"], default="Ejemplos evaluados",
                            required=True, label_visibility="collapsed")
try:
    if mode == "Ejemplos evaluados":
        saved = examples()
        example = st.selectbox("Respuesta guardada", list(saved))
        question, text, chunks = saved[example]
        st.subheader(question)
        st.html(render_result(ROOT, text, chunks))
    else:
        live_result()
except (OSError, ValueError, RuntimeError, KeyError) as exc:
    st.error(str(exc))
