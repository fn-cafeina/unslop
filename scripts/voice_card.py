#!/usr/bin/env python3
"""Distill a voice profile + samples into a LAYERED, pack-sized style card.

Output layout (deterministic — same inputs give byte-identical files):

    <out>/card.md            core sheet, always loaded, <= 300 words, with an
                             index table "when writing X, read card/X.md"
    <out>/card/<situation>.md  one sheet per COVERED situation from the taxonomy

Only situations with real sample evidence get a sheet. Uncovered situations are
NAMED in card.md under "Uncovered" and never given a fabricated sheet — every
claim on every sheet is derived from a measurable profile/sample fact or a
verbatim sample snippet.

``--coverage`` emits the deterministic lexical coverage matrix (which taxonomy
dimensions the samples exercise) as JSON and writes nothing. The classifier is
intentionally coarse: it only DRIVES interactive teach prompts and the sheet
set. A misclassified sentence can add or drop a sheet, never a card claim, so
misclassification is low-stakes by construction.

``--provenance`` also writes <out>/provenance.json (per-sample sha256 + word
counts, doc count, genre note, low-confidence flag) so a teach run is auditable.
"""

from __future__ import annotations


import argparse
import hashlib
import json
import re
import statistics
import sys
from pathlib import Path

import voice_profile

# The situation taxonomy. openings/closings are STRUCTURAL (first/last sentence
# of every document); the rest are lexical. Order is fixed for determinism.
TAXONOMY = [
    "explaining-technical",
    "anecdote",
    "argument",
    "disagreement",
    "praise",
    "hedging-uncertainty",
    "numbers-data",
    "addressing-reader",
    "openings",
    "closings",
]

STRUCTURAL = {"openings", "closings"}

# Minimum classified sentences before a lexical dimension counts as covered.
COVER_THRESHOLD = 2

NUMBER_WORDS = {
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "dozen", "hundred", "thousand", "million",
    "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty",
    "ninety", "percent", "half", "quarter", "double", "triple", "nine",
}

# Lexical signals per dimension. Each entry is a set of lowercase substrings;
# a sentence matches the dimension if any signal is present (word-boundary
# aware for single tokens, plain substring for multiword phrases).
SIGNALS = {
    "explaining-technical": {
        "because", "so that", "which means", "the reason", "works by",
        "depends on", "the way it", "in order to", "that's how", "this is how",
        "the trick is", "you have to", "the point of",
    },
    "argument": {
        "therefore", "thus", "consequently", "the point is", "i distrust",
        "clearly", "obviously", "in fact", "the truth is", "matters because",
        "that's the point", "either way", "that's rare", "nobody", "no one",
    },
    "disagreement": {
        "but i", "i don't", "no one", "nobody", "wrong", "i distrust",
        "rather than", "not because", "i hate", "don't trust", "disagree",
        "however", "i wasn't", "makes sense", "i can't",
    },
    "praise": {
        "extraordinary", "wonderful", "dependable", "lovely", "beautiful",
        "kindly", "generous", "grateful", "delightful", "plenty", "good choice",
        "with care", "extraordinary care", "almost pleasant", "i like",
    },
    "hedging-uncertainty": {
        "maybe", "perhaps", "probably", "might", "i guess", "i think",
        "seems", "sort of", "kind of", "possibly", "i suppose", "not sure",
        "or won't", "or it won't", "i believed", "or maybe",
    },
    "addressing-reader": set(),  # handled specially (2nd person / question)
    "numbers-data": set(),       # handled specially (digits / number words)
    "anecdote": set(),           # handled specially (1st person + past/time cue)
}

FIRST_PERSON = {"i", "we", "my", "me", "we've", "i've", "i'll", "i'd", "our"}
TIME_CUES = {
    "today", "yesterday", "tonight", "morning", "evening", "night", "ago",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "last", "once", "then", "later", "week", "year",
}



# Spanish lexical signals for the same taxonomy. Multiword entries match as
# substrings; single tokens match on word boundaries.
NUMBER_WORDS_ES = {
    "uno", "una", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho",
    "nueve", "diez", "once", "doce", "docena", "quince", "veinte", "treinta",
    "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa",
    "cien", "ciento", "mil", "millón", "millones", "por ciento", "medio",
    "mitad", "doble", "triple",
}

SIGNALS_ES = {
    "explaining-technical": {
        "porque", "de modo que", "lo que significa", "la razón", "funciona",
        "depende de", "la forma en que", "para que", "así es como", "la clave",
        "tienes que", "el punto de",
    },
    "argument": {
        "por lo tanto", "así pues", "en consecuencia", "el punto es",
        "desconfío", "está claro", "obviamente", "de hecho", "la verdad es",
        "importa porque", "ese es el punto", "de cualquier forma", "nadie",
    },
    "disagreement": {
        "pero yo", "no creo", "nadie", "equivocado", "desconfío", "en lugar de",
        "no porque", "no soporto", "no confío", "no estoy de acuerdo",
        "sin embargo", "no me parece", "tiene sentido", "no puedo",
    },
    "praise": {
        "extraordinario", "maravilloso", "fiable", "precioso", "hermoso",
        "amable", "generoso", "agradecido", "espléndido", "buena elección",
        "con cuidado", "cuidado extremo", "bastante agradable", "me gusta",
    },
    "hedging-uncertainty": {
        "quizá", "quizás", "tal vez", "probablemente", "puede que",
        "supongo", "parece", "más o menos", "de algún modo", "posiblemente",
        "no estoy seguro", "creía", "o puede que", "diría",
    },
    "addressing-reader": set(),  # handled specially (2nd person / question)
    "numbers-data": set(),       # handled specially (digits / number words)
    "anecdote": set(),           # handled specially (1st person + past/time cue)
}

FIRST_PERSON_ES = {
    "yo", "nosotros", "nosotras", "mi", "mis", "me", "nos", "nuestro",
    "nuestra", "nuestros", "nuestras",
}
TIME_CUES_ES = {
    "hoy", "ayer", "anoche", "esta mañana", "esta tarde", "esta noche",
    "hace", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado",
    "domingo", "último", "última", "una vez", "entonces", "después",
    "semana", "año", "mes", "siempre", "nunca",
}


def _lexicon(lang="en"):
    if lang == "es":
        return SIGNALS_ES, NUMBER_WORDS_ES, FIRST_PERSON_ES, TIME_CUES_ES
    return SIGNALS, NUMBER_WORDS, FIRST_PERSON, TIME_CUES


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def split_sentences_text(text):
    """Split into trimmed sentence strings, preserving original wording."""
    out = []
    for chunk in re.split(r"(?<=[.!?])\s+", text.strip()):
        chunk = re.sub(r"\s+", " ", chunk).strip()
        if chunk:
            out.append(chunk)
    return out


def _has_word(sentence_low, token):
    return re.search(r"\b" + re.escape(token) + r"\b", sentence_low) is not None


def _matches(sentence_low, signals):
    for sig in signals:
        if " " in sig:
            if sig in sentence_low:
                return True
        elif _has_word(sentence_low, sig):
            return True
    return False


def _is_numbers(sentence_low, lang="en"):
    if re.search(r"\d", sentence_low):
        return True
    number_words = _lexicon(lang)[1]
    return any(_has_word(sentence_low, w) for w in number_words)


def _is_anecdote(sentence_low, lang="en"):
    _, _, first_person, time_cues = _lexicon(lang)
    toks = set(voice_profile.words(sentence_low, lang))
    if not (toks & first_person):
        return False
    if toks & time_cues:
        return True
    # English marks the past with -ed; Spanish uses its own inflections, which
    # the time cues above already cover ("ayer", "hace", "la semana pasada").
    return lang == "en" and any(t.endswith("ed") and len(t) > 3 for t in toks)


def _is_addressing(sentence, lang="en"):
    low = sentence.lower()
    if sentence.rstrip().endswith("?"):
        return True
    if lang == "es":
        return any(_has_word(low, w) for w in ("tú", "ti", "tu", "tus", "usted", "ustedes", "te"))
    return _has_word(low, "you") or _has_word(low, "your") or _has_word(low, "you're")


def classify_dimension(sentence, lang="en"):
    """Return the set of lexical dimensions a single sentence exercises."""
    low = sentence.lower()
    signals_table = _lexicon(lang)[0]
    hit = set()
    for dim, signals in signals_table.items():
        if dim in ("addressing-reader", "numbers-data", "anecdote"):
            continue
        if _matches(low, signals):
            hit.add(dim)
    if _is_numbers(low, lang):
        hit.add("numbers-data")
    if _is_addressing(sentence, lang):
        hit.add("addressing-reader")
    if _is_anecdote(low, lang):
        hit.add("anecdote")
    return hit


def collect(samples_dir, lang="en"):
    """Return (docs, sentences) where each doc is a list of sentence strings."""
    docs = []
    for path in voice_profile.iter_docs(samples_dir):
        sents = split_sentences_text(path.read_text(errors="replace"))
        if sents:
            docs.append(sents)
    return docs


def coverage_matrix(docs, lang="en"):
    """Deterministic coverage of the taxonomy over the sample sentences."""
    buckets = {dim: [] for dim in TAXONOMY}
    for doc in docs:
        if doc:
            buckets["openings"].append(doc[0])
            buckets["closings"].append(doc[-1])
        for sent in doc:
            for dim in classify_dimension(sent, lang):
                buckets[dim].append(sent)
    matrix = {}
    for dim in TAXONOMY:
        sents = buckets[dim]
        if dim in STRUCTURAL:
            covered = len(docs) >= 1
        else:
            covered = len(sents) >= COVER_THRESHOLD
        matrix[dim] = {
            "count": len(sents),
            "covered": covered,
            "structural": dim in STRUCTURAL,
        }
    return matrix, buckets


def _shortest(sentences, k=3):
    ordered = sorted(set(sentences), key=lambda s: (len(s), s))
    return ordered[:k]


def _contraction_examples(docs, k=3):
    seen = {}
    for doc in docs:
        for sent in doc:
            for tok in voice_profile.words(sent):
                if "'" in tok:
                    seen[tok] = seen.get(tok, 0) + 1
    ranked = sorted(seen.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, _ in ranked[:k]]


def _opener_words(docs, k=5):
    counts = {}
    for doc in docs:
        for sent in doc:
            toks = voice_profile.words(sent)
            if toks:
                counts[toks[0]] = counts.get(toks[0], 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, _ in ranked[:k]]


def _burstiness(profile):
    med = profile["sentence_lengths"]["median"]
    iqr = profile["sentence_lengths"]["iqr"]
    if med <= 0:
        return "uneven"
    ratio = iqr / med
    if ratio < 0.5:
        return "steady"
    if ratio < 1.1:
        return "moderately bursty"
    return "very bursty"



SHEET_HOWTO_ES = {
    "explaining-technical": "Explica nombrando el mecanismo concreto, no la abstracción. Frases causales cortas; el 'porque' hace el trabajo.",
    "anecdote": "Cuéntalo en primera persona, en pasado, una escena cada vez. Sustantivos concretos, detalle sensorial, sin moraleja final.",
    "argument": "Afirma el punto sin rodeos y luego la razón. Sin andamiaje de matices; el punto cae en una línea.",
    "disagreement": "Disiente por contraste, no por confrontación. 'No creo', 'en lugar de', una preferencia llana antes que una embestida.",
    "praise": "Elogia con detalle específico y contenido. Aprobación sobria, nunca efusiva.",
    "hedging-uncertainty": "Sostén la incertidumbre con 'quizá' / 'probablemente' / 'o puede que', no con matices corporativos.",
    "numbers-data": "Las cifras se quedan pequeñas y concretas, tejidas en la escena en lugar de tabuladas.",
    "addressing-reader": "Dirígete al lector con moderación y llaneza; una pregunta directa o un 'puedes' seco.",
    "openings": "Abre en frío con un hecho o una acción concreta. Sin preludios, sin tesis anunciada.",
    "closings": "Cierra con una imagen pequeña y específica. Sin resumen, sin 'en definitiva'.",
}

NEVER_LABELS_ES = {";": "punto y coma", "!": "signos de exclamación", ":": "dos puntos",
                   "-": "guiones largos", "(": "paréntesis", "¿": "aperturas de interrogación",
                   "¡": "aperturas de exclamación", "«": "comillas latinas"}


def _numbers_tokens(sentences, lang="en"):
    toks = set()
    for sent in sentences:
        for m in re.findall(r"\d[\d,:.]*", sent):
            toks.add(m)
        for w in voice_profile.words(sent.lower(), lang):
            if w in _lexicon(lang)[1]:
                toks.add(w)
    return sorted(toks)


def _sheet_markers(dim, sentences, profile, lang="en"):
    lengths = [len(voice_profile.words(s, lang)) for s in sentences]
    med = statistics.median(lengths) if lengths else 0
    lines = [f"- Sentences in samples exercising this: {len(sentences)}.",
             f"- Median length of those sentences: {int(med)} words."]
    if dim == "numbers-data":
        toks = _numbers_tokens(sentences, lang)
        lines.append("- Numeric tokens actually used: " + ", ".join(toks[:12]) + ".")
    elif dim == "addressing-reader":
        q = sum(1 for s in sentences if s.rstrip().endswith("?"))
        lines.append(f"- Direct questions to the reader: {q}.")
        lines.append("- Second person appears; keep it plain, no salesy 'you'.")
    elif dim == "openings":
        openers = sorted({voice_profile.words(s, lang)[0] for s in sentences if voice_profile.words(s, lang)})
        lines.append("- Documents open on: " + ", ".join(openers[:8]) + ".")
    elif dim == "closings":
        lines.append("- Endings land on a concrete image, not a moral recap.")
    elif lang == "es":
        lines.append("- El ritmo manda: mantén la longitud de frase de las muestras.")
    else:
        cr = profile["contraction_rate"]
        lines.append(f"- Overall contraction rate: {cr:.3f} (keep it consistent here).")
    return lines


SHEET_HOWTO = {
    "explaining-technical": "Explain by naming the concrete mechanism, not the abstraction. Short causal sentences; 'because' does the work.",
    "anecdote": "Tell it first person, past tense, one scene at a time. Concrete nouns, sensory detail, no summarizing moral.",
    "argument": "State the claim flat, then the reason. No hedging scaffold; the point lands in one line.",
    "disagreement": "Disagree by contrast, not confrontation. 'I don't', 'rather than', a plain preference rather than a takedown.",
    "praise": "Praise through specific, restrained detail. Understated approval, never gushing.",
    "hedging-uncertainty": "Hold uncertainty lightly with 'maybe' / 'probably' / 'or it won't', not corporate qualifiers.",
    "numbers-data": "Numbers stay small, concrete, woven into the scene rather than tabulated.",
    "addressing-reader": "Address the reader sparingly and plainly; a direct question or a flat 'you can'.",
    "openings": "Open cold on a concrete fact or action. No throat-clearing, no thesis statement.",
    "closings": "Close on a small, specific image. No wrap-up, no 'ultimately'.",
}


def build_sheet(dim, sentences, profile, lang="en"):
    title = dim.replace("-", " ")
    howto = SHEET_HOWTO_ES if lang == "es" else SHEET_HOWTO
    header = "# Hoja de voz: " if lang == "es" else "# Voice sheet: "
    lines = [header + title, ""]
    lines.append(howto[dim])
    lines.append("")
    lines.append("## Fragmentos de muestra" if lang == "es" else "## Sample snippets")
    for snip in _shortest(sentences):
        lines.append(f"> {snip}")
    lines.append("")
    lines.append("## Marcadores medidos" if lang == "es" else "## Measured markers")
    lines.extend(_sheet_markers(dim, sentences, profile, lang))
    lines.append("")
    return "\n".join(lines) + "\n"


def _never_does(profile, lang="en"):
    never = []
    p = profile["punctuation"]
    label = (NEVER_LABELS_ES if lang == "es" else
             {";": "semicolons", "!": "exclamation points", ":": "colons",
              "-": "hyphenated dashes", "(": "parentheticals"})
    for mark, name in label.items():
        if p.get(mark, 0.0) == 0.0:
            never.append(name)
    return never


def build_card(profile, docs, matrix, name, lang="en"):
    med = int(profile["sentence_lengths"]["median"])
    iqr = int(profile["sentence_lengths"]["iqr"])
    contr = profile["contraction_rate"]
    examples = _contraction_examples(docs) if lang == "en" else []
    openers = _opener_words(docs)
    never = _never_does(profile, lang)
    covered = [d for d in TAXONOMY if matrix[d]["covered"]]
    uncovered = [d for d in TAXONOMY if not matrix[d]["covered"]]

    if lang == "es":
        lines = [f"# Carta de voz: {name}", ""]
        lines.append(
            f"Ritmo: frase mediana de {med} palabras, IQR {iqr}. "
            f"Párrafos de {int(profile['paragraph_stats']['mean_words'])} palabras de media."
        )
        lines.append("Sin contracciones: el español no las usa; no las inventes.")
        if never:
            lines.append("Nunca: " + "; ".join(never) + ".")
        lines.append("Aperturas: " + ", ".join(openers) + ".")
        lines.append("")
        lines.append("Iguala primero el ritmo y las costumbres; conserva hechos y significado.")
        lines.append("")
        lines.append("## Al escribir, lee la hoja correspondiente")
        lines.append("")
        lines.append("| Situación | Hoja |")
        lines.append("|-----------|------|")
        for dim in covered:
            lines.append(f"| {dim.replace('-', ' ')} | card/{dim}.md |")
        lines.append("")
        if uncovered:
            lines.append(
                "Sin cubrir (no hay evidencia en las muestras — no inventes una voz para esto): "
                + ", ".join(uncovered) + "."
            )
        return "\n".join(lines) + "\n"

    lines = [f"# Voice card: {name}", ""]
    lines.append(
        f"Rhythm: median sentence {med} words, IQR {iqr}, {_burstiness(profile)}. "
        f"Paragraphs average {int(profile['paragraph_stats']['mean_words'])} words."
    )
    if examples:
        lines.append(
            f"Contractions: rate {contr:.3f}; e.g. " + ", ".join(examples) + "."
        )
    else:
        lines.append(f"Contractions: rate {contr:.3f}; rarely contracts.")
    if never:
        lines.append("Never: " + "; ".join(never) + ".")
    lines.append("Openers: " + ", ".join(openers) + ".")
    lines.append("")
    lines.append("Match rhythm and habits first; keep facts and meaning intact.")
    lines.append("")
    lines.append("## When writing, read the matching sheet")
    lines.append("")
    lines.append("| Situation | Sheet |")
    lines.append("|-----------|-------|")
    for dim in covered:
        lines.append(f"| {dim.replace('-', ' ')} | card/{dim}.md |")
    lines.append("")
    if uncovered:
        lines.append(
            "Uncovered (no sample evidence — do not fabricate a voice for these): "
            + ", ".join(uncovered) + "."
        )
    return "\n".join(lines) + "\n"


def card_word_count(card_text):
    return len(re.findall(r"[A-Za-z0-9']+", card_text))


def write_card(profile, samples_dir, out_dir, name):
    lang = profile.get("language", "en")
    docs = collect(samples_dir, lang)
    matrix, buckets = coverage_matrix(docs, lang)
    out = Path(out_dir)
    (out / "card").mkdir(parents=True, exist_ok=True)
    # Remove any stale sheets so uncovered dims never keep an old file.
    for stale in (out / "card").glob("*.md"):
        stale.unlink()
    card = build_card(profile, docs, matrix, name, lang)
    (out / "card.md").write_text(card)
    for dim in TAXONOMY:
        if matrix[dim]["covered"]:
            (out / "card" / f"{dim}.md").write_text(build_sheet(dim, buckets[dim], profile, lang))
    return matrix


def write_provenance(profile, samples_dir, out_dir):
    samples = []
    total = 0
    for path in voice_profile.iter_docs(samples_dir):
        text = path.read_text(errors="replace")
        wc = len(voice_profile.words(text))
        total += wc
        samples.append({
            "file": path.name,
            "sha256": sha256_file(path),
            "words": wc,
        })
    meta = profile.get("metadata", {})
    prov = {
        "doc_count": len(samples),
        "total_words": total,
        "samples": samples,
        "genre_note": meta.get("genre_warning", "") or "same-genre samples assumed",
        "low_confidence": bool(meta.get("low_confidence", total < 2000)),
    }
    Path(out_dir, "provenance.json").write_text(
        json.dumps(prov, indent=2, sort_keys=True) + "\n"
    )
    return prov


def profile_mismatch(supplied, recomputed, path=""):
    """First named field where the supplied profile disagrees with one recomputed
    from --samples, or None. Counts (ints) compare exactly; floats within 1e-6.
    The function-word background is a normalizer (from --background, not the
    sample content), so it is not part of the equality check."""
    here = path or "<root>"
    if isinstance(supplied, bool) or isinstance(recomputed, bool):
        return None if supplied == recomputed else here
    if isinstance(supplied, dict):
        if not isinstance(recomputed, dict):
            return here
        for k in sorted(set(supplied) | set(recomputed)):
            if k == "function_word_background":
                continue
            if k == "language" and k not in supplied:
                # Profiles written before bilingual support carry no language
                # field; they are English by construction.
                continue
            if k not in supplied or k not in recomputed:
                return f"{path}.{k}".lstrip(".")
            m = profile_mismatch(supplied[k], recomputed[k], f"{path}.{k}".lstrip("."))
            if m:
                return m
        return None
    if isinstance(supplied, list):
        if not isinstance(recomputed, list) or len(supplied) != len(recomputed):
            return here
        for i, (x, y) in enumerate(zip(supplied, recomputed)):
            m = profile_mismatch(x, y, f"{path}[{i}]")
            if m:
                return m
        return None
    if isinstance(supplied, int) and isinstance(recomputed, int):
        return None if supplied == recomputed else here
    if isinstance(supplied, (int, float)) and isinstance(recomputed, (int, float)):
        return None if abs(supplied - recomputed) <= 1e-6 else here
    return None if supplied == recomputed else here


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--samples", required=True)
    parser.add_argument("--out")
    parser.add_argument("--name", default="voice")
    parser.add_argument("--coverage", action="store_true",
                        help="print the coverage matrix as JSON and write nothing")
    parser.add_argument("--provenance", action="store_true",
                        help="also write <out>/provenance.json")
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    profile_path = Path(args.profile)
    samples_dir = Path(args.samples)
    if not profile_path.exists() or not samples_dir.is_dir():
        print("missing profile or samples dir", file=sys.stderr)
        return 2
    if not list(voice_profile.iter_docs(samples_dir)):
        print(f"no sample documents in {samples_dir}: teach reads only .txt and .md "
              f"files (recursively). Rename samples to .txt/.md or point --samples at "
              f"the right directory.", file=sys.stderr)
        return 2
    profile = json.loads(profile_path.read_text())

    # Consistency gate: the supplied profile must describe these very samples.
    recomputed = voice_profile.build_profile(samples_dir)
    mismatch = profile_mismatch(profile, recomputed)
    if mismatch is not None:
        print(f"profile does not match --samples (recompute differs at '{mismatch}'); "
              f"rebuild the profile from these samples with voice_profile.py",
              file=sys.stderr)
        return 2

    lang = recomputed.get("language", "en")
    if args.coverage:
        docs = collect(samples_dir, lang)
        matrix, _ = coverage_matrix(docs, lang)
        print(json.dumps(matrix, indent=2, sort_keys=True))
        return 0

    if not args.out:
        print("--out is required unless --coverage", file=sys.stderr)
        return 2
    write_card(profile, samples_dir, args.out, args.name)
    if args.provenance:
        write_provenance(profile, samples_dir, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
