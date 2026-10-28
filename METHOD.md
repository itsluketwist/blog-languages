# Method

How every number and figure in this repo is produced. The code is in `src/`, and all
hand-curated lists are in `src/config.py`.

```bash
pip install -r requirements.txt
python src/build_languages.py   # 1. language table + developer counts
python src/fetch_hf.py          # 2–3. Hugging Face counts
python src/plots.py             # 4–5. statistics + figures
```

## 1. Languages and developer counts — `build_languages.py` → `data/languages.csv`

**Sources:**
- [GitHub Innovation Graph](https://github.com/github/innovationgraph) `data/languages.csv`.
  Each row is `num_pushers` (unique developers who pushed code in that language) for one
  economy, language and quarter.
- [GitHub Linguist](https://github.com/github-linguist/linguist) `lib/linguist/languages.yml`,
  for language types and aliases.

**Steps:**
1. Take the latest quarter, **2026 Q1**.
2. **Developers** = `num_pushers` summed over all economies.
   - The Innovation Graph only publishes economy/language pairs with ≥100 developers,
     so this is a lower bound.
3. Keep languages with `language_type == programming`, plus the SQL dialects.
4. Fold SQL, PLpgSQL, TSQL, PLSQL, SQLPL and HiveQL into one **SQL** row by summing.
   A developer who writes two dialects is counted twice.
5. Remove three groups:
   - **Build/config formats:** Dockerfile, Makefile, CMake, Procfile, Meson, QMake, M4,
     Inno Setup, NSIS, BitBake, GDB, and others (`EXCLUDED`).
   - **Hack:** it shares the `.php` extension with PHP, which inflates its count
     implausibly (112k developers in 96 economies).
   - **Languages that tags can't measure** (`UNMEASURABLE`), because their names mostly
     mean something else on the Hub: CUDA, Metal, WebAssembly, Apex, Arc, Reason, Hy,
     Io, Berry, FLUX, and single-letter or common-word names (E, J, M, V, q, Red, Max,
     Turing, Move, …).
6. Flag 20 **legacy** languages by hand: COBOL, Fortran, Pascal, Ada, Smalltalk, BASIC,
   Visual Basic 6.0, VBA, Modula-2, Modula-3, REXX, RPGLE, Forth, Classic ASP,
   ActionScript, Eiffel, ABAP, Common Lisp, Prolog and CoffeeScript.

Result: **259 languages**.

## 2. Hub tags per language

Each language gets a set of candidate tags (461 distinct tags overall), all lowercase:

- **Included:** the language name, its slug (spaces → `-`), its Linguist aliases, and
  hand-added extras (`EXTRA_TAGS`).
  - Examples of extras: `text-to-sql`, `text2sql` and `nl2sql` → SQL; `golang` → Go;
    `lean4` → Lean; `smart-contracts` → Solidity; `nl2bash` → Shell.
- **Removed:** aliases that almost always mean something else (`DROPPED_TAGS`): `m2`
  (Apple M2 chip), `mps` (Apple's GPU backend for PyTorch), `be` (Belarusian), `al`,
  `dcl` and `inc`.
- **Marked ambiguous** (146 tags) if any of these is true:
  - it is in the hand list `AMBIGUOUS`: common words, runtimes and other names like
    `go`, `rust`, `swift`, `julia`, `ruby`, `cuda`, `delphi`, `coffee`, `smpl`, `mumps`;
  - it is an ISO 639-1 or ISO 639-3 natural-language code, such as `lua`, `ada`, `nim`
    or `ts` (taken from `pycountry`);
  - it is two characters or shorter.

## 3. Hugging Face counts — `fetch_hf.py` → `data/hf_counts.csv`

**Fetching:**
- For every tag, list all models and all datasets from the Hub API:
  `GET https://huggingface.co/api/{models|datasets}?filter=<tag>&limit=1000`, following
  `Link: rel=next` pages.
- Tag filters are case-sensitive, so each tag is queried as written, Capitalised, and in
  the language's own spelling (e.g. `python`, `Python`; `javascript`, `Javascript`,
  `JavaScript`). Results are merged by repo id.
- Fetched on **2026-10-27**. Each tag's listing is cached in `data/raw/hf/` (git-ignored).

**A repo counts for a language** if, after lowercasing its tags, any of these holds:

1. It carries one of the language's **unambiguous** tags. → counts.
2. Otherwise, all of its matched tags are natural-language codes **and** it has more
   than one other natural-language tag besides `en`. → doesn't count, because it is a
   multilingual model listing e.g. Tsonga (`ts`) or Luba-Lulua (`lua`).
3. Otherwise, it also carries a **code tag** (`CODE_TAGS`: `code`, `code-generation`,
   `text-to-code`, `program-synthesis`, `coder`, `starcoder`, …) **or** another
   language's unambiguous tag. → counts.

**Outputs:**
- `data/hf_counts.csv`, per language:
  - `models` and `datasets`: counts after filtering
  - `*_raw`: any-tag-match counts before filtering
  - summed `*_downloads` and `*_likes`
- `data/hf_summary.json`: distinct repos matched to any language (3,550 models, 2,033
  datasets) and repos tagged `code` (14,805 / 4,770).

**Validation:** I compared raw and filtered counts and inspected samples of the matched
repos for every high-count tag and every tag with a low share of code-tagged repos. The
`AMBIGUOUS`, `DROPPED_TAGS` and `UNMEASURABLE` lists came out of that review.

## 4. Statistics — `plots.py` → `data/stats.json`, `data/residuals_*.csv`

Computed separately for models and for datasets ("count" below):

- **Shares:** count ÷ sum of counts over all languages. This is a share of
  language–repo pairs, because one repo can carry several languages. Developer shares
  are computed the same way.
- **Zipf fit:**
  - Rank languages with count ≥ 1 by count. Ties are in arbitrary order.
  - OLS fit of log₁₀(count) on log₁₀(rank), leaving out rank 1 (as the talk does for
    English).
- **Developer fit:** OLS fit of log₁₀(count) on log₁₀(developers) over languages with
  count ≥ 1. The reported R² is this fit's.
- **Residual:** log₁₀(count) − log₁₀(predicted), with zero counts set to 0.5. A residual
  of −1 means 10× fewer repos than the fit predicts.
- **Groups** used for colour, in order of precedence:
  - **legacy**: the hand-flagged list from step 1;
  - **under-resourced**: ≥10k developers and residual ≤ −1;
  - **top**: the 5 languages with the most repos in each developer decade bin
    (10²–10³, 10³–10⁴, …);
  - **other**: everything else.
- **Gini:** computed over all 259 languages, including zeros.

## 5. Figures — `plots.py` → `figures/`

- **`zipf.png`:** rank vs. count, log-log, for models (left) and datasets (right), with
  the Zipf fit dashed and the top 8 labelled.
  - The callout is the language with the most developers per model among those with
    ≥100k developers and ≥1 model (Perl).
- **`developers_vs_models.png`** and **`developers_vs_datasets.png`:** developers (x)
  vs. count (y), log-log, with the developer fit line.
  - Languages with zero repos are drawn on a separate "0" row.
  - Colours follow the groups above.
  - The side panel lists the top 4 residuals, the 6 largest under-resourced languages,
    and the 3 legacy languages with the most repos.
- **`share.png`:** for the 15 languages with the most developers, the share of
  developers next to the share of models.
