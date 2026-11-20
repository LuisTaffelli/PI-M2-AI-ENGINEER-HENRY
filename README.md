# Nubbix Assist · PI del módulo 2

Asistente RAG para consultar políticas de Nubbix en español con citas al corpus. La ingesta y la búsqueda funcionan localmente. Para responder y evaluar groundedness se puede elegir OpenAI o Gemini por separado.

## Preparación

Entorno verificado en Linux con Python 3.12 y CPU. Desde la raíz del proyecto:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.9.1
python -m pip install -r requirements.txt
python ingest/run.py prepare-model
```

La última orden descarga la revisión de E5 fijada en [config.yaml](config.yaml). Después se puede construir y consultar el índice local con esa caché. La pregunta lleva el prefijo `query: ` y cada chunk, `passage: `. El adaptador valida el límite configurado antes de codificar y comprueba los 384 valores de cada vector normalizado.

## Ingesta y consulta

```sh
python ingest/run.py inspect data/corpus/hr_policies.md --section Beneficios
python ingest/run.py inspect data/corpus/hr_policies.md --strategy words_v1
BUILD_H2=$(python ingest/run.py build --strategy headings_v1 | python -c 'import json,sys; print(json.load(sys.stdin)["build_id"])')
BUILD_WORDS=$(python ingest/run.py build --strategy words_v1 | python -c 'import json,sys; print(json.load(sys.stdin)["build_id"])')
export PYTHONPATH=src
python -m nubbix_assist.cli.query --build "$BUILD_H2" --retrieve-only "¿Qué cubre el crédito de capacitación?"
```

Cada build guarda su catálogo, estado BM25 y colección Chroma en `data/indexes/<build_id>/`. Se publica después de comprobar sus hashes e IDs. La consulta reabre el build seleccionado. Por defecto recupera hasta diez candidatos por rama y fusiona las posiciones con RRF (constante 60). Envía hasta cinco chunks a generación. El filtro opcional `--source data/corpus/hr_policies.md` se aplica a ambas ramas.

Para generar una respuesta, copiá [.env.example](.env.example) a `.env` y elegí `openai` o `gemini` en `NUBBIX_GENERATOR_PROVIDER`. Indicá en `NUBBIX_GENERATOR_MODEL` un modelo disponible en tu cuenta que admita salidas JSON con esquema. Completá la clave del proveedor seleccionado. El juez usa los campos `NUBBIX_JUDGE_PROVIDER` y `NUBBIX_JUDGE_MODEL`.

```sh
python -m nubbix_assist.cli.query --build "$BUILD_H2" "¿Qué cubre el crédito de capacitación?"
```

La salida JSON contiene `user_question`, `system_answer` y `chunks_related`. Cada cita resuelve ID, origen, texto y puntaje RRF desde el catálogo. Las trazas con rankings, contexto, intentos y uso reportado quedan en `runs/`. Generación permite hasta dos intentos por pregunta. El presupuesto de entrada predeterminado es de 48 000 bytes y la salida reserva hasta 2048 tokens por llamada. Ajustá estos valores al modelo elegido.

Ejemplo del formato de rechazo previsto para la pregunta fuera de alcance del golden:

```json
{
  "user_question": "¿Cuántos cupos por mes tiene la guardería infantil de la sede central?",
  "system_answer": "La documentación disponible no alcanza para responder la pregunta.",
  "chunks_related": []
}
```

## Corpus y comparación del chunking

| Estrategia | HR | IT | Finance | Total |
|---|---:|---:|---:|---:|
| `headings_v1` · una sección H2 | 6 | 6 | 6 | 18 |
| `words_v1` · 80 palabras con solapamiento de 20 | 8 | 8 | 8 | 24 |

Los [tres Markdown originales](data/corpus/) conservan los [hashes de procedencia](docs/fuentes/procedencia.json). El cuerpo de cada chunk se recupera con `raw_text[start_char:end_char]`. En RR. HH., «Beneficios» ocupa `[2473, 2732)`.

En una consulta real sobre libros de tecnología y rendición de cursos, ambas estrategias recuperaron «Beneficios» y «Presupuesto de Capacitación y Reembolsos Educativos» entre sus primeros cinco resultados. La selección de la estrategia final queda para la comparación completa.

## Evaluación

El [golden](evals/dataset.jsonl) contiene 27 preguntas en borrador, con extractos, offsets, hechos esperados e IDs relevantes por estrategia. Incluye paráfrasis, distractores, dos cruces documentales y un caso fuera de alcance. Revisá la suficiencia de la evidencia y las etiquetas de cada estrategia antes de marcar una pregunta como `reviewed`. El runner confirma versión del corpus, existencia de los IDs y coherencia de los intervalos.

```sh
python evals/runner.py --builds "$BUILD_H2" "$BUILD_WORDS" --check-dataset
# Tras la revisión humana
python evals/runner.py --builds "$BUILD_H2" "$BUILD_WORDS" --retrieve-only
# Con generador y juez configurados. Este límite autoriza llamadas facturables.
python evals/runner.py --builds "$BUILD_H2" "$BUILD_WORDS" --max-calls 162
```

La corrida completa mide precision@5, recall@5, hit rate, groundedness por afirmación y rechazo correcto. El límite de 162 cubre hasta dos intentos de generación y una llamada al juez por cada una de las 27 preguntas y cada estrategia. El reporte detallado queda en `runs/<run_id>/eval.json` e informa cobertura, errores y casos sin afirmaciones evaluables. Las métricas comparativas y los resultados de las APIs están pendientes de la ronda con etiquetas revisadas y credenciales.

Las pruebas locales de contratos se ejecutan con `PYTHONPATH=src python -m unittest discover -s tests -v`. Las pruebas de los adaptadores usan respuestas controladas.

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


## Decisiones y flujo de trabajo

La [arquitectura](docs/ARQUITECTURA.md), los [contratos](docs/CONTRATOS.md), el [almacenamiento](docs/ALMACENAMIENTO.md) y el [registro ADR](docs/adr/README.md) describen los límites del proyecto. Subimos cada cambio independiente a `main` con su propio commit y push. Corremos las pruebas pertinentes antes de subir cambios de código.

## Fuentes

- [Consigna guardada](docs/fuentes/consigna.md).
- [Fuente en Aula Viva](https://aula-viva.soyhenry.com/clase/6yf8ZcZ3a3O-).
