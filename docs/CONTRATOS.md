# Contratos de datos y aceptación

Contratos de diseño para el primer incremento. Los criterios de aceptación se comprobarán al implementar.

Estos registros son los límites entre módulos de [la arquitectura](ARQUITECTURA.md). Su validación concreta se fijará antes de programar.

En la implementación, cada funcionalidad tendrá sus contratos y validadores: documentos en ingestion/, chunks en chunking/, manifests en artifacts/, embeddings en embeddings/, candidatos en retrieval/, respuestas en generation/ y etiquetas/métricas en evals/. Este documento es una vista conjunta, no un archivo global de código. [MODULARIDAD.md](MODULARIDAD.md) define el límite entre validadores comunes y particulares del proveedor.

Los contratos se alojarán en el paquete contracts/ de su funcionalidad. En embeddings se separan provider.py, inputs.py, outputs.py y spec.py; el servicio y los adaptadores consumen las mismas definiciones, sin depender de un proveedor concreto.

## 1. Documento y chunk

Documento conserva source (ruta relativa), title, source_sha256 de los bytes y raw_text UTF-8 sin reescrituras ni cambios de saltos de línea.

| Campo del chunk | Significado |
|---|---|
| chunk_id | ID determinista y diferente entre estrategias |
| source, source_sha256 | Documento y versión exacta |
| strategy, strategy_fingerprint | Regla/versionado y huella de parámetros |
| start_char, end_char | Intervalo del original, inicio incluido y fin excluido |
| section_paths | Secciones alcanzadas; pueden ser varias en ventanas fijas |
| body | Subcadena original exacta |
| content | Texto preparado con contexto de documento/secciones y body |
| content_sha256 | Huella del texto preparado |
| ordinal | Orden dentro de documento/estrategia |

Offsets cuentan caracteres decodificados, no bytes ni tokens. Los títulos agregados no alteran los offsets del body.

En `headings_v1`, cada H2 abre una sección. El cuerpo empieza después de la línea de encabezado y termina al inicio del siguiente H2 o al final del archivo. Conserva los separadores que caigan dentro del intervalo. El título H1 y el texto anterior al primer H2 quedan fuera del cuerpo de las secciones. Los bloques de código delimitados por acentos graves o virgulillas pueden contener líneas de ejemplo con `##` sin abrir una sección. Los ordinales comienzan en uno y `section_paths` contiene el título del H2. El campo `content` antepone el título del documento y el de la sección, con una línea vacía antes de `body`.

El ID deriva de versión de esquema, documento/hash, estrategia/parámetros, intervalo y contenido preparado; no de la fecha de corrida. Se rechazan IDs duplicados, vacíos, intervalos inválidos y cuerpos distintos de su fuente.

El registro completo persiste en el catálogo. El adaptador de la base transforma sus metadatos al formato admitido sin perder la representación canónica.

## 2. Manifest del build

| Grupo | Datos |
|---|---|
| Identidad | schema_version, build_id, fingerprint, created_at y estado listo |
| Corpus | Sources/hashes ordenados y hash agregado |
| Chunking | Estrategia/versionado, parámetros y envoltorio |
| Embeddings | Modelo local/revisión, dimensión, normalización, prefijos por rol y límites |
| Vector DB | Proveedor/versión, ruta, colección, métrica y parámetros efectivos |
| Léxico | Variante/parámetros BM25, tokenización versionada y estado persistido |
| Integridad | Cantidad, huella del conjunto de IDs, hashes de catálogo y estado léxico |
| Reproducibilidad | Dependencias efectivas y referencia de código disponible |

La configuración de construcción determina compatibilidad del índice. Prompts de generación, juez y top_k pertenecen a la corrida y no obligan por sí solos a reembeddear.

Al abrir, se verifica manifest, archivos e IDs de la colección. Al comparar estrategias se verifica también que corpus y embeddings coincidan.

## 3. Resultado de recuperación

| Campo | Significado |
|---|---|
| question, build_id, retrieval_config | Pregunta y configuración efectiva |
| vector_candidates | IDs únicos, posiciones y distancias coseno |
| lexical_candidates | IDs únicos, posiciones y puntajes BM25 |
| selected_chunks | Hasta top_k IDs únicos con rrf_score y su registro |
| timings, warnings | Tiempos y candidatos insuficientes/incidencias |

Cada posición empieza en uno. RRF suma 1 / (constante + posición) por ranking; orden descendente y desempate por ID. Si faltan candidatos no se duplican.

selected_chunks es el contexto de generación; se registra el texto realmente enviado.

La normalización léxica propuesta se verifica al menos con estos pares: ExpenseHub a expensehub; ZQ-17 a zq-17; #it-ops a #it-ops; Y a y; política a política; 45,000 a 45,000. Los separadores de montos no se reinterpretan automáticamente como decimales o miles de otro país. Pregunta y corpus pasan por las mismas reglas.

Un documento sin términos de consulta no entra al ranking BM25. Si no hay coincidencias, la lista vacía es válida y la fusión conserva los candidatos vectoriales. El estado persistido identifica vocabulario/IDF, frecuencias por chunk, longitudes, cantidad de documentos, parámetros y versión de tokenización.

## 4. Generación y contrato público

Entrada al generador: pregunta, chunks con IDs, prompt versionado y configuración del LLM.

En cada intento, generación entrega a `llm/contracts/` los mensajes preparados, el esquema de salida y los límites efectivos. El adaptador devuelve el contenido emitido, motivo de finalización y uso reportado, o un error clasificado. El caso de uso conserva el contexto y decide si queda un intento disponible. La validación de referencias pertenece a generación. El juez reutiliza la integración con la API y aplica su propio esquema de afirmaciones y evidencia.

Salida interna del LLM: system_answer y cited_chunk_ids. La aplicación produce:

| Campo público | Origen |
|---|---|
| user_question | Pregunta original |
| system_answer | Texto del generador con IDs entre corchetes |
| chunks_related | Citas usadas y validadas |
| chunks_related[].chunk_id | ID presente en el contexto enviado |
| chunks_related[].source | Documento del catálogo |
| chunks_related[].content | Contenido preparado del catálogo |
| chunks_related[].score | rrf_score, no probabilidad |

Con multi-query, el puntaje RRF corresponde a la fusión de los rankings de las consultas distintas. Con re-ranking, el cross-encoder determina el orden de selección. La traza conserva los puntajes del modelo y los candidatos en orden RRF en `details.reranking`. Las citas retienen el puntaje RRF de cada fragmento.

Toda referencia del texto debe estar en chunks_related y cada elemento de esa lista debe estar citado. Se resuelven texto, origen y score desde artefactos de la aplicación, no desde campos inventados por el LLM.

Una respuesta factual sin citas o con IDs ajenos al contexto es inválida. Una respuesta explícita de insuficiencia puede devolver lista vacía; no se contabiliza automáticamente como respuesta correcta.

Validar referencias existentes no demuestra apoyo semántico: esa dimensión se revisa con el juez y casos humanos.

El caso de uso de respuesta devuelve internamente la respuesta pública, el resultado de recuperación que efectivamente usó y el identificador de corrida. La CLI serializa solo la respuesta pública. El runner reutiliza esa recuperación para medir y la respuesta para juzgar; no vuelve a buscar contexto para reconstruir qué ocurrió.

## 5. Golden y métricas

| Campo | Significado |
|---|---|
| question_id, question, kind | ID estable, pregunta y tipo |
| answerable | Existe evidencia para responder en este corpus |
| evidence | Fuente/hash, intervalo y extracto necesarios |
| expected_chunks | IDs relevantes por huella de estrategia |
| labeling_status | Borrador o revisado |
| reviewed_strategies | Huellas de las estrategias cuyas etiquetas se revisaron, cuando la aprobación es parcial |
| corpus_fingerprint | Corpus usado para etiquetar |
| expected_facts | Hechos esperados revisados por Luis |

La evidencia permanece independiente de los chunks. Los IDs se revisan por estrategia; una simple intersección de spans no basta. Se etiquetan alternativas relevantes sin adaptar el golden al resultado del buscador.

El runner exige al menos 25 preguntas, IDs únicos y etiquetas existentes en cada build elegido. Para la evaluación definitiva se requiere `labeling_status=reviewed` y aprobación para cada estrategia seleccionada. En un registro revisado sin `reviewed_strategies`, la aprobación abarca las estrategias de `expected_chunks`. Al añadir una estrategia, se enumeran las huellas ya aprobadas antes de proponer sus nuevas etiquetas. Los casos respondibles tienen evidencia e IDs esperados por estrategia.

El modo `--preliminary-retrieval` permite medir la búsqueda local con etiquetas en borrador. Conserva las validaciones de corpus y referencias y registra cuántas preguntas están revisadas para todas las estrategias elegidas. Cada caso informa el estado de su etiqueta para ese índice.

Cada resultado conserva IDs recuperados/esperados, precision@k, recall@k, hit, respuesta, citas, tiempos, validaciones y estado del juez.

El juez identifica afirmaciones sostenidas, no sostenidas o inciertas y justifica sus referencias. Groundedness es la proporción de afirmaciones sostenidas entre todas las identificadas; las inciertas no cuentan como sostenidas. Sin afirmaciones comprobables: no aplicable. Fallo del proveedor/parsing: error.

Los resúmenes muestran cantidades total, válida, fallida y no aplicable junto con promedios macro. La cobertura del juez y los fallos de generación se reportan; no se eliminan silenciosamente. expected_facts permite revisar completitud separadamente.

### Revisión manual del caso de capacitación

Para la pregunta sobre libros y rendición de un curso, las dos piezas de evidencia son el beneficio que incluye libros de tecnología y la instrucción de cargar la factura del curso en ExpenseHub dentro de los 30 días posteriores a la compra. La regla general sobre rendiciones antes del día 25 es un distractor para esta pregunta. [Beneficios](../data/corpus/hr_policies.md#beneficios) · [Capacitación](../data/corpus/finance_processes.md#presupuesto-de-capacitación-y-reembolsos-educativos).

En la simulación de ventanas de 80 palabras con solapamiento de 20, numeradas desde uno dentro del documento, la ventana 4 de Finance conserva la oración completa. La 5 comparte el final sobre plataforma y plazo, pero empieza dentro de esa oración. Al etiquetar, comprobar si cada fragmento incluye el vínculo con capacitación o si necesita otro fragmento. En HR las ventanas 7 y 8 se solapan sobre la mención a los libros. Estas posiciones orientan la revisión humana cuando existan IDs de ingesta.

Para diagnosticar una respuesta, el runner conserva qué evidencia llegó, cuál fue citada y qué afirmó el generador. Omitir la regla de HR, citar un ID inexistente y atribuir un plazo equivocado a una cita válida son tres resultados distinguibles en esa misma traza.

## 6. Casos de aceptación para implementar después

La inspección por H2 ya tiene pruebas para estabilidad de IDs, cambios de fuente y rechazo de offsets, cuerpos e IDs inconsistentes. La tabla recoge también casos previstos para los próximos incrementos.

| Caso | Resultado esperado |
|---|---|
| Mismo contenido y configuración | Mismos IDs de chunks |
| Dos estrategias sobre todo el corpus | Al menos una produce 20 o más chunks; conteos reales registrados |
| Cambio de texto o reglas | Huella nueva y revisión de etiquetas afectadas |
| Offsets/body inconsistentes | Ingesta rechazada antes de publicar |
| Caída durante la ingesta | Build parcial no consultable; anterior disponible |
| Proceso nuevo abre build listo | Consulta sin indexar documentos otra vez |
| Otro modelo, incluso de igual dimensión | Error antes de buscar |
| Proveedor devuelve lote incompleto, IDs desordenados o valores no finitos | Validador común rechaza la salida |
| Proveedor aplica prefijo dos veces o trunca texto | Verificación específica del adaptador detecta el incumplimiento |
| Nuevo proveedor que cumple el contrato | Ingesta y consulta mantienen su lógica; cambia el adaptador/configuración/ensamblado |
| IDs distintos entre BM25, catálogo y colección | Error de integridad |
| Escala BM25 distinta, mismo ranking | Misma fusión RRF |
| Cero coincidencias léxicas | BM25 vacío válido; sin resultados de puntaje cero agregados arbitrariamente |
| Empate o pocos candidatos | Orden definido y cantidad real |
| Pregunta de capacitación/rendición | Puede recuperar HR y Finance juntas |
| Filtro explícito | Mismo conjunto permitido en ambas ramas |
| ID inventado o contenido alterado por el LLM | No se publica una cita falsa |
| Salida inválida repetida | Error al agotar intentos |
| Contexto demasiado largo | Error visible sin truncación de evidencia |
| Golden borrador o con IDs ausentes | Eval detenida antes de llamar modelos |
| Corpus/modelos distintos entre builds | Rechazar comparación presentada como solo chunking |
| Juez falla en parte de la suite | Mostrar cobertura y errores además del promedio |
| Respuesta fiel pero incompleta | Groundedness puede ser alto; revisar suficiencia aparte |

Los casos guían verificaciones posteriores a la revisión del diseño; no obligan a crear un framework de testing ni sustituyen el runner académico.
