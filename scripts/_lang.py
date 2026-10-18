#!/usr/bin/env python3
"""Shared cheap English-detection helpers for banned_phrase_scan.py,
structure_scan.py, and silhouette_scan.py. All three scanners must decline the
same non-English inputs, so this table and its two functions live in exactly
one place.

Also home to the shared prose-view helpers (tokenizer, markdown stripper,
paragraph splitter) used by structure_scan.py and silhouette_scan.py. Those
two scanners previously carried private copies of these functions that had
drifted from each other (structure blanked blockquote lines, silhouette
didn't; silhouette stripped **bold**, structure didn't). strip_markdown_for_prose
below is the UNION of both original code paths, gated behind flags so each
caller reconciles the drift deliberately rather than silently: structure_scan
passes blank_blockquotes=True, silhouette_scan passes strip_bold=True."""

from __future__ import annotations

import re


# A small set of high-frequency English function words used only for a cheap
# language check. The words are chosen to be distinctively English: Spanish,
# French, German, etc. rarely use them, so their share of tokens is a robust
# signal without a language-model dependency.
ENGLISH_FUNCTION_WORDS = frozenset({
    "the", "and", "is", "are", "was", "were", "of", "to", "in", "that", "it",
    "for", "with", "on", "this", "but", "not", "you", "have", "be", "as", "at",
    "or", "we", "they", "will", "would", "there", "their", "what", "which",
    "when", "from", "been", "has", "had", "its", "an", "by", "our", "your",
    "if", "than", "then", "them", "these", "those", "about", "into", "over",
    "after", "before", "how", "why", "where", "who", "can", "could", "should",
    "do", "does", "did", "so", "out", "just", "more", "most", "some", "such",
    "only", "also", "because", "while", "between", "through", "during", "being",
})


def english_function_share(text: str) -> float:
    """Share of word tokens that are common English function words."""
    tokens = re.findall(r"[a-z']+", text.lower())
    if not tokens:
        return 1.0
    hits = sum(1 for t in tokens if t in ENGLISH_FUNCTION_WORDS)
    return hits / len(tokens)


def is_probably_english(text: str, threshold: float = 0.10, min_tokens: int = 15) -> bool:
    """Cheap English detector backing a graceful non-English decline.

    Conservative on purpose: inputs below ``min_tokens`` are always treated as
    English (too little signal to decline), and ``threshold`` is low enough that
    even terse or ESL-flavored English clears it. Only prose with almost no
    English function words (i.e. another language) is declined.
    """
    tokens = re.findall(r"[a-z']+", text.lower())
    if len(tokens) < min_tokens:
        return True
    return english_function_share(text) >= threshold


# Spanish function words, same construction as the English table above. The list
# is deliberately generous (articles, pronouns, prepositions, auxiliaries and
# high-frequency adverbs) because the decision it feeds is a tri-state language
# route, not a fine-grained classification.
SPANISH_FUNCTION_WORDS = frozenset({
    "el", "la", "los", "las", "un", "una", "unos", "unas", "lo", "le", "les",
    "me", "te", "se", "nos", "os", "su", "sus", "mi", "mis", "tu", "tus",
    "nuestro", "nuestra", "nuestros", "nuestras", "este", "esta", "estos",
    "estas", "ese", "esa", "esos", "esas", "aquel", "aquella", "aquellos",
    "aquellas", "esto", "eso", "aquello", "quien", "quienes", "cual",
    "cuales", "algo", "alguien", "nada", "nadie", "todo", "todos", "toda",
    "todas", "otro", "otra", "otros", "otras", "mismo", "misma", "cada",
    "ambos", "de", "del", "a", "al", "en", "con", "sin", "por", "para",
    "sobre", "entre", "hasta", "desde", "hacia", "según", "contra", "durante",
    "mediante", "tras", "y", "e", "o", "u", "ni", "pero", "sino", "aunque",
    "porque", "pues", "como", "cuando", "donde", "mientras", "si", "no", "sí",
    "ya", "aún", "todavía", "también", "tampoco", "más", "menos", "muy",
    "tan", "tanto", "mucho", "mucha", "muchos", "muchas", "poco", "poca",
    "pocos", "pocas", "casi", "solo", "solamente", "siempre", "nunca",
    "jamás", "ahora", "antes", "después", "luego", "entonces", "así",
    "además", "incluso", "quizá", "quizás", "acaso", "aquí", "allí", "ahí",
    "allá", "hoy", "ayer", "mañana", "es", "son", "era", "eran", "fue",
    "fueron", "ser", "está", "están", "estoy", "estamos", "estaba",
    "estaban", "estar", "hay", "había", "hubo", "haber", "ha", "han", "he",
    "hemos", "tiene", "tienen", "tenía", "tener", "puede", "pueden", "podía",
    "hacer", "hace", "hacen", "hizo", "decir", "dice", "dicen", "dijo",
    "vamos", "va", "van", "ir", "sé", "sabe", "saben", "quiere", "quieren",
    "debe", "deben", "parece", "parecen",
})

# Function words of the languages that surround Spanish (Portuguese, French,
# Italian, German). Spanish shares articles and prepositions with its Romance
# neighbors, so the function-word share alone cannot separate them; these words
# cannot appear in Spanish prose, and a couple of them settle the route.
FOREIGN_FUNCTION_WORDS = frozenset({
    # Portuguese
    "não", "uma", "com", "mais", "também", "muito", "você", "são", "foi",
    "dos", "das", "pelo", "pela", "seus", "suas", "isso", "aos",
    # French
    "les", "des", "une", "est", "pas", "dans", "pour", "avec", "mais",
    "aussi", "cette", "nous", "vous", "ils", "elles", "être", "été", "aux",
    "ces", "sont", "était", "votre", "notre", "leur",
    # Italian
    "gli", "della", "delle", "sono", "anche", "questo", "questa", "perché",
    "molto", "nella", "degli",
    # German
    "der", "die", "das", "und", "ist", "nicht", "sich", "mit", "auf", "für",
    "ein", "eine", "sind", "auch", "dass", "werden", "wird", "nur", "eine",
    "des", "dem", "den",
})

# Two foreign markers (chars that Spanish never uses) or two foreign function
# words veto a supported-language verdict.
FOREIGN_WORD_MIN_HITS = 2
FOREIGN_WORD_MIN_SHARE = 0.03
UNSUPPORTED_LANGUAGE_MARKERS = (
    "ã", "õ", "ç", "ê", "ô", "à", "ë", "ï", "œ", "æ", "ä", "ö", "ß", "å", "ø",
    "è", "ù", "î", "û", "ò", "ì",
)

MIN_LANGUAGE_TOKENS = 15
_TOKEN_RE = re.compile(r"[^\W\d_]+", re.UNICODE)
_MARKER_RE = re.compile("[%s]" % "".join(UNSUPPORTED_LANGUAGE_MARKERS))

# One-entry memo. Language detection and the scan-first short-text check run
# back to back on the same string, and a full tokenization of a large document
# is the single most expensive part of the route; caching the last input turns
# two passes over the text into one.
_LAST_TEXT: str | None = None
_LAST_TOKENS: list[str] = []


def _word_tokens(text: str) -> list[str]:
    """Unicode word tokens (letters incl. accents), lowercased."""
    global _LAST_TEXT, _LAST_TOKENS
    cached = _LAST_TEXT
    if cached is not None and cached == text:
        return _LAST_TOKENS
    tokens = _TOKEN_RE.findall(text.lower())
    _LAST_TEXT, _LAST_TOKENS = text, tokens
    return tokens


def _share(tokens: list[str], vocabulary: frozenset[str]) -> float:
    if not tokens:
        return 0.0
    return sum(1 for token in tokens if token in vocabulary) / len(tokens)


def spanish_function_share(text: str) -> float:
    """Share of word tokens that are common Spanish function words."""
    return _share(_word_tokens(text), SPANISH_FUNCTION_WORDS)


def is_probably_spanish(text: str, threshold: float = 0.10, min_tokens: int = 15) -> bool:
    """Cheap Spanish detector.

    Conservative in the opposite direction from ``is_probably_english``: short
    inputs need stronger evidence (0.15) because the default route for
    low-signal text is English.
    """
    tokens = _word_tokens(text)
    if len(tokens) < min_tokens:
        return _share(tokens, SPANISH_FUNCTION_WORDS) >= 0.15
    return _share(tokens, SPANISH_FUNCTION_WORDS) >= threshold


def _foreign_evidence(text: str, tokens: list[str]) -> bool:
    """Orthographic or lexical evidence of an unsupported neighbor language."""
    # One regex pass over the lowered text instead of one str.count per marker.
    if len(_MARKER_RE.findall(text.lower())) >= 2:
        return True
    hits = sum(1 for token in tokens if token in FOREIGN_FUNCTION_WORDS)
    if hits < FOREIGN_WORD_MIN_HITS:
        return False
    return not tokens or hits / len(tokens) >= FOREIGN_WORD_MIN_SHARE


def word_token_count(text: str) -> int:
    """Number of Unicode word tokens (the language signal's unit)."""
    return len(_word_tokens(text))


def detect_language(text: str) -> str:
    """Route text to a supported scan language: "en", "es", or "other".

    English is the sticky default: inputs with too little signal stay "en" so
    the pre-existing behavior (better to scan than to decline) is preserved.
    Spanish needs positive evidence, and foreign function words or non-Spanish
    orthography veto it unless English itself has a strong claim — which keeps
    an English article about France from declining over two French quotes.
    "other" is the only value that may decline.
    """
    tokens = _word_tokens(text)
    if not tokens:
        return "en"
    english_share = _share(tokens, ENGLISH_FUNCTION_WORDS)
    spanish_share = _share(tokens, SPANISH_FUNCTION_WORDS)
    if _foreign_evidence(text, tokens) and not (
        english_share >= 0.20 and english_share > spanish_share
    ):
        return "other"
    if len(tokens) < MIN_LANGUAGE_TOKENS:
        if spanish_share >= 0.15 and spanish_share >= english_share:
            return "es"
        return "en"
    if spanish_share >= 0.10 and spanish_share >= english_share:
        return "es"
    if english_share >= 0.10:
        return "en"
    return "other"


def words(text: str) -> list[str]:
    return re.findall(r"[^\W_]+(?:[-'][^\W_]+)?", text.lower())


def strip_markdown_for_prose(
    text: str, *, blank_blockquotes: bool = False, strip_bold: bool = False
) -> str:
    """Strip markdown structure down to a prose view for cadence/discourse
    metrics. UNION of structure_scan's and silhouette_scan's original
    strippers -- each original branch is preserved verbatim, gated behind the
    flag that reproduces that caller's exact prior behavior.

    blank_blockquotes=True reproduces structure_scan's prior strip (blanks
    both blockquote and heading lines in one combined check). strip_bold=True
    reproduces silhouette_scan's prior strip (also collapses **bold** markers
    after list/ordinal stripping).
    """
    text = re.sub(r"```[\s\S]*?```", "\n\n", text)
    kept = []
    for line in text.splitlines():
        if blank_blockquotes:
            if re.match(r"\s*>", line) or re.match(r"\s{0,3}#{1,6}\s+", line):
                kept.append("")
                continue
        else:
            if re.match(r"\s{0,3}#{1,6}\s+", line):
                kept.append("")  # drop heading text from the prose view
                continue
        line = re.sub(r"^\s*[-*+]\s+", "", line)
        line = re.sub(r"^\s*\d+[.)]\s+", "", line)
        if strip_bold:
            line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
        kept.append(line)
    return "\n".join(kept)


def paragraphs(
    text: str, *, blank_blockquotes: bool = False, strip_bold: bool = False
) -> list[str]:
    stripped = strip_markdown_for_prose(
        text, blank_blockquotes=blank_blockquotes, strip_bold=strip_bold
    )
    return [
        re.sub(r"\s+", " ", p).strip()
        for p in re.split(r"\n\s*\n", stripped)
        if p.strip()
    ]
