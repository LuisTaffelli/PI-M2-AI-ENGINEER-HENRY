# ADR 0016 · Limitar a dos los intentos de generación por pregunta

- Estado: Aceptada

## Contexto

Una consulta puede fallar por un timeout, por una salida inválida o por una cita ajena al contexto. La recuperación ya realizada permite inspeccionar qué evidencia recibió el modelo.

## Decisión

El caso de uso de respuesta administra un máximo de dos llamadas de generación por pregunta. El primer intento consume una. Un fallo transitorio o una reparación de formato o citas puede consumir la segunda si queda presupuesto en la corrida. Ambos intentos usan el mismo contexto. El adaptador del proveedor debe permitir contabilizar cada llamada, incluidos los reintentos que pudiera hacer el SDK.

## Consecuencias

Un timeout seguido de una cita inválida agota los dos intentos. Se conserva la traza y la CLI devuelve un error. Una credencial inválida corta la ejecución en el primer intento. El límite pertenece a generación. El juez de evaluación tiene su propia operación y consume el presupuesto global de la corrida.

## Alternativas consideradas

Dar un reintento al adaptador y otro a la reparación permitiría superar el límite cuando ambos fallos ocurren en la misma consulta.

## Referencias

- [Comportamiento ante fallos](../ARQUITECTURA.md#10-errores-límites-y-trazas).
