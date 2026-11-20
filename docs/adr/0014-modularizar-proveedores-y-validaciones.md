# ADR 0014: Modularizar componentes, proveedores y validaciones

- Estado: Aceptada
- Fecha: 20/11/2026

## Contexto

Luis aceptó la CLI con núcleo reutilizable y pidió una separación mantenible, citando embeddings como ejemplo: proveedores y validadores correspondientes en módulos propios.

El mapa inicial describía responsabilidades mediante archivos como embeddings.py o llm.py. Esos archivos podían acumular configuración, SDK, transformación, validación y coordinación.

## Decisión

Organizar por funcionalidad y, dentro de las integraciones externas, por proveedor. Separar contratos, coordinación, implementación concreta y validaciones. Cada funcionalidad conserva los contratos y reglas que le pertenecen.

La configuración y el arranque ensamblan las implementaciones elegidas. Los casos de uso trabajan contra contratos estables y reciben sus dependencias ya construidas.

Se distinguen tres niveles: reglas comunes del componente, reglas particulares del proveedor y reglas del caso de uso. Por ejemplo, la forma de un vector pertenece a embeddings; el límite del tokenizer a su proveedor; las citas al contexto de generación.

El [diseño de modularidad](../MODULARIDAD.md) concreta esta decisión para embeddings y establece las reglas para aplicarla al resto del sistema. Su árbol de archivos es orientativo y no representa implementación.

## Consecuencias

- Un proveedor nuevo agrega su adaptador, configuración, validadores y ensamblado; no modifica la lógica de ingesta o consulta si respeta el contrato.
- Varios modelos del mismo proveedor se expresan mediante configuración y huella de modelo.
- Las validaciones comunes se reutilizan y las particularidades permanecen dentro del proveedor.
- La aplicación puede probar contratos y errores sin cargar SDK ni conectar modelos.
- Los SDK se importan dentro del paquete del proveedor; el arranque importa adaptadores concretos, no los casos de uso.
- Se crean módulos con un motivo de cambio claro. La división requiere contratos explícitos y añade navegación entre archivos.
- Se implementan los proveedores efectivamente elegidos; queda definido el punto de extensión para otros.

## Alternativas consideradas

Un archivo global por integración mezclaría responsabilidades. Un archivo global de todos los contratos, otro de validaciones y otro de utilidades trasladaría esa concentración a nuevos lugares.

Se adopta agrupación por funcionalidad, con contratos y validaciones cercanos al componente al que pertenecen. Los elementos compartidos se limitan a primitivas pequeñas utilizadas realmente en varias funcionalidades.

## Referencias

- [ADR 0003: aplicación modular con CLI](0003-aplicacion-python-modular-con-cli.md).
- [ADR 0015: contratos como paquete por funcionalidad](0015-contratos-como-paquete-por-funcionalidad.md).
- [Modularidad y proveedores](../MODULARIDAD.md).
- [Arquitectura](../ARQUITECTURA.md).
- [Contratos](../CONTRATOS.md).
