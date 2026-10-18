Unslop es una skill para agentes que detecta y elimina patrones de escritura generada por IA sin tocar el significado. Se instala como cualquier skill y no necesita servicios externos.

El producto tiene cuatro comandos. rewrite diagnostica y reconstruye un documento; cleanup propone cambios que tú aceptas o rechazas; teach construye un perfil de voz a partir de tus muestras; mimic escribe en esa voz pasando antes por los detectores.

Los detectores son deterministas y viven en scripts de Python sin dependencias. Hay tres capas: frases, estructura y silueta. Cada una devuelve JSON y un código de salida distinto de cero cuando encuentra algo.

La regla que gobierna todo lo demás es conservadora: un hallazgo del escáner no autoriza una edición. El contrato exige que el defecto sea más claro que la preservación.

El repositorio incluye las evals que definen el comportamiento esperado. Si un patrón no tiene una prueba que falle sin él, el patrón no entra.
