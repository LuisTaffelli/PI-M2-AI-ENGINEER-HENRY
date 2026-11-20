# ADR 0009: Resolver las citas desde el catálogo de chunks

- Estado: Aceptada
- Fecha: 20/11/2026
- Referencia anterior: A07

## Contexto

La respuesta debe permitir rastrear origen y contenido. Un LLM puede proponer un ID inexistente o modificar el texto que presenta como fuente.

## Decisión

El LLM devuelve la respuesta y los IDs citados. La aplicación comprueba su pertenencia al contexto, obtiene source y content del catálogo y toma score de la misma recuperación.

## Consecuencias

- El contrato público mantiene user_question, system_answer y chunks_related.
- Referencias del texto y lista de citas deben corresponderse.
- La existencia de un ID es una validación mecánica; groundedness evalúa apoyo semántico.
- La traza conserva también candidatos y contexto no citados.

## Alternativas consideradas

Confiar en todos los campos generados por el LLM simplificaría la salida interna, pero no comprobaría la procedencia de la cita.

## Referencias

- [Arquitectura](../ARQUITECTURA.md).
- [Consigna](../fuentes/consigna.md).

