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

El dataset contiene 27 preguntas con extractos, offsets, hechos esperados e IDs de fragmentos relevantes por estrategia. Incluye paráfrasis, distractores, dos cruces documentales y una pregunta fuera de alcance. Una misma respuesta puede estar completa en dos ventanas solapadas. Al revisar las etiquetas, comprobá en el texto de cada fragmento qué hecho permite sostener. El validador comprueba la versión del corpus, los intervalos y los IDs, y cuenta las preguntas pendientes para los índices elegidos. [Dataset](../../evals/dataset.jsonl) · [Contrato de etiquetas](../CONTRATOS.md) · [Respuestas y fragmentos para la revisión conjunta](revision-golden.md)

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

### Resultados del 22 de noviembre de 2026

Se usaron los mismos cinco fragmentos por consulta que en la evaluación de recuperación, el mismo golden revisado, `gpt-6-luna` como generador y `gemini-3.5-flash-lite` como juez. Antes de la comparación, un piloto independiente con `q09` verificó que cada afirmación citara el pasaje correcto de RR. HH. o Finanzas. [JSON del piloto](../../evals/resultados/2026-11-22-ejemplo-q09.json) · [Resultados de recuperación](../../evals/resultados/2026-11-22-retrieval-golden-revisado.csv)

| Medición | Secciones H2 | Ventanas de 80 palabras |
| --- | ---: | ---: |
| Respuestas generadas y revisadas por el juez | 27/27 | 27/27 |
| Preguntas respondibles contestadas con evidencia | 26/26 | 25/26 |
| Afirmaciones que el juez marcó como respaldadas | 36/36 | 34/34 |
| Groundedness medio entre respuestas con afirmaciones | 100 % (26 respuestas) | 100 % (25 respuestas) |
| Rechazos indebidos entre preguntas respondibles | 0/26 | 1/26 |
| Rechazos correctos fuera de alcance | 1/1 | 1/1 |

Para cada afirmación, el juez compara su texto con los pasajes citados. La métrica de groundedness de una respuesta es la proporción de afirmaciones respaldadas. Los rechazos se evalúan aparte. La diferencia entre las estrategias apareció en `q11`. Con H2 se citó el reemplazo de notebooks cada tres años. Con ventanas el pasaje quedó octavo, fuera del contexto de cinco fragmentos, y se rechazó la pregunta. En `q27` ambos índices devolvieron el rechazo previsto con citas vacías. Es el único caso fuera de alcance del golden. [Detalle de las 54 respuestas](../../evals/resultados/2026-11-22-generacion-golden-revisado.csv)

La comparación usó **129 llamadas de las 162 autorizadas**. OpenAI generó las 54 respuestas en un intento cada una. En la primera pasada del juez hubo 15 errores HTTP 503. Se conservaron las respuestas y se volvieron a enviar únicamente los casos pendientes al mismo juez con el mismo prompt. Esos 21 intentos adicionales completaron los 54 veredictos, con 75 llamadas totales a Gemini. Se comprobó cada una de las 55 citas contra el ID, el texto y el intervalo de caracteres de su fuente.

OpenAI informó 58.698 tokens de entrada (45.571 de escritura en caché y cero de lectura) y 7.770 de salida. A la tarifa estándar del modelo, el consumo estimado fue de USD 0,010894 para la comparación. El piloto previo añadió USD 0,000252. [Tarifas de GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) · [Cálculo de la caché](https://developers.openai.com/api/docs/guides/prompt-caching)

Para la parte opcional, el plan de los tres *extra credits* y el bonus incluye las pruebas de aceptación y los primeros resultados locales de multi-query. [Plan y resultados del piloto](extra-credits.md)

### Configuración y ejecución

Después de revisar las etiquetas, configurá el generador en `.env` y elegí por separado `NUBBIX_JUDGE_PROVIDER` y `NUBBIX_JUDGE_MODEL`. El juez divide cada respuesta en afirmaciones comprobables y contrasta cada una con las citas. Esto permite detectar una respuesta que menciona un ID real pero atribuye a ese fragmento algo que el texto no dice. Para el caso fuera de alcance se mide si el asistente rechaza correctamente la pregunta. [Configuración del generador](consulta.md#generar-una-respuesta) · [Prompt del juez](../../prompts/groundedness.yaml)

El ejemplo siguiente realiza llamadas facturables y fija su límite. Con 27 preguntas, dos intentos de generación como máximo y una llamada al juez por estrategia y pregunta, el máximo teórico es de 162 llamadas para dos índices y 243 para tres. Elegí el presupuesto al ejecutar.

```sh
python evals/runner.py --builds "$BUILD_H2" "$BUILD_WORDS" --max-calls 162
```

El reporte `runs/<run_id>/eval.json` guarda los resultados por pregunta y estrategia, la cobertura, los errores y los casos que carecen de afirmaciones evaluables. Las pruebas locales de contrato verifican los adaptadores de OpenAI y Gemini con respuestas controladas.

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```
