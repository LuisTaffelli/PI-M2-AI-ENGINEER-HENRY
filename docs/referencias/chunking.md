# Qué cambia al cortar el corpus

Las tres estrategias trabajan sobre los mismos documentos y usan el mismo modelo de embeddings y buscador. La diferencia está en qué texto viaja junto dentro de un fragmento. Cada H2 suele representar una política, mientras que una ventana corrida puede empezar en una política y terminar en la siguiente. [Corpus](../../data/corpus/) · [Decisión de diseño](../adr/0007-comparar-secciones-y-ventanas-de-palabras.md)

## Cuántos fragmentos produjo cada estrategia

| Estrategia | RR. HH. | IT | Finanzas | Total |
|---|---:|---:|---:|---:|
| `headings_v1` · un fragmento por H2 | 6 | 6 | 6 | 18 |
| `words_v1` · ventanas corridas de 80 palabras con 20 de solapamiento | 8 | 8 | 8 | 24 |
| `section_words_v1` · las mismas ventanas dentro de cada H2 | 8 | 7 | 6 | 21 |

El híbrido reinicia el solapamiento al cambiar de sección y repite el encabezado en el texto indexado. En la pregunta sobre capacitación (`q09`), tanto H2 como el híbrido ubicaron el fragmento de Finanzas primero y el de RR. HH. segundo. La primera ventana corrida recuperada contenía la política de Finanzas junto a texto sobre el cobro de haberes.

## Comparación preliminar de las 27 preguntas

El 22/11/2026 se realizaron 81 búsquedas locales con `top_k=5`. Una pregunta (`q09`) tenía las etiquetas revisadas para las tres estrategias. Las 26 restantes conservaban sus etiquetas en borrador. El promedio de precisión y recall incluye las 26 preguntas respondibles, y el detalle por pregunta está en el CSV en escala de 0 a 1. Las celdas de `q27`, sobre guardería, están vacías porque carece de fragmentos relevantes. La traza local de esta medición es `runs/2765b989f4bd4b56a7a10f42dd1fe8c2/eval.json`. [Tabla comparativa en el README](../../README.md#qué-aprendimos-del-chunking) · [Resultados por pregunta](../../evals/resultados/2026-11-22-retrieval-preliminar.csv)

Por secciones y con el híbrido, 24 de las 26 preguntas respondibles tienen un solo fragmento etiquetado como relevante. Cuando el buscador lo devuelve entre los cinco primeros, la precisión es 1/5 (20 %) y el recall es 1/1 (100 %). En las ventanas corridas, el solapamiento hace que varias preguntas tengan más de un fragmento relevante. Esto ayuda a explicar que su precisión media sea mayor aunque en `q11` se haya perdido la evidencia sobre el plazo de renovación de notebooks. [Política de renovación de equipos](../../data/corpus/it_manual.md#equipos-de-trabajo-y-hardware)

## Qué pasó al usar ventanas de 160 palabras

Se repitieron las 27 consultas con ventanas por sección de 80 y de 160 palabras, manteniendo 20 de solapamiento. Los tres cuerpos de sección que exceden 80 palabras miden 82, 83 y 84. Con 160 todos caben enteros. Verificamos que los 18 fragmentos resultantes coincidieran con H2 en sección y texto, salvo los espacios finales, antes de trasladar sus etiquetas y consultar el índice.

| Ventana por sección | Fragmentos | Precisión@5 | Recall@5 | Primer resultado relevante |
|---|---:|---:|---:|---:|
| 80 palabras | 21 | 21,54 % | 100 % | 20/26 |
| 160 palabras | 18 | 21,54 % | 100 % | 21/26 |

Con 160, un fragmento relevante pasó al primer puesto en `q06`, `q12` y `q18` y bajó al segundo en `q11` y `q26`. Las dos variantes recuperaron toda la evidencia etiquetada en el top 5 en las 26 preguntas respondibles. El híbrido de 80 sigue siendo el que permite estudiar el efecto de subdividir secciones en este corpus. [Cómo reproducir la evaluación principal](evaluacion.md) · [Consigna de Henry](../fuentes/consigna.md) · [Fuente en Aula Viva](https://aula-viva.soyhenry.com/clase/6yf8ZcZ3a3O-)
