# Nubbix Assist · PI del módulo 2

Asistente RAG para consultar las políticas internas de Nubbix y responder con citas rastreables a los documentos del corpus.

## Estado del primer incremento

La ingesta local lee los Markdown y permite inspeccionar un chunk por sección H2. Cada chunk identifica el archivo, su versión y el intervalo exacto del texto original. El índice, la consulta y la evaluación quedan para los siguientes incrementos.

Luis pidió definir la arquitectura antes de programar y eligió embeddings locales con LLM por API. El diseño base quedó acordado para el primer incremento.

- [Arquitectura y flujos](docs/ARQUITECTURA.md): responsabilidades, persistencia, recuperación, generación, errores y evaluación.
- [Contratos y aceptación](docs/CONTRATOS.md): datos, referencias, golden y verificaciones previstas.
- [Modularidad y proveedores](docs/MODULARIDAD.md): paquetes por funcionalidad, adaptadores y validadores comunes/específicos.
- [Almacenamiento e índices](docs/ALMACENAMIENTO.md): contratos del vector store, catálogo y ciclo de vida de un build.
- [Registro ADR](docs/adr/README.md): índice de decisiones, estados y pendientes, con un archivo por decisión.

## Corpus

| Documento | Tema | Secciones con encabezado H2 |
|---|---|---:|
| `data/corpus/hr_policies.md` | Licencias, modalidad de trabajo y beneficios | 6 |
| `data/corpus/it_manual.md` | Accesos, equipos, seguridad y soporte | 6 |
| `data/corpus/finance_processes.md` | Reintegros, compras y procesos financieros | 6 |

Los originales se conservan en `data/corpus/`. La procedencia y los SHA-256 están registrados en `docs/fuentes/procedencia.json`.

El corte por sección produjo 18 chunks, seis por documento. La consigna exige al menos 20 en **al menos una** de las dos estrategias. Falta implementar y medir el corte por ventanas.

## Inspeccionar un chunk

Podés inspeccionar «Beneficios» desde la raíz del proyecto con Python 3.10 o posterior y su biblioteca estándar.

```sh
python ingest/run.py inspect data/corpus/hr_policies.md --section Beneficios
```

El comando muestra el chunk como JSON. Al omitir `--section`, muestra todas las secciones del archivo. En la versión del corpus registrada, «Beneficios» ocupa el intervalo `[2473, 2732)`. Podés comprobarlo con `document.raw_text[2473:2732] == chunk.body`. El campo `content` agrega el título del documento y el de la sección para el modelo.

## Flujo que vamos a construir

```text
Ingesta:  documentos → chunks + metadatos → embeddings → colección persistida
Consulta: pregunta → búsqueda léxica y vectorial → fusión → LLM → JSON con citas
Evaluación: mismo golden y top_k → métricas de retrieval por estrategia + groundedness
```

## Ruta de trabajo

Subimos cada cambio independiente a `main` con su propio commit y push. El mensaje del commit describe qué incorpora y, cuando el cambio afecta al código, corremos las pruebas antes de subirlo.

1. Tomar el diseño de los cuatro bloques como referencia para la implementación.
2. Fijar la regla de corte y los metadatos de los chunks. Elegir cada dependencia cuando su integración la requiera.
3. Implementar carga y chunking por incrementos, inspeccionar chunks y empezar el golden.
4. Construir la ingesta persistente y la consulta separada siguiendo los contratos revisados.
5. Generar respuestas con citas e integrar búsqueda híbrida.
6. Completar las dos estrategias y el golden revisado de al menos 25 preguntas.
7. Ejecutar evals separadas, comparar con el mismo dataset y top_k y documentar resultados reales.

La base acordada usa Python modular y CLI, con núcleo reutilizable y separación por proveedores y validadores. La ingesta guarda una versión por estrategia en Chroma local. La consulta combina los rankings de BM25 y vectores con RRF. Los modelos concretos y las versiones de dependencias siguen abiertos. La UI y el retrieval avanzado son opcionales según la consigna.

## Estructura

- `data/corpus/`: documentos originales.
- [ingest/run.py](ingest/run.py) permite inspeccionar los cortes de ingesta desde la consola.
- [src/nubbix_assist/](src/nubbix_assist/) contiene el núcleo compartido de ingesta y consulta. [ingestion/](src/nubbix_assist/ingestion/) carga documentos y [chunking/](src/nubbix_assist/chunking/) agrupa las estrategias de corte y sus reglas comunes.
- [embeddings/](src/nubbix_assist/embeddings/), [vector_store/](src/nubbix_assist/vector_store/) y [llm/](src/nubbix_assist/llm/) tienen contratos propios en `contracts/` y un lugar para cada adaptador en `providers/`.
- [evals/](evals/) reúne el golden, el runner, las métricas de recuperación y el juez de groundedness.
- `prompts/`: prompts de generación y juez fuera del código.
- `docs/fuentes/`: consigna y registro de procedencia.
- `docs/ARQUITECTURA.md` y `docs/CONTRATOS.md`: diseño previo a la implementación.
- `docs/MODULARIDAD.md`: límites de componentes, proveedores y validaciones.
- `docs/adr/`: decisiones de arquitectura individuales, índice y plantilla.
- `docs/USO_IA.md`: asistencia recibida y decisiones revisables.

## Contrato final requerido

`{user_question, system_answer, chunks_related}`. Cada referencia debe permitir rastrear el documento y el contenido usado. Es un requisito pendiente de implementar.

## Fuentes

- [Consigna guardada](docs/fuentes/consigna.md).
- [Fuente en Aula Viva](https://aula-viva.soyhenry.com/clase/6yf8ZcZ3a3O-).

## Próximo paso

Comparar el corte por H2 con la propuesta de ventanas de palabras. Revisar si cada corte conserva la frase sobre el crédito de capacitación y la evidencia complementaria de Finance.
