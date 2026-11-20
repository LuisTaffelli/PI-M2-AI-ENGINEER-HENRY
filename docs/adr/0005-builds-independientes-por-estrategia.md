# ADR 0005: Construir builds independientes por estrategia y configuración

- Estado: Aceptada
- Fecha: 20/11/2026
- Referencia anterior: A03

## Contexto

La consigna pide separar los índices de las dos estrategias. Catálogo, BM25 y vectores deben representar la misma versión de los chunks.

## Decisión

Guardar cada build en su propio directorio, con el catálogo, el estado de BM25, Chroma y el manifiesto. Cada build identifica una estrategia, un corpus y su configuración de construcción.

## Consecuencias

- Evita mezclar estrategias o estados de distintos índices.
- Consulta y evals seleccionan versiones explícitas.
- Conserva más artefactos en disco que sobrescribir una única colección.
- Ante un fallo se prevé reconstrucción completa; actualizaciones incrementales y reanudación quedan pospuestas.

## Alternativas consideradas

Sobrescribir un índice compartido o actualizarlo incrementalmente desde el inicio. Reducen copias, pero complican la consistencia y la comparación inicial.

## Referencias

- [Arquitectura](../ARQUITECTURA.md).
- [Consigna](../fuentes/consigna.md).

