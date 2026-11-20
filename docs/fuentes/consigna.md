Contexto y Objetivos
Contexto y Objetivos

Sos un/a AI Engineer de Nubbix, el SaaS de gestión para pymes de LATAM para el que construiste el servicio de triage de tickets en el Módulo 1. La empresa creció a 350 empleados y su conocimiento interno no acompañó ese crecimiento: las políticas de HR (licencias, beneficios, home office), el manual de IT (accesos, equipos, seguridad) y los procesos de Finance (reintegros, viáticos, compras) viven dispersos en PDFs, wikis y mails. Los equipos de People e IT pierden horas por semana respondiendo las mismas preguntas, y las respuestas no siempre coinciden con la política vigente.

Tu misión: construir Nubbix Assist, el asistente de conocimiento interno de la empresa — un chatbot que responde las preguntas de los empleados a partir de la documentación oficial y cita siempre las fuentes que usó para responder. El corpus documental lo provee Henry.

Podés reutilizar componentes propios de tu proyecto de M1 (cliente LLM, registro de métricas, estructura de evals); se recomienda, pero no es obligatorio: el proyecto se puede resolver de forma completa sin depender de la entrega anterior.

🎯 Objetivos (qué vas a entregar y por qué importa)
Construir un pipeline de ingesta reproducible: procesamiento del corpus, chunking con una estrategia justificada y generación de embeddings. Ingesta y consulta son procesos separados: el índice se construye una vez por comando y se consulta todas las veces que haga falta.
Montar el índice en una vector DB y servir búsqueda híbrida (léxica + vectorial). La búsqueda vectorial sola falla con términos exactos (nombres de plataformas, montos, canales de Slack); la léxica sola falla con sinónimos. Combinarlas es lo que hace robusto al retrieval.
Decidir con datos: comparar dos estrategias de chunking sobre el mismo corpus y elegir una en base a métricas de retrieval, no a intuición. Esta comparación es un entregable central del módulo, no un anexo.
Evaluar el sistema separando retrieval de generación: precision/recall de los chunks recuperados contra un golden dataset, y groundedness de las respuestas (que lo que responde el asistente se sostenga en los chunks que cita). Si el sistema responde mal, primero tenés que poder saber cuál de las dos etapas falla.

¿Por qué esto es importante? RAG es la forma estándar de conectar un LLM con conocimiento privado y actualizable sin reentrenarlo. Pero un RAG que "parece funcionar" en una demo puede estar recuperando los chunks equivocados o inventando datos con tono convincente. Saber construir el pipeline, medirlo por etapas y defender cada decisión con números es lo que separa un prototipo de un sistema en el que una empresa puede confiar.

📢 Consigna

Construir un chatbot de conocimiento interno que responde preguntas sobre la documentación de la empresa citando las fuentes.

El sistema procesa el corpus provisto, lo divide en chunks (al menos 20 chunks resultantes con, como mínimo, una de tus dos estrategias), genera embeddings, indexa en una vector DB y responde consultas con búsqueda híbrida. Cada respuesta se devuelve en JSON con el contrato {user_question, system_answer, chunks_related}, donde chunks_related contiene los chunks usados para responder, identificados de forma que la cita se pueda rastrear hasta su documento de origen.

El proyecto incluye una comparación documentada de dos estrategias de chunking sobre el mismo corpus, decidida con métricas de retrieval, y una suite de evals ejecutable por comando que mide por separado retrieval (precision/recall contra un golden dataset que construís vos) y generación (groundedness).

Bonus/opcional dentro de la consigna: rechazo honesto — cuando la respuesta no está en la base documental, el asistente lo dice en lugar de inventar. El comportamiento se incluye en el golden dataset (preguntas fuera de alcance) y se mide en la suite de evals.

📄 Corpus provisto

El corpus está formado por tres documentos en Markdown, ubicados en data/corpus/:

Documento	Contenido
hr_policies.md	Licencias y vacaciones, home office, ausentismo, cumpleaños, feriados y beneficios.
it_manual.md	Accesos y permisos, equipos, contraseñas y MFA, seguridad de datos, mesa de ayuda y offboarding.
finance_processes.md	Reintegros y viáticos, compras, pago de haberes, capacitación, bonos y facturación.

Los documentos están organizados por secciones con encabezados, y algunos temas cruzan documentos (por ejemplo, el crédito de capacitación aparece en HR y su rendición en Finance). Tené esto en cuenta al diseñar tus estrategias de chunking y tu golden dataset.

Ejemplos ilustrativos de preguntas
Ejemplos ilustrativos de preguntas

No vas a recibir un golden dataset armado — construirlo es parte del proyecto. Estos ejemplos son solo una referencia de los tipos de pregunta que tu dataset debería cubrir, no una lista para copiar:

Directa: "¿Con cuánta anticipación tengo que pedir las vacaciones?"
Con sinónimos (no repite las palabras del documento): "¿Cuánta plata me dan por mes para pagar internet en casa?"
Cruza documentos: "Si me roban la notebook durante un viaje de trabajo, ¿qué tengo que hacer y puedo pedir reintegro de los gastos?"
Con distractor cercano: "¿Cuántos días me corresponden por casamiento?" (la respuesta convive en la misma sección con otras licencias parecidas)
Fuera de alcance (bonus): "¿Nubbix tiene estacionamiento para empleados en la oficina?"

Entregables del proyecto y requisitos de entrega
Entregables del proyecto y requisitos de entrega

Enviar mediante un enlace público al repositorio en Git. Asegurate de que el repositorio sea autocontenido y que se pueda ejecutar sin depender de elementos externos no documentados.

📂 Estructura de repositorio esperada
Entregable	Archivo/Formato	Contenido mínimo
Corpus documental	data/corpus/	Los tres documentos provistos por Henry, sin modificar (o instrucciones claras de descarga en el README).
Pipeline de ingesta	ingest/ (ej. ingest/ingest.py + ingest/chunking.py)	Corre por comando de cero al índice completo: carga el corpus, aplica la estrategia de chunking elegida por parámetro (las dos estrategias implementadas), genera embeddings e indexa cada chunk con sus metadatos (documento de origen, sección, estrategia).
Índice en vector DB	Chroma local persistente (o una DB gestionada)	Índice persistido en disco o en la nube: consultar no implica volver a indexar. Cada estrategia de chunking se indexa por separado (por ejemplo, una colección por estrategia) para poder compararlas.
Servicio de consulta	src/ (CLI o endpoint)	Recibe la pregunta; ejecuta búsqueda híbrida (léxica + vectorial) con un método de combinación documentado; genera la respuesta con un LLM usando solo los chunks recuperados; devuelve JSON con {user_question, system_answer, chunks_related} y citas a los chunks usados.
Prompts	prompts/*.yaml (recomendado)	Prompt de generación y prompt del juez de groundedness fuera del código, como en M1.
Golden dataset	evals/dataset.jsonl	≥25 preguntas, cada una con sus chunks esperados etiquetados. Incluye preguntas difíciles (sinónimos, preguntas que cruzan documentos), no solo las obvias.
Suite de evals	evals/runner.py	Script ejecutable por comando (no framework de testing) que mide retrieval (precision y recall) y generación (groundedness) por separado, para cada estrategia de chunking, y reporta los resultados.
Comparación de chunking	Sección en el README.md	Tabla con las métricas de retrieval de ambas estrategias, medidas con el mismo dataset y el mismo top_k, y la decisión final justificada con esos números.
README	README.md	Setup y uso (con ejemplo de comando y respuesta JSON), descripción del corpus, decisiones de chunking con la comparación y sus números, resultados de evals de retrieval y generación, decisiones técnicas (modelo de embeddings, vector DB, método de búsqueda híbrida).
Configuración	.env.example, requirements.txt	Variables de entorno documentadas (nunca credenciales reales); dependencias declaradas.
Rechazo honesto (bonus)	Casos en evals/dataset.jsonl + sección en el README	Preguntas fuera de alcance marcadas en el dataset, métrica de rechazo correcto reportada por el runner y ejemplo documentado en el README.
🧾 Formato de salida esperado

El formato exacto de chunk_id y los campos adicionales los definís vos; lo mínimo es que cada chunk citado permita identificar su documento de origen y su contenido.

{
  "user_question": "¿Hasta qué día del mes puedo cargar una rendición de gastos?",
  "system_answer": "Las rendiciones se cargan en ExpenseHub antes del día 25 de cada mes; las que se ingresan después se procesan en el ciclo de pagos del mes siguiente [finance_processes.md_0].",
  "chunks_related": [
    {
      "chunk_id": "finance_processes.md_0",
      "source": "finance_processes.md",
      "content": "## Reintegro de Gastos y Viáticos\n...",
      "score": 0.87
    }
  ]
}


Tené en cuenta lo aprendido en el Módulo 2: embeddings y similitud (Clase 1), estrategias de chunking y metadatos (Clase 2), vector databases y búsqueda híbrida (Clase 3), técnicas de retrieval avanzado (Clase 4) y evaluación de sistemas RAG (Clase 5).

✅ Checklist de entrega
Claves de API cargadas por variable de entorno, nunca en el código.
La ingesta corre de cero con un solo comando por estrategia y deja el índice persistido.
Al menos una consulta ejecutada que devuelva JSON válido con citas a chunks reales del índice.
Suite de evals corrida sobre las dos estrategias, con resultados reflejados en el README.
README y código consistentes entre sí: alguien que clone el repo debería poder instalarlo, indexar y consultar sin preguntarte nada.

Evaluación
Evaluación

La corrección se realiza mediante rúbrica, con niveles Excelente / Satisfactorio / Insuficiente por categoría. El puntaje mínimo de aprobación es 70/100; un puntaje de 81 a 100 se considera que supera lo esperado.

Categorías evaluadas:

Ingesta y reproducibilidad — pipeline de ingesta por comando de principio a fin, indexación en vector DB y búsqueda híbrida (léxica + vectorial) funcionando.
Estrategia de chunking — comparación de dos estrategias medida contra el golden dataset y decisión fundamentada con números.
Calidad del retrieval — golden dataset (≥25 preguntas, con casos complejos o que cruzan documentos) y medición de precision y recall separada de la generación.
Groundedness y respuestas — contrato JSON con citas y evaluación automatizada (LLM-as-judge) de que las respuestas se sostienen en los chunks citados.
Código y README — modularidad (/src, /ingest, /evals), README con setup, corpus, decisiones técnicas, números comparativos y conclusiones.

El bonus (rechazo honesto) y los extra credits no son requisito de aprobación. Si los abordás, documentalos con su efecto medido.

⭐ Extra credit (opcional)
Re-ranking con cross-encoder, con el delta de métricas medido contra el pipeline sin re-ranking (y su costo en latencia).
Query rewriting / multi-query para preguntas mal formuladas, con su efecto medido.
UI mínima (Streamlit o similar) con las citas navegables. No se ve en el módulo: es una milla extra de investigación propia.

Guía para el desarrollo del proyecto integrador
Guía para el desarrollo del proyecto integrador
Propósito de esta guía

Esta guía te acompaña en el desarrollo del Proyecto Integrador de AI Engineering correspondiente al Módulo 2. No reemplaza la consigna ni define pasos obligatorios: te orienta para que puedas organizarte, priorizar correctamente y evitar errores comunes.

El foco está en ayudarte a construir un MVP funcional, medido y bien documentado, alineado con los estándares esperados para un perfil Junior en AI Engineering.

Qué se espera del proyecto

Se espera que desarrolles un asistente RAG que responda sobre la documentación de Nubbix aplicando lo aprendido en el módulo, y que cumpla con los requisitos definidos en la consigna oficial.

Más allá de la cantidad de funcionalidades, se valorará especialmente:

Que la ingesta y la consulta funcionen de punta a punta, como procesos separados.
Que cada respuesta cite chunks reales y que esas citas sostengan lo que se responde.
Que las decisiones de chunking y de búsqueda estén respaldadas por métricas, no por intuición.
Que el código sea legible, modular y esté versionado con Git.
Que la documentación permita entender, instalar y ejecutar el sistema sin ayuda externa.
Cómo orientar el desarrollo

Antes de escribir código:

Leé la consigna completa y los tres documentos del corpus. Conocer el corpus es la base de todas tus decisiones.
Identificá las funcionalidades mínimas obligatorias y las opcionales (bonus y extra credits).
Definí una estructura simple (ingest/, src/, evals/, data/, prompts/) antes de empezar.
Pensá qué metadatos va a llevar cada chunk (documento, sección, estrategia): los vas a necesitar para citar y para evaluar.

Durante el desarrollo:

Priorizá el flujo mínimo: una estrategia de chunking, búsqueda vectorial y una respuesta con citas. Recién después sumá la búsqueda léxica, la fusión híbrida y la segunda estrategia.
Leé tus chunks a ojo antes de medir nada: la mitad de los problemas de RAG se detectan leyendo 20 chunks (cortes a mitad de una lista, secciones sin su encabezado, chunks demasiado cortos para tener sentido solos).
Empezá el golden dataset temprano, a medida que conocés el corpus. Las métricas formales se trabajan en la Clase 5, pero las preguntas y sus chunks esperados las podés ir armando desde el principio.
Probá el asistente con preguntas variadas, incluidas las que usan sinónimos o cruzan documentos.
Hacé commits pequeños y descriptivos.

Al finalizar:

Borrá el índice local y corré la ingesta desde cero, idealmente desde un clon nuevo del repositorio.
Verificá que el JSON de salida sea consumible por otro sistema sin transformaciones adicionales.
Confirmá que los números del README coinciden con lo que reporta tu runner.
Revisá que las credenciales sensibles no queden expuestas en el repositorio.
Buenas prácticas recomendadas

Chunking

Elegí dos estrategias que realmente se diferencien (por ejemplo, tamaño fijo con overlap vs. por estructura de encabezados); comparar dos variantes casi iguales no aporta información.
Hacé que la estrategia se seleccione por parámetro en el comando de ingesta, para poder reproducir ambas.
Si un chunk pierde su encabezado al subdividirse, repetilo: el chunk debe entenderse por sí solo.
Documentá los parámetros de cada estrategia (tamaño, overlap, límites) y por qué los elegiste.

Embeddings e indexación

Usá el mismo modelo de embeddings para indexar y para consultar; mezclarlos rompe la comparación de similitud.
Registrá en el README qué modelo usaste, sus dimensiones y la métrica de distancia configurada en la vector DB.
No re-indexes en cada consulta: la ingesta construye el índice, la consulta solo lo lee.

Búsqueda híbrida

Documentá cómo combinás los resultados léxicos y vectoriales (por ejemplo, Reciprocal Rank Fusion o una suma ponderada) y con qué parámetros.
Revisá casos concretos donde la búsqueda léxica rescata lo que la vectorial pierde, y al revés: son la mejor evidencia de que la hibridación está funcionando.

Golden dataset y evals

Los chunks esperados dependen de la estrategia de chunking: un mismo dato puede quedar en chunks distintos según cómo cortes el corpus. Etiquetá los chunks esperados para cada estrategia, así la comparación usa la misma fórmula en ambas.
Incluí preguntas difíciles: sinónimos, preguntas que cruzan documentos y preguntas con distractores cercanos.
Medí siempre con el mismo dataset y el mismo top_k al comparar.
Interpretá precision y recall juntas: si la mayoría de tus preguntas tiene un solo chunk esperado y recuperás 3, precision@3 tiene un techo cercano a 0.33 aunque el sistema funcione bien. Recall, hit rate y MRR ayudan a completar la lectura.
Separá la evaluación de retrieval de la de generación: primero confirmá que el chunk correcto llega al contexto; después, que la respuesta se sostiene en él.

Generación y citas

Indicá en el prompt que la respuesta debe basarse únicamente en los chunks provistos y citar sus identificadores.
Si abordás el bonus, definí una respuesta de rechazo explícita y consistente, para poder medirla automáticamente.
Versioná los prompts de generación y del juez en archivos YAML, como en M1.

Calidad del código

Separá responsabilidades: chunking, embeddings, vector store, retriever híbrido, generación y evals no deberían vivir en el mismo archivo.
Usá nombres que expliquen la intención y extraé la lógica repetida.
No armes un framework propio: la complejidad va a las decisiones de retrieval y a los evals, no a la arquitectura.

Documentación

Tu README es la primera impresión del proyecto. Debe permitir que alguien más lo entienda, lo instale y lo ejecute sin preguntarte nada.
Presentá la comparación de chunking como tabla y cerrala con una decisión explícita, incluyendo los trade-offs que encontraste (una estrategia puede ganar en unas métricas y perder en otras).
Documentá las limitaciones conocidas de tu solución.

Git y GitHub

Usá mensajes de commit claros (por ejemplo: feat: agregar búsqueda híbrida con RRF).
Versioná el proyecto desde el inicio.
No subas el índice persistido, credenciales ni dependencias instaladas: configurá el .gitignore desde el principio.
Errores comunes a evitar
Saltar a los extra credits (re-ranking, UI) antes de tener el flujo principal funcionando y medido.
Dejar credenciales sensibles dentro del código fuente.
Re-indexar el corpus en cada consulta.
Comparar estrategias de chunking con datasets, top_k o fórmulas distintas.
Armar un golden dataset solo con preguntas obvias que repiten las palabras del documento.
Evaluar únicamente la respuesta final, sin saber si el problema está en el retrieval o en la generación.
Citar chunks que no sostienen lo que dice la respuesta.
Re-rankear todo por defecto sin medir su efecto ni su costo en latencia.
No probar la ingesta desde cero antes de entregar.
Sobre el uso de IA

Podés utilizar herramientas de IA como apoyo durante el desarrollo, siguiendo lo aprendido en el módulo. Documentá los prompts que usaste y explicá cómo influyeron en las decisiones técnicas del proyecto. Si usás IA para generar preguntas del golden dataset, revisá y etiquetá vos cada una contra el corpus: un dataset mal etiquetado invalida todas tus métricas. El objetivo del Proyecto Integrador es demostrar tu comprensión sobre cómo se construye y se evalúa un sistema RAG, no delegar esa comprensión a otra herramienta.

Cierre

Esta guía está pensada para ayudarte a tomar buenas decisiones técnicas y de organización. El objetivo final es que puedas demostrar que comprendés el flujo completo de un sistema RAG — desde la ingesta y el chunking hasta la búsqueda híbrida, la generación con citas y su evaluación por etapas — y que podés entregar una solución funcional, medida y bien presentada.
