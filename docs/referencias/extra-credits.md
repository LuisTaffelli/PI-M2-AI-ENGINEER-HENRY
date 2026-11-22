# Extra credits de Nubbix Assist

Los tres extras se pueden probar sobre los índices existentes. La CLI y la interfaz usan el mismo buscador. Los dos experimentos de recuperación se ejecutaron en CPU con cero llamadas a los proveedores de generación. [Consigna](../fuentes/consigna.md) · [Métricas y versiones](../../evals/resultados/extras-2026-11-22/resumen.json) · [Consultas, reformulaciones y rankings por caso](../../evals/resultados/extras-2026-11-22/preguntas.csv)

## Re-ranking con cross-encoder

BM25 y E5 proponen candidatos. Se fusionan sus rankings con RRF y el modelo multilingüe mMARCO puntúa los diez primeros, leyendo la pregunta y el texto de cada fragmento juntos. El generador recibe los cinco mejor puntuados. Se comparó contra los primeros cinco del mismo conjunto en orden RRF y se verificó esa igualdad en cada pasada. El puntaje público de una cita sigue siendo RRF. La traza guarda también el orden previo y los puntajes del cross-encoder. [Modelo y revisión](https://huggingface.co/cross-encoder/mmarco-mMiniLMv2-L12-H384-v1/tree/1427fd652930e4ba29e8149678df786c240d8825)

| 27 consultas originales | Precisión@5 | Recall@5 | Acierto en primer lugar | Latencia mediana | p95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| H2, base → re-ranking | 21,54 → 21,54 % | 100 → 100 % | 23 → 26 de 26 | 7,93 → 169,36 ms | 9,40 → 188,31 ms |
| Ventanas, base → re-ranking | 23,85 → 24,62 % | 96,15 → 100 % | 22 → 24 de 26 | 7,98 → 180,06 ms | 9,07 → 199,11 ms |

La respuesta de renovación de notebooks (`q11`) pasó del puesto 8 al 1 con ventanas. El recall de ventanas ganó 3,85 puntos porcentuales y la mediana aumentó 172,08 ms. En H2, que ya recuperaba toda la evidencia, mejoró la posición del primer resultado. El modo base sigue siendo el predeterminado.

## Multi-query automático

El reformulador conserva la consulta original. Expande abreviaturas de chat y términos laborales, corrige acentos y errores cercanos al vocabulario del índice y puede separar dos subpreguntas. Cada consulta distinta aporta un ranking híbrido. Se fusionan con RRF con el mismo peso y se eligen cinco pasajes. El reformulador usa un glosario y el vocabulario de BM25. No necesita otro LLM. La traza registra el texto emitido y los diez candidatos por consulta. [Implementación](../../src/nubbix_assist/retrieval/rewrite.py)

Se escribieron 27 variantes informales antes de la medición, una por pregunta, conservando la intención y las etiquetas del golden. Cada comparación usa la misma entrada con multi-query apagado y encendido, y re-ranking apagado. Las preguntas originales sirven como control. Las variantes son una muestra construida para este corpus. [27 consultas informales](../../evals/preguntas_informales.json)

| Consultas informales | Precisión@5 | Recall@5 | Acierto en primer lugar | Latencia mediana | p95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| H2, base → multi-query | 16,92 → 18,46 % | 76,92 → 86,54 % | 17 → 18 de 26 | 7,32 → 10,66 ms | 8,93 → 21,29 ms |
| Ventanas, base → multi-query | 20,00 → 20,77 % | 80,77 → 86,54 % | 18 → 16 de 26 | 7,00 → 10,21 ms | 8,37 → 17,64 ms |

Con H2, multi-query recuperó evidencia sobre accesos de producción, Wi-Fi público y viáticos que se perdía con las consultas informales originales. En los dos índices, al preguntar por un equipo dañado durante un viaje (`q18`), conservó el pasaje de IT y perdió el de Finanzas. Con ventanas, aumentó la cobertura media mientras bajaron los aciertos en la primera posición. En el control de preguntas bien formuladas, H2 mantuvo todos sus promedios de calidad y el recall de ventanas subió del 96,15 % al 100 %.

## Reproducir los experimentos

Con el entorno activado, los dos índices preparados y sus identificadores en `BUILD_H2` y `BUILD_WORDS`, ejecutá desde la raíz:

```sh
python ingest/run.py prepare-reranker
PYTHONPATH=src python -m nubbix_assist.cli.query --build "$BUILD_WORDS" --retrieve-only --rerank "¿Cada cuánto reemplazan las notebooks por antigüedad?"
PYTHONPATH=src python -m nubbix_assist.cli.query --build "$BUILD_H2" --retrieve-only --multi-query "necesito acceso a prod, quien lo tiene q aprobar?"
python evals/extra_credits.py --builds "$BUILD_H2" "$BUILD_WORDS" --repeats 3 --threads 4
```

El benchmark escribe `runs/extra-credits/resumen.json` y `preguntas.csv`. El promedio de precisión y recall pondera por igual las 26 preguntas respondibles. El caso de guardería se busca y se cronometra con los demás. Las latencias cubren toda la búsqueda local y excluyen carga del modelo y generación. Se midieron en un Intel Core i9-12900KF con cuatro hilos de PyTorch, modelos precargados, calentamiento inicial y tres pasadas de cada consulta alternando el orden de los modos. En la CLI se pueden combinar ambos flags. Las tablas aíslan cada cambio. [Preparar los índices](evaluacion.md#preparar-los-índices-y-las-etiquetas)

## Interfaz con citas navegables

Desde la raíz, con el mismo entorno virtual del PI:

```sh
python -m pip install -r requirements-ui.txt
python -m streamlit run ui/app.py --server.address 127.0.0.1
```

Abrí la dirección local que imprime Streamlit. **Ejemplos evaluados** reúne las 27 preguntas del golden. En **Respuesta guardada** podés buscar un tema y en **Versión** elegir la respuesta con secciones H2 o con ventanas de 80 palabras. Capacitación también incluye el piloto original. Las 55 respuestas se leen sin índices ni claves. Al pulsar una cita numerada se abre el pasaje y su sección. **Leer el documento completo** resalta ese intervalo en el Markdown original. El lector verifica el hash del archivo y sus offsets. La respuesta de guardería aparece con citas vacías.

En **Nueva consulta**, **Buscar pasajes** usa el índice local. **Generar respuesta** llama al generador configurado en el `.env` del servidor con un máximo de dos intentos. En **Opciones de búsqueda** se eligen el índice y los extras. Se verificaron los enlaces de RR. HH. y Finanzas, el rechazo y la navegación en Chromium con vistas de escritorio y móvil. El envío a generación se probó con el índice real y un transporte de prueba que devolvió la respuesta guardada del piloto. [Captura de la cita de Finanzas](citas-navegables.png)

## Antecedente: piloto manual de cuatro preguntas


Se eligieron cuatro preguntas y se escribieron dos consultas alternativas por pregunta. Cada una de las tres búsquedas produjo hasta diez resultados con el mismo índice. Se fusionaron los tres rankings con Reciprocal Rank Fusion (constante 60, igual peso) y se conservaron cinco fragmentos. Los primeros cinco de cada búsqueda original coincidieron con la evaluación de referencia. El experimento usó los modelos e índices locales y consumió **cero llamadas de API**.

Las celdas muestran las posiciones de **todos** los fragmentos etiquetados como relevantes entre los cinco primeros. El guion indica que ninguno llegó a esos cinco.

| Pregunta | H2 original | H2 multi-query | Ventanas de 80 original | Ventanas de 80 multi-query |
| --- | --- | --- | --- | --- |
| `q06` Permiso para trabajar desde el exterior | 1 | 1 | 1 | 1 |
| `q09` Libros técnicos y rendición de un curso | 1, 2 | 1, 3 | 1, 2, 3 | 1, 2 |
| `q11` Renovación de notebooks | 2 | 1 | — | 1 |
| `q18` Equipo temporal y factura de reintegro | 1, 4 | 1, 4 | 1, 5 | 1 |

Con ventanas, multi-query recuperó el pasaje de `q11` y dejó afuera un fragmento etiquetado en cada pregunta de dos documentos. Con H2 mantuvo la cobertura de evidencia de las cuatro preguntas. Estos resultados exploratorios justifican medir tanto las mejoras como las regresiones en una muestra de preguntas difíciles independiente. El experimento automático de arriba utiliza el mismo golden y 27 formulaciones informales nuevas.

<details>
<summary>Consultas alternativas usadas en el piloto</summary>

| ID | Primera consulta adicional | Segunda consulta adicional |
| --- | --- | --- |
| `q06` | ¿Qué permisos necesito para teletrabajar dieciséis días seguidos en el extranjero? | Si trabajo temporalmente fuera de mi país de residencia, ¿quién debe dar el visto bueno para esas dos semanas y dos días? |
| `q09` | ¿Puedo comprar libros técnicos con el beneficio de formación? | ¿Cómo presento el comprobante de un curso que pagué? |
| `q11` | ¿Con qué frecuencia se cambia la computadora de trabajo? | ¿Cada cuánto toca renovar la laptop de la empresa? |
| `q18` | ¿Cómo consigo una computadora provisoria si la mía se rompe durante un viaje laboral? | ¿Qué comprobante exige la empresa para que me reintegren los gastos de ese incidente durante el viaje? |

Las preguntas originales y las etiquetas por índice están en el [golden revisado](../../evals/dataset.jsonl).

</details>
