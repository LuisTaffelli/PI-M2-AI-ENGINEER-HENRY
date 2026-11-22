"""Lector HTML de citas. El texto del modelo y del corpus se trata como texto plano."""
from html import escape
from pathlib import Path
import re

from nubbix_assist.ingestion.markdown_loader import load_markdown


def source_view(root, chunk, number):
    document = load_markdown(Path(chunk.source), project_root=root)
    start, end = chunk.start_char, chunk.end_char
    raw = document.raw_text
    if document.source_sha256 != chunk.source_sha256 or raw[start:end] != chunk.body:
        raise ValueError("El documento cambió desde la ingesta. Reconstruí su índice para leer la cita.")
    key = escape(chunk.chunk_id, quote=True)
    section = escape(" · ".join(chunk.section_paths))
    label = escape(document.title.removesuffix(" - Nubbix"))
    link = f'<a class="source-link" href="#pasaje-{key}"><b>[{number}]</b> {label} · {section}</a>'
    excerpt = escape(chunk.body)
    article = f'''<section class="source-view" id="pasaje-{key}" tabindex="-1">
      <div class="source-meta">{label} · Cita {number}</div><h3>{section}</h3>
      <blockquote>{excerpt}</blockquote>
      <details><summary>Leer el documento completo</summary>
        <p class="source-meta">{escape(chunk.source)} · caracteres {start}–{end}</p>
        <pre>{escape(raw[:start])}<mark>{excerpt}</mark>{escape(raw[end:])}</pre>
      </details><a href="#resultado">Volver al resultado</a></section>'''
    return link, article


def render_result(root, text, chunks, *, heading="Respuesta"):
    numbers = {chunk.chunk_id: n for n, chunk in enumerate(chunks, 1)}
    def reference(match):
        key = match[1]
        n = numbers.get(key)
        if n is None:
            return match[0]
        return f'<a class="inline-cite" aria-label="Abrir cita {n}" href="#pasaje-{key}">[{n}]</a>'

    answer = re.sub(r"\[([0-9a-f]{64})\]", reference, escape(text))
    views = [source_view(root, chunk, n) for n, chunk in enumerate(chunks, 1)]
    links = "".join(link for link, _ in views)
    caption = '<h3 class="source-meta">Fuentes</h3>' if links else ""
    return f'''<div class="nubbix-reader" id="resultado">
      <h2>{escape(heading)}</h2><p class="answer">{answer}</p>{caption}
      <nav aria-label="Fuentes citadas">{links}</nav>
      {"".join(article for _, article in views)}</div>'''
