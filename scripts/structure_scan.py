#!/usr/bin/env python3
"""Scan prose for macro-structure AI-writing patterns."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from _lang import (  # noqa: E402
    ENGLISH_FUNCTION_WORDS,
    english_function_share,
    is_probably_english,
    detect_language,
    paragraphs as _prose_paragraphs,
    words,
)
from readability_metrics import split_sentences  # noqa: E402


STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "can", "it", "its", "this", "that",
    "these", "those", "we", "you", "they", "i", "he", "she", "as", "than",
    "if", "then", "so", "not", "no", "yes", "into", "over", "under",
}


CONNECTIVE_OPENERS = re.compile(
    r"^(however|moreover|furthermore|additionally|in addition|overall|"
    r"consequently|nevertheless)\b",
    re.I,
)
# Paragraph-initial "Every <noun> <verb-phrase>" template opener ("Every
# transformation is scored ...", "Every rewrite passes ..."). As a RHYTHM tell
# this is about REPETITION, so the metric below fires only at 2+ such paragraph
# openers; a lone "Every child deserves a good school." stays clean. The verb is
# a copula/auxiliary or a present/past inflection (-s / -ed) so the second word
# reads as a predicate, not another noun.
EVERY_OPENER_RE = re.compile(
    r"^every\s+[a-z][\w'-]*\s+(?:is|are|was|were|be|been|being|has|have|had|"
    r"do|does|did|can|will|shall|must|should|would|may|might|"
    r"[a-z]+(?:s|ed))\b",
    re.I,
)
SIGNPOST_RE = re.compile(
    r"\b(first,|next,|having (?:covered|established)|in (?:this|the following|"
    r"the next) section|as (?:mentioned|noted) (?:above|earlier)|let us turn|"
    r"let's turn)\b",
    re.I,
)
CLOSER_RE = re.compile(
    r",\s+(ensuring|highlighting|reflecting|allowing|enabling|underscoring|"
    r"showcasing|emphasizing|fostering|driving|paving|reinforcing|solidifying|"
    r"demonstrating|contributing to)\b[^.!?]*[.!?\"]?$",
    re.I,
)
CODA_START_RE = re.compile(
    r"^(ultimately,|in the end,|in conclusion|as we've seen|only time will tell|"
    r"remember,|the future\b)",
    re.I,
)
BOLD_COLON_RE = re.compile(r"^\s*[-*+]?\s*\*\*[^*]{1,40}\*\*\s*:", re.M)


# --- Spanish lexicon ---------------------------------------------------------
# Same metrics, Spanish word lists. The geometry (thresholds, floors, sweeps)
# is language-neutral and stays exactly as it is; only the vocabulary moves.
STOPWORDS_ES = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "que",
    "y", "o", "u", "en", "a", "al", "con", "sin", "por", "para", "sobre",
    "entre", "es", "son", "era", "eran", "fue", "ser", "está", "están",
    "estar", "hay", "ha", "han", "se", "su", "sus", "lo", "le", "les", "me",
    "te", "nos", "os", "mi", "tu", "más", "pero", "porque", "como", "cuando",
    "donde", "si", "no", "ni", "también", "muy", "todo", "todos", "toda",
    "todas", "otro", "otra", "mismo", "misma", "cada", "ambos", "este",
    "esta", "estos", "estas", "ese", "esa", "esos", "esas", "aquel", "esto",
    "eso", "algo", "alguien", "nada", "nadie", "ya", "aún", "todavía", "tan",
    "tanto", "poco", "casi", "solo", "solamente", "siempre", "nunca", "ahora",
    "antes", "después", "luego", "entonces", "así", "además", "incluso",
    "aquí", "allí", "ahí", "hoy", "ayer", "mañana",
}

CONNECTIVE_OPENERS_ES = re.compile(
    r"^(además|asimismo|por otro lado|sin embargo|no obstante|en consecuencia|"
    r"por lo tanto|de hecho|en cambio|por su parte)\b",
    re.I,
)
# Spanish "Cada <sustantivo> <verbo>" template opener. Fires only at 2+ such
# paragraph openers, same as the English table.
EVERY_OPENER_RE_ES = re.compile(
    r"^cada\s+[a-záéíóúñ][\w'-]*\s+(?:es|son|era|eran|fue|fueron|está|están|"
    r"tiene|tienen|debe|deben|puede|pueden|hace|hacen|necesita|necesitan|"
    r"importa|importan|cuenta|cuentan|merece|merecen|[a-záéíóúñ]+(?:a|e|ió|ó|an|en))\b",
    re.I,
)
SIGNPOST_RE_ES = re.compile(
    r"\b(primero,|en primer lugar,|a continuación,|en (?:esta|la siguiente|"
    r"la próxima) (?:sección|parte)|como (?:se )?(?:mencionó|vimos|dije) "
    r"(?:anteriormente|antes|arriba)|pasemos a|veamos ahora)\b",
    re.I,
)
CLOSER_RE_ES = re.compile(
    r",\s+(?:destacando|reflejando|permitiendo|asegurando|garantizando|"
    r"contribuyendo a|subrayando|impulsando|fomentando|reforzando|demostrando|"
    r"mostrando|marcando|consolidando|evidenciando|sugiriendo|indicando|"
    r"reduciendo|mejorando|optimizando)\b[^.!?]*[.!?\"]?$",
    re.I,
)
CODA_START_RE_ES = re.compile(
    r"^(en última instancia,|al final del día,|en conclusión|en definitiva,|"
    r"en resumen,|como hemos visto|recordemos que|solo el tiempo lo dirá|"
    r"el futuro\b)",
    re.I,
)

TRIAD_RE = re.compile(
    r"\b[A-Za-z][A-Za-z-]+,\s+[A-Za-z][A-Za-z-]+,\s+and\s+[A-Za-z][A-Za-z-]+\b"
)
TRIAD_RE_ES = re.compile(
    r"\b[A-Za-zÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜáéíóúñü-]+,\s+[A-Za-zÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜáéíóúñü-]+,\s+y\s+"
    r"[A-Za-zÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜáéíóúñü-]+\b"
)

ENUMERATION = {
    "the", "a", "an", "section", "chapter", "figure", "table", "step", "part",
    "appendix",
}
ENUMERATION_ES = {
    "el", "la", "los", "las", "un", "una", "sección", "capítulo", "figura",
    "tabla", "paso", "parte", "anexo",
}

LEXICONS = {
    "en": {
        "stopwords": STOPWORDS,
        "connective_openers": CONNECTIVE_OPENERS,
        "every_opener": EVERY_OPENER_RE,
        "signpost": SIGNPOST_RE,
        "closer": CLOSER_RE,
        "coda": CODA_START_RE,
        "triad": TRIAD_RE,
        "enumeration": ENUMERATION,
    },
    "es": {
        "stopwords": STOPWORDS_ES,
        "connective_openers": CONNECTIVE_OPENERS_ES,
        "every_opener": EVERY_OPENER_RE_ES,
        "signpost": SIGNPOST_RE_ES,
        "closer": CLOSER_RE_ES,
        "coda": CODA_START_RE_ES,
        "triad": TRIAD_RE_ES,
        "enumeration": ENUMERATION_ES,
    },
}


def prose_paragraphs(text: str) -> list[str]:
    return _prose_paragraphs(text, blank_blockquotes=True)


def cv(values: list[int]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    if mean == 0:
        return 0.0
    return math.sqrt(sum((v - mean) ** 2 for v in values) / len(values)) / mean


def content_bigrams(text: str, stopwords: set[str] | None = None) -> set[tuple[str, str]]:
    stopwords = STOPWORDS if stopwords is None else stopwords
    toks = [w for w in words(text) if len(w) > 3 and w not in stopwords]
    return set(zip(toks, toks[1:]))


def triad_count(text: str, pattern: re.Pattern[str] | None = None) -> int:
    return len((pattern or TRIAD_RE).findall(text))


def flag(metric: str, value: float | int, threshold: str, detail: str, suggestion: str) -> dict:
    return {
        "metric": metric,
        "value": value,
        "threshold": threshold,
        "severity": "soft",
        "detail": detail,
        "suggestion": suggestion,
    }


# Metrics a given --genre suppresses outright (the genre's normal shape trips
# the metric without being AI-slop). Table form so each suppression is a single
# lookup instead of an inline `genre != "..."` conditional per metric.
GENRE_SUPPRESSIONS = {
    "docs": {"bold_colon_listicle"},
    "social": {"one_line_staccato"},
}


def scan(text: str, genre: str = "prose", lang: str | None = None) -> dict:
    if lang is None:
        lang = detect_language(text)
    # Unsupported languages fall back to the English lexicon (the historical
    # default); the CLI declines them only when nothing flagged.
    lexicon = LEXICONS["es"] if lang == "es" else LEXICONS["en"]
    paragraphs = prose_paragraphs(text)
    prose_text = "\n\n".join(paragraphs)
    sentences = split_sentences(prose_text, lang)
    sentence_lengths = [len(words(s)) for s in sentences]
    prose_words = words(prose_text)
    para_lengths = [len(words(p)) for p in paragraphs]
    metrics = {
        "sentence_burstiness": round(cv(sentence_lengths), 3),
        "summary_sandwich": 0.0,
        "paragraph_cv": round(cv(para_lengths), 3),
        "sentence_mean_len": round(sum(sentence_lengths) / len(sentence_lengths), 1) if sentence_lengths else 0,
        "triad_density": round((triad_count(prose_text, lexicon["triad"]) / len(prose_words) * 1000), 3) if prose_words else 0,
        "em_dash_per_1k": round((text.count("—") / len(prose_words) * 1000), 3) if prose_words else 0,
        "bold_colon_listicle_count": len(BOLD_COLON_RE.findall(text)),
        "one_line_staccato_share": 0.0,
        "connective_paragraph_openers": 0,
        "every_template_openers": 0,
        "signpost_density": 0.0,
        "opener_unique_ratio": 0.0,
        "top_opener_share": 0.0,
        "max_consecutive_opener": 0,
        "participial_closer_share": 0.0,
        "conclusion_coda": False,
    }
    flags = []

    if len(paragraphs) >= 2:
        first = content_bigrams(paragraphs[0], lexicon["stopwords"])
        last = content_bigrams(paragraphs[-1], lexicon["stopwords"])
        union = first | last
        metrics["summary_sandwich"] = round(len(first & last) / len(union), 3) if union else 0.0

    if len(sentences) >= 8 and metrics["sentence_burstiness"] < 0.55:
        flags.append(flag(
            "sentence_burstiness",
            metrics["sentence_burstiness"],
            "< 0.55 over at least 8 prose sentences",
            "Sentence lengths are unusually uniform for running prose.",
            "Vary sentence length and cadence; if this is formal reference prose, review before treating it as blocking.",
        ))

    if len(paragraphs) >= 3:
        coda = bool(lexicon["coda"].search(paragraphs[-1]))
        if not coda:
            coda = len(content_bigrams(paragraphs[0], lexicon["stopwords"]) & content_bigrams(paragraphs[-1], lexicon["stopwords"])) >= 2
        metrics["conclusion_coda"] = coda
        if coda:
            flags.append(flag(
                "conclusion_coda",
                1,
                "last paragraph starts with a stock coda or repeats 2+ first-paragraph content bigrams",
                "The ending reads like a recap/moral coda instead of a concrete final point.",
                "Cut the wrap-up or end on a specific fact; if this is an abstract or executive summary, judge the genre before changing it.",
            ))

    if (metrics["bold_colon_listicle_count"] >= 3
            and "bold_colon_listicle" not in GENRE_SUPPRESSIONS.get(genre, set())):
        flags.append(flag(
            "bold_colon_listicle",
            metrics["bold_colon_listicle_count"],
            ">= 3 bold-label colon lines",
            "The raw Markdown has repeated bold-label listicle formatting.",
            "Convert to prose or plain bullets; if this is a reference doc, rerun with --genre docs.",
        ))

    if paragraphs:
        one_line = 0
        for p in paragraphs:
            ps = split_sentences(p, lang)
            if len(ps) == 1 and len(words(ps[0])) < 12:
                one_line += 1
        metrics["one_line_staccato_share"] = round(one_line / len(paragraphs), 3)
        if (len(paragraphs) >= 6 and metrics["one_line_staccato_share"] > 0.6
                and "one_line_staccato" not in GENRE_SUPPRESSIONS.get(genre, set())):
            flags.append(flag(
                "one_line_staccato",
                metrics["one_line_staccato_share"],
                "> 0.60 over at least 6 paragraphs",
                "Most paragraphs are short single-sentence beats.",
                "Merge related beats and vary paragraph length; if this is social copy, rerun with --genre social.",
            ))

    connective = sum(1 for p in paragraphs if lexicon["connective_openers"].search(p))
    metrics["connective_paragraph_openers"] = connective
    if connective >= 3 or (len(paragraphs) >= 8 and connective / len(paragraphs) > 0.4):
        flags.append(flag(
            "connective_paragraph_openers",
            connective,
            ">= 3 paragraphs or > 40% of 8+ paragraphs",
            "Paragraphs repeatedly open with formal transition words.",
            "Replace scaffold openers with specific topic sentences; academic prose may justify some connectors.",
        ))

    every_openers = sum(1 for p in paragraphs if lexicon["every_opener"].search(p))
    metrics["every_template_openers"] = every_openers
    if every_openers >= 2:
        flags.append(flag(
            "every_template_openers",
            every_openers,
            ">= 2 paragraphs opening 'Every <noun> <verb>'",
            "Paragraphs repeatedly open on the 'Every ___ is/does ...' template.",
            "Vary the paragraph openings; a repeated Every-template is a machine rhythm tell even when each sentence is fine on its own.",
        ))

    if prose_words:
        signposts = len(lexicon["signpost"].findall(prose_text))
        metrics["signpost_density"] = round(signposts / len(prose_words) * 100, 3)
        if len(prose_words) >= 150 and metrics["signpost_density"] > 0.6:
            flags.append(flag(
                "signpost_density",
                metrics["signpost_density"],
                "> 0.6 per 100 prose words, minimum 150 words",
                "The text over-explains its own structure.",
                "Remove roadmap language unless the genre is a textbook, legal brief, or long guide.",
            ))

    if len(sentences) >= 5:
        openers = []
        for s in sentences:
            ws = words(s)
            if not ws:
                continue
            openers.append(ws[0])
        enumeration = lexicon["enumeration"]
        counted = [o for o in openers if o not in enumeration]
        top_count = 0
        if counted:
            counts = Counter(counted)
            top_count = max(counts.values())
            metrics["opener_unique_ratio"] = round(len(counts) / len(counted), 3)
            metrics["top_opener_share"] = round(top_count / len(counted), 3)
        run = max_run = 0
        prev = None
        for opener in counted:
            run = run + 1 if opener == prev else 1
            prev = opener
            max_run = max(max_run, run)
        metrics["max_consecutive_opener"] = max_run
        top_repeat = metrics["top_opener_share"] > 0.25 and top_count >= 4
        if metrics["opener_unique_ratio"] < 0.55 or top_repeat or max_run >= 4:
            flags.append(flag(
                "opener_repetition",
                metrics["opener_unique_ratio"],
                "unique ratio < 0.55, one opener > 25% with 4+ uses, or 4 consecutive identical openers",
                "Sentence openings repeat in a template-like rhythm.",
                "Rewrite repeated starts; step-by-step docs may need repeated imperative openers.",
            ))

    if sentences:
        closer_count = sum(1 for s in sentences if lexicon["closer"].search(s))
        metrics["participial_closer_share"] = round(closer_count / len(sentences), 3)
        if len(sentences) >= 8 and metrics["participial_closer_share"] >= 0.15:
            flags.append(flag(
                "participial_closer_share",
                metrics["participial_closer_share"],
                ">= 0.15 over at least 8 prose sentences",
                "Many sentences end with editorial -ing consequence tails.",
                "Make the consequence concrete or cut the tail; analytical prose may allow an occasional closer.",
            ))

    return {
        "language": lang,
        "flags": flags,
        "flagged": {f["metric"]: True for f in flags},
        "metrics": metrics,
        "genre": genre,
        "prose_sentences": len(sentences),
        "prose_paragraphs": len(paragraphs),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?")
    parser.add_argument("--genre", choices=["prose", "docs", "social"], default="prose")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.path:
        path = Path(args.path)
        if not path.exists():
            print(f"Missing file: {path}", file=sys.stderr)
            return 2
        text = path.read_text(errors="replace")
    else:
        text = sys.stdin.buffer.read().decode("utf-8", errors="replace")

    lang = detect_language(text)
    result = scan(text, args.genre, lang=lang)

    # Language route: English and Spanish both scan; everything else declines,
    # and only when nothing flagged (function-word absence alone is not evidence
    # of a foreign language: imperative stacks and buzzword lists are slop with
    # few function words).
    if not result.get("flags") and lang == "other":
        print(json.dumps({"non_english": True, "language": "other", "violations": [], "flags": []}, indent=2))
        print("note: input appears to be an unsupported language; scanner declined (supported: English, Spanish).", file=sys.stderr)
        return 0

    print(json.dumps(result, indent=2))
    return 1 if result["flags"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
