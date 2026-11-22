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
BUILD_HYBRID=$(python ingest/run.py build --strategy section_words_v1 | python -c 'import json,sys; print(json.load(sys.stdin)["build_id"])')
export PYTHONPATH=src
python -m nubbix_assist.cli.query --build "$BUILD_H2" --retrieve-only "¿Qué cubre el crédito de capacitación?"
```

Cada build guarda su catálogo, estado BM25 y colección Chroma en `data/indexes/<build_id>/`. Se publica después de comprobar sus hashes e IDs. La consulta reabre el build seleccionado. Por defecto recupera hasta diez candidatos por rama y fusiona las posiciones con RRF (constante 60). Envía hasta cinco chunks a generación. El filtro opcional `--source data/corpus/hr_policies.md` se aplica a ambas ramas.

Para generar una respuesta, copiá [.env.example](.env.example) a `.env` y elegí `openai` o `gemini` en `NUBBIX_GENERATOR_PROVIDER`. Indicá en `NUBBIX_GENERATOR_MODEL` un modelo disponible en tu cuenta que admita salidas JSON con esquema. Completá la clave del proveedor seleccionado. El juez usa los campos `NUBBIX_JUDGE_PROVIDER` y `NUBBIX_JUDGE_MODEL`.

```sh
python -m nubbix_assist.cli.query --build "$BUILD_H2" "¿Qué cubre el crédito de capacitación?"
```

La CLI devuelve `user_question`, `system_answer` y `chunks_related`. Cada cita identifica el fragmento y su documento e incluye el texto y el puntaje de búsqueda. Podés inspeccionar la evidencia con `--retrieve-only` antes de llamar al modelo.

### Cómo se construye y se evalúa la respuesta

- El [prompt de generación](prompts/generation.yaml) limita la respuesta a los fragmentos recuperados y pide una cita por afirmación. Si falta evidencia, pide un rechazo explícito. El código verifica que los IDs citados pertenezcan al contexto.
- El [prompt del juez](prompts/groundedness.yaml) divide la respuesta en afirmaciones y contrasta cada una con sus citas. Así se puede detectar una cita real cuyo texto no respalda lo afirmado.

En `runs/<run_id>/query.json` quedan los rankings, el contexto, la huella del prompt, el modelo y el uso que informe el proveedor. La generación admite hasta dos intentos por pregunta, con un límite predeterminado de 48 000 bytes de entrada y hasta 2048 tokens de salida por llamada.

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
| `section_words_v1` · ventanas 80/20 dentro de cada H2 | 8 | 7 | 6 | 21 |

Los [tres Markdown originales](data/corpus/) conservan los [hashes de procedencia](docs/fuentes/procedencia.json). El cuerpo de cada chunk se recupera con `raw_text[start_char:end_char]`. En RR. HH., «Beneficios» ocupa `[2473, 2732)`.

El híbrido abre una ventana al comenzar cada H2, repite el encabezado en el texto indexado y mantiene entera cada sección de hasta 80 palabras. En este corpus solo tres secciones superan ese límite. En la pregunta de capacitación (`q09`), tanto el híbrido como H2 recuperaron la sección de Finanzas en primer lugar y la de RR. HH. en segundo. La primera ventana de `words_v1` también incluyó texto sobre cobro de haberes. La elección final queda para la comparación de todo el dataset.

## Evaluación

El [golden](evals/dataset.jsonl) contiene 27 preguntas con extractos, offsets, hechos esperados e IDs relevantes por estrategia. Incluye paráfrasis, distractores, dos cruces documentales y un caso fuera de alcance. La revisión de `q09` cubre las tres estrategias. Las otras 26 preguntas están en borrador.

### Medición preliminar de recuperación · 22/11/2026

Se hicieron 81 búsquedas locales, una por pregunta y estrategia, con el mismo modelo, búsqueda híbrida y cinco resultados por consulta. Los promedios dan el mismo peso a cada una de las 26 preguntas respondibles. La pregunta sobre guardería (`q27`) se ejecutó en los tres índices y se excluyó de los promedios porque carece de fragmentos relevantes. El rechazo se evalúa en la etapa de generación.

| Estrategia | Precisión@5 | Recall@5 | Preguntas con toda la evidencia etiquetada en el top 5 |
|---|---:|---:|---:|
| Secciones H2 | 21,54 % | 100 % | 26/26 |
| Ventanas corridas 80/20 | 23,08 % | 96,15 % | 25/26 |
| Ventanas 80/20 por sección | 21,54 % | 100 % | 26/26 |

En `q11`, sobre renovación de notebooks, solo las ventanas corridas dejaron fuera del top 5 el fragmento que indica **cada 3 años**. Su precisión media fue mayor porque varias preguntas tienen más de una ventana relevante que cubre la misma evidencia. En H2 y en el híbrido, 24 de las 26 preguntas respondibles tienen un solo fragmento relevante, de modo que recuperarlo da un máximo de 20 % de precisión@5 en esas preguntas.

Los valores por pregunta se guardaron en el [CSV de la medición](evals/resultados/2026-11-22-retrieval-preliminar.csv), con precisión y recall en escala de 0 a 1 y celdas vacías para `q27`. La traza local corresponde a la corrida `2765b989f4bd4b56a7a10f42dd1fe8c2`.

**Prueba del híbrido con 160 palabras.** Se repitieron las 27 consultas con ventanas de 80 y 160 palabras, solapamiento de 20 y el mismo buscador. La sección más extensa tiene 84 palabras. Con 160, los 18 fragmentos coinciden en sección y texto con H2, salvo espacios finales, por lo que se pudieron trasladar sus etiquetas antes de consultar el índice.

| Ventana por sección | Fragmentos | Precisión@5 | Recall@5 | Primer resultado relevante |
|---|---:|---:|---:|---:|
| 80 palabras | 21 | 21,54 % | 100 % | 20/26 |
| 160 palabras | 18 | 21,54 % | 100 % | 21/26 |

Ambas variantes recuperaron toda la evidencia etiquetada en las 26 preguntas respondibles. Con 160, un fragmento relevante pasó al primer puesto en `q06`, `q12` y `q18`, y bajó al segundo en `q11` y `q26`. El híbrido de 80 sigue siendo la variante que permite estudiar el efecto de subdividir secciones en este corpus.

```sh
python evals/runner.py --builds "$BUILD_H2" "$BUILD_WORDS" --check-dataset
python evals/runner.py --builds "$BUILD_H2" "$BUILD_WORDS" "$BUILD_HYBRID" --check-dataset
# Medición preliminar local con las etiquetas actuales
python evals/runner.py --builds "$BUILD_H2" "$BUILD_WORDS" "$BUILD_HYBRID" --preliminary-retrieval
# Tras la revisión humana
python evals/runner.py --builds "$BUILD_H2" "$BUILD_WORDS" --retrieve-only
# Para incluir el híbrido una vez revisadas sus etiquetas
python evals/runner.py --builds "$BUILD_H2" "$BUILD_WORDS" "$BUILD_HYBRID" --retrieve-only
# Con generador y juez configurados. Este límite autoriza llamadas facturables.
python evals/runner.py --builds "$BUILD_H2" "$BUILD_WORDS" --max-calls 162
```

La corrida completa mide precision@5, recall@5, hit rate, groundedness por afirmación y rechazo correcto. Con 27 preguntas y hasta tres llamadas por pregunta y estrategia, el máximo teórico es de 162 llamadas para dos estrategias y 243 para tres. El presupuesto se elige al ejecutar. El reporte detallado queda en `runs/<run_id>/eval.json` e informa cobertura, errores y casos sin afirmaciones evaluables. Quedan pendientes las métricas definitivas con todas las etiquetas revisadas y la evaluación de las respuestas con generador y juez.

Las pruebas locales de contratos se ejecutan con `PYTHONPATH=src python -m unittest discover -s tests -v`. Las pruebas de los adaptadores usan respuestas controladas.

## Estructura

- `data/corpus/`: documentos originales.
- [ingest/run.py](ingest/run.py) permite inspeccionar los cortes de ingesta desde la consola.
- [src/nubbix_assist/](src/nubbix_assist/) contiene el núcleo compartido de ingesta y consulta. [ingestion/](src/nubbix_assist/ingestion/) carga documentos y [chunking/](src/nubbix_assist/chunking/) agrupa las estrategias de corte y sus reglas comunes.
- [embeddings/](src/nubbix_assist/embeddings/), [vector_store/](src/nubbix_assist/vector_store/) y [llm/](src/nubbix_assist/llm/) tienen contratos propios en `contracts/` y un lugar para cada adaptador en `providers/`.
- [evals/](evals/) reúne el golden, el runner, las métricas de recuperación y el juez de groundedness.
- En `docs/` se registran la [procedencia del corpus](docs/fuentes/procedencia.json), los [límites de cada componente](docs/MODULARIDAD.md) y el [uso de IA](docs/USO_IA.md).

## Decisiones y flujo de trabajo

La [arquitectura](docs/ARQUITECTURA.md), los [contratos](docs/CONTRATOS.md), el [almacenamiento](docs/ALMACENAMIENTO.md) y el [registro ADR](docs/adr/README.md) describen los límites del proyecto. Subimos cada cambio independiente a `main` con su propio commit y push. Corremos las pruebas pertinentes antes de subir cambios de código.

## Fuentes

- [Consigna guardada](docs/fuentes/consigna.md).
- [Fuente en Aula Viva](https://aula-viva.soyhenry.com/clase/6yf8ZcZ3a3O-).
