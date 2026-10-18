# Catálogo de frases señaladas (español)

Catálogo autoritativo de los patrones de escritura generada por IA específicos del
español, ejecutados por `scripts/patterns_es.py` a través de `scripts/banned_phrase_scan.py`.

Reglas que comparte con el catálogo inglés (`references/taboo-phrases.md`):

- **Las categorías son una sola taxonomía compartida.** Un patrón español que significa
  lo mismo que uno inglés usa la misma categoría, de modo que la cobertura, las filas
  de protección, los rule-packs y la lista bloqueante del contrato siguen valiendo.
- **`hard`**: siempre es una señal de IA, sin importar el contexto.
  **`soft`**: depende del contexto; puede ser apropiado en registro académico o formal.
- Los ejemplos entre comillas («», “”, comillas dobles), bloques de código y citas de
  bloque (`>`) quedan exentos por defecto: documentar un mal ejemplo no es escribir mal.
- Los usos literales viven detrás de una supresión contextual (borrador jurídico,
  patrimonio real, prosa clínica, ingeniería, finanzas), nunca detrás de un regex más laxo.

La paridad entre este catálogo y las claves de `BANNED_PHRASES_ES` la exige
`evals/check_taboo_parity.py`. La cobertura por evals la exige
`evals/check_pattern_coverage.py`.

## Throat-Clearing Openers

Estas frases retrasan el contenido. Se cortan por completo. Severity: **hard**.

| Frase | Por qué molesta |
|-------|-----------------|
| "la verdad es que" | Implica que antes no había verdad |
| "seamos claros" | Posicionamiento defensivo |
| "seamos honestos" | Implica deshonestidad previa |
| "vamos a ser honestos" | Variante larga del mismo gesto |
| "aquí está la cuestión:" | Retrasa el contenido con un preludio |
| "lo que nadie te cuenta" | Tono de revelación, clickbait |
| "no es ningún secreto que" | Performático |

## Filler y conectores vacíos

| Frase | Por qué molesta |
|-------|-----------------|
| "es importante destacar que" | Relleno: lo importante se dice y ya |
| "cabe destacar que" | Relleno de registro formal |
| "cabe mencionar que" | Variante del mismo relleno |
| "es importante señalar que" | Variante del mismo relleno |
| "en la era digital" | Marco genérico sin fecha ni lugar |
| "en el mundo actual" | Marco genérico |
| "hoy más que nunca" | Urgencia sin dato |

Severity: **hard**. Además, el regex de párrafo "en un mundo donde…" activa la misma
familia sin frase literal.

## The Conclusion Scaffold

La conclusión se escribe terminando, no anunciando el cierre. Severity: **hard**.

| Frase | Por qué molesta |
|-------|-----------------|
| "en conclusión" | Cierre anunciado |
| "en resumen" | Cierre anunciado |
| "para resumir" | Cierre anunciado |
| "en definitiva" | Cierre anunciado |
| "para concluir" | Cierre anunciado |
| "como hemos visto" | Recapitulación de relleno |

Protección: en escritura jurídica española estos conectores son estructura precisa
(«en conclusión, el tribunal desestima»); el contexto legal los suprime. El regex de
coda ("en última instancia," "recordemos que") activa la misma categoría.

## Significance & Legacy Inflation

| Frase | Por qué molesta |
|-------|-----------------|
| "desempeña un papel crucial" | Infla la función; di qué hace |
| "desempeña un papel fundamental" | Variante |
| "desempeña un papel clave" | Variante |
| "juega un papel crucial" | Variante |
| "juega un papel fundamental" | Variante |
| "juega un papel vital" | Variante |
| "un testimonio de" | Legado inflado; en legal es una copia certificada y en histórico una pieza, y esa es la parte protegida |
| "marca un antes y un después" | Hito sin dato |
| "deja una huella imborrable" | Legado inflado |

Severity: **hard**. Protección: la prosa clínica y científica usa la formulación causal
con precisión («juega un papel central en la fisiología»), y el contexto legal o
histórico protege «un testimonio de».

## Vague Attribution

| Frase | Por qué molesta |
|-------|-----------------|
| "expertos señalan" | Sin nombres ni fuente |
| "expertos aseguran" | Sin nombres ni fuente |
| "según los expertos" | Sin nombres ni fuente |
| "los estudios demuestran" | Sin cita |
| "diversos estudios sugieren" | Sin cita |
| "los analistas predicen" | Sin nombres ni pronóstico citado |
| "fuentes cercanas" | Fuente fantasma (soft) |

Severity: **hard** salvo "fuentes cercanas" (**soft**). Protección: una cita o fuente
explícita («según el informe publicado por…») suprime la familia.

## Promotional Language

| Frase | Por qué molesta |
|-------|-----------------|
| "un rico patrimonio cultural" | Folleto turístico |
| "el secreto mejor guardado" | Folleto turístico |
| "una joya escondida" | Folleto turístico |
| "una experiencia inolvidable" | Folleto turístico |
| "un destino imperdible" | Folleto turístico |

Severity: **hard**. Protección: la descripción patrimonial real (museo, archivo, época,
siglo) sin vocabulario promocional queda limpia.

## AI Vocabulary

| Término | Problema |
|---------|----------|
| "sumérgete en" | Apertura de folleto |
| "desbloquea el potencial" | Promesa vacía |
| "desbloquear todo el potencial" | Variante |
| "en el fascinante mundo de" | Apertura de folleto |
| "aprovecha al máximo" | Relleno con imperativo |
| "vibrante" | Adjetivo de folleto (soft) |

Severity: **hard** salvo "vibrante" (**soft**). Los regex "en el panorama actual" y
"nos encontramos ante un…" activan la misma categoría en registro formal vacío.

## Business Jargon

| Término | Problema |
|---------|----------|
| "sinergia" | Jerga; sugiere coordinación, colaboración |
| "sinergias" | Variante |
| "holístico" | Jerga; sugiere completo, integral |
| "holística" | Variante |
| "empoderar" | Jerga; sugiere dar capacidad, permitir |
| "robusto" | Jerga; sugiere sólido, resistente |

Severity: **soft**. Protección: las sinergias de costes de una fusión y el "sistema
robusto" de ingeniería nombran lo que sostienen y quedan limpios.

## False Agency

| Frase | Por qué molesta |
|-------|-----------------|
| "los datos hablan por sí solos" | Los datos no hablan; alguien los interpreta |
| "el mercado premia" | Sujeto colectivo sin actor |
| "la innovación exige" | Abstacción con voluntad |

Severity: **hard**.

## Communication Artifacts

| Frase | Por qué molesta |
|-------|-----------------|
| "¿en qué puedo ayudarte hoy?" | Artefacto de asistente |
| "¿en qué más puedo ayudarte?" | Artefacto de asistente |
| "como modelo de lenguaje" | Artefacto de asistente |
| "estoy aquí para ayudarte" | Artefacto de asistente |

Severity: **hard**.

## Knowledge-Cutoff Disclaimers

| Frase | Por qué molesta |
|-------|-----------------|
| "hasta mi última actualización" | Fecha de entrenamiento filtrada |
| "no tengo acceso a información en tiempo real" | Límite de modelo filtrado |

Severity: **hard**.

## Rhetorical Question Openers

| Frase | Por qué molesta |
|-------|-----------------|
| "¿alguna vez te has preguntado" | Apertura de anzuelo |

Severity: **hard**.

## Copula Avoidance

La IA evita "es/son" y sustituye la cópula por verbos pomposos. Solo se marcan con
lista cerrada de sustantivos abstractos, para que el uso verbal ordinario
(«constituye una prueba», «funciona como interfaz») quede limpio. Severity: **hard**.

| Patrón | Arreglo |
|--------|---------|
| "se erige / se consolida / se posiciona / se presenta como un referente (símbolo, pilar, hito, motor…)" | Usa un verbo directo |
| "representa / constituye un hito (paso, avance, testimonio, símbolo, compromiso, reto…)" | Usa un verbo directo |
| "funciona / actúa / opera / sirve como un puente (motor, catalizador, pilar, brújula…)" | Usa un verbo directo |
| "juega / desempeña un papel central (decisivo, esencial, importante…)" | Di qué hace |

Protección: el borrador jurídico («el impago constituye una infracción») y la prosa
clínica («juega un papel central en la fisiología») quedan limpios.

## Negative Parallelisms y Binary Contrasts

| Patrón | Arreglo |
|--------|---------|
| "no solo … sino también" | Frase directa |
| "no es solo X, es Y" | Contrasta sin el molde |
| "no se trata de X, sino de Y" | Una sola frase |

Severity: **hard**. Protección: en contratos, "no solo … sino también" delimita
alcance con precisión.

## Emphasis Crutches

| Patrón | Arreglo |
|--------|---------|
| "la verdad incómoda" | Di lo que importa |
| "lo que realmente importa" | Di lo que importa |
| "no es casualidad que" | Afirma o aporta el dato |
| "sin duda alguna" | Elimina el énfasis vacío |
| "la parte que nadie cuenta" | Elimina la promesa de revelación |

Severity: **hard**.

## Anti-Slop Register

La pila de fragmentos negados ("Sin adornos. Sin relleno. Sin promesas.") es el
anti-slop como estilo: prosa de folleto con ínfulas de franqueza. Severity: **soft**:
une los fragmentos en una frase variada.

## Reader-Steering Frames

| Patrón | Arreglo |
|--------|---------|
| "imagínate", "imagina por un momento", "piensa por un momento", "piénsalo bien", "¿te suena familiar?" | Empieza por el asunto |
| "pasemos a…", "a continuación,", "en esta sección", "como se mencionó anteriormente" | Empieza por el asunto |

Severity: **soft**. La aparición a mitad de frase («continúa a continuación con…») es
uso corriente y no se marca.

## Hedge Stack

| Patrón | Arreglo |
|--------|---------|
| "podría quizá", "podría posiblemente", "tal vez quizá", "quizás tal vez", "puede que tal vez" | Elimina la redundancia |

Severity: **soft**.

## Numbered List Inflation

| Patrón | Arreglo |
|--------|---------|
| "en primer lugar… en segundo lugar… en tercer lugar… en último lugar" | Lista solo los puntos que importan |

Severity: **soft**; el patrón exige al menos dos ocurrencias, así que una enumeración
aislada queda limpia.

## Alcance e idioma

El escáner enruta por idioma: el español se detecta con palabras funcionales y
marcadores ortográficos, y solo los idiomas no soportados reciben el declive elegante
(`non_english: true`, salida 0) — y únicamente cuando el escaneo no encontró nada.
