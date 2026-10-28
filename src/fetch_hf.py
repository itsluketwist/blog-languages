"""Count Hugging Face models and datasets per programming language.

A model/dataset counts for a language when one of its hub tags is the language's
name, an alias or another spelling (see data/languages.csv). Tags that are ambiguous
on their own ("go", "r", "julia", "ruby", natural-language codes like "lua" or "ts",
...) only count when the repo is also tagged as being about code, or carries another,
unambiguous programming-language tag. Tags that are also natural-language codes
additionally don't count on repos tagged with several other natural languages
(multilingual models list "ts" for Tsonga, "lua" for Luba-Lulua, ...). Quantised or
converted re-uploads of another model (gguf, mlx, ...) are left out, so each model
is counted once.

The fetched hub metadata is saved to data/hf_snapshot.json.gz, and by default the
counts are rebuilt from that snapshot, so the results reproduce exactly. Pass
--refresh to fetch fresh data from the hub (and overwrite the snapshot). During a
fetch, each tag's listing is cached under data/raw/hf/<date>/ so an interrupted run
can be resumed the same day. Set HF_TOKEN for higher rate limits.

Usage:
    python src/fetch_hf.py            # rebuild counts from the committed snapshot
    python src/fetch_hf.py --refresh  # fetch fresh data from the hub
"""

import argparse
import gzip
import json
import os
import time
from collections import Counter

import pandas as pd
import requests

from build_languages import natural_language_codes
from config import CODE_TAGS, DATA, DEDICATED_MAX_LANGUAGES

API = "https://huggingface.co/api"
RAW = DATA / "raw" / "hf"
SNAPSHOT = DATA / "hf_snapshot.json.gz"
KINDS = ("models", "datasets")
FIELDS = ("tags", "downloads", "likes", "createdAt")

# a repo is a converted copy of another model (not a new model) if it has the hub's
# own "quantized" marker, or is in a quantised/converted weight format. the format
# tags are needed because many re-uploads don't declare the marker
QUANTIZED_PREFIX = "base_model:quantized:"
CONVERTED_FORMATS = {"gguf", "mlx", "awq", "gptq", "exl2"}

session = requests.Session()
if token := os.environ.get("HF_TOKEN"):
    session.headers["Authorization"] = f"Bearer {token}"


def get(
    url: str,
    params: dict | None = None,
) -> requests.Response:
    """
    Get a hub api url, retrying with backoff on rate limits, server errors and dropped connections.

    Returns the successful response.
    """
    attempts = 8
    for attempt in range(attempts):
        wait = 2**attempt * 5
        try:
            response = session.get(
                url,
                params=params,
                timeout=60,
            )
        except (requests.ConnectionError, requests.Timeout) as error:
            # give up on the last attempt, otherwise wait and try again
            if attempt == attempts - 1:
                raise
            print(f"  {type(error).__name__}, retrying in {wait}s")
            time.sleep(wait)
            continue
        if response.status_code == 429 or response.status_code >= 500:
            wait = int(response.headers.get("Retry-After", wait))
            print(f"  {response.status_code}, retrying in {wait}s")
            time.sleep(wait)
            continue
        response.raise_for_status()
        return response
    response.raise_for_status()
    return response


def list_repos(
    kind: str,
    tag: str,
) -> list[dict]:
    """
    List every model or dataset carrying exactly this tag, following pagination.

    Returns one dict per repo with its id and the FIELDS we keep.
    """
    items = []
    url = f"{API}/{kind}"
    params = {"filter": tag, "limit": 1000}
    while url:
        response = get(url, params)
        items += [
            {"id": item["id"], **{k: item.get(k) for k in FIELDS}}
            for item in response.json()
        ]
        # the next page's url already contains the query, so params are dropped
        url = response.links.get("next", {}).get("url")
        params = None
    return items


def fetch_tag(
    kind: str,
    tag: str,
    cache_dir: str,
    spellings: tuple[str, ...] = (),
) -> list[dict]:
    """
    Fetch every repo with this tag, in all its case variants, using the day's cache.

    Returns the merged list of repos (one entry per repo id).
    """
    path = RAW / cache_dir / kind / f"{tag.replace('/', '_')}.json"
    if path.exists():
        return json.loads(path.read_text())

    # hub tags are case-sensitive, so also ask for e.g. "Python" and "JavaScript"
    items = {}
    for variant in dict.fromkeys([tag, tag.capitalize(), *spellings]):
        for item in list_repos(kind, variant):
            items[item["id"]] = item
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(list(items.values())))
    return list(items.values())


def fetch_snapshot(
    languages: pd.DataFrame,
) -> dict:
    """
    Fetch the listing of every language tag, for models and datasets, from the hub.

    Returns the snapshot: the fetch date, each tag's repo ids per kind, each repo's
    metadata per kind, and the number of repos tagged "code" per kind.
    """
    fetched = time.strftime("%Y-%m-%d")
    tags_of = {r.language: r.hf_tags.split("|") for r in languages.itertuples()}
    all_tags = sorted({t for tags in tags_of.values() for t in tags})

    # the language's own spelling is also queried, e.g. "JavaScript" for "javascript"
    spellings: dict[str, list[str]] = {}
    for lang in tags_of:
        spellings.setdefault(lang.lower(), []).append(lang)

    snapshot = {"fetched": fetched, "listings": {}, "repos": {}, "tagged_code": {}}
    for kind in KINDS:
        listings, repos = {}, {}
        for i, tag in enumerate(all_tags, 1):
            items = fetch_tag(kind, tag, fetched, tuple(spellings.get(tag, [])))
            print(f"[{kind} {i}/{len(all_tags)}] {tag}: {len(items)}")
            listings[tag] = sorted(item["id"] for item in items)
            for item in items:
                repos[item["id"]] = {k: item[k] for k in FIELDS}
        snapshot["listings"][kind] = listings
        snapshot["repos"][kind] = repos
        # context number for the write-up: how big is the "code" corner of the hub?
        snapshot["tagged_code"][kind] = len(fetch_tag(kind, "code", fetched))
    return snapshot


def count(
    kind: str,
    languages: pd.DataFrame,
    listings: dict[str, list[str]],
    repos: dict[str, dict],
) -> tuple[pd.DataFrame, dict]:
    """
    Apply the counting rules to one kind (models or datasets) of the snapshot.

    Returns a per-language table of counts, downloads and likes, and summary numbers.
    """
    tags_of = {r.language: r.hf_tags.split("|") for r in languages.itertuples()}
    ambiguous_of = {
        r.language: set(r.ambiguous_tags.split("|"))
        if isinstance(r.ambiguous_tags, str)
        else set()
        for r in languages.itertuples()
    }
    # every tag that names a programming language on its own
    unambiguous = {
        t for lang, tags in tags_of.items() for t in tags if t not in ambiguous_of[lang]
    }
    iso_codes = natural_language_codes()

    def is_converted(repo_id: str) -> bool:
        tags = {t.lower() for t in repos[repo_id]["tags"] or []}
        return bool(tags & CONVERTED_FORMATS) or any(
            t.startswith(QUANTIZED_PREFIX) for t in tags
        )

    counted: dict[str, set[str]] = {}
    raw_hits: dict[str, set[str]] = {}
    for lang, lang_tags in tags_of.items():
        # every repo carrying any of the language's tags, before any filtering
        raw_hits[lang] = {
            repo_id for tag in lang_tags for repo_id in listings.get(tag, [])
        }
        ids = set()
        for repo_id in raw_hits[lang]:
            # rule 0: a quantised/converted copy of another model isn't a new model
            if is_converted(repo_id):
                continue
            repo_tags = {t.lower() for t in repos[repo_id]["tags"] or []}
            matched = repo_tags & set(lang_tags)

            # rule 1: an unambiguous language tag always counts
            if matched - ambiguous_of[lang]:
                ids.add(repo_id)
                continue

            # rule 2: a natural-language code on a multilingual repo means the human
            # language. models tag languages as "ts", datasets as "language:ts"
            other_natural = (
                ({t.removeprefix("language:") for t in repo_tags - matched} & iso_codes)
                - matched
                - {"en"}
            )
            if matched <= iso_codes and len(other_natural) > 1:
                continue

            # rule 3: an ambiguous tag counts alongside a code tag or another
            # language's unambiguous tag
            if repo_tags & CODE_TAGS or (repo_tags - matched) & unambiguous:
                ids.add(repo_id)
        counted[lang] = ids

    # how many languages each repo counts for, to separate dedicated from general models
    languages_per_repo = Counter(r for ids in counted.values() for r in ids)

    rows = []
    for lang, ids in counted.items():
        rows.append(
            {
                "language": lang,
                f"{kind}": len(ids),
                f"{kind}_raw": len(raw_hits[lang]),
                f"{kind}_dedicated": sum(
                    languages_per_repo[r] <= DEDICATED_MAX_LANGUAGES for r in ids
                ),
                f"{kind}_downloads": sum(repos[r]["downloads"] or 0 for r in ids),
                f"{kind}_likes": sum(repos[r]["likes"] or 0 for r in ids),
            },
        )

    all_raw = set().union(*raw_hits.values())
    summary = {
        f"{kind}_tagged_code": None,  # filled in from the snapshot by the caller
        f"{kind}_with_any_language": len(languages_per_repo),
        f"{kind}_converted_removed": sum(is_converted(r) for r in all_raw),
        f"{kind}_general_over_{DEDICATED_MAX_LANGUAGES}_languages": sum(
            n > DEDICATED_MAX_LANGUAGES for n in languages_per_repo.values()
        ),
    }
    return pd.DataFrame(rows), summary


def main() -> None:
    """Write data/hf_counts.csv and data/hf_summary.json, from the snapshot or the hub."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    languages = pd.read_csv(DATA / "languages.csv")

    # fetch from the hub only when asked to, or when there is no snapshot yet
    if args.refresh or not SNAPSHOT.exists():
        snapshot = fetch_snapshot(languages)
        with gzip.open(SNAPSHOT, "wt", encoding="utf-8") as f:
            json.dump(snapshot, f, sort_keys=True)
        print(f"Wrote {SNAPSHOT}")
    else:
        with gzip.open(SNAPSHOT, "rt", encoding="utf-8") as f:
            snapshot = json.load(f)
        print(f"Using snapshot fetched on {snapshot['fetched']}")

    out = languages[["language", "developers", "legacy"]]
    summary = {"fetched": snapshot["fetched"]}
    for kind in KINDS:
        table, kind_summary = count(
            kind,
            languages,
            snapshot["listings"][kind],
            snapshot["repos"][kind],
        )
        kind_summary[f"{kind}_tagged_code"] = snapshot["tagged_code"][kind]
        out = out.merge(table, on="language")
        summary.update(kind_summary)

    out.to_csv(DATA / "hf_counts.csv", index=False)
    (DATA / "hf_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {DATA / 'hf_counts.csv'}")


if __name__ == "__main__":
    main()
