# ADR 0007 · Corte por secciones H2 para el corpus de Nubbix

- Estado: Aceptada
- Propuesta el 20/11/2026 y aceptada el 22/11/2026.
- Referencia anterior: A05

## Decisión

Elegimos `headings_v1` como estrategia principal para este corpus. Cada política conserva bajo su encabezado las reglas, los plazos y las excepciones que las acompañan. Los tres documentos tienen seis secciones H2 cada uno.

## Evidencia y alternativas

Se compararon tres índices con las mismas 27 preguntas revisadas y cinco resultados por consulta. En las 26 preguntas respondibles, tanto H2 como el híbrido lograron 100 % de recall@5 y 21,54 % de precisión@5. H2 ubicó evidencia en primer lugar en 23 preguntas y el híbrido en 21. La pregunta sobre guardería se reserva para evaluar el rechazo del generador. [Resultados por pregunta](../../evals/resultados/2026-11-22-retrieval-golden-revisado.csv)

- Las ventanas corridas (`words_v1`, 80 palabras con 20 compartidas) produjeron 24 fragmentos. Alcanzaron 23,85 % de precisión@5 y 96,15 % de recall@5. Perdieron el pasaje sobre renovación de notebooks.
- Las ventanas dentro de cada H2 (`section_words_v1`) produjeron 21 fragmentos. En la consulta sobre días de examen ofrecieron un pasaje más corto que H2. Solo tres secciones del corpus superan las 80 palabras, y el solapamiento puede ocupar dos puestos con texto de la misma política. [Comparación de los cortes](../referencias/chunking.md)

Con secciones más extensas convendrá repetir la comparación. El requisito de obtener al menos 20 fragmentos con una de las estrategias se cumple en ambos índices de ventanas. [Consigna](../fuentes/consigna.md)
