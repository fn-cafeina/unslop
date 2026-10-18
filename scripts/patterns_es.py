#!/usr/bin/env python3
"""Spanish pattern pack: the AI-writing tells that are specific to Spanish.

Data only. The machinery (masking, boundaries, contextual suppression, the
decline path) lives in ``banned_phrase_scan.py`` and ``_lang.py``; this module
carries the tables so both languages stay one scanner, not two forks.

Two rules keep this pack honest:

1. Category names are the shared taxonomy. A Spanish tell that means the same
   thing as an English one uses the same category, so coverage, protections,
   rules packs, and the contract's blocking list keep working unchanged.
2. Every entry is a phrase or regex whose Spanish use is *distinctively* the
   tell. Literal uses live behind a contextual suppression (legal drafting,
   real patrimony, clinical prose, engineering), never behind a weaker regex.

Documented in ``references/taboo-phrases-es.md``; parity is enforced by
``evals/check_taboo_parity.py``.
"""

from __future__ import annotations

# Phrases with categories, suggestions, and severity.
# severity: "hard" = always an AI tell; "soft" = context-dependent
BANNED_PHRASES_ES: dict[str, dict[str, str | None]] = {
    # --- Throat-clearing and filler -----------------------------------------
    "la verdad es que": {"category": "throat_clearing", "severity": "hard", "suggestion": None},
    "seamos claros": {"category": "throat_clearing", "severity": "hard", "suggestion": None},
    "seamos honestos": {"category": "throat_clearing", "severity": "hard", "suggestion": None},
    "vamos a ser honestos": {"category": "throat_clearing", "severity": "hard", "suggestion": None},
    "aquí está la cuestión:": {"category": "throat_clearing", "severity": "hard", "suggestion": None},
    "lo que nadie te cuenta": {"category": "throat_clearing", "severity": "hard", "suggestion": None},
    "no es ningún secreto que": {"category": "throat_clearing", "severity": "hard", "suggestion": None},
    "es importante destacar que": {"category": "filler", "severity": "hard", "suggestion": None},
    "cabe destacar que": {"category": "filler", "severity": "hard", "suggestion": None},
    "cabe mencionar que": {"category": "filler", "severity": "hard", "suggestion": None},
    "es importante señalar que": {"category": "filler", "severity": "hard", "suggestion": None},
    "en la era digital": {"category": "filler", "severity": "hard", "suggestion": None},
    "en el mundo actual": {"category": "filler", "severity": "hard", "suggestion": None},
    "hoy más que nunca": {"category": "filler", "severity": "hard", "suggestion": None},

    # --- Conclusion and sequencing scaffolding -------------------------------
    "en conclusión": {"category": "conclusion_scaffold", "severity": "hard", "suggestion": None},
    "en resumen": {"category": "conclusion_scaffold", "severity": "hard", "suggestion": None},
    "para resumir": {"category": "conclusion_scaffold", "severity": "hard", "suggestion": None},
    "en definitiva": {"category": "conclusion_scaffold", "severity": "hard", "suggestion": None},
    "para concluir": {"category": "conclusion_scaffold", "severity": "hard", "suggestion": None},
    "como hemos visto": {"category": "conclusion_scaffold", "severity": "hard", "suggestion": None},

    # --- Significance inflation ----------------------------------------------
    "desempeña un papel crucial": {
        "category": "significance_inflation", "severity": "hard",
        "suggestion": "Say what it does.",
    },
    "desempeña un papel fundamental": {
        "category": "significance_inflation", "severity": "hard",
        "suggestion": "Say what it does.",
    },
    "desempeña un papel clave": {
        "category": "significance_inflation", "severity": "hard",
        "suggestion": "Say what it does.",
    },
    "juega un papel crucial": {
        "category": "significance_inflation", "severity": "hard",
        "suggestion": "Say what it does.",
    },
    "juega un papel fundamental": {
        "category": "significance_inflation", "severity": "hard",
        "suggestion": "Say what it does.",
    },
    "juega un papel vital": {
        "category": "significance_inflation", "severity": "hard",
        "suggestion": "Say what it does.",
    },
    "un testimonio de": {"category": "significance_inflation", "severity": "hard", "suggestion": None},
    "marca un antes y un después": {
        "category": "significance_inflation", "severity": "hard", "suggestion": None,
    },
    "deja una huella imborrable": {
        "category": "significance_inflation", "severity": "hard", "suggestion": None,
    },

    # --- Vague attribution ----------------------------------------------------
    "expertos señalan": {"category": "vague_attribution", "severity": "hard", "suggestion": "Name the experts or cite the source."},
    "expertos aseguran": {"category": "vague_attribution", "severity": "hard", "suggestion": "Name the experts or cite the source."},
    "según los expertos": {"category": "vague_attribution", "severity": "hard", "suggestion": "Name the experts or cite the source."},
    "los estudios demuestran": {"category": "vague_attribution", "severity": "hard", "suggestion": "Cite the study."},
    "diversos estudios sugieren": {"category": "vague_attribution", "severity": "hard", "suggestion": "Cite the study."},
    "los analistas predicen": {"category": "vague_attribution", "severity": "hard", "suggestion": "Name the analysts or cite the forecast."},
    "fuentes cercanas": {"category": "vague_attribution", "severity": "soft", "suggestion": "Name the source."},

    # --- Promotional language -------------------------------------------------
    "un rico patrimonio cultural": {"category": "promotional", "severity": "hard", "suggestion": None},
    "el secreto mejor guardado": {"category": "promotional", "severity": "hard", "suggestion": None},
    "una joya escondida": {"category": "promotional", "severity": "hard", "suggestion": None},
    "una experiencia inolvidable": {"category": "promotional", "severity": "hard", "suggestion": None},
    "un destino imperdible": {"category": "promotional", "severity": "hard", "suggestion": None},

    # --- AI vocabulary (hard openers, soft single words) ----------------------
    "sumérgete en": {"category": "ai_vocabulary", "severity": "hard", "suggestion": None},
    "desbloquea el potencial": {"category": "ai_vocabulary", "severity": "hard", "suggestion": None},
    "desbloquear todo el potencial": {"category": "ai_vocabulary", "severity": "hard", "suggestion": None},
    "en el fascinante mundo de": {"category": "ai_vocabulary", "severity": "hard", "suggestion": None},
    "aprovecha al máximo": {"category": "ai_vocabulary", "severity": "hard", "suggestion": "usa, emplea"},
    "sinergia": {"category": "jargon", "severity": "soft", "suggestion": "coordinación, colaboración"},
    "sinergias": {"category": "jargon", "severity": "soft", "suggestion": "coordinación, colaboración"},
    "holístico": {"category": "jargon", "severity": "soft", "suggestion": "completo, integral"},
    "holística": {"category": "jargon", "severity": "soft", "suggestion": "completa, integral"},
    "empoderar": {"category": "jargon", "severity": "soft", "suggestion": "dar capacidad, permitir"},
    "vibrante": {"category": "ai_vocabulary", "severity": "soft", "suggestion": "activo, concurrido"},
    "robusto": {"category": "jargon", "severity": "soft", "suggestion": "sólido, resistente"},

    # --- False agency ---------------------------------------------------------
    "los datos hablan por sí solos": {"category": "false_agency", "severity": "hard", "suggestion": None},
    "el mercado premia": {"category": "false_agency", "severity": "hard", "suggestion": None},
    "la innovación exige": {"category": "false_agency", "severity": "hard", "suggestion": None},

    # --- Assistant artifacts and cutoff disclaimers ---------------------------
    "¿en qué puedo ayudarte hoy?": {"category": "assistant_artifact", "severity": "hard", "suggestion": None},
    "¿en qué más puedo ayudarte?": {"category": "assistant_artifact", "severity": "hard", "suggestion": None},
    "como modelo de lenguaje": {"category": "assistant_artifact", "severity": "hard", "suggestion": None},
    "estoy aquí para ayudarte": {"category": "assistant_artifact", "severity": "hard", "suggestion": None},
    "hasta mi última actualización": {"category": "knowledge_cutoff", "severity": "hard", "suggestion": None},
    "no tengo acceso a información en tiempo real": {
        "category": "knowledge_cutoff", "severity": "hard", "suggestion": None,
    },

    # --- Rhetorical openers ---------------------------------------------------
    "¿alguna vez te has preguntado": {"category": "rhetorical_question", "severity": "hard", "suggestion": None},
}


# Structural patterns: regexes over the masked text.
STRUCTURAL_PATTERNS_ES: list[dict[str, str]] = [
    # Copula avoidance: the Spanish "serves as / stands as" family. The abstract
    # noun list keeps ordinary verb use ("constituye una prueba", "funciona como
    # interfaz") clean instead of flagging every instance of the verb.
    {
        "pattern": r"\b(?:se\s+erige|se\s+consolida|se\s+posiciona|se\s+presenta)\s+como\s+(?:un|una|el|la)\s+"
                   r"(?:referente|símbolo|ejemplo|pilar|hito|motor|puente|faro|guía|modelo|testimonio|"
                   r"avance|pieza\s+clave|punto\s+de\s+referencia|punto\s+de\s+inflexión)\b",
        "category": "copula_avoidance",
        "severity": "hard",
        "suggestion": "Use a direct verb.",
    },
    {
        "pattern": r"\b(?:representa|constituye)\s+(?:un|una)\s+"
                   r"(?:hito|paso\s+(?:importante|firme|decisivo)|avance|punto\s+de\s+inflexión|"
                   r"testimonio|ejemplo|símbolo|compromiso|logro|reto|oportunidad\s+única|pieza\s+clave)\b",
        "category": "copula_avoidance",
        "severity": "hard",
        "suggestion": "Use a direct verb.",
    },
    {
        "pattern": r"\b(?:funciona|actúa|opera|sirve)\s+como\s+(?:un|una|el|la)\s+"
                   r"(?:puente|motor|catalizador|pilar|base|fundamento|guía|faro|brújula|plataforma|"
                   r"vehículo|enlace|punto\s+de\s+partida|punto\s+de\s+encuentro)\b",
        "category": "copula_avoidance",
        "severity": "hard",
        "suggestion": "Use a direct verb.",
    },
    {
        # The inflected adjectives not already covered by the literal phrase
        # table above; keeping them apart avoids a phrase and a regex reporting
        # the same span twice.
        "pattern": r"\b(?:juega|desempeña)\s+un\s+papel\s+"
                   r"(?:central|decisivo|esencial|importante|preponderante|protagónico)\b",
        "category": "significance_inflation",
        "severity": "hard",
        "suggestion": "Say what it does.",
    },

    # Negative parallelism and binary contrast.
    {
        "pattern": r"\bno\s+solo\s+[^.!?\n]{1,90}?\bsino\b(?:\s+también\b)?",
        "category": "negative_parallelism",
        "severity": "hard",
        "suggestion": "Use a direct sentence.",
    },
    {
        "pattern": r"\bno\s+(?:es|era|fue|somos|son|fueron)\s+solo\s+[^.;!?\n]{1,60}[,;—–-]\s*"
                   r"(?:es|era|fue|son|fueron)\b",
        "category": "negative_parallelism",
        "severity": "hard",
        "suggestion": "State the contrast directly.",
    },
    {
        "pattern": r"\bno\s+se\s+trata\s+de\s+[^.!?\n]{1,90}?\bsino\s+de\b",
        "category": "binary_contrast",
        "severity": "hard",
        "suggestion": "State the point in one sentence.",
    },

    # Emphasis crutches.
    {
        "pattern": r"\b(?:la\s+verdad\s+incómoda|lo\s+que\s+(?:realmente|de\s+verdad)\s+importa|"
                   r"no\s+es\s+casualidad\s+que|sin\s+duda\s+alguna|la\s+parte\s+que\s+nadie\s+cuenta)\b",
        "category": "emphasis_crutch",
        "severity": "hard",
        "suggestion": "State what matters.",
    },

    # Anti-slop register: the negated-fragment stack.
    {
        "pattern": r"(?im)(?:^|[.!?]\s+)(?:sin|con|más|menos|ni)\s+[a-záéíóúñ]{3,14}[.!?]\s+"
                   r"(?:sin|con|más|menos|ni)\s+[a-záéíóúñ]{3,14}[.!?]",
        "category": "anti_slop_register",
        "severity": "soft",
        "suggestion": "Join the fragments into a varied sentence.",
    },

    # Reader steering and rhetorical scaffolding.
    {
        "pattern": r"\b(?:imag[ií]nate|imagina\s+por\s+un\s+momento|piensa\s+por\s+un\s+momento|"
                   r"piénsalo\s+bien)\b|¿te\s+suena\s+familiar\?",
        "category": "reader_addressing",
        "severity": "soft",
        "suggestion": "Start with the point.",
    },
    {
        "pattern": r"(?m)^\s*(?:pasemos\s+a\b|a\s+continuación,|en\s+esta\s+sección\b|"
                   r"como\s+(?:se\s+)?(?:mencionó|vimos)\s+(?:anteriormente|arriba)\b)",
        "category": "reader_addressing",
        "severity": "soft",
        "suggestion": "Start with the point.",
    },

    # Hedging.
    {
        "pattern": r"\b(?:podría\s+quizá|podría\s+posiblemente|tal\s+vez\s+quizá|quizás\s+tal\s+vez|"
                   r"puede\s+que\s+tal\s+vez)\b",
        "category": "hedge_stack",
        "severity": "soft",
        "suggestion": "Drop the redundant hedge.",
    },

    # Cadence and list inflation.
    {
        "pattern": r"(?m)^(?:en\s+última\s+instancia,|al\s+final\s+del\s+día,|recordemos\s+que|"
                   r"el\s+futuro\s+(?:dirá|lo\s+dirá))",
        "category": "conclusion_scaffold",
        "severity": "soft",
        "suggestion": "End on the last real point.",
    },
    {
        "pattern": r"\b(?:en\s+primer\s+lugar|en\s+segundo\s+lugar|en\s+tercer\s+lugar|"
                   r"en\s+último\s+lugar)\b",
        "category": "numbered_list_inflation",
        "severity": "soft",
        "suggestion": "List only the points that matter.",
        "min_matches": "2",
    },
    {
        "pattern": r"\ben\s+un\s+mundo\s+(?:donde|cada\s+vez\s+más)\b",
        "category": "filler",
        "severity": "hard",
        "suggestion": "Say where and when.",
    },
    {
        "pattern": r"\ben\s+el\s+panorama\s+(?:actual|tecnológico|digital|competitivo)\b",
        "category": "ai_vocabulary",
        "severity": "soft",
        "suggestion": "Name the market or the field.",
    },
    {
        "pattern": r"\bnos\s+encontramos\s+ante\s+(?:un|una|el|la)\b",
        "category": "ai_vocabulary",
        "severity": "soft",
        "suggestion": "Say what is happening.",
    },
    {
        "pattern": r"\bsegún\s+(?:diversos|varios|algunos|muchos|numerosos)\s+"
                   r"(?:expertos|analistas|estudios|informes)\b",
        "category": "vague_attribution",
        "severity": "hard",
        "suggestion": "Name the source.",
    },
]


# Domain context used to suppress ordinary, non-slop Spanish uses. Mirrors the
# English context tables: legal drafting, real patrimony, cited sources, and
# clinical/scientific prose.
LEGAL_CONTEXT_ES = (
    r"\b(?:acuerdo|apelaci[óo]n|arrendamiento|art[íi]culo|cl[áa]usula|contratante|"
    r"contrato|convenio|delito|demandad[oa]|demandante|disposici[óo]n|escritura|"
    r"inquilino|juez|juzgado|jurisprudencia|legislaci[óo]n|ley|licitaci[óo]n|"
    r"ministerio|notari[ao]|pliego|procedimiento|procesal|procurador|reglamento|"
    r"requerimiento|resoluci[óo]n|sentencia|tribunal)\b"
)
HISTORICAL_CONTEXT_ES = (
    # "patrimonio" is deliberately absent: the phrase under protection contains
    # it, so including it would suppress every instance of the tell itself.
    r"\b(?:archivo|arqueolog|artesan|biblioteca|catálogo|crónica|conservaci[óo]n|"
    r"documento|época|excavaci[óo]n|herencia|hist[óo]ric|legado|museo|"
    r"restauraci[óo]n|tradici[óo]n|siglo|monumento|yacimiento)\w*\b"
)
PROMOTIONAL_CONTEXT_ES = (
    r"\b(?:visita|turis|destino|imperdible|playa|hotel|reserva|viaj\w*|degusta\w*|"
    r"saborea\w*|escapada|gastronom\w*|descuento|oferta|alojamiento)\w*\b"
)
SOURCE_CONTEXT_ES = (
    r"\b(?:según|de\s+acuerdo\s+con|cita\w*|publicad[oa]s?\s+(?:en|por)|"
    r"recogid[oa]s?\s+(?:en|por)|basad[oa]s?\s+en)\b|"
    r"\b(?:el|los|un|una)\s+(?:estudio|informe|ensayo|metaanálisis|revisión)\s+"
    r"(?:de|publicad[oa]|citad[oa])\b"
)
MEDICAL_CONTEXT_ES = (
    r"\b(?:anatom|bacteri|biolog|biomarcador|cancer|cardio|celular|c[ée]lula|clínic|"
    r"diagn[óo]stic|dosis|ensayo\s+clínico|enfermedad|estudio|farmac|genes?|gen[ée]tic|"
    r"genoma|hígado|infecci[óo]n|inflamaci[óo]n|inmun|m[ée]dic|médic|neurolog|"
    r"oncolog|paciente|patolog|fisiolog|proteína|riñón|síntoma|tejido|terapia|"
    r"tratamiento|tumor|virus)\w*\b"
)
