"""Build the language table: one row per programming language, with its developer count and hub tags.

"Developers" comes from the GitHub Innovation Graph: the number of unique developers
who pushed code in each language during the pinned quarter (config.PERIOD), summed
over economies. The Innovation Graph only publishes economy/language pairs with at
least 100 developers, so counts for small languages are lower bounds.

Usage:
    python src/build_languages.py [--innovation-graph PATH] [--linguist PATH]
"""

import argparse
import io

import pandas as pd
import pycountry
import requests
import yaml

from config import (
    AMBIGUOUS,
    DATA,
    DROPPED_TAGS,
    EXCLUDED,
    EXTRA_TAGS,
    INNOVATION_GRAPH_URL,
    LEGACY,
    LINGUIST_URL,
    PERIOD,
    SQL_DIALECTS,
    UNMEASURABLE,
)


def read_text(
    path_or_url: str,
) -> str:
    """
    Read a text file from a local path or a url.

    Returns the file's contents.
    """
    if path_or_url.startswith("http"):
        response = requests.get(
            path_or_url,
            timeout=120,
        )
        response.raise_for_status()
        return response.text
    with open(path_or_url, encoding="utf-8") as f:
        return f.read()


def load_developers(
    path_or_url: str,
) -> tuple[pd.DataFrame, str]:
    """
    Sum unique pushers per language over all economies, for the pinned quarter.

    Returns the per-language table and the period label (e.g. "2026Q1").
    """
    # keep_default_na=False stops pandas reading namibia's code "NA" as missing
    df = pd.read_csv(
        io.StringIO(read_text(path_or_url)),
        keep_default_na=False,
    )
    year, quarter = PERIOD
    latest = df[(df.year == year) & (df.quarter == quarter)]
    if latest.empty:
        raise ValueError(f"no innovation graph rows for {year}Q{quarter}")

    devs = (
        latest.groupby("language")
        .agg(
            developers=("num_pushers", "sum"),
            economies=("iso2_code", "nunique"),
            language_type=("language_type", "first"),
        )
        .reset_index()
    )
    return devs, f"{year}Q{quarter}"


def natural_language_codes() -> set[str]:
    """
    Collect iso 639 codes, which hugging face also uses as (natural) language tags.

    Returns the set of lowercase two- and three-letter codes.
    """
    codes = set()
    for lang in pycountry.languages:
        for attr in ("alpha_2", "alpha_3"):
            if hasattr(lang, attr):
                codes.add(getattr(lang, attr).lower())
    return codes


def slug(
    name: str,
) -> str:
    """
    Turn a language name into a hub-style tag.

    Returns the lowercase name with spaces replaced by dashes.
    """
    return name.lower().replace(" ", "-")


def hf_tags(
    name: str,
    aliases: list[str],
) -> list[str]:
    """
    List the hub tags that can refer to a language: its name, slug, aliases and extras.

    Returns the sorted tags, without any in DROPPED_TAGS.
    """
    tags = {name.lower(), slug(name), *(a.lower() for a in aliases)}
    tags.update(EXTRA_TAGS.get(name, []))
    return sorted(t for t in tags if t and t not in DROPPED_TAGS)


def main() -> None:
    """Build data/languages.csv from the innovation graph and linguist."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--innovation-graph", default=INNOVATION_GRAPH_URL)
    parser.add_argument("--linguist", default=LINGUIST_URL)
    args = parser.parse_args()

    linguist = yaml.safe_load(read_text(args.linguist))
    devs, period = load_developers(args.innovation_graph)

    # keep programming languages (plus the sql dialects), drop build/config formats
    # and languages that hub tags can't measure
    keep = devs[
        ((devs.language_type == "programming") | devs.language.isin(SQL_DIALECTS))
        & ~devs.language.isin(EXCLUDED | UNMEASURABLE)
    ].copy()

    # fold sql dialects into one "SQL" row. someone writing two dialects is
    # counted twice, so this slightly overstates sql
    is_sql = keep.language.isin(SQL_DIALECTS)
    sql_row = pd.DataFrame(
        [
            {
                "language": "SQL",
                "developers": keep[is_sql].developers.sum(),
                "economies": keep[is_sql].economies.max(),
                "language_type": "programming",
            },
        ],
    )
    keep = pd.concat([keep[~is_sql], sql_row], ignore_index=True)

    iso_codes = natural_language_codes()
    rows = []
    for _, row in keep.iterrows():
        meta = linguist.get(row.language, {})
        aliases = list(meta.get("aliases", []) or [])
        # the sql row also answers to every dialect's name and aliases
        if row.language == "SQL":
            for dialect in sorted(SQL_DIALECTS):
                aliases += [dialect.lower()]
                aliases += linguist.get(dialect, {}).get("aliases") or []
        tags = hf_tags(row.language, aliases)
        # a tag is ambiguous if it is hand-listed, a natural-language code, or very short
        ambiguous = sorted(
            t for t in tags if t in AMBIGUOUS or t in iso_codes or len(t) <= 2
        )
        rows.append(
            {
                "language": row.language,
                "developers": int(row.developers),
                "economies": int(row.economies),
                "legacy": row.language in LEGACY,
                "hf_tags": "|".join(tags),
                "ambiguous_tags": "|".join(ambiguous),
            },
        )

    # sort by developers, breaking ties by name so the file is always identical
    out = pd.DataFrame(rows).sort_values(
        ["developers", "language"],
        ascending=[False, True],
    )
    out.insert(1, "period", period)
    DATA.mkdir(exist_ok=True)
    out.to_csv(DATA / "languages.csv", index=False)
    print(f"Wrote {len(out)} languages for {period} to {DATA / 'languages.csv'}")


if __name__ == "__main__":
    main()
