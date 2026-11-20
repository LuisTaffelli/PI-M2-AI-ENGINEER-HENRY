# Almacenamiento e identidad de índices

Diseño acordado para el primer incremento.

Desarrolla los ADR [0004](adr/0004-persistencia-vectorial-con-chroma-local.md), [0005](adr/0005-builds-independientes-por-estrategia.md) y [0006](adr/0006-publicar-builds-tras-verificar-integridad.md).

## 1. Responsabilidades

| Componente | Es dueño de | Consume |
|---|---|---|
| vector_store/ | Contrato y adaptadores de persistencia/búsqueda vectorial | IDs, vectores, especificación compatible y filtros admitidos |
| artifacts/ | Catálogo de chunks, manifest e integridad del build | Contratos de chunks, embeddings y resultados de inspección |
| lexical/ | Tokenización, estado BM25 y ranking léxico | El mismo catálogo e IDs |
| ingestion/ | Coordinar construcción y publicación | Los tres componentes anteriores y embeddings |
| retrieval/ | Consultar ambas ramas y fusionar | Un build listo y la pregunta/vector compatibles |

El vector store devuelve IDs y distancias. El catálogo proporciona el texto y origen canónicos. El componente de artefactos verifica el conjunto; no incorpora código del SDK vectorial.

## 2. Contratos del vector store

Se mantiene el patrón por funcionalidad:

~~~text
vector_store/
  contracts/
    __init__.py
    provider.py
    inputs.py
    outputs.py
    spec.py
  service.py
  validators.py
  errors.py
  providers/
    chroma/
      adapter.py
      config.py
      validators.py
~~~

Estos archivos ya tienen su lugar en el repositorio. El primer adaptador previsto es Chroma local. Otro backend podrá integrarse mediante el mismo contrato y su propio adaptador.

| Operación | Entrada/salida prevista |
|---|---|
| Crear un espacio de construcción | Identidad de build y especificación de índice; produce una referencia del espacio |
| Escribir un lote | Referencia, IDs y vectores del espacio esperado; confirma escritura o devuelve error |
| Abrir un índice existente | Referencia y especificación esperada; no crea una colección faltante |
| Buscar | Vector, cantidad y filtros validados; devuelve IDs únicos y distancias |
| Inspeccionar | Devuelve identidad, dimensiones/métrica y conjunto de IDs para comprobar integridad |

La especificación identifica backend, dimensión, métrica y huella de embeddings. El contrato no expone clientes del SDK ni exige a retrieval conocer nombres de colecciones o rutas internas.

Los validadores comunes comprueban lotes, IDs, dimensiones, valores y forma del resultado. Los del backend comprueban configuración y capacidades particulares. La comparación de los IDs del catálogo, BM25 y vectores pertenece a artifacts/.

## 3. Contenido de un build

Una versión propuesta agrupa:

- manifest.json con identidad, huellas, estrategia, configuración e integridad.
- chunks.jsonl con el catálogo canónico y su procedencia.
- Estado BM25 persistido, con formato documentado y política de tokenización.
- Directorio de la base vectorial del backend elegido.

Cada estrategia tiene su build. Los nombres concretos de archivos del backend permanecen dentro de su adaptador; no pasan a ser parte del contrato del RAG.

Los índices y corridas son artefactos generados y se excluyen de Git. El corpus, configuración, prompts, golden revisado y decisiones sí se versionan.

## 4. Publicación y lectura

La ingesta crea una versión nueva, construye las dos ramas desde el catálogo y verifica conjuntos de IDs, vectores, huellas y reapertura. Publica el manifest listo al final.

Un proceso de consulta selecciona un build explícito y verifica su compatibilidad antes de usarlo. Una colección ausente es un error; abrir una consulta no crea un índice vacío ni reconstruye el corpus.

Si falla una ingesta, la versión anterior permanece seleccionable. El build parcial queda fuera de consulta. La publicación no promete una transacción entre archivos y base: el manifest hace visible únicamente un conjunto ya comprobado.

La primera versión tiene una ingesta por vez. Limpieza automática, ingesta incremental y reanudación de lotes quedan fuera del primer alcance.

## 5. Casos que debemos poder verificar

- Abrir un build listo en otro proceso sin generar embeddings de documentos.
- Rechazar una versión parcial, un archivo ausente o IDs distintos entre las ramas.
- Rechazar otra huella de embeddings aunque la dimensión coincida.
- Mantener el build anterior utilizable después de una construcción fallida.
- Resolver contenido y citas desde el catálogo del build consultado.

Estas verificaciones son criterios previstos, no resultados de una implementación.
