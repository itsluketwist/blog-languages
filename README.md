# blog-languages

How well are programming languages served by open AI models and datasets, relative to
how many people write them? A programming-language version of the EMNLP 2025 keynote
analysis of natural languages on Hugging Face.

## Data

| What | Source | Notes |
|---|---|---|
| Developers per language (the "speakers") | [GitHub Innovation Graph](https://github.com/github/innovationgraph) `languages.csv` | Unique developers pushing code in each language in the latest quarter, summed over economies. Only economy/language pairs with ≥100 developers are published, so small languages are undercounted. |
| Language names and aliases | [GitHub Linguist](https://github.com/github-linguist/linguist) `languages.yml` | Only `type: programming`; build/config formats (Dockerfile, Makefile, …) are dropped and SQL dialects are folded into one "SQL" row. |
| Models and datasets per language | Hugging Face Hub API | A repo counts for a language when it has a tag matching the language's name or an alias. Ambiguous tags (`go`, `r`, `julia`, natural-language codes such as `lua` or `ts`) only count alongside a code tag. |

## Running it

```bash
pip install -r requirements.txt
cd src
python build_languages.py   # -> data/languages.csv
python fetch_hf.py          # -> data/hf_counts.csv, data/hf_summary.json (set HF_TOKEN for higher rate limits)
python plots.py             # -> figures/*.png, data/stats.json, data/residuals_*.csv
```

`build_languages.py` takes `--innovation-graph` and `--linguist` to read local copies
instead of downloading. `fetch_hf.py` caches each tag's API listing in `data/raw/hf/`.

## Figures

- `figures/zipf.png`: rank vs. number of models / datasets per language (log-log)
- `figures/developers_vs_models.png`, `figures/developers_vs_datasets.png`: developers vs. models, with an OLS fit and highlighted groups
- `figures/share.png`: share of developers vs. share of models for the most-used languages
