# ADR 0013: Evaluar multilingual-e5-small como candidato local

- Estado: Propuesta
- Fecha: 20/11/2026
- Referencia anterior: A11

## Contexto

Luis eligió embeddings locales. La propuesta necesita un candidato multilingüe y límites explícitos, antes de fijar el modelo definitivo.

## Decisión

Se propone evaluar intfloat/multilingual-e5-small mediante Sentence Transformers como candidato, no darlo por elegido ni instalado.

## Consecuencias

- Su ficha declara 384 dimensiones, prefijos por rol y límite de 512 tokens.
- Se deben fijar revisión, normalización y prefijos y validar el contenido completo sin truncación silenciosa.
- Falta comprobar compatibilidad del entorno y calidad sobre el corpus.
- Cambiar después el modelo requiere otro build y su huella correspondiente.

## Alternativas consideradas

Otro modelo local puede resultar más apropiado tras revisar recursos y resultados. Los embeddings por API cambiarían la modalidad que eligió Luis.

## Referencias

- [Arquitectura](../ARQUITECTURA.md).
- [Consigna](../fuentes/consigna.md).
- [Ficha del candidato](https://huggingface.co/intfloat/multilingual-e5-small).
- [ADR 0002: modalidad mixta](0002-embeddings-locales-y-llm-por-api.md).

