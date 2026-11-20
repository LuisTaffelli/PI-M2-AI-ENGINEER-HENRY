# Arquitectura de Nubbix Assist

Diseño base del primer incremento. Los ADR identifican los acuerdos y las opciones en estudio.

Luis confirmó arquitectura antes de implementar, ejecución mixta, CLI con núcleo reutilizable y separación por componentes, proveedores y validadores. Las tecnologías y parámetros todavía propuestos conservan ese estado en el registro ADR, junto con los requisitos explícitos de la consigna.

## 1. Objetivo y alcance

Responder preguntas sobre el corpus de Nubbix con citas rastreables y poder distinguir errores de recuperación de errores de generación.

La base acordada es una aplicación Python modular, ejecutada por CLI en una sola máquina. Los módulos son responsabilidades dentro del proyecto, no servicios que deban desplegarse por separado.

La [consigna](fuentes/consigna.md) exige dos estrategias de chunking sobre el mismo corpus, al menos 20 chunks en una de ellas, vector DB persistente, búsqueda híbrida, JSON con citas, golden de al menos 25 preguntas y evaluación separada de retrieval y groundedness mediante juez LLM.

UI, re-ranking y multi-query quedan como extensiones opcionales. La evaluación del rechazo fuera de alcance es un bonus. Reutilizar componentes de M1 es opcional; no implica depender de aquella aplicación completa.

## 2. Tres flujos

~~~mermaid
flowchart TB
    subgraph I["Ingesta local"]
        C["Corpus original"] --> L["Carga y validación"]
        L --> K["Chunking y metadatos"]
        K --> E["Embeddings locales"]
        E --> V["Colección vectorial"]
        K --> B["Índice BM25"]
        K --> A["Catálogo de chunks"]
        V --> M["Verificar y publicar manifest listo"]
        B --> M
        A --> M
    end
    subgraph Q["Consulta"]
        P["Pregunta y build seleccionado"] --> R["Validar manifest y compatibilidad"]
        M -. "artefactos persistidos" .-> R
        R --> S["Vectorial y BM25 locales"]
        S --> F["RRF y top_k"]
        F --> X["Contexto con IDs"]
        X --> G["Generación por API"]
        G --> Z["Validar formato y referencias"]
        Z --> O["JSON con citas del catálogo"]
    end
    subgraph EV["Evaluación"]
        D["Golden revisado por Luis"] --> RT["Métricas de recuperación"]
        D --> GE["Groundedness con juez por API"]
        F -. "mismo recuperador" .-> RT
        O -. "misma respuesta" .-> GE
        RT --> REP["Reporte por estrategia y pregunta"]
        GE --> REP
    end
~~~

La consulta genera el embedding de la pregunta; no vuelve a procesar ni embeddear los documentos. Las evals usan los mismos componentes que la CLI, sin otra implementación del RAG.

El caso de respuesta conserva su recuperación y traza internas. Para una evaluación completa, el runner mide esa recuperación y juzga la respuesta obtenida con ella; no repite una búsqueda para inferir qué evidencia usó el generador. Una evaluación exclusivamente de retrieval no llama a generación.

La ingesta y la recuperación se ejecutan localmente. Generación envía a la API la pregunta y el contexto seleccionado; el juez recibe pregunta, respuesta y chunks citados. Los artefactos del índice y el resto del corpus permanecen locales. La descarga inicial del modelo de embeddings requerirá conexión; una vez disponible se configurará su carga local.

## 3. Responsabilidades y dependencias

El repositorio contiene los paquetes y archivos de este mapa. La tabla describe las responsabilidades que se implementarán en cada uno. La separación por componentes, proveedores y validaciones quedó acordada en [ADR 0014](adr/0014-modularizar-proveedores-y-validaciones.md).

| Ubicación | Responsabilidad | Límite |
|---|---|---|
| ingest/run.py | Entrada reproducible de ingesta; delega al caso de uso | No concentra el pipeline |
| src/nubbix_assist/ingestion/ | Caso de ingesta, cargador Markdown y contratos de documento | No responde preguntas |
| src/nubbix_assist/chunking/ | Contratos, validadores y un módulo por estrategia | No llama modelos ni bases |
| src/nubbix_assist/configuration/ | Carga de configuración efectiva y rutas | No crea clientes ni contiene claves |
| src/nubbix_assist/artifacts/ | Contratos de manifest, repositorio y validadores de integridad | No repara índices al consultar |
| src/nubbix_assist/embeddings/ | Servicio y contrato comunes; paquete/configuración/validación por proveedor | No conoce prompts de respuesta |
| src/nubbix_assist/vector_store/ | Contrato de almacenamiento/búsqueda y adaptador/validación por backend | No decide qué responder |
| src/nubbix_assist/lexical/ | Tokenización, indexación, búsqueda y sus validaciones | No modifica originales |
| src/nubbix_assist/retrieval/ | Contratos de candidatos, coordinación y módulo de fusión RRF | No llama al generador |
| src/nubbix_assist/llm/ | Servicio/contrato común y paquete por proveedor API | No construye índices ni valida citas de negocio |
| src/nubbix_assist/generation/ | Contexto, prompts, coordinación y validación de respuesta/citas | No vuelve a recuperar documentos |
| src/nubbix_assist/query/ | Caso de consulta y su resultado interno | No duplica algoritmos de búsqueda |
| src/nubbix_assist/cli/ | Comandos, entrada y serialización | No concentra la lógica |
| src/nubbix_assist/bootstrap.py | Selección y ensamblado explícito de implementaciones | No contiene reglas de embeddings o generación |
| evals/ | Runner, métricas de retrieval y componente de groundedness con contratos/validación | No cambia etiquetas según resultados |

Cada funcionalidad conserva su paquete contracts/ y sus validadores. En embeddings, el paquete separa interfaz del proveedor, entradas, salidas y especificación del espacio, como registra [ADR 0015](adr/0015-contratos-como-paquete-por-funcionalidad.md). Los SDK particulares quedan dentro del paquete de su proveedor. Los casos de uso consumen contratos y el arranque ensambla las implementaciones concretas.

El [diseño de modularidad](MODULARIDAD.md) detalla la distribución de embeddings y su extensión a otros componentes. Se implementan los proveedores elegidos, con un punto de extensión explícito.

Se propone config.yaml versionado, prompts YAML externos y secretos desde el entorno. Las rutas relativas se resuelven desde la raíz del proyecto, independientemente del directorio de ejecución. No se requiere un orquestador RAG externo para coordinar estas llamadas.

## 4. Persistencia y fuente de verdad

| Artefacto | Ubicación propuesta | Git |
|---|---|---|
| Corpus original | data/corpus/ | Sí |
| Configuración y prompts | config.yaml y prompts/ | Sí |
| Golden revisado y etiquetas | evals/dataset.jsonl | Sí |
| Catálogo, BM25, manifest y Chroma | data/indexes/{build_id}/ | No |
| Trazas y resultados detallados | runs/{run_id}/ | No |
| Tablas finales y decisiones | README y docs/ | Sí |

Un build contiene una estrategia y una versión del corpus. Cada build tiene una base Chroma local propia, con su colección, para separar físicamente las estrategias.

El catálogo de chunks determina contenido y origen de cada referencia. Chroma y BM25 contienen exactamente los mismos IDs. El contexto del LLM y las citas se resuelven contra ese catálogo, aunque la base también guarde el texto para inspección.

El [diseño de almacenamiento](ALMACENAMIENTO.md) concreta los contratos, sus responsables y la lectura/publicación de builds manteniendo separados vector store, artefactos y léxico.

## 5. Ciclo de vida de un build

Una ingesta construye una versión nueva, sin sobrescribir la que ya funciona:

1. Validar corpus y parámetros y calcular sus huellas.
2. Generar el catálogo y comprobar IDs, offsets, contenido y conteos.
3. Crear embeddings, colección y estado BM25 desde el mismo catálogo.
4. Verificar conjuntos de IDs, dimensiones y valores finitos de los vectores.
5. Cerrar la escritura y verificar que los artefactos pueden volver a abrirse.
6. Publicar un manifest listo mediante archivo temporal en el mismo directorio y reemplazo atómico.

Sin manifest listo, un build parcial no es consultable. No se presupone una transacción entre Chroma y archivos: el manifest publica el conjunto ya verificado. La versión inicial ejecutará una ingesta por vez.

Consulta y evals seleccionan builds explícitos, sin elegir silenciosamente “el último”. Dos construcciones iguales pueden tener distintos build_id, pero deben conservar la huella de configuración y los IDs de chunks. ANN y proveedores remotos no se presuponen idénticos bit por bit entre corridas.

Si falla la construcción, el primer mecanismo de recuperación es repetir la ingesta completa. Reanudar lotes y actualizar documentos incrementalmente queda para después del flujo obligatorio medido.

## 6. Dos estrategias de chunking

| Estrategia propuesta | Regla inicial | Ventaja buscada | Riesgo a medir |
|---|---|---|---|
| headings_v1 | Una sección H2 por chunk, con contexto de documento/sección | Mantener listas y políticas juntas | Un chunk puede mezclar varias condiciones o licencias |
| words_v1 | Ventanas de 80 palabras y overlap de 20; avance de 60 | Fragmentos más específicos | Cortes de listas/condiciones y redundancia |

En words_v1 una palabra es una secuencia separada por espacios en blanco: no es un token del modelo. Se recorre el documento completo, incluyendo encabezados, sin cruzar documentos. Los offsets apuntan al original y el contexto agregado se guarda como envoltorio separado.

Se verificaron 443 palabras en HR, 449 en IT y 448 en Finance. La inspección con `headings_v1` produjo 18 chunks con metadatos, seis por archivo. La implementación de `words_v1` produjo 24 ventanas, ocho por archivo.

Ambas estrategias agregan contexto de documento/sección con el mismo criterio y comparten modelo de embeddings y política léxica. Los parámetros son una línea de partida, no valores óptimos.

El texto preparado, incluidos encabezados y prefijos del modelo, debe caber en el límite del embedding. La ingesta falla ante exceso; no se admite truncación silenciosa. Una subdivisión adicional cambia la versión de estrategia y sus etiquetas.

## 7. Embeddings locales

La aplicación genera los vectores y los pasa explícitamente al almacén; no delega esa decisión a una función automática de la base.

El servicio de embeddings coordina validadores comunes y un adaptador de proveedor. Configuración, preparación por rol, tokenizer y validaciones particulares quedan en el paquete de ese proveedor, como detalla [MODULARIDAD.md](MODULARIDAD.md).

Se propone evaluar intfloat/multilingual-e5-small mediante Sentence Transformers: su ficha declara embeddings de 384 dimensiones, prefijos query/passage y un límite de 512 tokens. Es un candidato multilingüe para esta escala, no una elección ya validada en la PC o en el corpus. La revisión exacta se fijará si lo elegimos.

El manifest registra proveedor local, modelo/revisión, dimensiones, normalización y tratamiento de documentos y preguntas. Algunos modelos requieren instrucciones distintas por rol dentro del mismo espacio compatible; se aplica cada una exactamente una vez.

Antes de buscar se compara esa huella, no solo la dimensión. Cambiar modelo, representación del texto o chunking requiere otro build. Cambiar solamente el prompt de generación no exige reindexar.

## 8. Recuperación híbrida

Propuesta inicial:

- Chroma local persistente, distancia coseno explícita.
- BM25 sobre el mismo catálogo, con su estado persistido. Consultar carga ese estado; no vuelve a indexar el corpus. Se propone k1 = 1,5, b = 0,75 e IDF positivo: ln(1 + (N - df + 0,5) / (df + 0,5)). La librería elegida deberá ofrecer esa variante o documentar el cambio antes de comparar.
- Normalización léxica idéntica para pregunta y documentos: Unicode NFKC y minúsculas mediante casefold. Se conservan tildes, términos de una letra, guiones internos, prefijo de canal y separadores internos de números. Inicialmente no se eliminan stopwords ni se aplica stemming; los ejemplos del contrato fijan el comportamiento esperado.
- Hasta 10 candidatos por rama y top_k final de 3, limitado por la cantidad disponible.
- RRF con constante 60 y posiciones desde 1. Se suma un aporte por cada ranking donde aparece el ID.
- IDs únicos en cada ranking y en la fusión; desempate por chunk_id.

La rama BM25 omite documentos sin coincidencias de términos y devuelve lista vacía si no hay coincidencias; no introduce resultados arbitrarios con puntaje cero. La otra rama puede aportar candidatos por sí sola en ese caso. Un ranking vacío válido se distingue de un error de ejecución de la rama.

Distancia coseno, puntaje BM25 y rrf_score se conservan separados. No son probabilidades. Los chunks solapados con distinto ID siguen siendo candidatos distintos; no se agrega una deduplicación semántica oculta a la comparación inicial.

Si se habilitan filtros explícitos, ambas ramas usan el mismo conjunto permitido. Las categorías inferidas por un clasificador no filtran por defecto: una pregunta puede requerir HR y Finance. La falta de candidatos se registra sin duplicar resultados.

## 9. Generación por API y citas

El generador recibe pregunta y contexto con IDs. El prompt distingue instrucciones de contenido documental y exige apoyo en ese contexto.

El LLM propone system_answer y los IDs usados. La aplicación verifica que estén en el contexto y que las referencias del texto sean consistentes; completa source, content y score desde sus artefactos. El modelo no determina esos campos.

El contrato público conserva user_question, system_answer y chunks_related. Esta última lista contiene las citas usadas; la traza conserva además todos los candidatos y el contexto enviado.

Una referencia existente es una comprobación mecánica. Decidir si sostiene una afirmación requiere revisión semántica y groundedness; una cita válida no demuestra por sí sola exactitud ni completitud.

El contexto completo debe caber junto con pregunta, instrucciones y salida reservada en el modelo API. Si no entra se revisan los parámetros mediante un error visible, sin cortar evidencia silenciosamente.

## 10. Errores, límites y trazas

| Situación | Conducta prevista |
|---|---|
| Corpus ausente, ilegible o modificado inesperadamente | Detener ingesta indicando archivo y motivo |
| Build incompleto, inconsistente o incompatible | Rechazar consulta antes de llamar a generación |
| Falla una rama de retrieval | Error; no presentar una búsqueda simple como híbrida |
| Timeout o fallo transitorio del proveedor | Reintentos acotados y registrados |
| JSON o referencias inválidos | Como máximo una reparación; luego error |
| Evidencia insuficiente | Permitir respuesta explícita de insuficiencia, sin inventar citas |
| Juez fallido o salida no interpretable | Caso no evaluado con motivo, separado del puntaje |

Generación admite hasta dos llamadas por pregunta, incluyendo el intento inicial y cualquier reintento o reparación. Timeouts y presupuesto por corrida se fijarán con el proveedor. No se multiplican retries de distintas capas sin control.

La CLI escribe JSON exitoso por stdout y diagnósticos por stderr; un fallo operativo tiene salida distinta de cero. Insuficiencia documental y caída de red son situaciones diferentes.

Cada corrida registra builds, configuración, prompts, modelos, IDs, rankings, contexto real, latencias, intentos y validaciones. Tokens y costos se calculan solo si existe información real suficiente; las claves quedan fuera de los registros.

## 11. Evaluación

El golden tiene al menos 25 preguntas revisadas por Luis: directas, paráfrasis, términos exactos, distractores y cruces documentales. Se conserva evidencia estable del corpus y una lista de IDs relevantes para cada estrategia.

Mapear spans puede ayudar a etiquetar, pero la intersección no garantiza evidencia suficiente. Luis revisa el mapeo y se congelan etiquetas antes de comparar.

Ambas estrategias se evalúan con el mismo corpus, preguntas, modelo de embeddings, configuración de retrieval, top_k y fórmulas:

- Precision@k: IDs relevantes recuperados entre k; lugares faltantes no cuentan como aciertos.
- Recall@k: IDs relevantes recuperados entre los IDs relevantes etiquetados.
- Hit rate complementario: al menos un ID relevante recuperado.
- Groundedness: juez LLM por API sobre afirmaciones y citas, con salida estructurada y prompt versionado.

Para la comparación de generación también se mantienen fijos proveedor/modelo generador, modelo juez, versiones de ambos prompts y parámetros de generación. Se registra la variación de las llamadas; no se atribuye un cambio de modelo o prompt al chunking.

Se reportan casos individuales y promedios macro. La granularidad y el overlap cambian el número de IDs relevantes; se revisa también la cobertura de la evidencia necesaria y las pérdidas por pregunta.

Los casos sin etiquetas revisadas invalidan la corrida. Los fuera de alcance, si se incorpora el bonus, se distinguen de los borradores: no se calcula recall dividiendo por cero ni se les asigna un acierto automático.

Los errores de generación/juez y los casos no aplicables se muestran con su cantidad y cobertura. Una respuesta sin afirmaciones comprobables no recibe groundedness perfecto por defecto. Groundedness mide apoyo en las citas, no completitud: una respuesta puede ser fiel y omitir información necesaria.

## 12. Antes de implementar

La [ruta de cierre](adr/README.md#ruta-para-cerrar-la-arquitectura) agrupa las revisiones en cuatro bloques: datos/versiones, recuperación/generación, ejecución/fallos y evaluación.

El diseño base cubre responsables, contratos, dependencias, persistencia, reglas de error y casos de aceptación. El primer incremento puede cargar el corpus y construir chunks en local. La configuración y las dependencias efectivas están versionadas. La selección de modelos remotos se hace por rol y el ajuste de calidad se mide en las evals.

Los pendientes y estados están en el [registro ADR](adr/README.md), con un archivo por decisión; los casos de aceptación están en [CONTRATOS.md](CONTRATOS.md). Los ADR distinguen acuerdos de opciones en estudio.

## 13. Fuentes y verificación

- [Consigna local](fuentes/consigna.md): requisitos académicos.
- [Procedencia del corpus](fuentes/procedencia.json): tres Markdown originales con hashes.
- [Clientes Chroma](https://docs.trychroma.com/docs/run-chroma/clients.md): persistencia local en disco mediante el cliente Python persistente.
- [Configuración Chroma](https://docs.trychroma.com/docs/collections/configure): métrica, distancia coseno e índice HNSW.
- [Sentence Transformers](https://www.sbert.net/docs/sentence_transformer/usage/usage.html): tratamiento de documentos y consultas según las instrucciones del modelo.
- [Ficha de multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small): dimensiones, prefijos, normalización y límite de entrada del candidato.

Páginas técnicas consultadas el 20/11/2026. Esta verificación documental no acredita una instalación, integración ni rendimiento medido.
