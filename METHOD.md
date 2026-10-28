# Method

How every number and figure in this repo is produced. The code is in `src/`, and all
hand-curated lists and pinned sources are in `src/config.py`. The analysis and figure
designs follow Anna Korhonen's EMNLP 2025 keynote, "AI for the Many: Starting from the
World, Not the Model"; where this method makes its own choices, they are described below.

```bash
pip install -r requirements.txt
python src/build_languages.py   # 1. language table + developer counts
python src/fetch_hf.py          # 2–3. Hugging Face counts (from the committed snapshot)
python src/plots.py             # 4–5. statistics + figures
```

Every output rebuilds byte-for-byte from the committed files. See
[Reproducibility](#reproducibility) below.

## 1. Languages and developer counts — `build_languages.py` → `data/languages.csv`

**Sources** (both pinned to a fixed commit in `src/config.py`):
- [GitHub Innovation Graph](https://github.com/github/innovationgraph) `data/languages.csv`.
  Each row is `num_pushers` (unique developers who pushed code in that language) for one
  economy, language and quarter.
- [GitHub Linguist](https://github.com/github-linguist/linguist) `lib/linguist/languages.yml`,
  for language types and aliases.

**Steps:**
1. Take the pinned quarter, **2026 Q1** (`PERIOD`).
2. **Developers** = `num_pushers` summed over all economies.
   - The Innovation Graph only publishes economy/language pairs with ≥100 developers,
     so this is a lower bound, and languages below that threshold everywhere (e.g. Coq)
     are absent.
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

Each language gets a set of candidate tags, all lowercase:

- **Included:** the language name, its slug (spaces → `-`), its Linguist aliases, and
  hand-added extras (`EXTRA_TAGS`).
  - The extras are **only other spellings or versions of the language's own name**:
    `golang` → Go, `cpp` → C++, `csharp` → C#, `lean4` → Lean, `bash` → Shell, and
    SQL dialect or engine names (`t-sql`, `mysql`, `postgresql`, `sqlite`) → SQL.
  - **Task tags are deliberately not used** (`text-to-sql`, `nl2sql`, `nl2bash`, `rtl`,
    `smart-contracts`, …). Only a few languages have such tags, so including them
    would favour exactly those languages.
- **Removed:** aliases that almost always mean something else (`DROPPED_TAGS`): `m2`
  (Apple M2 chip), `mps` (Apple's GPU backend for PyTorch), `be` (Belarusian), `al`,
  `dcl` and `inc`.
- **Marked ambiguous** if any of these is true:
  - it is in the hand list `AMBIGUOUS`: common words, runtimes and other names like
    `go`, `rust`, `swift`, `julia`, `ruby`, `cuda`, `delphi`, `coffee`, `smpl`, `mumps`;
  - it is an ISO 639-1 or ISO 639-3 natural-language code, such as `lua`, `ada`, `nim`
    or `ts` (taken from `pycountry`);
  - it is two characters or shorter.

## 3. Hugging Face counts — `fetch_hf.py` → `data/hf_counts.csv`

**Fetching** (only with `--refresh`, or when there is no snapshot):
- For every tag, list all models and all datasets from the Hub API:
  `GET https://huggingface.co/api/{models|datasets}?filter=<tag>&limit=1000`, following
  `Link: rel=next` pages.
- Tag filters are case-sensitive, so each tag is queried as written, Capitalised, and in
  the language's own spelling (e.g. `python`, `Python`; `javascript`, `Javascript`,
  `JavaScript`). Results are merged by repo id.
- Fetched on **2026-10-28**. The id, tags, downloads and likes of every listed repo are
  saved in `data/hf_snapshot.json.gz`, and all counts are computed from that file.

**A repo counts for a language** if, after lowercasing its tags:

0. It is **not a converted copy** of another model. A repo is skipped if it has the
   Hub's `base_model:quantized:` marker or a converted weight-format tag (`gguf`,
   `mlx`, `awq`, `gptq`, `exl2`). The format tags are needed because many re-uploads
   don't declare the marker. This counts each model once, in its original format. It
   also drops the few fine-tunes published *only* as GGUF/MLX.
1. It carries one of the language's **unambiguous** tags. → counts.
2. Otherwise, all of its matched tags are natural-language codes **and** it lists more
   than one other natural language besides English (models tag them as `ts`, datasets
   as `language:ts`; both are recognised). → doesn't count, because it is a
   multilingual model listing e.g. Tsonga (`ts`) or Luba-Lulua (`lua`).
3. Otherwise, it also carries a **code tag** (`CODE_TAGS`: `code`, `language:code`,
   `code-generation`, `text-to-code`, `program-synthesis`, `coder`, `starcoder`, …)
   **or** another language's unambiguous tag. → counts.

**Outputs:**
- `data/hf_counts.csv`, per language:
  - `models` and `datasets`: counts after the rules above (**main counts**)
  - `*_dedicated`: the same, restricted to repos that count for ≤3 programming
    languages (a sensitivity check; see §4)
  - `*_raw`: any-tag-match counts before filtering
  - summed `*_downloads` and `*_likes`
- `data/hf_summary.json`:
  - distinct repos matched to any language (2,000 models, 1,883 datasets)
  - converted copies removed (1,927 models, 4 datasets)
  - repos counting for >3 languages (67 models, 56 datasets)
  - repos tagged `code` (14,837 / 4,785)

**Validation:**
- `tests/test_counting.py` checks each rule on made-up repos.
- I compared raw and filtered counts, and inspected samples of the matched repos for
  every high-count tag and every tag with a low share of code-tagged repos. The
  `AMBIGUOUS`, `DROPPED_TAGS` and `UNMEASURABLE` lists came out of that review.
- After the final rules, I hand-checked 10 random counted models each for Rust, Go,
  C, Swift, PowerShell, HCL, SQL and Lean.

## 4. Statistics — `plots.py` → `data/stats.json`, `data/residuals_*.csv`

Computed separately for models and for datasets ("count" below):

- **Shares:** count ÷ sum of counts over all languages. This is a share of
  language–repo pairs, because one repo can carry several languages. Developer shares
  are computed the same way.
- **Zipf fit:**
  - Rank languages with count ≥ 1 by count, breaking ties alphabetically.
  - OLS fit of log₁₀(count) on log₁₀(rank), leaving out rank 1 (as the talk does for
    English).
  - Ranks quoted in the text are competition ranks: tied languages share the best rank
    (e.g. "joint 64th").
- **Developer fit:** OLS fit of log₁₀(count) on log₁₀(developers) over languages with
  count ≥ 1. The reported R² is this fit's.
- **Residual:** log₁₀(count) − log₁₀(predicted), with zero counts set to 0.5. A residual
  of −1 means 10× fewer repos than the fit predicts.
- **Robustness** (`stats.json` → `robustness`):
  - the developer fit over **all** 259 languages, with zero counts set to 0.5;
  - Spearman rank correlation of developers and count over all languages;
  - the developer fit on the `*_dedicated` counts (general code models that tag more
    than 3 languages left out).
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
  developers next to the share of models and of datasets. Each share is out of the
  total over all 259 languages.

## Reproducibility

- Python packages are pinned in `requirements.txt`.
- The Innovation Graph and Linguist files are read from fixed commits, and the quarter
  is fixed (`src/config.py`).
- The Hub can't be pinned to a date, so its metadata is committed as
  `data/hf_snapshot.json.gz`.
  - `python src/fetch_hf.py` rebuilds every count from it, with no network access.
  - `python src/fetch_hf.py --refresh` fetches fresh data and overwrites the snapshot.
  - During a refresh, each tag's listing is cached in `data/raw/hf/<date>/`
    (git-ignored), so an interrupted fetch resumes the same day.
- All sorting breaks ties by name, so rebuilding gives byte-identical CSVs and JSON.
