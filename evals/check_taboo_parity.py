#!/usr/bin/env python3
"""Check that scanner dictionary phrases are documented in the taboo catalogs."""

import sys

from _check_support import ROOT  # noqa: E402

sys.path.insert(0, str(ROOT))

from scripts.banned_phrase_scan import BANNED_PHRASES, BANNED_PHRASES_ES  # noqa: E402


CATALOG = (ROOT / "references" / "taboo-phrases.md").read_text().lower()
CATALOG_ES = (ROOT / "references" / "taboo-phrases-es.md").read_text().lower()

DOCUMENTED_FAMILIES = {
    "period.": "period\\.",
    "full stop.": "full stop\\.",
    "garnered significant attention": "garnered significant/considerable attention",
    "garnered considerable attention": "garnered significant/considerable attention",
    "let's dive in": "let's dive in",
    "let's unpack": "let's unpack",
    "tells a clear story": "the data tells a (clear) story",
}


def _missing(phrases: dict, catalog: str) -> list[str]:
    return [
        phrase
        for phrase in sorted(phrases)
        if DOCUMENTED_FAMILIES.get(phrase, phrase).lower() not in catalog
    ]


def main() -> int:
    failures = []
    for language, phrases, catalog, path in (
        ("en", BANNED_PHRASES, CATALOG, "references/taboo-phrases.md"),
        ("es", BANNED_PHRASES_ES, CATALOG_ES, "references/taboo-phrases-es.md"),
    ):
        missing = _missing(phrases, catalog)
        if missing:
            failures.append((language, path, missing))

    if failures:
        print("Missing taboo catalog entries:")
        for language, path, missing in failures:
            print(f"[{language}] {path} is missing {len(missing)} entries:")
            for phrase in missing:
                print(f"  - {phrase}")
        return 1

    print(
        f"taboo parity ok: {len(BANNED_PHRASES)} English and "
        f"{len(BANNED_PHRASES_ES)} Spanish banned phrase keys documented"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
