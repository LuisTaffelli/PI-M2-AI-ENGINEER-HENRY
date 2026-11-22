# Uso de IA y decisiones de desarrollo

## 20/11/2026 · Preparación inicial

**Pedido de Luis:** «Bueno, arranquemos a hacer el proyecto porque sino me olvidare jklasdjsakld».

**Asistencia de Codex:** recuperó el contexto del repaso de M2-L3, leyó la consigna local y los tres documentos del ZIP del corpus, preparó la estructura inicial y copió los originales conservando sus bytes. Registró hashes y verificó los conteos de documentos y secciones.

**Propuesta para aprender:** avanzar en incrementos cortos empezando por cargar los Markdown. La modalidad de acompañamiento se consultó; todavía no se registra una respuesta de Luis a esa consulta.

**Hallazgo:** hay 18 secciones H2. Una estrategia de un chunk por sección daría 18; al menos una estrategia debe producir 20 o más, y el requisito se comprobará con la implementación real.

**Decisiones pendientes:** estrategias y parámetros de chunking, modelo de embeddings, base vectorial, proveedor de generación y formato detallado de las etiquetas del golden. No se fijaron etiquetas ni se generaron métricas.

Esta preparación no incluye llamadas a modelos ni instalación de dependencias. No representa el proyecto terminado ni una entrega académica.

## 20/11/2026 · Arquitectura antes del código

**Pedido de Luis:** «Primero hagamos la arquitectura bien solida antes de hacer cualquier tipo de codigo porfis xd».

**Cambio de dirección:** el ejercicio del cargador se pospone. La prioridad confirmada es revisar la arquitectura antes de implementar.

**Decisión de Luis:** «Mixto: embeddings locales y LLM por API». La ingesta y recuperación serán locales; generación y juez de groundedness usarán una API. El proveedor y los modelos específicos siguen abiertos.

**Asistencia de Codex:** releyó la consigna y los documentos del proyecto, verificó conteos de palabras/secciones y preparó ARQUITECTURA.md, CONTRATOS.md y DECISIONES.md. Propuso tres flujos, módulos con límites, builds independientes con catálogo/Chroma/BM25, publicación tras verificación, contratos de citas y evaluación con etiquetas por estrategia.

**Influencia técnica:** propuso H2 frente a ventanas de 80 palabras con overlap de 20, RRF con parámetros explícitos, un modelo local multilingüe como candidato y un único núcleo de consulta compartido con las evals. Las propuestas se distinguen de requisitos y de elecciones confirmadas por Luis.

**Fuentes técnicas:** documentación oficial de Chroma, Sentence Transformers y ficha de multilingual-e5-small, enlazadas en ARQUITECTURA.md. Se consultaron para comprobar capacidades, no para afirmar una integración instalada o un rendimiento medido.

**Pendientes:** revisar la arquitectura con Luis, elegir proveedor/modelos finales, fijar presupuesto y dependencias y cerrar la política léxica antes del primer incremento.

Se editaron documentos Markdown. No se añadió código de aplicación ni se instalaron paquetes o conectaron modelos.

## 20/11/2026 · Registro de decisiones en ADR

**Pedido de Luis:** organizar las decisiones en una carpeta ADR dentro de docs para evitar un DECISIONES.md monolítico.

**Asistencia de Codex:** migró el registro inicial a docs/adr/, con índice, plantilla y un archivo por decisión. Conservó las dos elecciones aceptadas de Luis y las once propuestas técnicas, incluyendo su correspondencia A01–A11, alternativas y pendientes.

**Resultado documental:** se reemplazó DECISIONES.md por los ADR individuales y se actualizaron los enlaces del README y la arquitectura. La mención anterior a su creación se conserva como historia del trabajo.

La reorganización no acepta propuestas adicionales ni introduce código del proyecto. Se verificaron enlaces locales, numeración y estados.

## 20/11/2026 · Revisión del límite de aplicación

**Pedido de Luis:** «Bueno sigamos n.n».

**Asistencia de Codex:** abrió la primera propuesta pendiente, ADR 0003, y precisó los casos de uso de ingesta, recuperación, respuesta y evaluación. Separó la entrada CLI/HTTP del núcleo y dejó explícito que las evals deben medir la recuperación usada en la respuesta, sin repetirla para reconstruir el contexto.

**Consulta pendiente:** preferencia de Luis entre CLI inicial y endpoint HTTP. La API del proveedor LLM ya elegida es un límite diferente de una API propia de la aplicación. ADR 0003 conserva su estado Propuesta.

Los cambios son documentales y no agregan implementación.

## 20/11/2026 · Aceptación de CLI y modularidad por proveedor

**Pedido de Luis:** aceptó la propuesta de CLI con núcleo reutilizable y pidió separar componentes por proveedores y sus validadores, usando embeddings como ejemplo de lo que no debe concentrarse en un solo script.

**Decisiones registradas:** ADR 0003 pasa a Aceptada. Se agrega ADR 0014, Aceptada, con la regla de separación por funcionalidad, proveedor y nivel de validación.

**Asistencia de Codex:** preparó MODULARIDAD.md con el contrato y servicio de embeddings, validadores comunes, adaptador/configuración/validadores de proveedor y ensamblado explícito. Actualizó la arquitectura para usar paquetes por funcionalidad y contratos propios, y trasladó la misma regla a LLM, vector store, chunking, retrieval y evaluación.

**Criterio:** proveedor y modelo son conceptos distintos; un modelo nuevo dentro del mismo proveedor se expresa mediante configuración. Los proveedores elegidos se ensamblan fuera de los casos de uso. Los validadores comunes se reutilizan y los específicos quedan junto al proveedor.

Chroma y el modelo de embeddings mantienen su estado de propuesta; el proveedor API sigue pendiente. Los cambios son documentación, sin código del proyecto.

## 20/11/2026 · Contratos como paquete

**Pedido de Luis:** expresó que le gusta la estructura y propuso alojar los contratos compartidos entre proveedores en una carpeta.

**Decisión:** ADR 0015, Aceptada. El diseño usa embeddings/contracts/ con interfaz, entradas, salidas y especificación del espacio en módulos propios. Se conserva el criterio por funcionalidad para LLM y vector store.

**Asistencia de Codex:** actualizó el árbol y las responsabilidades del diseño, vinculó el nuevo ADR y aclaró las dependencias: servicio y adaptadores comparten el contrato; bootstrap selecciona el proveedor.

La modificación afecta documentos; no se crearon archivos Python ni se cambió la modalidad mixta acordada.

## 20/11/2026 · Ruta de cierre y almacenamiento

**Pedido de Luis:** identificar con qué seguir para terminar la arquitectura.

**Asistencia de Codex:** organizó el cierre en cuatro bloques dentro del índice ADR y precisó que los parámetros óptimos se miden durante la implementación, mientras los límites, contratos, errores y criterios de aceptación se definen antes.

**Primer bloque desarrollado:** ALMACENAMIENTO.md distingue vector store, catálogo/manifests y estado BM25; define el paquete de contratos del backend y el ciclo de publicación/consulta de un build.

Los ADR 0004–0013 conservan su estado Propuesta. Esta revisión no elige el backend ni los modelos y no agrega implementación.

## Acuerdo sobre el recorrido de los cuatro bloques

Luis indicó «Dale me parece bien avanzar asi» al revisar la propuesta conjunta. Se registraron Chroma local, los builds independientes verificados, la búsqueda híbrida con citas, el uso de la misma recuperación para evaluar y los dos intentos totales de generación. Los cortes 80/20, el detalle del versionado de corridas y el modelo concreto conservan su carácter de propuestas.

Codex contrastó la pregunta de capacitación con las dos fuentes y simuló los límites de las ventanas sobre los Markdown originales. El contraste documenta un caso para revisar durante el etiquetado humano. La selección de proveedores, el presupuesto de ejecución y las métricas quedan para sus respectivos incrementos.

## 20/11/2026 · Creación de la estructura del proyecto

Luis pidió crear las carpetas y los archivos de la arquitectura acordada. Codex preparó los paquetes por componente, los contratos y los espacios de adaptadores y validadores. Los módulos describen su responsabilidad. Las plantillas de prompts y el golden quedan para completar durante los próximos incrementos.

## Primer corte por sección

Luis pidió continuar con el ejemplo de «Beneficios». Codex implementó la carga de Markdown, el corte por H2 y el comando de inspección. El cuerpo conserva el intervalo original y el título se agrega por separado al texto preparado. Se comprobó el caso de RR. HH. y se incorporaron pruebas de trazabilidad con acentos y saltos de línea CRLF.

## Implementación del RAG y preparación del golden

Luis pidió completar las implementaciones y eligió OpenAI y Gemini. Codex implementó los cortes, índices, recuperación híbrida, validación de citas, adaptadores y runner en commits separados. Se construyeron ambos índices con los originales y se reabrieron en un proceso independiente. El golden incluye 27 propuestas con extractos y etiquetas por estrategia. La revisión de Luis, las llamadas a modelos remotos y la comparación formal siguen pendientes.

## 22/11/2026 · Revisión de capacitación y tercera estrategia

Luis aprobó las etiquetas de la pregunta de capacitación para H2 y ventanas corridas, y propuso combinar ambos métodos para evitar mezclar temas. Codex implementó ventanas 80/20 dentro de cada sección, preparó etiquetas candidatas a partir de los extractos del corpus y verificó la consulta en los tres índices locales. Las etiquetas del híbrido quedan para la revisión humana y la elección final depende de la comparación sobre el golden.

## 22/11/2026 · Cotejo conjunto del dataset

Luis aprobó las preguntas 09, 11 y 18 a 26 para las tres estrategias. Al pedir que el cotejo restante se hiciera en una sola tanda, Codex contrastó las otras 16 preguntas con el corpus y los catálogos de fragmentos. Precisó los días consecutivos en la 06 y añadió una segunda ventana que conserva la regla de contraseñas en la 13. Se repitió la medición preliminar local con esas correcciones. La [tabla de revisión](referencias/revision-golden.md) reúne la evidencia de los casos que quedaban pendientes de aprobación humana.

Luis leyó la tabla y aprobó los 16 casos restantes. Codex registró la aprobación en el dataset y corrió la evaluación local con las 27 preguntas revisadas. La comparación de secciones e híbrido se basa en los fragmentos y rankings de esa corrida. [Resultados de recuperación](referencias/chunking.md#secciones-e-híbrido-con-el-dataset-aprobado)

## 22/11/2026 · Evaluación con los dos proveedores

Luis configuró las credenciales locales y aprobó el piloto de capacitación y, después, un máximo de 162 llamadas para comparar H2 y ventanas. OpenAI generó las respuestas y Gemini evaluó el respaldo de sus afirmaciones. Codex cotejó las citas con los archivos originales, recuperó los veredictos pendientes tras errores temporales del juez y documentó las métricas y los rechazos. [Resultados y consumo](referencias/evaluacion.md#resultados-del-22-de-noviembre-de-2026)

## 22/11/2026 · Re-ranking, multi-query e interfaz

Luis pidió implementar los tres extra credits. Codex integró el cross-encoder local y la reformulación por vocabulario, redactó 27 versiones informales de las preguntas y comparó los rankings contra los del buscador base. Para verificar las citas navegables usó las respuestas guardadas del proyecto y los documentos originales. Estas pruebas usaron cero llamadas a OpenAI y Gemini. [Resultados y captura](referencias/extra-credits.md)

Luis pidió aplicar su estilo Mochi al lector y sumar un pequeño cerezo. Codex generó con IA el paisaje de la cabecera y el cerezo en flor que aparece al pie de la página. Ambas ilustraciones y la tipografía Baskervville se sirven desde el repositorio. [Captura del lector](referencias/citas-navegables.png) · [Licencia de la tipografía](../ui/static/fonts/Baskervville-OFL.txt)
