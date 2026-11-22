# Qué cambia al cortar el corpus

Las tres estrategias trabajan sobre los mismos documentos y usan el mismo modelo de embeddings y buscador. La diferencia está en qué texto viaja junto dentro de un fragmento. Cada H2 suele representar una política, mientras que una ventana corrida puede empezar en una política y terminar en la siguiente. [Corpus](../../data/corpus/) · [Decisión de diseño](../adr/0007-comparar-secciones-y-ventanas-de-palabras.md)

## Cuántos fragmentos produjo cada estrategia

| Estrategia | RR. HH. | IT | Finanzas | Total |
|---|---:|---:|---:|---:|
| `headings_v1` · un fragmento por H2 | 6 | 6 | 6 | 18 |
| `words_v1` · ventanas corridas de 80 palabras con 20 de solapamiento | 8 | 8 | 8 | 24 |
| `section_words_v1` · las mismas ventanas dentro de cada H2 | 8 | 7 | 6 | 21 |

El híbrido reinicia el solapamiento al cambiar de sección y repite el encabezado en el texto indexado. En la pregunta sobre capacitación (`q09`), tanto H2 como el híbrido ubicaron el fragmento de Finanzas primero y el de RR. HH. segundo. La primera ventana corrida recuperada contenía la política de Finanzas junto a texto sobre el cobro de haberes.

## Secciones e híbrido con el dataset aprobado

En el corte por secciones, todo el cuerpo bajo un H2 se indexa y se cita junto. El híbrido conserva ese encabezado en cada ventana y divide el cuerpo al superar 80 palabras, con 20 compartidas entre ventanas consecutivas. De las 18 secciones del corpus, solo tres superan el umbral. Con políticas breves, el corte por H2 evita duplicar parte del texto. En secciones extensas, las ventanas acotan el pasaje que puede recuperar la consulta, aunque un corte también puede separar una condición de la regla que la explica.

La pregunta sobre días de examen (`q02`) ilustra las dos caras del solapamiento. H2 recuperó primero las 84 palabras de «Licencias y Vacaciones». El híbrido recuperó primero una ventana de 24 palabras con ambos límites (2 días por examen y 10 al año), y en tercer lugar otra ventana de esa misma sección. El pasaje más específico facilita verificar la respuesta, aunque dos de los cinco puestos del contexto corresponden a la misma política. [Política de licencias](../../data/corpus/hr_policies.md#licencias-y-vacaciones)

La corrida de recuperación con las 27 etiquetas revisadas colocó evidencia relevante en primer lugar para 23 de las 26 preguntas respondibles con H2 y para 21 con el híbrido. Los dos alcanzaron 21,54 % de precisión@5 y 100 % de recall@5. Se eligió H2 para este corpus por el orden de los resultados, la integridad de las políticas y sus 18 fragmentos frente a los 21 del híbrido. La traza local es `runs/b399821329934b418a95671c814f623b/eval.json`. El CSV incluye la posición del primer fragmento relevante dentro de los cinco recuperados. [Resultados de recuperación por pregunta](../../evals/resultados/2026-11-22-retrieval-golden-revisado.csv)

## Comparación preliminar de las 27 preguntas

El 22/11/2026 se realizaron 81 búsquedas locales con `top_k=5`. Una pregunta (`q09`) tenía las etiquetas revisadas para las tres estrategias. Las 26 restantes conservaban sus etiquetas en borrador. El promedio de precisión y recall incluye las 26 preguntas respondibles, y el detalle por pregunta está en el CSV en escala de 0 a 1. Las celdas de `q27`, sobre guardería, están vacías porque carece de fragmentos relevantes. La traza local de esta medición es `runs/2765b989f4bd4b56a7a10f42dd1fe8c2/eval.json`. [Resultados por pregunta de la primera corrida](../../evals/resultados/2026-11-22-retrieval-preliminar.csv)

Por secciones y con el híbrido, 24 de las 26 preguntas respondibles tienen un solo fragmento etiquetado como relevante. Cuando el buscador lo devuelve entre los cinco primeros, la precisión es 1/5 (20 %) y el recall es 1/1 (100 %). En las ventanas corridas, el solapamiento hace que varias preguntas tengan más de un fragmento relevante. Esto ayuda a explicar que su precisión media sea mayor aunque en `q11` se haya perdido la evidencia sobre el plazo de renovación de notebooks. [Política de renovación de equipos](../../data/corpus/it_manual.md#equipos-de-trabajo-y-hardware)

### Segunda medición tras revisar las etiquetas

Se precisó la condición de días consecutivos en la pregunta de trabajo remoto (`q06`) y se añadió una segunda ventana válida a la pregunta de contraseñas (`q13`). Las dos ventanas contienen el mínimo de 16 caracteres y el vencimiento a 90 días. Al repetir las 81 búsquedas, solo cambió la puntuación de `q13` con ventanas corridas. Su precisión@5 pasó de 1/5 a 2/5, con recall@5 del 100 %. Esto elevó la precisión media de esa estrategia de 23,08 % a 23,85 %. Se mantuvo su recall medio de 96,15 % y las métricas de las otras dos estrategias. La traza local de esta corrida es `runs/771f2c3653c64ab8985f9594f7d3c1f3/eval.json`. [Resultados actualizados por pregunta](../../evals/resultados/2026-11-22-retrieval-etiquetas-corregidas.csv) · [Tabla del README](../../README.md#qué-aprendimos-del-chunking)

## Qué pasó al usar ventanas de 160 palabras

Este experimento usó las 27 preguntas de la primera corrida con ventanas por sección de 80 y de 160 palabras, manteniendo 20 de solapamiento. Los tres cuerpos de sección que exceden 80 palabras miden 82, 83 y 84. Con 160 todos caben enteros. Verificamos que los 18 fragmentos resultantes coincidieran con H2 en sección y texto, salvo los espacios finales, antes de trasladar sus etiquetas y consultar el índice.

| Ventana por sección | Fragmentos | Precisión@5 | Recall@5 | Primer resultado relevante |
|---|---:|---:|---:|---:|
| 80 palabras | 21 | 21,54 % | 100 % | 20/26 |
| 160 palabras | 18 | 21,54 % | 100 % | 21/26 |

Con 160, un fragmento relevante pasó al primer puesto en `q06`, `q12` y `q18` y bajó al segundo en `q11` y `q26`. Las dos variantes recuperaron toda la evidencia etiquetada en el top 5 en las 26 preguntas respondibles. El híbrido de 80 sigue siendo el que permite estudiar el efecto de subdividir secciones en este corpus. [Cómo reproducir la evaluación principal](evaluacion.md) · [Consigna de Henry](../fuentes/consigna.md) · [Fuente en Aula Viva](https://aula-viva.soyhenry.com/clase/6yf8ZcZ3a3O-)
