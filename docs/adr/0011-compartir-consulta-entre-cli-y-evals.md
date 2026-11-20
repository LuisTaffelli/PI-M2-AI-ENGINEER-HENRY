# ADR 0011: Reutilizar el núcleo de consulta en CLI y evaluaciones

- Estado: Aceptada
- Fecha: 20/11/2026
- Referencia anterior: A09

## Contexto

Una implementación paralela para las evals podría comportarse de forma distinta a la aplicación entregada.

## Decisión

La CLI y el runner usan los mismos componentes de recuperación y generación. El runner toma los IDs de la traza de esa respuesta y añade etiquetas, métricas y juez.

## Consecuencias

- Se mide el flujo que se entrega.
- Retrieval puede evaluarse sin llamar al generador.
- La comparación mantiene corpus, configuración, modelos y prompts constantes, salvo el chunking estudiado.
- Fallos de generación y del juez se reportan con cobertura, no como resultados perfectos.

## Alternativas consideradas

Un pipeline de evaluación separado da flexibilidad, pero puede introducir divergencias y atribuir diferencias a la causa equivocada.

## Referencias

- [Arquitectura](../ARQUITECTURA.md).
- [Consigna](../fuentes/consigna.md).

