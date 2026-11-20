# ADR 0017 · Ofrecer OpenAI y Gemini para generación y juez

- Estado: Aceptada

## Contexto

Luis eligió ambos proveedores para la parte remota del RAG. El generador y el juez comparten un contrato de solicitud y respuesta estructuradas.

## Decisión

Cada rol selecciona su proveedor y modelo mediante variables de entorno. El adaptador OpenAI usa Chat Completions y el de Gemini usa generateContent. Las credenciales, los encabezados y la validación del transporte quedan dentro del proveedor correspondiente. La generación conserva el control del segundo intento y el runner comparte un presupuesto entre ambos roles.

## Consecuencias

Se puede comparar el chunking fijando el mismo par de modelos en ambas estrategias. Las pruebas de contrato ejercitan los dos formatos de transporte. La disponibilidad y calidad de cada modelo seleccionado se verifican con la cuenta que lo ejecuta.

## Alternativas consideradas

Un único proveedor simplificaría la configuración. El usuario eligió conservar la posibilidad de alternarlos y de asignar roles diferentes.
