# ADR 0007: Comparar secciones H2 con ventanas de palabras

- Estado: Propuesta
- Fecha: 20/11/2026
- Referencia anterior: A05

## Contexto

Se verificaron tres documentos con seis secciones H2 cada uno: 18 en total. Los conteos de palabras son HR 443, IT 449 y Finance 448. La consigna requiere al menos 20 chunks en una estrategia.

## Decisión

Se propone comparar headings_v1, un chunk por sección H2, con words_v1, ventanas de 80 palabras y overlap de 20. Ambas conservan origen y contexto de documento/sección.

## Consecuencias

- H2 busca preservar políticas y listas completas; puede mezclar condiciones en un chunk.
- Ventanas busca más especificidad; puede cortar condiciones y generar redundancia.
- Una simulación sobre los originales contó 18 secciones y 24 ventanas, ocho por archivo. La ingesta futura deberá reproducir esta distribución y permitir revisar los cortes.
- Palabras no significa tokens: los textos preparados deben validarse contra el límite del modelo.
- La elección final depende de métricas, no de que una estrategia cumpla el mínimo.

## Alternativas consideradas

Dos variantes de tamaño casi iguales aportarían menos contraste. Otras estrategias podrán evaluarse después, documentando reglas y nuevos IDs.

## Referencias

- [Arquitectura](../ARQUITECTURA.md).
- [Consigna](../fuentes/consigna.md).

