# ADR 0002: Ejecutar embeddings locales y LLM por API

- Estado: Aceptada
- Fecha: 20/11/2026

## Contexto

Se consultó la modalidad de ejecución y Luis respondió: «Mixto: embeddings locales y LLM por API».

## Decisión

Ejecutar la generación de embeddings, la ingesta y la recuperación localmente. Usar una API para generar respuestas y para el juez LLM de groundedness.

## Consecuencias

- La ingesta no envía el corpus a un proveedor de embeddings.
- Generación envía pregunta y contexto seleccionado; el juez recibe pregunta, respuesta y citas.
- La descarga inicial del modelo local necesita conexión; después se prevé carga local.
- Proveedor API, modelos exactos, límites y presupuesto siguen abiertos.

## Alternativas consideradas

Ejecutar todos los modelos localmente o usar API tanto para embeddings como para generación. La modalidad mixta fue elegida por Luis.

## Referencias

- [Arquitectura](../ARQUITECTURA.md).
- [Consigna](../fuentes/consigna.md).

