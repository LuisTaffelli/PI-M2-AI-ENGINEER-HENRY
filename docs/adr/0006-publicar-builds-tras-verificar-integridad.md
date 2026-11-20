# ADR 0006: Publicar builds solo después de verificar su integridad

- Estado: Aceptada
- Fecha: 20/11/2026
- Referencia anterior: A04

## Contexto

Una caída durante la ingesta puede dejar solo parte de los vectores o archivos. No hay una transacción única entre Chroma y los artefactos auxiliares.

## Decisión

Construir una versión nueva y comprobar conteos, IDs, dimensiones y reapertura. La ingesta publica el manifiesto al final mediante reemplazo atómico dentro del mismo directorio.

## Consecuencias

- Sin manifest listo, la consulta rechaza el build.
- Una construcción parcial no sustituye al build anterior.
- La primera versión ejecuta una ingesta por vez.
- La publicación requiere comprobaciones adicionales y no promete una transacción distribuida.

## Alternativas consideradas

Marcar el índice como disponible al empezar o confiar solo en la existencia de una colección. Ninguna opción demuestra que estén completos todos los artefactos.

## Referencias

- [Arquitectura](../ARQUITECTURA.md).
- [Consigna](../fuentes/consigna.md).

