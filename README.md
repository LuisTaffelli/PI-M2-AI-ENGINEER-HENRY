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

Para obtener la respuesta redactada, configurá el modelo y la clave de OpenAI o Gemini en `.env` según la guía y repetí la consulta sin `--retrieve-only`. La salida es JSON. En una respuesta con evidencia, cada elemento de `chunks_related` identifica el fragmento, su documento, su texto y su puntaje. Este es el formato previsto para una pregunta fuera del corpus. [Configuración de la API y consulta completa](docs/referencias/consulta.md#generar-una-respuesta)

```json
{
  "user_question": "¿Cuántos cupos por mes tiene la guardería infantil de la sede central?",
  "system_answer": "La documentación disponible no alcanza para responder la pregunta.",
  "chunks_related": []
}
```

## Qué aprendimos del chunking

Comparamos tres maneras de dividir el mismo corpus. Se ejecutaron las 27 preguntas de referencia con cada índice. La tabla promedia las 26 que tienen evidencia documental y mide qué fragmentos aparecieron entre los primeros cinco.

| Estrategia | Fragmentos | Precisión@5 | Recall@5 |
|---|---:|---:|---:|
| Una sección por encabezado H2 | 18 | 21,54 % | 100 % |
| Ventanas de 80 palabras con 20 de solapamiento | 24 | 23,08 % | 96,15 % |
| Las mismas ventanas dentro de cada sección | 21 | 21,54 % | 100 % |

Con las etiquetas actuales, los cortes por sección y el híbrido recuperaron toda la evidencia esperada. Las ventanas corridas perdieron el pasaje sobre renovación de notebooks. Conservamos 80 palabras para el híbrido porque con 160 todas las secciones caben enteras. **Los resultados son preliminares.** Al hacer esta medición, solo la pregunta de capacitación (`q09`) tenía etiquetas revisadas para las tres estrategias. La decisión final y la evaluación de respuestas con generador y juez quedan pendientes. [Experimentos y resultados por pregunta](docs/referencias/chunking.md) · [Cómo reproducir la evaluación](docs/referencias/evaluacion.md)

El diseño del sistema, las decisiones y la asistencia recibida están documentados en la [arquitectura](docs/ARQUITECTURA.md), el [registro de decisiones](docs/adr/README.md) y el [registro de uso de IA](docs/USO_IA.md).
