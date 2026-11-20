# ADR 0015: Organizar los contratos como paquete por funcionalidad

- Estado: Aceptada
- Fecha: 20/11/2026

## Contexto

Luis aprobó la estructura modular y propuso una carpeta para los contratos compartidos por los proveedores.

El diseño de embeddings reunía la interfaz, entradas, salidas y especificación del espacio en contracts.py. Estas responsabilidades se pueden identificar dentro de un paquete público propio.

## Decisión

Usar embeddings/contracts/ para la interfaz común y los tipos que comparten el servicio y los adaptadores. Separar provider.py, inputs.py, outputs.py y spec.py, con __init__.py para exportar su superficie pública.

El servicio consume el contrato y cada proveedor lo implementa. Bootstrap selecciona y ensambla el adaptador. El paquete de contratos permanece independiente de SDK, implementaciones y efectos externos.

Mantener esta organización dentro de cada funcionalidad, como llm/contracts/ o vector_store/contracts/, al definir sus contratos concretos.

## Consecuencias

- Interfaz y datos tienen ubicaciones específicas y pueden evolucionar por separado.
- Proveedores y servicio comparten definiciones sin importarse mutuamente.
- El paquete no descarga modelos, abre índices ni selecciona proveedores al importarse.
- Las validaciones comunes y particulares conservan sus límites del ADR 0014.
- Los contratos de distintas funcionalidades permanecen cerca de sus componentes y se evitan duplicaciones.
- El paquete añade archivos y requiere cuidar sus exportaciones y dependencias para evitar ciclos.

## Alternativas consideradas

Un único contracts.py reuniría responsabilidades de interfaz y varios tipos de datos. Una carpeta global para todos los contratos concentraría los dominios de toda la aplicación.

Se elige un paquete por funcionalidad, con un punto público de importación y módulos definidos por responsabilidad.

## Referencias

- [ADR 0014: modularidad y proveedores](0014-modularizar-proveedores-y-validaciones.md).
- [Diseño de modularidad](../MODULARIDAD.md).
- [Vista de contratos](../CONTRATOS.md).
