# ADR 0008: Fusionar búsqueda vectorial y BM25 con RRF

- Estado: Aceptada
- Fecha: 20/11/2026
- Referencia anterior: A06

## Contexto

La consigna exige búsqueda híbrida. Los términos exactos y las paráfrasis necesitan señales complementarias, con scores de escalas distintas.

## Decisión

BM25 y la búsqueda vectorial consultan el mismo catálogo. Cada rama recupera hasta diez candidatos (`candidates: 10`). RRF combina ambos rankings con `rrf_constant: 60` y el generador recibe hasta cinco fragmentos (`top_k: 5`). La evaluación usa estos mismos parámetros para comparar las estrategias de chunking. [Configuración](../../config.yaml) · [Evaluación de recuperación](../referencias/evaluacion.md#medir-la-recuperación-local)

## Consecuencias

- Posiciones desde uno, IDs únicos y desempate por ID.
- Distancia coseno, score BM25 y score RRF se conservan separados; no son probabilidades.
- Una rama léxica sin coincidencias puede estar vacía; no agrega resultados arbitrarios de score cero.
- El proyecto implementa BM25 y usa el mismo tokenizador al indexar los fragmentos y al buscar una pregunta. [Índice léxico](../../src/nubbix_assist/lexical/index.py) · [Búsqueda léxica](../../src/nubbix_assist/lexical/search.py)
- Para evaluar el orden de los resultados, la comparación también cuenta cuántas preguntas recuperan un fragmento relevante en el primer puesto. [Resultados de chunking](../referencias/chunking.md)

## Alternativas consideradas

Fusión ponderada con normalización requiere calibrar escalas y pesos. Solo búsqueda vectorial no cumple el requisito híbrido.

## Referencias

- [Arquitectura](../ARQUITECTURA.md).
- [Consigna](../fuentes/consigna.md).

