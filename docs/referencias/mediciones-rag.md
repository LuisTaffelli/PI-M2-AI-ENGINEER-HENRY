# Diagnóstico del RAG por etapa · 25/11/2026

Mediciones del [golden ampliado](../../evals/dataset.jsonl): 36 preguntas, 26 respondibles y 10 sin respuesta. Los 27 casos originales no cambiaron. Esta corrida usó CPU en un i9-12900KF, modelos locales ya descargados y **cero llamadas a APIs**. No se comparan sus latencias directamente con las de otras fechas.

## Ranking y cobertura

RR@k = 1 / posición del primer fragmento esperado si aparece dentro de k; si no aparece, vale 0. MRR es la media de los RR de las 26 respondibles. Las 10 sin respuesta no entran en estas métricas: un buscador puede devolver pasajes cercanos aunque ninguno contenga la respuesta.

| Corte | Búsqueda | Precisión@5 | Recall@5 | Recall@10 | MRR@5 | MRR@10 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| H2 | BM25 | 20,77 % | 98,08 % | 100,00 % | 0,836 | 0,836 |
| H2 | Vectorial | 20,77 % | 96,15 % | 100,00 % | 0,875 | 0,880 |
| H2 | Híbrida RRF | 21,54 % | 100,00 % | 100,00 % | 0,942 | 0,942 |
| Ventanas 80/20 | BM25 | 22,31 % | 90,38 % | 96,15 % | 0,840 | 0,846 |
| Ventanas 80/20 | Vectorial | 24,62 % | 100,00 % | 100,00 % | 0,936 | 0,936 |
| Ventanas 80/20 | Híbrida RRF | 23,85 % | 96,15 % | 100,00 % | 0,904 | 0,909 |
| Ventanas dentro de H2 | BM25 | 20,77 % | 98,08 % | 100,00 % | 0,876 | 0,876 |
| Ventanas dentro de H2 | Vectorial | 20,00 % | 92,31 % | 100,00 % | 0,859 | 0,870 |
| Ventanas dentro de H2 | Híbrida RRF | 21,54 % | 100,00 % | 100,00 % | 0,904 | 0,904 |

[RR, precisión y recall por pregunta y corte](../../evals/resultados/2026-11-25-rag-ampliado/ranking-por-pregunta.csv). `k=10` mide la salida del ranking; el generador sigue recibiendo hasta cinco fragmentos.

## Ingesta reproducida desde cero

Una construcción por corte, cada una en un proceso nuevo y con el modelo presente en caché. Son observaciones individuales, no percentiles. El total también incluye escribir el catálogo y publicar el índice; los tiempos de Chroma y embeddings se cronometan por separado.

| Corte | Fragmentos | Carga E5 | Corpus + chunking | Embeddings de documentos | Índice BM25 | Índice Chroma | Validar/publicar | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| H2 | 18 | 2571,48 ms | 0,93 ms | 493,35 ms | 0,99 ms | 262,90 ms | 3,57 ms | 3335,52 ms |
| Ventanas 80/20 | 24 | 2521,02 ms | 1,15 ms | 723,60 ms | 1,22 ms | 260,55 ms | 4,44 ms | 3514,94 ms |
| Ventanas dentro de H2 | 21 | 2528,82 ms | 1,11 ms | 569,77 ms | 1,64 ms | 265,44 ms | 4,28 ms | 3374,29 ms |

[Manifiestos resumidos y tiempos](../../evals/resultados/2026-11-25-rag-ampliado/ingesta.json).

## Recuperación local por consulta

Cada celda es mediana / p95 en ms, con **36 consultas por corte**. El p95 es la observación en la posición ⌈0,95 × n⌉ del orden ascendente. La rama vectorial suma el embedding y la consulta a Chroma para cada pregunta antes de calcular percentiles. BM25 y vectorial se midieron dentro del recorrido híbrido, no como comandos de punta a punta separados. La fusión RRF sola no incluye recuperar candidatos. El total híbrido incluye las dos ramas y la selección final, no la carga de E5 ni la generación.

| Corte | Embedding de pregunta | BM25 | Chroma | Vectorial con embedding | Fusión RRF | Total híbrido |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| H2 | 9,512 / 12,620 | 0,062 / 0,073 | 0,613 / 1,102 | 10,143 / 13,331 | 0,010 / 0,012 | 10,248 / 13,436 |
| Ventanas 80/20 | 9,396 / 11,688 | 0,078 / 0,090 | 0,583 / 0,910 | 9,998 / 12,269 | 0,010 / 0,013 | 10,133 / 12,400 |
| Ventanas dentro de H2 | 9,284 / 11,597 | 0,067 / 0,076 | 0,592 / 0,905 | 9,907 / 12,165 | 0,011 / 0,016 | 10,021 / 12,287 |

[Tiempos por pregunta](../../evals/resultados/2026-11-25-rag-ampliado/latencia-por-pregunta.csv) · [Resumen del runner](../../evals/resultados/2026-11-25-rag-ampliado/resumen-recuperacion.json).

## Extras: reformulación y re-ranking

Corrida separada: CPU, dos hilos de PyTorch, un calentamiento por modo y tres pasadas alternadas (**108 mediciones por modo, corte y tipo de entrada**). Precisión, recall y MRR usan las 26 consultas respondibles; los tiempos incluyen las 36. El tiempo del extra mide solo su etapa (reformulador o cross-encoder), no el costo adicional total del modo. Las demás etapas están en el JSON.

| Corte | Entrada | Modo | Precisión@5 | Recall@5 | MRR@5 | Mediana extra | Total mediana / p95 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| H2 | Original | Base | 21,54 % | 100,00 % | 0,942 | — | 10,91 / 13,05 ms |
| H2 | Original | Multi-query | 21,54 % | 100,00 % | 0,942 | 0,55 ms | 14,46 / 23,44 ms |
| H2 | Original | Re-ranking | 21,54 % | 100,00 % | 1,000 | 303,52 ms | 313,94 / 339,08 ms |
| H2 | Informal | Base | 16,92 % | 76,92 % | 0,700 | — | 9,79 / 12,47 ms |
| H2 | Informal | Multi-query | 18,46 % | 86,54 % | 0,766 | 0,48 ms | 14,14 / 25,01 ms |
| Ventanas 80/20 | Original | Base | 23,85 % | 96,15 % | 0,904 | — | 10,95 / 13,67 ms |
| Ventanas 80/20 | Original | Multi-query | 24,62 % | 100,00 % | 0,904 | 0,57 ms | 15,01 / 23,67 ms |
| Ventanas 80/20 | Original | Re-ranking | 24,62 % | 100,00 % | 0,962 | 322,99 ms | 334,09 / 361,79 ms |
| Ventanas 80/20 | Informal | Base | 20,00 % | 80,77 % | 0,734 | — | 9,72 / 12,07 ms |
| Ventanas 80/20 | Informal | Multi-query | 20,77 % | 86,54 % | 0,708 | 0,48 ms | 14,31 / 25,03 ms |

[Desglose por etapas y percentiles](../../evals/resultados/2026-11-25-rag-ampliado/resumen-extras.json) · [RR y ranking por pregunta y modo](../../evals/resultados/2026-11-25-rag-ampliado/extras-por-pregunta.csv).

## Generación, juez y rechazo honesto

Corrida real sobre las 36 preguntas y los dos cortes principales con `gpt-6-luna` como generador y `gemini-3.5-flash-lite` como juez. Usó **159 de 216 llamadas**: 144 en la primera pasada y 15 reintentos solo del juez. Se ejecutó en serie. La evaluación del 22/11 se conserva por separado; esa versión del golden tenía un solo caso negativo.

| Corte | Respuestas generadas | Respondibles con respuesta | Rechazos correctos / con salida / esperados | Veredictos obtenidos | Afirmaciones respaldadas / juzgadas | Groundedness medio (n) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| H2 | 36/36 | 26/26 | 10 / 10 / 10 | 36/36 | 36/36 | 100,00 % (26) |
| Ventanas 80/20 | 36/36 | 25/26 | 10 / 10 / 10 | 36/36 | 34/34 | 100,00 % (25) |

El groundedness mide si las citas sostienen las afirmaciones que el juez extrajo; no prueba que la respuesta cubra todos los hechos pedidos. Los rechazos sin afirmaciones no se incluyen en ese promedio. Como en la corrida original, el corte por ventanas se abstuvo indebidamente en q11: el fragmento sobre renovación de notebooks quedó fuera del top 5. H2 sí respondió. Un rechazo correcto en los diez negativos no predice la tasa de acierto fuera de este corpus.

| Corte | Generación | Juez | Consulta sin juez | Evaluación con juez |
| --- | ---: | ---: | ---: | ---: |
| H2 | 3,97 / 6,18 s (n=36) | 3,60 / 7,32 s (n=36) | 3,99 / 6,19 s (n=36) | 7,55 / 14,87 s (n=36) |
| Ventanas 80/20 | 4,27 / 5,65 s (n=36) | 3,76 / 7,07 s (n=36) | 4,29 / 5,66 s (n=36) | 8,25 / 12,10 s (n=36) |

Cada celda es mediana / p95 de la **primera pasada**. Generación incluye validación y guardado de la traza; consulta suma recuperación y generación. Evaluación incluye el juez y la contabilidad del caso. Si hubo errores, su tiempo está en la etapa que efectivamente se ejecutó. Los reintentos manuales del juez no se agregan a estos percentiles; permiten recuperar la cobertura sin volver a generar.

[Respuestas, errores y tiempos por caso](../../evals/resultados/2026-11-25-rag-ampliado/generacion-juez-por-pregunta.csv) · [Resumen y cobertura](../../evals/resultados/2026-11-25-rag-ampliado/resumen-generacion-juez.json) · [Tiempos de reintentos del juez](../../evals/resultados/2026-11-25-rag-ampliado/reintentos-juez.csv).

**Interfaz y citas:** prueba funcional de navegación con ejemplos guardados. No se midió latencia de navegador.

## Cómo reproducir

Usá el [setup del README](../../README.md#probar-el-asistente). Al construir, agregá `--timings` al comando de ingesta para obtener `timing_ms`. El siguiente comando mide localmente y escribe los casos y tiempos en `runs/<run_id>/eval.json`:

```sh
python evals/runner.py --builds "$BUILD_H2" "$BUILD_WORDS" "$BUILD_HYBRID" --retrieve-only
```

Para preparar los tres IDs y lanzar generación y juez con un presupuesto explícito, seguí la [guía de evaluación](evaluacion.md).
