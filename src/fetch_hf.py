"""Count Hugging Face models and datasets per programming language.

A model/dataset counts for a language when one of its Hub tags is the language's
name or an alias (see data/languages.csv). Tags that are ambiguous on their own
("go", "r", "julia", "ruby", natural-language codes like "lua" or "ts", ...) only
count when the repo is also tagged as being about code, or carries another,
unambiguous programming-language tag. Tags that are also natural-language codes
additionally don't count on repos tagged with several other natural languages
(multilingual models list "ts" for Tsonga, "be" for Belarusian, ...).

Each tag's raw API listing is cached under data/raw/hf/ so the script can be
re-run (or resumed after a rate limit) cheaply. Set HF_TOKEN for higher limits.

Usage:
    python src/fetch_hf.py           # fetch (uses cache) + aggregate
    python src/fetch_hf.py --refresh # ignore the cache
"""

import argparse
import json
import os
import time
from collections import defaultdict

import pandas as pd
import requests

from build_languages import natural_language_codes
from config import CODE_TAGS, DATA

API = "https://huggingface.co/api"
RAW = DATA / "raw" / "hf"
FIELDS = ("id", "tags", "downloads", "likes", "createdAt")

session = requests.Session()
if token := os.environ.get("HF_TOKEN"):
    session.headers["Authorization"] = f"Bearer {token}"


def get(url: str, params: dict | None = None) -> requests.Response:
    for attempt in range(8):
        response = session.get(url, params=params, timeout=60)
        if response.status_code == 429 or response.status_code >= 500:
            wait = int(response.headers.get("Retry-After", 2 ** attempt * 5))
            print(f"  {response.status_code}, retrying in {wait}s")
            time.sleep(wait)
            continue
        response.raise_for_status()
        return response
    response.raise_for_status()
    return response


def list_repos(kind: str, tag: str) -> list[dict]:
    """Every model or dataset carrying exactly this tag."""
    items, url, params = [], f"{API}/{kind}", {"filter": tag, "limit": 1000}
    while url:
        response = get(url, params)
        items += [{k: item.get(k) for k in FIELDS} for item in response.json()]
        url, params = response.links.get("next", {}).get("url"), None
    return items


def fetch_tag(kind: str, tag: str, refresh: bool, spellings: tuple[str, ...] = ()) -> list[dict]:
    path = RAW / kind / f"{tag.replace('/', '_')}.json"
    if path.exists() and not refresh:
        return json.loads(path.read_text())
    items = {}
    # Hub tags are case-sensitive, so also ask for e.g. "Python" and "JavaScript".
    for variant in dict.fromkeys([tag, tag.capitalize(), *spellings]):
        for item in list_repos(kind, variant):
            items[item["id"]] = item
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(list(items.values())))
    return list(items.values())


def count(kind: str, languages: pd.DataFrame, refresh: bool) -> tuple[pd.DataFrame, dict]:
    tags_of = {r.language: r.hf_tags.split("|") for r in languages.itertuples()}
    ambiguous_of = {
        r.language: set(r.ambiguous_tags.split("|")) if isinstance(r.ambiguous_tags, str) else set()
        for r in languages.itertuples()
    }
    unambiguous = {t for lang, tags in tags_of.items() for t in tags if t not in ambiguous_of[lang]}
    iso_codes = natural_language_codes()

    repos: dict[str, dict] = {}
    hits = defaultdict(set)  # language -> repo ids
    all_tags = sorted({t for tags in tags_of.values() for t in tags})
    spellings = defaultdict(list)
    for lang in tags_of:
        spellings[lang.lower()].append(lang)
    for i, tag in enumerate(all_tags, 1):
        items = fetch_tag(kind, tag, refresh, tuple(spellings[tag]))
        print(f"[{kind} {i}/{len(all_tags)}] {tag}: {len(items)}")
        for item in items:
            repos[item["id"]] = item
            for lang, tags in tags_of.items():
                if tag in tags:
                    hits[lang].add(item["id"])

    rows, counted = [], {}
    for lang, tags in tags_of.items():
        ids, ids_raw = set(), hits[lang]
        for repo_id in ids_raw:
            repo_tags = {t.lower() for t in repos[repo_id]["tags"] or []}
            matched = repo_tags & set(tags)
            if matched - ambiguous_of[lang]:
                ids.add(repo_id)
                continue
            other_natural = (repo_tags - matched) & iso_codes - {"en"}
            if matched <= iso_codes and len(other_natural) > 1:
                continue
            if repo_tags & CODE_TAGS or (repo_tags - matched) & unambiguous:
                ids.add(repo_id)
        counted[lang] = ids
        rows.append({
            "language": lang,
            f"{kind}": len(ids),
            f"{kind}_raw": len(ids_raw),
            f"{kind}_downloads": sum(repos[r]["downloads"] or 0 for r in ids),
            f"{kind}_likes": sum(repos[r]["likes"] or 0 for r in ids),
        })

    # Context numbers for the write-up: how big is the "code" corner of the Hub?
    summary = {
        f"{kind}_tagged_code": len(fetch_tag(kind, "code", refresh)),
        f"{kind}_with_any_language": len(set().union(*counted.values())),
    }
    print(summary)
    return pd.DataFrame(rows), summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    languages = pd.read_csv(DATA / "languages.csv")
    models, models_summary = count("models", languages, args.refresh)
    datasets, datasets_summary = count("datasets", languages, args.refresh)
    out = languages[["language", "developers", "legacy"]].merge(models).merge(datasets)
    out.to_csv(DATA / "hf_counts.csv", index=False)
    summary = {"fetched": time.strftime("%Y-%m-%d"), **models_summary, **datasets_summary}
    (DATA / "hf_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"Wrote {DATA / 'hf_counts.csv'}")


if __name__ == "__main__":
    main()
