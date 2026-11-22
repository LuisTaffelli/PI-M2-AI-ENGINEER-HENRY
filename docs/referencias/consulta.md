# Del documento a la respuesta

Una pregunta como «¿Qué cubre el crédito de capacitación y cómo rindo la factura de un curso?» tiene dos fuentes. RR. HH. enumera los gastos cubiertos. Finanzas dice que la factura se carga en ExpenseHub dentro de los 30 días posteriores a la compra. Los comandos de esta guía se ejecutan desde la raíz, con el entorno y el índice `BUILD_H2` preparados como indica el README. [Preparación](../../README.md#probar-el-asistente) · [Beneficios](../../data/corpus/hr_policies.md#beneficios) · [Reembolsos educativos](../../data/corpus/finance_processes.md#presupuesto-de-capacitación-y-reembolsos-educativos)

## Inspeccionar los cortes y la búsqueda

```sh
python ingest/run.py inspect data/corpus/hr_policies.md --section Beneficios
python ingest/run.py inspect data/corpus/hr_policies.md --strategy words_v1
export PYTHONPATH=src
python -m nubbix_assist.cli.query --build "$BUILD_H2" --retrieve-only "¿Qué beneficio cubre libros de tecnología y cómo se rinde la factura de un curso?"
```

`inspect` muestra el texto, el encabezado y los offsets de cada fragmento. El cuerpo se puede reconstruir como `raw_text[start_char:end_char]`. Por ejemplo, «Beneficios» ocupa el intervalo `[2473, 2732)` en el índice por secciones. Los tres Markdown conservan sus hashes originales. [Procedencia del corpus](../fuentes/procedencia.json)

El comando `prepare-model` descarga la revisión fijada de `multilingual-e5-small`. El modelo distingue el fragmento que va a indexar de la pregunta que va a buscar mediante los prefijos `passage: ` y `query: `, respectivamente. El adaptador comprueba el límite de longitud y verifica que cada vector normalizado tenga 384 componentes. [Configuración](../../config.yaml) · [Embeddings](../../src/nubbix_assist/embeddings/)

Cada índice vive en `data/indexes/<build_id>/` con su catálogo de fragmentos, el índice léxico BM25 y la colección Chroma. La ingesta comprueba hashes e identificadores antes de publicarlo. Al consultar, el buscador recupera hasta diez candidatos por rama y combina sus posiciones con RRF (constante 60). Los cinco primeros forman el contexto. La opción `--source data/corpus/hr_policies.md` limita ambas ramas a las políticas de RR. HH. [Almacenamiento](../ALMACENAMIENTO.md)

## Generar una respuesta

Copiá `.env.example` a `.env`. En `NUBBIX_GENERATOR_PROVIDER` elegí `openai` o `gemini`. En `NUBBIX_GENERATOR_MODEL` indicá un modelo de tu cuenta que admita salidas JSON con esquema. Completá la clave correspondiente en `OPENAI_API_KEY` o `GEMINI_API_KEY`. El comando siguiente realiza una consulta al proveedor elegido. [Plantilla de configuración](../../.env.example)

```sh
export PYTHONPATH=src
python -m nubbix_assist.cli.query --build "$BUILD_H2" "¿Qué beneficio cubre libros de tecnología y cómo se rinde la factura de un curso?"
```

El generador recibe la pregunta y los fragmentos con sus IDs. El prompt le pide que base cada afirmación en la evidencia y cite su ID junto al texto. Al construir el JSON público, la aplicación recupera del catálogo el origen y el contenido de cada cita y adjunta el puntaje RRF de la búsqueda. Cuando falta evidencia, el prompt pide el rechazo documentado en el README y una lista de citas vacía. [Prompt de generación](../../prompts/generation.yaml) · [Contrato de respuesta](../CONTRATOS.md)

La traza en `runs/<run_id>/query.json` conserva los rankings, el contexto, la huella del prompt y, por intento, el proveedor, el modelo y el uso que informe la API. Se permiten hasta dos intentos con un máximo predeterminado de 48 000 bytes de entrada y hasta 2048 tokens de salida por llamada. [Configuración de límites](../../config.yaml)

El 22 de noviembre de 2026, `gpt-6-luna` respondió esa pregunta en el primer intento (1.010 tokens de entrada y 302 de salida). `gemini-3.5-flash-lite` encontró dos afirmaciones y marcó ambas como respaldadas. Los dos pasajes citados coinciden con los etiquetados en el golden y se cotejaron con sus documentos originales. [Respuesta JSON del piloto](../../evals/resultados/2026-11-22-ejemplo-q09.json) · [Beneficios de RR. HH.](../../data/corpus/hr_policies.md#beneficios) · [Rendición en Finanzas](../../data/corpus/finance_processes.md#presupuesto-de-capacitación-y-reembolsos-educativos)

## Dónde está el código

La [CLI de ingesta](../../ingest/run.py) usa el [cargador de documentos](../../src/nubbix_assist/ingestion/) y las [estrategias de chunking](../../src/nubbix_assist/chunking/). El [núcleo de consulta](../../src/nubbix_assist/) comparte sus adaptadores de [índice vectorial](../../src/nubbix_assist/vector_store/) y [modelos de lenguaje](../../src/nubbix_assist/llm/) con el [evaluador](../../evals/). Cada cambio independiente sigue el flujo de pruebas pertinentes, commit y push a `main`. [Límites entre componentes y proveedores](../MODULARIDAD.md)
