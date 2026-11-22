# Cómo evaluar Nubbix Assist

La evaluación responde dos preguntas. Primero, ¿aparecen los fragmentos correctos entre los cinco que recibe el generador? Después, ¿las afirmaciones de la respuesta están respaldadas por sus citas? Ambas etapas usan la misma recuperación. Los comandos se ejecutan desde la raíz con el entorno activado y el modelo local preparado. [Preparación](../../README.md#probar-el-asistente) · [Resultados de recuperación](chunking.md)

## Preparar los índices y las etiquetas

Estos comandos construyen los tres índices desde cero. Si ya los tenés, asigná sus identificadores a las variables y pasá directamente a `--check-dataset`.

```sh
BUILD_H2=$(python ingest/run.py build --strategy headings_v1 | python -c 'import json,sys; print(json.load(sys.stdin)["build_id"])')
BUILD_WORDS=$(python ingest/run.py build --strategy words_v1 | python -c 'import json,sys; print(json.load(sys.stdin)["build_id"])')
BUILD_HYBRID=$(python ingest/run.py build --strategy section_words_v1 | python -c 'import json,sys; print(json.load(sys.stdin)["build_id"])')
python evals/runner.py --builds "$BUILD_H2" "$BUILD_WORDS" "$BUILD_HYBRID" --check-dataset
```

El dataset contiene 27 preguntas con extractos, offsets, hechos esperados e IDs de fragmentos relevantes por estrategia. Incluye paráfrasis, distractores, dos cruces documentales y una pregunta fuera de alcance. Una misma respuesta puede estar completa en dos ventanas solapadas. Al revisar las etiquetas, comprobá en el texto de cada fragmento qué hecho permite sostener. El validador comprueba la versión del corpus, los intervalos y los IDs, y cuenta las preguntas pendientes para los índices elegidos. [Dataset](../../evals/dataset.jsonl) · [Contrato de etiquetas](../CONTRATOS.md)

## Medir la recuperación local

```sh
python evals/runner.py --builds "$BUILD_H2" "$BUILD_WORDS" "$BUILD_HYBRID" --preliminary-retrieval
```

Ese modo admite etiquetas en borrador y registra su estado. Una vez revisadas, usá `--retrieve-only` para la medición definitiva. El primer comando compara las dos estrategias originales y el segundo incluye el híbrido.

```sh
python evals/runner.py --builds "$BUILD_H2" "$BUILD_WORDS" --retrieve-only
python evals/runner.py --builds "$BUILD_H2" "$BUILD_WORDS" "$BUILD_HYBRID" --retrieve-only
```

**Precisión@5** indica qué proporción de los cinco resultados estaba etiquetada como relevante. **Recall@5** indica qué proporción de los fragmentos esperados apareció entre esos cinco. **Hit rate** cuenta las preguntas en las que se recuperó al menos un fragmento relevante. El promedio da el mismo peso a cada pregunta respondible. La pregunta sobre guardería (`q27`) se busca en todos los índices y queda fuera de estos promedios porque carece de fragmentos relevantes.

## Evaluar respuestas con generador y juez

Después de revisar las etiquetas, configurá el generador en `.env` y elegí por separado `NUBBIX_JUDGE_PROVIDER` y `NUBBIX_JUDGE_MODEL`. El juez divide cada respuesta en afirmaciones comprobables y contrasta cada una con las citas. Esto permite detectar una respuesta que menciona un ID real pero atribuye a ese fragmento algo que el texto no dice. Para el caso fuera de alcance se mide si el asistente rechaza correctamente la pregunta. [Configuración del generador](consulta.md#generar-una-respuesta) · [Prompt del juez](../../prompts/groundedness.yaml)

El ejemplo siguiente realiza llamadas facturables y fija su límite. Con 27 preguntas, dos intentos de generación como máximo y una llamada al juez por estrategia y pregunta, el máximo teórico es de 162 llamadas para dos índices y 243 para tres. Elegí el presupuesto al ejecutar.

```sh
python evals/runner.py --builds "$BUILD_H2" "$BUILD_WORDS" --max-calls 162
```

El reporte `runs/<run_id>/eval.json` guarda los resultados por pregunta y estrategia, la cobertura, los errores y los casos que carecen de afirmaciones evaluables. Las pruebas locales de contrato verifican los adaptadores de OpenAI y Gemini con respuestas controladas.

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```
