#!/usr/bin/env python3
"""
Calculate readability metrics for transformed text.

Outputs:
- Flesch-Kincaid grade level
- Sentence length variance
- Word repetition score
- Paragraph length stats

Usage:
    python readability_metrics.py < input.txt
    python readability_metrics.py input.txt
"""

from __future__ import annotations

import argparse
import sys
import re
import json
from collections import Counter
from pathlib import Path
from typing import TypedDict

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from _lang import detect_language  # noqa: E402


class ReadabilityMetrics(TypedDict):
    language: str
    flesch_kincaid_grade: float | None
    flesch_reading_ease: float | None
    szigriszt_pazos: float | None
    sentence_count: int
    word_count: int
    avg_sentence_length: float
    sentence_length_variance: float
    min_sentence_length: int
    max_sentence_length: int
    consecutive_similar_length: int
    word_repetition_score: float
    top_repeated_words: list[tuple[str, int]]
    paragraph_count: int
    avg_paragraph_length: float
    flags: list[str]


def count_syllables(word: str) -> int:
    """Count syllables in a word (approximation)."""
    word = word.lower().strip()
    if not word:
        return 0

    # Handle special cases
    if len(word) <= 3:
        return 1

    # Count vowel groups
    vowels = "aeiouy"
    count = 0
    prev_is_vowel = False

    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_is_vowel:
            count += 1
        prev_is_vowel = is_vowel

    # Adjust for silent e
    if word.endswith('e') and count > 1:
        count -= 1

    # Adjust for -le endings
    if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
        count += 1

    return max(1, count)


def count_syllables_es(word: str) -> int:
    """Spanish syllable count.

    Much more regular than English: silent h disappears, and every vowel group
    is one syllable except at a hiatus (two strong vowels, or either vowel
    carrying the accent that breaks the diphthong).
    """
    letters = "".join(ch for ch in word.lower() if ch.isalpha() and ch != "h")
    vowels = "aeiouáéíóúü"
    strong = "aeoáéó"
    accented_weak = "íú"
    syllables = 0
    i = 0
    while i < len(letters):
        if letters[i] not in vowels:
            i += 1
            continue
        syllables += 1
        previous = letters[i]
        j = i + 1
        while j < len(letters) and letters[j] in vowels:
            current = letters[j]
            if (previous in strong and current in strong) or current in accented_weak or previous in accented_weak:
                syllables += 1
            previous = current
            j += 1
        i = j
    return max(1, syllables)


def split_sentences(text: str, lang: str = "en") -> list[str]:
    """Split text into sentences.

    The Spanish variant also accepts sentences that open on ¿ ¡ « or an
    accented capital, which the English pattern would miss.
    """
    if lang == "es":
        pattern = r'([.!?…]["”»]?)\s+(?=["“«¿¡]?[A-ZÁÉÍÓÚÑÜ])'
        closing = r'[.!?…]["”»]?$'
    else:
        pattern = r'([.!?]["”]?)\s+(?=["“]?[A-Z])'
        closing = r'[.!?]["”]?$'
    parts = re.split(pattern, text)
    sentences = []
    current = ""
    for part in parts:
        if re.match(closing, part):
            current += part
            sentences.append(current.strip())
            current = ""
        else:
            current += part
    if current.strip():
        sentences.append(current.strip())
    # Filter empty and clean up
    return [s.strip() for s in sentences if s.strip()]


def split_staccato_units(text: str) -> list[str]:
    units = re.split(r'\s*[—;]\s*|(?<=[.!?])\s+', text)
    return [u.strip() for u in units if u.strip()]


def split_words(text: str) -> list[str]:
    """Split text into words."""
    # Remove punctuation except hyphens in words. Numeric tokens are real words
    # (a data table is not "empty text"), so keep them.
    text = re.sub(r'[^\w\s-]', ' ', text)
    words = text.lower().split()
    return [w for w in words if w]


def calculate_metrics(text: str, lang: str | None = None) -> ReadabilityMetrics:
    """Calculate all readability metrics.

    The rhythm metrics (variance, runs, repetition, staccato) are
    language-neutral. The readability index is not: English gets
    Flesch-Kincaid, Spanish gets Szigriszt-Pazos (INFLESZ), and an unsupported
    language gets no index at all rather than a meaningless English one.
    """
    if lang is None:
        lang = detect_language(text)
    sentences = split_sentences(text, lang)
    words = split_words(text)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    if not sentences or not words:
        return {
            "language": lang,
            "flesch_kincaid_grade": None,
            "flesch_reading_ease": None,
            "szigriszt_pazos": None,
            "sentence_count": 0,
            "word_count": 0,
            "avg_sentence_length": 0,
            "sentence_length_variance": 0,
            "min_sentence_length": 0,
            "max_sentence_length": 0,
            "consecutive_similar_length": 0,
            "word_repetition_score": 0,
            "top_repeated_words": [],
            "paragraph_count": len(paragraphs),
            "avg_paragraph_length": 0,
            "flags": ["Empty or invalid text"]
        }

    # Basic counts
    sentence_count = len(sentences)
    word_count = len(words)
    syllable_counter = count_syllables_es if lang == "es" else count_syllables
    syllable_count = sum(syllable_counter(w) for w in words)

    # Sentence lengths
    sentence_lengths = [len(split_words(s)) for s in sentences]
    avg_sentence_length = word_count / sentence_count if sentence_count else 0

    # Variance calculation
    if len(sentence_lengths) > 1:
        mean = sum(sentence_lengths) / len(sentence_lengths)
        variance = sum((x - mean) ** 2 for x in sentence_lengths) / len(sentence_lengths)
    else:
        variance = 0

    # Consecutive similar length sentences
    consecutive_similar = 0
    max_consecutive = 0
    for i in range(1, len(sentence_lengths)):
        # "Similar" = within 3 words of each other
        if abs(sentence_lengths[i] - sentence_lengths[i-1]) <= 3:
            consecutive_similar += 1
            max_consecutive = max(max_consecutive, consecutive_similar)
        else:
            consecutive_similar = 0

    # Longest run of tiny (<=5-word) sentence-like units — the staccato "anti-slop" cadence.
    # Tracked independently of sentence_count so short de-slopped outputs don't slip.
    staccato_lengths = [len(split_words(s)) for s in split_staccato_units(text)]
    staccato_run = 0
    max_staccato_run = 0
    for length in staccato_lengths:
        if length <= 5:
            staccato_run += 1
            max_staccato_run = max(max_staccato_run, staccato_run)
        else:
            staccato_run = 0

    # Readability index. English: Flesch reading ease + Flesch-Kincaid grade.
    # Spanish: Szigriszt-Pazos (INFLESZ), 206.84 - 0.60*P - 1.02*F, with P =
    # syllables per 100 words and F = sentences per 100 words. Unsupported
    # languages get neither.
    avg_syllables_per_word = syllable_count / word_count if word_count else 0

    flesch_reading_ease = None
    flesch_kincaid_grade = None
    szigriszt_pazos = None
    if lang == "en":
        flesch_reading_ease = (
            206.835
            - (1.015 * avg_sentence_length)
            - (84.6 * avg_syllables_per_word)
        )
        flesch_kincaid_grade = (
            (0.39 * avg_sentence_length)
            + (11.8 * avg_syllables_per_word)
            - 15.59
        )
    elif lang == "es":
        szigriszt_pazos = (
            206.84
            - (0.60 * avg_syllables_per_word * 100)
            - (1.02 * (sentence_count / word_count * 100))
        )

    # Word repetition (excluding common words)
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
        'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how',
        'not', 'no', 'yes', 'if', 'then', 'else', 'so', 'as', 'than', 'just',
        'el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'que', 'y', 'o',
        'en', 'a', 'al', 'con', 'sin', 'por', 'para', 'sobre', 'entre', 'es',
        'son', 'se', 'su', 'sus', 'lo', 'le', 'les', 'me', 'te', 'nos', 'mi',
        'más', 'pero', 'como', 'cuando', 'si', 'no', 'ni', 'también', 'muy',
        'todo', 'todos', 'esta', 'este', 'estos', 'estas', 'ese', 'esa', 'ya',
        'tan', 'solo', 'siempre', 'nunca', 'ahora', 'antes', 'después', 'así',
        'aquí', 'allí', 'hay', 'ha', 'han', 'era', 'fue', 'ser', 'está'
    }

    content_words = [w for w in words if w not in stop_words and len(w) > 2]
    word_freq = Counter(content_words)

    # Repetition score: percentage of content words appearing 3+ times
    repeated_words = {w: c for w, c in word_freq.items() if c >= 3}
    repetition_score = (
        sum(repeated_words.values()) / len(content_words) * 100
        if content_words else 0
    )

    top_repeated = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

    # Paragraph stats
    para_lengths = [len(split_words(p)) for p in paragraphs]
    avg_para_length = sum(para_lengths) / len(para_lengths) if para_lengths else 0

    # Generate flags
    flags: list[str] = []

    if flesch_kincaid_grade is not None and flesch_kincaid_grade > 12:
        flags.append(f"High reading level ({flesch_kincaid_grade:.1f} grade)")

    # INFLESZ bands run from >80 (muy fácil) to <35 (muy difícil); flag only the
    # genuinely dense end so a normal Spanish op-ed stays advisory-free.
    if szigriszt_pazos is not None and szigriszt_pazos < 40:
        flags.append(f"Difficult reading level (INFLESZ {szigriszt_pazos:.1f})")

    if variance < 10 and sentence_count > 3:
        flags.append("Low sentence length variance (monotonous rhythm)")

    if max_consecutive >= 3:
        flags.append(f"{max_consecutive}+ consecutive similar-length sentences")

    if repetition_score > 15:
        flags.append(f"High word repetition ({repetition_score:.1f}%)")

    if avg_sentence_length > 25:
        flags.append(f"Long average sentence length ({avg_sentence_length:.1f} words)")

    if avg_sentence_length < 8 and sentence_count > 3:
        flags.append("Very short sentences (may feel choppy)")

    # Staccato cadence is the loudest "anti-slop AI" signature; flag it even on
    # short outputs (no sentence_count gate) so de-slopped text can't hide it.
    if max_staccato_run >= 3:
        flags.append(f"Staccato cadence: {max_staccato_run} consecutive tiny sentences (anti-slop AI tell)")
    elif avg_sentence_length < 6 and sentence_count >= 2:
        flags.append(f"Staccato cadence (avg {avg_sentence_length:.1f} words/sentence — anti-slop AI tell)")

    if max(sentence_lengths) - min(sentence_lengths) < 5 and sentence_count > 5:
        flags.append("Sentences all similar length (AI tell)")

    return {
        "language": lang,
        "flesch_kincaid_grade": (
            round(flesch_kincaid_grade, 1) if flesch_kincaid_grade is not None else None
        ),
        "flesch_reading_ease": (
            round(flesch_reading_ease, 1) if flesch_reading_ease is not None else None
        ),
        "szigriszt_pazos": (
            round(szigriszt_pazos, 1) if szigriszt_pazos is not None else None
        ),
        "sentence_count": sentence_count,
        "word_count": word_count,
        "avg_sentence_length": round(avg_sentence_length, 1),
        "sentence_length_variance": round(variance, 1),
        "min_sentence_length": min(sentence_lengths) if sentence_lengths else 0,
        "max_sentence_length": max(sentence_lengths) if sentence_lengths else 0,
        "consecutive_similar_length": max_consecutive,
        "word_repetition_score": round(repetition_score, 1),
        "top_repeated_words": top_repeated,
        "paragraph_count": len(paragraphs),
        "avg_paragraph_length": round(avg_para_length, 1),
        "flags": flags
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate readability metrics for transformed text."
    )
    parser.add_argument("path", nargs="?", help="Path to input text file (default: read stdin)")
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args(sys.argv[1:])

    # Read input
    if args.path:
        try:
            with open(args.path, 'r', errors="replace") as f:
                text = f.read()
        except OSError as e:
            print(json.dumps({"error": f"Could not read input: {e}"}))
            sys.exit(2)
    else:
        text = sys.stdin.buffer.read().decode("utf-8", errors="replace")

    if not text.strip():
        print(json.dumps({"error": "No input provided"}))
        sys.exit(1)

    metrics = calculate_metrics(text)
    print(json.dumps(metrics, indent=2))

    # Exit with 1 if any flags (warnings)
    sys.exit(1 if metrics["flags"] else 0)


if __name__ == "__main__":
    main()
