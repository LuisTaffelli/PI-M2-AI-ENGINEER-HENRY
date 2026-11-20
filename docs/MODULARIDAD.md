# Modularidad y límites de proveedores

La estructura de paquetes ya incluye la carga de documentos y el corte por encabezados. Los módulos de proveedores describen sus responsabilidades para las próximas integraciones.

La separación por componentes, proveedores y validadores fue confirmada por Luis en [ADR 0014](adr/0014-modularizar-proveedores-y-validaciones.md). La CLI con núcleo reutilizable está aceptada en [ADR 0003](adr/0003-aplicacion-python-modular-con-cli.md).

Los contratos se organizan como un paquete dentro de su funcionalidad, según [ADR 0015](adr/0015-contratos-como-paquete-por-funcionalidad.md).

## 1. Organización por funcionalidad

Cada funcionalidad mantiene juntos sus contratos, coordinación, reglas y adaptadores. Los casos de uso reciben las implementaciones elegidas mediante el ensamblado de la aplicación.

La dirección de dependencia es: entrada hacia caso de uso, caso de uso hacia contrato del componente, adaptador hacia ese mismo contrato. El módulo de arranque conoce las implementaciones concretas y las conecta.

Por ejemplo, ingesta y consulta reciben un servicio de embeddings. Ese servicio usa el contrato del proveedor y validadores comunes; el adaptador elegido resuelve la integración con su SDK.

El arranque tiene un registro explícito de proveedores disponibles y construye solo el configurado. Importar contratos, leer el golden o calcular métricas no descarga modelos, crea clientes ni abre índices.

## 2. Paquete de embeddings

El paquete de embeddings tiene la siguiente estructura.

~~~text
src/nubbix_assist/
  bootstrap.py
  embeddings/
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
      sentence_transformers/
        adapter.py
        config.py
        validators.py
~~~

Sentence Transformers figura como candidato a implementación local. El árbol no confirma el modelo E5 ni instala un proveedor.

| Módulo | Responsabilidad |
|---|---|
| contracts/provider.py | Interfaz común: describir el espacio, codificar documentos y codificar preguntas |
| contracts/inputs.py | Tipos de entrada e identificación de textos/documentos/preguntas |
| contracts/outputs.py | Tipos de salida y correspondencia de IDs con vectores |
| contracts/spec.py | Identidad del espacio: proveedor/modelo/revisión, dimensión, normalización e instrucciones |
| contracts/__init__.py | Exportar los nombres públicos, sin inicialización ni efectos externos |
| service.py | Coordinar validación de entrada, llamada al adaptador y validación de salida |
| validators.py del componente | Comprobar invariantes de textos, IDs, lotes, dimensiones y valores |
| errors.py | Errores del componente independientes del SDK |
| providers/.../adapter.py | Integrar el SDK, preparar el rol, preservar el orden y transformar sus resultados/errores al contrato |
| providers/.../config.py | Configuración tipada del proveedor: modelo/revisión, ruta o caché, dispositivo y parámetros |
| providers/.../validators.py | Comprobar configuración, capacidades del modelo y límites particulares |
| bootstrap.py | Leer configuración efectiva, elegir y ensamblar adaptador/servicio |

Un modelo, como multilingual-e5-small, es una configuración de un proveedor local; no requiere un paquete nuevo solo por tener otro nombre.

## 3. Contrato de embeddings

El servicio consume la interfaz de contracts/provider.py; cada adaptador la implementa. Ambos dependen del mismo contrato. El ensamblado elige el adaptador concreto y se lo entrega al servicio.

Las dependencias internas de este paquete permanecen acotadas: provider usa inputs, outputs y spec; outputs puede referirse a spec. Estos módulos describen la interfaz y los datos sin importar el servicio, validadores de ejecución o implementaciones concretas.

| Registro u operación | Contenido |
|---|---|
| EmbeddingSpec | Proveedor, modelo/revisión resuelta, dimensión, normalización e instrucciones por rol |
| Entrada de documentos | IDs estables y textos preparados en el mismo orden |
| Entrada de pregunta | ID de correlación y texto de consulta |
| Salida | IDs y vectores en correspondencia uno a uno, más la huella del espacio efectivo |
| Operaciones del proveedor | Describir su espacio efectivo, codificar documentos y codificar preguntas |

El servicio coordina. El adaptador es dueño de aplicar los prefijos/instrucciones específicos del modelo exactamente una vez y de contar el texto final contra su límite. La preparación de chunks y títulos ocurre antes, en su componente.

La huella del espacio efectivo se verifica contra lo esperado; declarar una dimensión en config no demuestra que el modelo cargado sea compatible. El dispositivo y los tiempos se registran como condiciones de ejecución, sin tratarlos por sí solos como un espacio semántico diferente.

## 4. Qué valida cada nivel

| Nivel | Ejemplos | Dueño |
|---|---|---|
| Entrada común | Textos válidos/no vacíos, IDs únicos y misma cantidad de IDs/textos | embeddings/validators.py |
| Configuración del proveedor | Modelo/revisión y opciones soportadas, disponibilidad del recurso local seleccionado | providers/{proveedor}/validators.py |
| Límite particular | Tokens del texto final con prefijos y tokens especiales; prohibir truncación silenciosa | Validador del proveedor, con su tokenizer |
| Salida común | Cantidad y orden de resultados, dimensión esperada, números finitos y vectores no nulos para coseno | embeddings/validators.py |
| Normalización declarada | Norma compatible con la política y tolerancia definida si se declara normalización | embeddings/validators.py |
| Compatibilidad del build | Huella de embeddings correspondiente al manifest seleccionado | artifacts/validators.py usando los contratos de embeddings |
| Uso de evidencia | Citas pertenecen al contexto y apuntan al catálogo | generation/validators.py |

Las validaciones particulares complementan las comunes. Los proveedores usan la misma batería de verificaciones de contrato; no mantienen copias divergentes de las reglas comunes.

La validación de estructura no demuestra por sí sola que un vector represente el texto correcto. La correspondencia y aplicación de instrucciones se verifican también con pruebas controladas del adaptador, antes de medir la calidad de retrieval.

No se rellena un resultado faltante con ceros, se modifica la dimensión o se normaliza silenciosamente para ocultar una salida incompatible. Las transformaciones válidas deben formar parte de la configuración declarada.

## 5. Errores y reintentos

El adaptador traduce errores del SDK a errores del componente: entrada inválida, configuración incompatible, salida inválida o fallo del proveedor. Conserva causa y datos de diagnóstico pertinentes sin filtrar secretos.

El caso de uso es dueño del presupuesto de intentos. El adaptador informa si el fallo puede ser transitorio; no agrega otra política de reintentos que multiplique llamadas.

Se respeta la modalidad local elegida: un fallo de embeddings no cambia automáticamente a un proveedor remoto. Cambiar proveedor/modelo requiere configuración explícita y verificar la compatibilidad del índice.

## 6. Aplicación a los demás componentes

| Funcionalidad | Separación prevista |
|---|---|
| LLM | Contratos/servicio comunes y paquete por proveedor con adaptador, configuración y validadores |
| Vector store | Contrato de almacenamiento/búsqueda y adaptador/validación del backend elegido |
| Chunking | Contratos y reglas comunes; módulo propio por estrategia |
| Léxico | Tokenización, estado/indexación, búsqueda y validación separados |
| Retrieval | Coordinación de ramas, contratos de candidatos y módulo de fusión RRF |
| Generación | Construcción de contexto, prompts, coordinación y validación de respuesta/citas |
| Artefactos | Contratos de manifest, repositorio de archivos y validación de integridad/compatibilidad |
| Evaluación | Runner, métricas de recuperación y componente de groundedness con su contrato/validación |
| CLI | Entrada/comandos y serialización; consume casos de uso |

Los validadores del proveedor LLM comprueban configuración, límites y formato de su respuesta de transporte. Las referencias a chunks y el contrato final pertenecen a generación. El significado de groundedness pertenece a evaluación, aunque use el mismo proveedor API.

Los contratos detallados se mantienen por funcionalidad. Un archivo global de todos los contratos o validadores no será el punto de acumulación de reglas del sistema.

Se aplica el criterio de paquete propio a llm/contracts/ y vector_store/contracts/ cuando se definan sus registros. Los módulos concretos se agrupan según las responsabilidades del contrato de cada componente; no se copian tipos de embeddings dentro de otros dominios.

## 7. Criterios de revisión al implementar

- Cambiar de proveedor requiere modificar su paquete y el ensamblado, manteniendo estables los casos de uso que consumen su contrato.
- Cambiar de modelo dentro del proveedor se expresa en configuración y huella; una incompatibilidad con el build se detecta.
- Los casos de uso no importan SDK de modelos ni conocen sus formatos de respuesta.
- Un adaptador puede reemplazarse por una implementación de prueba sin cargar un modelo real.
- Se rechazan resultados desordenados, incompletos, con otra dimensión o con valores inválidos.
- Se prueban límites y prefijos con las particularidades del proveedor elegido.
- Añadir un proveedor no obliga a copiar las validaciones comunes.

Son criterios para verificaciones futuras; todavía no se implementaron esas pruebas ni los proveedores.
