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

El golden actual contiene 36 preguntas: 26 respondibles con extractos, offsets, hechos esperados e IDs por estrategia y 10 sin respuesta. Incluye paráfrasis, distractores y cruces documentales. La edición de 27 preguntas usada el 22/11 incluía solo un caso sin respuesta. [Cómo se revisó la ampliación](revision-golden.md#ampliación-de-los-casos-sin-respuesta--25112026) Una misma respuesta puede estar completa en dos ventanas solapadas. Al revisar las etiquetas, comprobá en el texto de cada fragmento qué hecho permite sostener. El validador comprueba la versión del corpus, los intervalos y los IDs, y cuenta las preguntas pendientes para los índices elegidos. [Dataset](../../evals/dataset.jsonl) · [Contrato de etiquetas](../CONTRATOS.md) · [Respuestas y fragmentos para la revisión conjunta](revision-golden.md)

## Medir la recuperación local

```sh
python evals/runner.py --builds "$BUILD_H2" "$BUILD_WORDS" "$BUILD_HYBRID" --preliminary-retrieval
```

Ese modo admite etiquetas en borrador y registra su estado. Una vez revisadas, usá `--retrieve-only` para la medición definitiva. El primer comando compara los dos cortes originales y el segundo añade las ventanas dentro de cada sección. Los dos comandos usan búsqueda híbrida.

```sh
python evals/runner.py --builds "$BUILD_H2" "$BUILD_WORDS" --retrieve-only
python evals/runner.py --builds "$BUILD_H2" "$BUILD_WORDS" "$BUILD_HYBRID" --retrieve-only
```

**Precisión@5** indica qué proporción de los cinco resultados estaba etiquetada como relevante. **Recall@5** indica qué proporción de los fragmentos esperados apareció entre esos cinco. **Hit rate** cuenta las preguntas en las que se recuperó al menos un fragmento relevante. El promedio da el mismo peso a cada pregunta respondible. Los casos sin respuesta se consultan y se cronometran, pero no se les asigna RR, precisión ni recall: por definición no tienen un fragmento esperado.

### Comparar BM25, vectorial y RRF

El 24 de noviembre de 2026 repetimos las 27 consultas sobre los tres índices y verificamos que cada fragmento esperado ocupaba el mismo puesto en el top 10 que en la corrida del día 22. Para cada corte usamos las mismas preguntas y etiquetas en las tres búsquedas. Tomamos hasta diez candidatos de BM25 y hasta diez de E5. Aplicamos RRF con constante 60 y el mismo peso por rama. El top 5 reconstruido coincidió en las 81 consultas con los cinco fragmentos seleccionados por el buscador. La medición usó recuperación local, con multi-query y re-ranking desactivados. [Configuración](../../config.yaml) · [Función de fusión](../../src/nubbix_assist/retrieval/rrf.py)

| Corte | Búsqueda | Precisión@5 | Recall@5 | Recall@10 |
|---|---|---:|---:|---:|
| Secciones H2 | BM25 | 20,77 % | 98,08 % | 100 % |
| Secciones H2 | Vectorial | 20,77 % | 96,15 % | 100 % |
| Secciones H2 | Híbrida (RRF) | 21,54 % | 100 % | 100 % |
| Ventanas corridas | BM25 | 22,31 % | 90,38 % | 96,15 % |
| Ventanas corridas | Vectorial | 24,62 % | 100 % | 100 % |
| Ventanas corridas | Híbrida (RRF) | 23,85 % | 96,15 % | 100 % |
| Ventanas por sección | BM25 | 20,77 % | 98,08 % | 100 % |
| Ventanas por sección | Vectorial | 20,00 % | 92,31 % | 100 % |
| Ventanas por sección | Híbrida (RRF) | 21,54 % | 100 % | 100 % |

Tres preguntas explican dónde cambió el contexto que recibe el generador.

| Pregunta y fragmento esperado | Corte | Puesto BM25 | Puesto vectorial | Puesto RRF |
|---|---|---:|---:|---:|
| `q12` · Apps aceptadas para MFA | H2 | 1 | 7 | 1 |
| `q18` · Equipo temporal durante un viaje (IT) | H2 | 1 | 2 | 1 |
| `q18` · Factura para el reintegro (Finanzas) | H2 | 7 | 3 | 4 |
| `q11` · Plazo de renovación de notebooks | Ventanas corridas | Fuera del top 10 | 1 | 8 |

En H2, BM25 aportó el primer puesto para MFA y el vectorial ubicó entre los primeros cinco los dos pasajes necesarios para contestar la consulta del viaje. RRF conservó esas evidencias en ambos casos. Con ventanas corridas, la fusión dejó octavo el fragmento de renovación de notebooks. Ese único caso explica la diferencia de recall@5 entre el vectorial y RRF en ese corte.

El CSV incluye una fila por fragmento esperado y corte. Una posición vacía indica que el fragmento quedó fuera de los diez primeros de ese método. La fila de `q27` en cada corte tiene el campo `chunk_esperado` vacío porque el corpus carece de evidencia para esa pregunta. [Posiciones de los tres métodos por pregunta y fragmento](../../evals/resultados/2026-11-24-comparacion-buscadores.csv)

<details>
<summary>Recalcular la tabla a partir de una corrida local</summary>

Ejecutá el comando `--retrieve-only` de los tres índices que aparece arriba. Desde la raíz del repositorio, asigná el `run_id` que imprime a `RUN_ID` y ejecutá este bloque. Lee los candidatos de cada traza y usa las funciones de fusión y métricas del proyecto.

```sh
PYTHONPATH=src python - "runs/$RUN_ID/eval.json" <<'PY'
import json
import sys
from pathlib import Path
from statistics import mean

from evals.metrics import retrieval_metrics
from nubbix_assist.retrieval.rrf import fuse

report = json.loads(Path(sys.argv[1]).read_text())
print("Corte | Búsqueda | Precisión@5 | Recall@5 | Recall@10")
for corte, estrategia in report["strategies"].items():
    resultados = {"BM25": [], "Vectorial": [], "RRF": []}
    for caso in estrategia["cases"]:
        traza = caso["trace"]
        config = traza["config"]
        assert (config["candidates"], config["top_k"]) == (10, 5)
        bm25 = [key for key, _ in traza["lexical_candidates"]]
        vectorial = [key for key, _ in traza["vector_candidates"]]
        rrf = [key for key, _ in fuse([bm25, vectorial], config["rrf_constant"], 10)]
        assert rrf[:5] == caso["retrieved_ids"]
        esperados = caso["expected_chunks"]
        if esperados:
            for nombre, ranking in (("BM25", bm25), ("Vectorial", vectorial), ("RRF", rrf)):
                top5 = retrieval_metrics(ranking, esperados, 5)
                top10 = retrieval_metrics(ranking, esperados, 10)
                resultados[nombre].append((top5["precision_at_k"], top5["recall_at_k"], top10["recall_at_k"]))
    for nombre, filas in resultados.items():
        promedios = [f"{mean(columna):.2%}" for columna in zip(*filas)]
        print(" | ".join([corte, nombre, *promedios]))
PY
```

</details>

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

Para cada afirmación, el juez compara su texto con los pasajes citados. La métrica de groundedness de una respuesta es la proporción de afirmaciones respaldadas. Los rechazos se evalúan aparte. La diferencia entre las estrategias apareció en `q11`. Con H2 se citó el reemplazo de notebooks cada tres años. Con ventanas el pasaje quedó octavo, fuera del contexto de cinco fragmentos, y se rechazó la pregunta. En `q27` ambos índices devolvieron el rechazo previsto con citas vacías. Era el único caso fuera de alcance del golden original. [Detalle de las 54 respuestas](../../evals/resultados/2026-11-22-generacion-golden-revisado.csv)

La comparación usó **129 llamadas de las 162 autorizadas**. OpenAI generó las 54 respuestas en un intento cada una. En la primera pasada del juez hubo 15 errores HTTP 503. Se conservaron las respuestas y se volvieron a enviar únicamente los casos pendientes al mismo juez con el mismo prompt. Esos 21 intentos adicionales completaron los 54 veredictos, con 75 llamadas totales a Gemini. Se comprobó cada una de las 55 citas contra el ID, el texto y el intervalo de caracteres de su fuente.

OpenAI informó 58.698 tokens de entrada (45.571 de escritura en caché y cero de lectura) y 7.770 de salida. A la tarifa estándar del modelo, el consumo estimado fue de USD 0,010894 para la comparación. El piloto previo añadió USD 0,000252. [Tarifas de GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) · [Cálculo de la caché](https://developers.openai.com/api/docs/guides/prompt-caching)

Los tres *extra credits* tienen una comparación de recuperación local y una interfaz con citas navegables. [Resultados y reproducción](extra-credits.md)

### Configuración y ejecución

Después de revisar las etiquetas, configurá el generador en `.env` y elegí por separado `NUBBIX_JUDGE_PROVIDER` y `NUBBIX_JUDGE_MODEL`. El juez divide cada respuesta en afirmaciones comprobables y contrasta cada una con las citas. Esto permite detectar una respuesta que menciona un ID real pero atribuye a ese fragmento algo que el texto no dice. Para el caso fuera de alcance se mide si el asistente rechaza correctamente la pregunta. [Configuración del generador](consulta.md#generar-una-respuesta) · [Prompt del juez](../../prompts/groundedness.yaml)

El ejemplo siguiente realiza llamadas facturables y fija su límite. Con 36 preguntas, dos intentos de generación como máximo y una llamada al juez por estrategia y pregunta, el máximo teórico es de 216 llamadas para dos índices y 324 para tres. Elegí el presupuesto al ejecutar.

```sh
python evals/runner.py --builds "$BUILD_H2" "$BUILD_WORDS" --max-calls 216
```

El reporte `runs/<run_id>/eval.json` guarda los resultados por pregunta y estrategia, la cobertura, los errores y los casos que carecen de afirmaciones evaluables. El informe también incluye RR por pregunta, MRR por método y tiempos por etapa con cantidad de observaciones, mediana y p95. [Desglose y datos del benchmark local](mediciones-rag.md). Las pruebas locales de contrato verifican los adaptadores de OpenAI y Gemini con respuestas controladas.

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```
