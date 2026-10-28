# blog-languages

<div>
    <!-- badges from : https://shields.io/ -->
    <!-- logos available : https://simpleicons.org/ -->
    <a href="https://lukastwist.com/blog/language-attention/">
        <img alt="Blog post" src="https://img.shields.io/badge/Blog-Read_the_post-6250d6?style=for-the-badge&logo=rss&logoColor=white" />
    </a>
    <a href="https://www.python.org/">
        <img alt="Python 3" src="https://img.shields.io/badge/Python_3-blue?style=for-the-badge&logo=python&logoColor=white" />
    </a>
    <a href="https://github.com/github/innovationgraph">
        <img alt="GitHub Innovation Graph" src="https://img.shields.io/badge/GitHub-222222?style=for-the-badge&logo=github&logoColor=white" />
    </a>
    <a href="https://huggingface.co">
        <img alt="Hugging Face" src="https://img.shields.io/badge/Hugging_Face-FFCC00?style=for-the-badge&logo=huggingface&logoColor=black" />
    </a>
    <a href="https://creativecommons.org/licenses/by/4.0/">
        <img alt="CC-BY-4.0 License" src="https://img.shields.io/badge/Licence-CC_BY_4.0-yellow?style=for-the-badge&logo=docs&logoColor=white" />
    </a>
</div>

How well are programming languages served by open AI models and datasets, relative to
how many people write them? A programming-language version of Anna Korhonen's EMNLP
2026 keynote analysis of natural languages on Hugging Face.

## Inspiration and credit

This project is directly inspired by, and closely follows, the analysis in
**Anna Korhonen's keynote at EMNLP 2026, "AI for the Many: Starting from the World,
Not the Model"** (Keynote 3, 27 October 2026). The talk examined the global AI divide through the lens
of language, showing how unevenly AI models and datasets are spread across the world's
languages.

The analysis design here is hers, applied to programming languages instead of natural
ones:
- the "highly concentrated" Zipf plot of models and datasets per language, fitted
  without the top-ranked language, with a "Rank N" callout for a large but
  under-served language;
- the speakers-vs-models scatter with an OLS fit, and its "explains only ~X% of the
  variation" headline;
- the colour groups (top 5 per speaker bin, under-resourced, dead/legacy languages) and
  the side panel of takeaways.

Developers stand in for speakers, and GitHub's language data for language censuses.
Any errors in this adaptation are mine.

## Data

| What | Source | Notes |
|---|---|---|
| Developers per language (the "speakers") | [GitHub Innovation Graph](https://github.com/github/innovationgraph) `languages.csv` | Unique developers pushing code in each language in 2026 Q1, summed over economies. Only economy/language pairs with ≥100 developers are published, so small languages are undercounted. |
| Language names and aliases | [GitHub Linguist](https://github.com/github-linguist/linguist) `languages.yml` | Only `type: programming`; build/config formats (Dockerfile, Makefile, …) are dropped and SQL dialects are folded into one "SQL" row. |
| Models and datasets per language | Hugging Face Hub API | A repo counts for a language when it has a tag matching the language's name, an alias or another spelling (no task tags such as `text-to-sql`). Quantised/converted re-uploads (GGUF, MLX, …) are skipped, so each model counts once. Ambiguous tags (`go`, `r`, `rust`, `julia`, natural-language codes such as `lua` or `ts`) only count alongside a code tag, and natural-language-code tags don't count on multilingual models. Languages whose names mostly mean something else on the Hub (CUDA, Metal, WebAssembly, …) are left out; see `src/config.py`. |

## Running it

```bash
pip install -r requirements.txt
python src/build_languages.py   # -> data/languages.csv
python src/fetch_hf.py          # -> data/hf_counts.csv, data/hf_summary.json
python src/plots.py             # -> figures/*.png, data/stats.json, data/residuals_*.csv
pytest tests                    # checks the counting rules
```

The outputs rebuild exactly from the committed files:
- the sources and quarter are pinned in `src/config.py`;
- `fetch_hf.py` counts from the committed Hub snapshot `data/hf_snapshot.json.gz`.

Run `python src/fetch_hf.py --refresh` to fetch fresh Hub data and overwrite the
snapshot (set `HF_TOKEN` for higher rate limits). `build_languages.py` takes
`--innovation-graph` and `--linguist` to read local copies instead of downloading.

## Results

- [ANALYSIS.md](ANALYSIS.md): findings, numbers and caveats for the blog post
- [METHOD.md](METHOD.md): exactly how the data and figures are produced

## Figures

- `figures/zipf.png`: rank vs. number of models / datasets per language (log-log)
- `figures/developers_vs_models.png`, `figures/developers_vs_datasets.png`: developers vs. models, with an OLS fit and highlighted groups
- `figures/share.png`: share of developers vs. share of models and datasets for the most-used languages

## Licence

Everything in this repository (code, figures, data and write-ups) is licensed under
[Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE). Reuse it freely,
with credit to Luke Twist and this repository.

- **Third-party sources:**
  - Developer counts come from the [GitHub Innovation Graph](https://github.com/github/innovationgraph)
    (CC0 1.0).
  - Language names and aliases come from [GitHub Linguist](https://github.com/github-linguist/linguist)
    (MIT).
  - `data/hf_snapshot.json.gz` holds public metadata (repo ids, tags, download and
    like counts) from the [Hugging Face Hub](https://huggingface.co) API; the
    repositories themselves belong to their owners.
