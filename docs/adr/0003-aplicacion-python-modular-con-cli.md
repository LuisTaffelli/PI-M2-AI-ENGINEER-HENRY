# ADR 0003: Organizar una aplicación Python modular con CLI

- Estado: Aceptada
- Fecha: 20/11/2026
- Referencia anterior: A01

## Contexto

El PI permite CLI o endpoint. Necesitamos seguir el recorrido de los datos y reutilizar los componentes en las evaluaciones.

## Decisión

Organizar una aplicación Python en una sola máquina, con módulos para ingesta, consulta y evaluación y una CLI como entrada inicial. Coordinar directamente las etapas, sin incorporar un framework RAG como dependencia inicial.

Luis aceptó la propuesta y precisó que los componentes deben modularizarse por responsabilidades, proveedores y sus validadores. Esa condición se registra en [ADR 0014](0014-modularizar-proveedores-y-validaciones.md).

## Límites de la aplicación

La forma de entrada queda separada de los casos de uso:

| Caso de uso | Recibe | Produce |
|---|---|---|
| Ingerir corpus | Corpus, estrategia y configuración de construcción | Identidad del build listo y conteos |
| Recuperar evidencia | Pregunta, build y parámetros de retrieval | Rankings y contexto seleccionado |
| Responder | Pregunta, build y configuración de consulta | Respuesta pública y traza interna de esa misma recuperación |
| Evaluar | Golden revisado, builds y configuración fija | Resultados por caso y reporte comparativo |

La CLI interpreta argumentos, llama al caso de uso y serializa la respuesta; no implementa búsqueda ni generación. Un endpoint o una UI posteriores llamarían a los mismos casos de uso.

Las dependencias siguen esta dirección: entrada o runner hacia casos de uso; casos de uso hacia componentes especializados. Los componentes no importan la CLI ni conocen argumentos de terminal.

El caso de respuesta conserva internamente la recuperación efectivamente usada para generar. La evaluación reutiliza esa traza para medir los chunks que llegaron al contexto, sin repetir la búsqueda para la misma respuesta. Una evaluación solo de retrieval llama directamente al recuperador y no genera una respuesta.

Usar un proveedor LLM por API no obliga a publicar un endpoint HTTP propio: son dos límites distintos. Luis confirmó la modalidad mixta y aceptó la CLI con núcleo reutilizable como entrada inicial.

## Consecuencias

- La lógica de negocio queda separada del transporte de entrada y salida.
- Los módulos no son microservicios ni necesitan despliegues independientes.
- Una UI podría consumir después el mismo núcleo.
- El JSON público mantiene su contrato; las trazas internas no se agregan automáticamente a stdout.
- UI, re-ranking, rewriting y evaluación del rechazo siguen como extensiones opcionales posteriores al mínimo medido.

## Alternativas consideradas

Endpoint web desde el inicio, un framework RAG u otros servicios separados. Podrían servir a otra escala; agregan alcance para este incremento.

## Referencias

- [Arquitectura](../ARQUITECTURA.md).
- [Consigna](../fuentes/consigna.md).

