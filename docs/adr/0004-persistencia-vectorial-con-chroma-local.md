# ADR 0004: Persistir los vectores con Chroma local

- Estado: Aceptada
- Fecha: 20/11/2026
- Referencia anterior: A02

## Contexto

El corpus es pequeño y la consigna requiere una vector DB persistente. El proyecto todavía no depende de PostgreSQL ni necesita un servicio externo para el índice.

## Decisión

Usar Chroma local persistente. La configuración inicial usa distancia coseno y recibe los embeddings de la aplicación.

## Consecuencias

- Evita operar un servidor adicional para el índice.
- Hay que verificar reapertura, integridad y compatibilidad con la versión instalada.
- El adaptador vectorial concentra la dependencia de Chroma.
- La propuesta no es un benchmark ni una garantía de mejor calidad de retrieval.

## Alternativas consideradas

pgvector permitiría integrar SQL y relaciones, pero sumaría la operación de PostgreSQL. Una base gestionada delegaría operación e introduciría cuenta y red para consultar el índice.

## Referencias

- [Arquitectura](../ARQUITECTURA.md).
- [Consigna](../fuentes/consigna.md).

