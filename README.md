# Nubbix Assist · PI del módulo 2

Nubbix Assist responde en español preguntas sobre las políticas internas de Nubbix y cita el fragmento que sostiene cada respuesta. Una pregunta sobre qué cubre el crédito de capacitación y cómo se rinde un curso combina dos fuentes. RR. HH. describe el beneficio y Finanzas indica el plazo y la plataforma. El corpus reúne tres documentos de Henry sobre RR. HH., IT y Finanzas. [Corpus original](data/corpus/) · [Consigna del proyecto](docs/fuentes/consigna.md)

## Cómo funciona

La ingesta divide los documentos en fragmentos, calcula sus embeddings con `multilingual-e5-small` y guarda un índice local en Chroma por cada estrategia de corte. En cada consulta, BM25 busca términos exactos y la búsqueda vectorial recupera pasajes de significado parecido. El sistema combina ambos rankings con Reciprocal Rank Fusion (RRF) y entrega hasta cinco fragmentos al generador.

El prompt de generación pide una cita por afirmación o un rechazo si falta evidencia. El código comprueba que cada ID citado exista en el contexto recuperado. En la evaluación, un segundo prompt le pide al juez que contraste cada afirmación con sus citas. Así se distingue encontrar el pasaje correcto de responder fielmente a lo que dice. [Generación, citas y trazas](docs/referencias/consulta.md)

## Probar el asistente

El proyecto se verificó en Linux con Python 3.12 y CPU. Desde la raíz del repositorio, instalá las dependencias y descargá el modelo local de embeddings.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.9.1
python -m pip install -r requirements.txt
python ingest/run.py prepare-model
```

Construí el índice por secciones una vez. Podés reutilizar su identificador para consultar cuantas veces quieras. Este ejemplo muestra los fragmentos recuperados y funciona sin clave de API.

```sh
BUILD_H2=$(python ingest/run.py build --strategy headings_v1 | python -c 'import json,sys; print(json.load(sys.stdin)["build_id"])')
export PYTHONPATH=src
python -m nubbix_assist.cli.query --build "$BUILD_H2" --retrieve-only "¿Qué cubre el crédito de capacitación?"
```

Para obtener la respuesta redactada, configurá el modelo y la clave en `.env` y repetí la consulta sin `--retrieve-only`. En el piloto de capacitación, el asistente citó a RR. HH. para el crédito anual de USD 500 y a Finanzas para la carga de la factura en ExpenseHub dentro de los 30 días de la compra. Cada entrada de `chunks_related` incluye el ID, el documento, el texto citado y su puntaje de recuperación. [Respuesta JSON real con ambas citas](evals/resultados/2026-11-22-ejemplo-q09.json) · [Comando del ejemplo](docs/referencias/consulta.md#generar-una-respuesta)

### Bonus de rechazo honesto

Ambas estrategias devolvieron este JSON para la única pregunta del golden que el corpus deja sin respuesta (`q27`).

```json
{
  "user_question": "¿Cuántos cupos por mes tiene la guardería infantil de la sede central?",
  "system_answer": "La documentación disponible no alcanza para responder la pregunta.",
  "chunks_related": []
}
```

## Qué aprendimos del chunking

Comparamos tres maneras de dividir el mismo corpus. Se ejecutaron las 27 preguntas de referencia con cada índice. La tabla promedia las 26 que tienen evidencia documental y mide qué fragmentos aparecieron entre los primeros cinco.

| Estrategia | Fragmentos | Precisión@5 | Recall@5 | Primer resultado relevante |
|---|---:|---:|---:|---:|
| Una sección por encabezado H2 | 18 | 21,54 % | 100 % | 23/26 |
| Ventanas de 80 palabras con 20 de solapamiento | 24 | 23,85 % | 96,15 % | 22/26 |
| Las mismas ventanas dentro de cada sección | 21 | 21,54 % | 100 % | 21/26 |

**Elegimos el corte por secciones para este corpus.** Cuando se preguntó cada cuánto se reemplazan las notebooks, recuperó la política y el asistente respondió «cada 3 años». Con ventanas de 80 palabras, el pasaje quedó fuera de los cinco primeros y el asistente rechazó una pregunta que tenía respuesta. Las ventanas dentro de cada sección también recuperaron toda la evidencia en la prueba de búsqueda. [Resultados por pregunta](evals/resultados/2026-11-22-retrieval-golden-revisado.csv) · [Comparación de cortes](docs/referencias/chunking.md)

## Qué aporta la búsqueda híbrida

Con el corte H2 fijo, comparamos tres búsquedas sobre las mismas 26 preguntas respondibles. BM25 y el buscador vectorial devuelven hasta diez candidatos cada uno. La búsqueda híbrida fusiona ambos rankings con RRF. El recall@10 mide cuánta evidencia aparece entre los diez primeros de cada método. El recall@5 mide cuánta llega a los cinco puestos que usa el generador.

| Búsqueda sobre secciones H2 | Precisión@5 | Recall@5 | Recall@10 |
|---|---:|---:|---:|
| BM25 | 20,77 % | 98,08 % | 100 % |
| Vectorial (E5) | 20,77 % | 96,15 % | 100 % |
| Híbrida (RRF) | 21,54 % | 100 % | 100 % |

En H2, los tres métodos encontraron toda la evidencia dentro de sus diez primeros resultados. La fusión también la conservó al quedarse con cinco. Por ejemplo, para «¿Qué apps acepta Nubbix para MFA?», BM25 y RRF ubicaron el pasaje en el primer puesto y el vectorial en el séptimo. El resultado cambió con las ventanas corridas de 80 palabras, donde el vectorial alcanzó 100 % de recall@5 y RRF obtuvo 96,15 %. [Comparación de los tres cortes y reproducción](docs/referencias/evaluacion.md#comparar-bm25-vectorial-y-rrf) · [Posiciones por pregunta](evals/resultados/2026-11-24-comparacion-buscadores.csv)

## Evaluación de las respuestas

| Corte | Preguntas respondibles contestadas | Afirmaciones respaldadas según el juez | Rechazo correcto fuera de alcance |
|---|---:|---:|---:|
| Secciones H2 | 26/26 | 36/36 | 1/1 |
| Ventanas de 80 palabras | 25/26 | 34/34 | 1/1 |

Evaluamos las mismas 27 preguntas con `gpt-6-luna` como generador y `gemini-3.5-flash-lite` como juez. Los rechazos carecen de afirmaciones verificables y se cuentan por separado. [Respuestas y veredictos por pregunta](evals/resultados/2026-11-22-generacion-golden-revisado.csv) · [Método y reproducción](docs/referencias/evaluacion.md)

## Extra credits

El re-ranking local llevó el pasaje de renovación de notebooks del octavo al primer puesto con ventanas. En H2, multi-query elevó el recall@5 del 76,92 % al 86,54 % en 27 versiones informales de las preguntas. Ambos modos son opcionales. La interfaz Streamlit permite abrir cada cita en su documento y probar los ejemplos guardados sin clave. [Resultados y comandos](docs/referencias/extra-credits.md) · [Abrir la interfaz](docs/referencias/extra-credits.md#interfaz-con-citas-navegables)

El diseño del sistema, las decisiones y la asistencia recibida están documentados en la [arquitectura](docs/ARQUITECTURA.md), el [registro de decisiones](docs/adr/README.md) y el [registro de uso de IA](docs/USO_IA.md).
