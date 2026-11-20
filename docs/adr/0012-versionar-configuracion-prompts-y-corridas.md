# ADR 0012: Versionar configuración y prompts e identificar corridas

- Estado: Propuesta
- Fecha: 20/11/2026
- Referencia anterior: A10

## Contexto

Necesitamos explicar por qué cambiaron resultados y distinguir una comparación de chunking de otros experimentos.

## Decisión

Se propone versionar configuración y prompts y registrar por corrida las huellas de corpus, builds, golden, modelos, parámetros, tiempos, intentos y validaciones.

## Consecuencias

- Los resultados detallados quedan en runs/ y las tablas finales se documentan en README/docs.
- Los artefactos de índices y secretos no se versionan.
- Tokens y costos se informan solo con datos suficientes.
- La reproducibilidad refiere a condiciones registradas; no se presupone igualdad bit por bit de ANN o llamadas remotas.

## Alternativas consideradas

Registrar solo promedios finales sería más corto, pero perdería errores por pregunta y datos para explicar diferencias.

## Referencias

- [Arquitectura](../ARQUITECTURA.md).
- [Consigna](../fuentes/consigna.md).

