# ADR 0010: Etiquetar evidencia y chunks relevantes por estrategia

- Estado: Aceptada
- Fecha: 20/11/2026
- Referencia anterior: A08

## Contexto

El golden debe tener al menos 25 preguntas revisadas. Los chunks cambian entre estrategias, aunque la evidencia original permanezca igual.

## Decisión

Guardar la evidencia del corpus y los IDs relevantes por estrategia. Luis revisa las etiquetas antes de congelarlas para la comparación.

## Consecuencias

- Luis revisa preguntas y etiquetas contra los documentos.
- El mapeo por spans ayuda, pero no sustituye la revisión de suficiencia.
- Borradores o IDs inexistentes detienen la evaluación.
- Solapamiento y granularidad afectan métricas y deben considerarse al interpretar resultados.

## Alternativas consideradas

Etiquetar solo IDs perdería el vínculo estable con la evidencia. Etiquetar solo spans no satisface por sí solo los IDs esperados por estrategia pedidos en la consigna.

## Referencias

- [Arquitectura](../ARQUITECTURA.md).
- [Consigna](../fuentes/consigna.md).

