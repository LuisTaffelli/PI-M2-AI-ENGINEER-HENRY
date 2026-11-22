# Registro de decisiones de arquitectura

Un ADR por decisión. Este índice reemplaza el registro inicial DECISIONES.md y distingue decisiones confirmadas por Luis de propuestas pendientes. La tabla muestra el estado vigente de cada una.

## Índice

| ADR | Decisión | Estado |
|---|---|---|
| 0001 | [Diseñar antes de implementar](0001-disenar-antes-de-implementar.md) | Aceptada |
| 0002 | [Ejecutar embeddings locales y LLM por API](0002-embeddings-locales-y-llm-por-api.md) | Aceptada |
| 0003 | [Organizar una aplicación Python modular con CLI](0003-aplicacion-python-modular-con-cli.md) | Aceptada |
| 0004 | [Persistir los vectores con Chroma local](0004-persistencia-vectorial-con-chroma-local.md) | Aceptada |
| 0005 | [Construir builds independientes por estrategia y configuración](0005-builds-independientes-por-estrategia.md) | Aceptada |
| 0006 | [Publicar builds solo después de verificar su integridad](0006-publicar-builds-tras-verificar-integridad.md) | Aceptada |
| 0007 | [Corte por secciones H2 para el corpus de Nubbix](0007-comparar-secciones-y-ventanas-de-palabras.md) | Aceptada |
| 0008 | [Fusionar búsqueda vectorial y BM25 con RRF](0008-busqueda-hibrida-con-bm25-y-rrf.md) | Aceptada |
| 0009 | [Resolver las citas desde el catálogo de chunks](0009-resolver-citas-desde-el-catalogo.md) | Aceptada |
| 0010 | [Etiquetar evidencia y chunks relevantes por estrategia](0010-golden-con-evidencia-y-etiquetas-por-estrategia.md) | Aceptada |
| 0011 | [Reutilizar el núcleo de consulta en CLI y evaluaciones](0011-compartir-consulta-entre-cli-y-evals.md) | Aceptada |
| 0012 | [Versionar configuración y prompts e identificar corridas](0012-versionar-configuracion-prompts-y-corridas.md) | Propuesta |
| 0013 | [Evaluar multilingual-e5-small como candidato local](0013-evaluar-multilingual-e5-small.md) | Propuesta |
| 0014 | [Modularizar componentes, proveedores y validaciones](0014-modularizar-proveedores-y-validaciones.md) | Aceptada |
| 0015 | [Organizar los contratos como paquete por funcionalidad](0015-contratos-como-paquete-por-funcionalidad.md) | Aceptada |
| 0016 | [Limitar a dos los intentos de generación por pregunta](0016-limitar-intentos-de-generacion.md) | Aceptada |
| 0017 | [Ofrecer OpenAI y Gemini para generación y juez](0017-openai-y-gemini.md) | Aceptada |

## Cómo mantener el registro

- Numeración correlativa y estable, con nombre descriptivo; no reutilizar IDs.
- Cada ADR incluye contexto, decisión, consecuencias y alternativas. Usar [la plantilla](template.md).
- Estados: Propuesta, Aceptada, Rechazada o Sustituida. Una propuesta no pasa a aceptada por haberse documentado o implementado.
- Las propuestas pueden revisarse. Para reemplazar una decisión aceptada, crear otro ADR y enlazar ambos, conservando el historial.
- Los ADR documentan razones; los contratos detallados viven en [CONTRATOS.md](../CONTRATOS.md) y los flujos en [ARQUITECTURA.md](../ARQUITECTURA.md).
- [MODULARIDAD.md](../MODULARIDAD.md) detalla componentes, proveedores y niveles de validación.
- Las referencias A01–A11 del registro anterior se conservan dentro de los ADR 0003–0013.

## Marco de la consigna

Tres documentos originales; dos estrategias y al menos 20 chunks en una; ingesta y consulta separadas; vector DB persistente por estrategia; búsqueda híbrida; JSON con citas; golden revisado de al menos 25 preguntas; retrieval y groundedness con juez LLM por separado; comparación documentada. La consigna no exige dos proveedores, UI, microservicios ni infraestructura para 350 usuarios simultáneos.

La fuente académica permanece en [la consigna](../fuentes/consigna.md). Estos requisitos no se presentan como elecciones de tecnología.

## Pendientes para la ronda de evaluación

La revisión de las 27 preguntas y la evaluación de recuperación están completas. Luis aceptó H2 para este corpus. Para la evaluación de respuestas falta elegir los modelos de generación y de juez, fijar el presupuesto y medir el respaldo de las afirmaciones citadas.

Para revisar la calidad de las respuestas durante esa ronda:

- Probar una consulta que pida cambiar una política sin respaldo y otra que lo sugiera con distintas palabras. Incluir como control una consulta legítima sobre seguridad del manual de IT. Registrar si la respuesta cita la política correcta o reconoce que falta evidencia, y si el control recibe una respuesta útil.
- Probar también un fragmento de prueba con una instrucción ajena a la política. Verificar que el generador lo trate como texto documental y que el juez fundamente su veredicto en la evidencia. Usar una copia de prueba para conservar la huella del corpus oficial.
- Si se ensayan filtros de palabras o una API de moderación, comparar su aporte sobre esos mismos casos y contar las consultas legítimas bloqueadas. La moderación de contenido y el seguimiento de instrucciones se evalúan por separado.
- Revisar el JSON de una consulta real contra el contrato del M2 y contrastar sus citas con el catálogo. Para interpretar el consumo, consultar en las trazas el modelo, la huella del prompt y los tokens informados por intento. Si se publica un costo estimado, indicar la tarifa y su fecha y distinguir cualquier uso desconocido de un consumo de cero.

## Ruta para cerrar la arquitectura

| Orden | Bloque | Qué debemos dejar definido | Documentos/ADR |
|---|---|---|---|
| 1 | Ingesta, almacenamiento y versiones | Dueños del catálogo/índices, identidad del build, publicación, dos estrategias y compatibilidad | [Almacenamiento](../ALMACENAMIENTO.md), ADR 0004–0007 |
| 2 | Recuperación, generación y citas | Contratos de ambas ramas y del LLM, selección de contexto, validación y salida pública | ADR 0008–0009 y contratos |
| 3 | Ejecución y fallos | Configuración/ensamblado, errores, responsable de retries, límites por corrida y trazas | ADR 0012–0013 y modularidad |
| 4 | Evaluación y aceptación | Golden por estrategia, mismo flujo real, métricas, errores del juez y casos verificables | ADR 0010–0011 y contratos |

Luis dio el visto bueno al recorrido de los cuatro bloques. El índice recoge las decisiones aceptadas y conserva como propuestas el detalle del versionado de corridas y el candidato de embeddings.

### Recorrido para revisar los cuatro bloques

Pregunta de diseño para la revisión conjunta, pendiente de etiquetado humano en el golden: «¿El crédito de capacitación cubre libros de tecnología? Si pago un curso, ¿hasta cuándo puedo presentar la factura y dónde la cargo?». HR enumera los libros entre los gastos cubiertos. Finance indica que la factura del curso se carga en ExpenseHub dentro de los 30 días posteriores a la compra. [Beneficios](../../data/corpus/hr_policies.md#beneficios) · [Reembolsos educativos](../../data/corpus/finance_processes.md#presupuesto-de-capacitación-y-reembolsos-educativos).

| Bloque | Diseño de la primera versión | Criterio que vamos a comprobar al implementar |
|---|---|---|
| 1. Datos | Preparar dos builds del mismo corpus. Uno usa secciones H2 y otro ventanas de 80 palabras con 20 de solapamiento. Cada uno publica su catálogo, BM25 y Chroma local después de verificar IDs y reapertura. | Un proceso nuevo puede abrir cualquiera de los dos. Si se interrumpe la segunda ingesta, la primera sigue disponible. Al menos una estrategia alcanza 20 chunks. |
| 2. Consulta | Buscar en los tres documentos con BM25 y vectores, fusionar por RRF y enviar al generador los tres primeros chunks con sus IDs. La aplicación resuelve las citas desde el catálogo. | En la traza se puede ver si entraron la regla de HR sobre libros y el procedimiento de Finance para cursos. Un ID ajeno al contexto produce un error de validación. |
| 3. Ejecución | El caso de uso controla los intentos. Generación admite hasta dos llamadas en total entre intento inicial, reintento transitorio y posible reparación. Cada llamada consume el presupuesto de la corrida. | Un timeout seguido de una respuesta inválida agota ambos intentos. Se registra el fallo, se conserva la recuperación y la CLI comunica el error. Una credencial inválida detiene la llamada sin reintentos. |
| 4. Evaluación | Congelar al menos 25 preguntas y sus etiquetas por estrategia. Comparar con el mismo top_k y medir sobre la recuperación que alimentó cada respuesta. El juez evalúa sus afirmaciones contra las citas. | Si falta la evidencia de HR, inspeccionar recall@3. Si llegaron ambas fuentes pero el generador atribuye 60 días a Finance, inspeccionar groundedness. Si responde solo el plazo correcto, revisar completitud aunque la afirmación esté sostenida. |

Las ventanas, el número de candidatos, el modelo de embeddings y los límites operativos son elecciones iniciales revisables. Antes de llamar a la API se fijarán proveedor, modelos de generación y juez, y tope de consumo. La elección de H2 para la entrega está documentada en el [ADR 0007](0007-comparar-secciones-y-ventanas-de-palabras.md).

Los cuatro flujos tienen responsables, contratos, persistencia, comportamiento ante fallos y criterios de aceptación para el primer incremento. La tabla de pendientes sitúa las elecciones de implementación en la etapa que las necesita.

Modelos/proveedores y versiones concretas se fijan antes de implementar sus integraciones. Los parámetros iniciales quedan explícitos en configuración y su calidad se mide durante implementación/evals; los valores óptimos y los benchmarks no son una condición previa para cerrar el diseño.

El registro describe el diseño; no acredita índices construidos, integraciones ejecutadas ni métricas medidas.
