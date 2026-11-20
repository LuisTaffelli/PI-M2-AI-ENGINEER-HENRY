# ADR 0008: Fusionar búsqueda vectorial y BM25 con RRF

- Estado: Aceptada
- Fecha: 20/11/2026
- Referencia anterior: A06

## Contexto

La consigna exige búsqueda híbrida. Los términos exactos y las paráfrasis necesitan señales complementarias, con scores de escalas distintas.

## Decisión

Combinar BM25 y búsqueda vectorial locales con RRF sobre el mismo catálogo. Entregar hasta tres chunks al generador. Para la primera comparación se proponen una constante de 60 y hasta diez candidatos por rama. Ambos parámetros se registrarán y se mantendrán fijos al comparar chunkings.

## Consecuencias

- Posiciones desde uno, IDs únicos y desempate por ID.
- Distancia coseno, score BM25 y score RRF se conservan separados; no son probabilidades.
- Una rama léxica sin coincidencias puede estar vacía; no agrega resultados arbitrarios de score cero.
- Las reglas léxicas y BM25 están propuestas en la arquitectura y falta elegir una librería compatible.
- Los parámetros y la mejora de retrieval deben medirse; el acuerdo no asegura mejor top-1.

## Alternativas consideradas

Fusión ponderada con normalización requiere calibrar escalas y pesos. Solo búsqueda vectorial no cumple el requisito híbrido.

## Referencias

- [Arquitectura](../ARQUITECTURA.md).
- [Consigna](../fuentes/consigna.md).

