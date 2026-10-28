# Analysis

Working notes for the blog post. Inspired by the EMNLP 2025 keynote on natural
languages, redone for programming languages. Method and definitions: [METHOD.md](METHOD.md).

**Data:** developer counts from the GitHub Innovation Graph (2026 Q1); Hugging Face tags
fetched on 2026-10-27. Covers 259 programming languages.

**Reading the shares:** a model tagged with two languages counts once for each. There
are 3,550 distinct language-tagged models but 4,965 model–language pairs. The %
figures below are shares of the pairs. Developer shares work the same way: 26.1M
developer–language pairs.

## 1. Code AI is highly concentrated

Figure: `figures/zipf.png`

| | Models | Datasets |
|---|---|---|
| Repos with a programming-language tag | 3,550 | 2,033 |
| Repos with the generic `code` tag (for scale) | 14,805 | 4,770 |
| Languages with ≥1 repo / with none | 100 / 159 | 101 / 158 |
| Python's share | 22.8% | 22.5% |
| Top-10 languages' share | 73.6% | 74.2% |
| Power-law fit, rank vs. count (slope, R²) | −2.06, 0.96 | −1.72, 0.98 |

- **Python** is the "English" of code AI. It ranks #1 for both models (1,132) and
  datasets (570).
- **SQL** is a close #2: 912 models and 405 datasets, driven by text-to-SQL.
- Concentration is extreme but no worse than the developer population itself.
  - JavaScript alone is 21.7% of developers, and the top 10 languages are 74.8%.
  - Gini coefficient: 0.94 for models, 0.93 for datasets, 0.93 for developers.
  - What differs is *which* languages get the resources (section 2).
- **Rank 74: Perl.** 138k developers, 1 model, 2 datasets. Of the 27 languages with
  100k+ developers, Perl has the fewest models per developer among those that have
  any models at all.

## 2. Developer population explains less than half of it

Figures: `figures/developers_vs_models.png`, `figures/developers_vs_datasets.png`

- Developer count explains **46%** of the variation in models per language and **33%**
  for datasets. This is the R² of a log-log OLS fit over languages with ≥1 repo.
  The talk reported ~30% for natural languages.
- A 10× larger developer base predicts only ~2.9× more models (fit slope 0.46) and
  ~2.1× more datasets (slope 0.33).

**Most for their size** (furthest above the fit):

| Language | Developers | Models | Datasets | Why |
|---|---|---|---|---|
| Lean | 4,432 | 235 | 211 | AI for formal maths / theorem proving |
| SQL | 375,726 | 912 | 405 | text-to-SQL; 1.4% of developers, 18.4% of models |
| Dafny | 122 | 13 | 16 | verified code generation |
| Verilog | 28,539 | 137 | 63 | hardware / RTL generation |
| Cypher | 2,393 | 43 | 27 | text-to-graph-query |
| Solidity | 53,061 | 112 | 66 | smart contracts |

The pattern: languages that are the target of a well-defined AI *task* (proving,
querying, chip design, contracts) attract many more models than their user base predicts.

**Many developers, few models.** Popular languages that fall well short:

| Language | Developers | Models | Datasets | Share of devs → share of models |
|---|---|---|---|---|
| JavaScript | 5,662,372 | 314 | 133 | 21.7% → 6.3% |
| TypeScript | 2,787,317 | 179 | 100 | 10.7% → 3.6% |
| Kotlin | 433,614 | 32 | 7 | 1.7% → 0.6% |
| Swift | 377,812 | 37 | 8 | 1.4% → 0.7% |
| Objective-C | 276,290 | 0 | 2 | 1.1% → 0% |
| Dart | 209,669 | 9 | 8 | 0.8% → 0.2% |
| Perl | 138,488 | 1 | 2 | 0.5% → 0.0% |

- **Developers per model:** SQL 412, Rust 1.5k, Python 3.6k, Go 3.7k, Java 6.4k,
  Ruby 11k, Kotlin 14k, TypeScript 16k, JavaScript 18k.
- **Mobile is notably under-served:** Kotlin, Swift, Objective-C and Dart.
- **Formal cut** (≥10k developers and ≥10× fewer models than the fit predicts): 32
  languages for models, 26 for datasets.
  - Biggest by developers: Batchfile (628k, 0 models), Objective-C, Perl, Mako, HLSL,
    ShaderLab.
  - Most of the rest are scripting, template, shader or editor languages: Vim Script,
    Emacs Lisp, Groovy, Tcl, Awk, sed, and others.

**Legacy languages** (the analogue of Latin and Ancient Greek):

- Some have more models than their small user base predicts:
  - COBOL: 4,232 developers, 19 models
  - Smalltalk: 8,825 developers, 18 models
  - Ada: 3,949 developers, 10 models
  - ABAP: 998 developers, 10 models
  - Fortran: 54,374 developers, 10 models (around the fit, not above it)
- COBOL and ABAP are enterprise and mainframe languages with a code-migration market.
- Most other legacy languages have nothing: Visual Basic 6.0, VBA, BASIC, Modula-2/3,
  Eiffel, REXX, ActionScript and CoffeeScript all have 0 models.

## 3. Caveats to state in the post

- **These are dedicated models only.** The counts cover models and datasets tagged with
  a specific language. Big general code models (StarCoder, Qwen-Coder, …) are usually
  tagged just `code`, so they aren't counted for any language even when they support
  it. The analysis measures *language-specific* resources, not capability.
- **Tag noise was significant and was cleaned (METHOD.md §3):**
  - `rust` mostly means "has Rust-format weights", not "writes Rust".
  - `swift` is a model family.
  - `ts`, `be` and `hy` are human-language codes on multilingual models.
  - Raw tag matches overstated many languages by 5× or more: Rust 1,186 → 210 models,
    Lua 348 → 16.
- **Languages left out:** a few could not be measured at all, because their names mean
  something else on the Hub (CUDA, Metal, WebAssembly, Apex, …).
- **Developer counts:**
  - They are a lower bound for small languages, since country/language pairs with
    <100 developers are not published.
  - They rely on GitHub's language detection. Hack was dropped because it is confused
    with PHP. Batchfile's 628k likely reflects incidental `.bat` files in repos rather
    than primary use.
- **SQL** combines several dialects, which slightly overstates its developer count.
