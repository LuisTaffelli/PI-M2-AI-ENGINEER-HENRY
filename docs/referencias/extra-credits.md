# Extra credits y bonus

Henry propone tres extras y un bonus de rechazo honesto. El punto de partida es la evaluación de 27 preguntas. El corte por secciones (H2) recuperó toda la evidencia etiquetada entre los primeros cinco resultados y ubicó un fragmento relevante primero en 23 de las 26 preguntas respondibles. Las dos estrategias principales generaron respuestas para el golden completo. [Consigna](../fuentes/consigna.md) · [Resultados de recuperación](../../evals/resultados/2026-11-22-retrieval-golden-revisado.csv) · [Evaluación del flujo principal](evaluacion.md)

## Orden de trabajo y evidencia para la entrega

| Orden | Qué vamos a implementar o probar | Cómo demostrarlo |
| --- | --- | --- |
| 1. Bonus de rechazo honesto | Comprobado para `q27`, la pregunta sobre cupos de guardería que el corpus deja sin respuesta. | Ambas estrategias rechazaron ese caso con citas vacías. Entre las 26 preguntas respondibles, H2 tuvo cero rechazos y ventanas tuvo uno. La ampliación pendiente consiste en evaluar más preguntas fuera de alcance con controles respondibles. [Ejemplo real](../../README.md#bonus-de-rechazo-honesto) |
| 2. Re-ranking con cross-encoder | Recuperar diez candidatos con la búsqueda híbrida. Comparar los cinco primeros del orden actual con los cinco que elija un modelo local apto para español tras puntuar cada par de pregunta y fragmento. | Usar los mismos diez candidatos, las mismas preguntas y el mismo índice en ambos modos. Reportar el cambio en precisión@5, recall@5 y aciertos en el primer puesto. Medir la latencia de recuperación en la misma máquina, con el modelo ya cargado, y reportar la mediana y el percentil 95 de varias pasadas. |
| 3. Multi-query para preguntas mal formuladas | Crear versiones difíciles de preguntas del golden que conserven la intención (abreviaturas, errores de tipeo o vocabulario coloquial). Implementar un reformulador que reciba solo la consulta. Fusionar los resultados de la consulta original y sus reformulaciones. | Fijar las preguntas difíciles y sus etiquetas antes de comparar. Probar cada entrada difícil con y sin reformulación, con el re-ranking apagado en ambas corridas. Reportar las mismas métricas de recuperación, cuánta evidencia se perdió o recuperó por caso y el costo en tiempo o llamadas. Usar las preguntas bien formuladas como control. |
| 4. UI mínima con citas navegables | Una pantalla de Streamlit que reutilice la consulta del CLI. Cada cita de la respuesta abre el documento en la sección correspondiente y muestra el fragmento que la respalda. | Probar en el navegador una pregunta que cite dos documentos (`q09`), abrir ambas citas y cotejar los textos. Probar el rechazo de `q27`. Incluir el comando de arranque y una captura o demo breve. |

El primer diagnóstico para el re-ranking es `q11`. En el índice de ventanas de 80 palabras, el fragmento sobre renovación de notebooks quedó **octavo** tras fusionar la búsqueda léxica y la vectorial. Entra en un conjunto de diez candidatos y queda fuera de los cinco que hoy recibe el generador. En H2 ya está segundo. Medir ambos índices permite ver si el modelo recupera ese pasaje y qué pasa con las consultas que ya funcionaban. [Cómo funciona un cross-encoder en esta etapa](https://www.sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html)

## Primer experimento local de multi-query

Se eligieron cuatro preguntas y se escribieron dos consultas alternativas por pregunta. Cada una de las tres búsquedas produjo hasta diez resultados con el mismo índice. Se fusionaron los tres rankings con Reciprocal Rank Fusion (constante 60, igual peso) y se conservaron cinco fragmentos. Los primeros cinco de cada búsqueda original coincidieron con la evaluación de referencia. El experimento usó los modelos e índices locales y consumió **cero llamadas de API**.

Las celdas muestran las posiciones de **todos** los fragmentos etiquetados como relevantes entre los cinco primeros. El guion indica que ninguno llegó a esos cinco.

| Pregunta | H2 original | H2 multi-query | Ventanas de 80 original | Ventanas de 80 multi-query |
| --- | --- | --- | --- | --- |
| `q06` Permiso para trabajar desde el exterior | 1 | 1 | 1 | 1 |
| `q09` Libros técnicos y rendición de un curso | 1, 2 | 1, 3 | 1, 2, 3 | 1, 2 |
| `q11` Renovación de notebooks | 2 | 1 | — | 1 |
| `q18` Equipo temporal y factura de reintegro | 1, 4 | 1, 4 | 1, 5 | 1 |

Con ventanas, multi-query recuperó el pasaje de `q11` y dejó afuera un fragmento etiquetado en cada pregunta de dos documentos. Con H2 mantuvo la cobertura de evidencia de las cuatro preguntas. Estos resultados exploratorios justifican medir tanto las mejoras como las regresiones en una muestra de preguntas difíciles independiente. El reformulador automático y su evaluación siguen pendientes.

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
