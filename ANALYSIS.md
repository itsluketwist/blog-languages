# Analysis

Working notes for the blog post. This redoes, for programming languages, the analysis
of natural languages in Anna Korhonen's EMNLP 2026 keynote, "AI for the Many: Starting
from the World, Not the Model". The questions, figure designs and groupings all come
from that talk (see the README for details). Method and definitions: [METHOD.md](METHOD.md).

**Data:** developer counts from the GitHub Innovation Graph (2026 Q1); Hugging Face tags
fetched on 2026-10-28 (snapshot committed). Covers 259 programming languages. Quantised
and converted re-uploads (GGUF, MLX, …) are removed, so each model counts once.

**Reading the shares:** a model tagged with two languages counts once for each. There
are 2,000 distinct language-tagged models but 2,582 model–language pairs. The %
figures below are shares of the pairs. Developer shares work the same way: 26.1M
developer–language pairs.

## 1. Code AI is highly concentrated

Figure: `figures/zipf.png`

| | Models | Datasets |
|---|---|---|
| Repos with a programming-language tag | 2,000 | 1,883 |
| Repos with the generic `code` tag (for scale) | 14,837 | 4,785 |
| Languages with ≥1 repo / with none | 91 / 168 | 102 / 157 |
| Python's share | 28.4% | 24.1% |
| Top-10 languages' share | 74.7% | 73.3% |
| Power-law fit, rank vs. count (slope, R²) | −1.84, 0.96 | −1.70, 0.97 |

- **Python** is the "English" of code AI. It ranks #1 for both models (734) and
  datasets (573).
- **SQL** is #2: 354 models and 256 datasets, from the `sql` tag and dialect names alone.
- Concentration is extreme, but no worse than the developer population itself.
  - JavaScript alone is 21.7% of developers, and the top 10 languages are 74.8%.
  - Gini coefficient: 0.94 for models, 0.93 for datasets, 0.93 for developers.
  - What differs is *which* languages get the resources (section 2).
- **Perl is joint 64th.** It has 138k developers, 1 model and 2 datasets. Of the 27
  languages with 100k+ developers, Perl has the fewest models per developer among
  those that have any models at all.

## 2. Developer population explains less than half of it

Figures: `figures/developers_vs_models.png`, `figures/developers_vs_datasets.png`

- Developer count explains **43%** of the variation in models per language and **34%**
  for datasets.
  - This is the R² of a log-log OLS fit over languages with ≥1 repo (91 for models,
    102 for datasets).
  - Fitting all 259 languages (zero counts set to 0.5) gives 37% and 32%.
  - The Spearman rank correlation over all languages is 0.48 for models and 0.43 for
    datasets.
  - For comparison, Korhonen's keynote (slide 12, "Does speaker population size explain
    model availability?") reports that speaker population explains only ~30% of the
    variation in *model* availability for natural languages. Its plot has no zero row,
    so like ours the fit appears to cover only languages with ≥1 model. Developer
    count explains somewhat more for programming languages (43%), but still less than
    half.
- A 10× larger developer base predicts only ~2.5× more models (fit slope 0.40) and
  ~2.1× more datasets (slope 0.33).

**Most for their size** (furthest above the model fit):

| Language | Developers | Models | Datasets | Why |
|---|---|---|---|---|
| Lean | 4,432 | 171 | 214 | AI for formal maths / theorem proving |
| SQL | 375,726 | 354 | 256 | text-to-SQL; 1.4% of developers, 13.7% of models |
| Python | 4,109,495 | 734 | 573 | the default language of code AI |
| Verilog | 28,539 | 92 | 61 | hardware / RTL generation |
| Cypher | 2,393 | 28 | 28 | text-to-graph-query |
| Solidity | 53,061 | 62 | 46 | smart contracts |

The pattern: languages that are the target of a well-defined AI *task* (proving,
querying, chip design, contracts) attract many more models than their user base
predicts. This holds when matching only on language names: no task tags such as
`text-to-sql` are used.

**Many developers, few models.** Popular languages that fall well short:

| Language | Developers | Models | Datasets | Share of devs → share of models |
|---|---|---|---|---|
| JavaScript | 5,662,372 | 137 | 133 | 21.7% → 5.3% |
| TypeScript | 2,787,317 | 98 | 100 | 10.7% → 3.8% |
| Kotlin | 433,614 | 6 | 7 | 1.7% → 0.2% |
| Swift | 377,812 | 6 | 8 | 1.4% → 0.2% |
| Objective-C | 276,290 | 0 | 2 | 1.1% → 0% |
| Dart | 209,669 | 7 | 8 | 0.8% → 0.3% |
| Perl | 138,488 | 1 | 2 | 0.5% → 0.0% |

- **Developers per model:**

  | SQL | Rust | Python | Go | Java | Ruby | TypeScript | JavaScript | Swift | Kotlin |
  |---|---|---|---|---|---|---|---|---|---|
  | 1.1k | 2.9k | 5.6k | 7.0k | 12k | 19k | 28k | 41k | 63k | 72k |

- **Mobile is notably under-served:** Kotlin, Swift, Objective-C and Dart have 19
  models between them.
- **Formal cut** (≥10k developers and ≥10× fewer models than the fit predicts): 30
  languages for models, 26 for datasets.
  - Biggest by developers: Batchfile (628k, 0 models), Objective-C, Perl, Mako, HLSL,
    GLSL.
  - Most of the rest are scripting, template, shader or editor languages: Vim Script,
    Emacs Lisp, Groovy, Tcl, Awk, sed, and others.

**Legacy languages** (the analogue of Latin and Ancient Greek):

- Some have more models than their small user base predicts:
  - Smalltalk: 8,825 developers, 18 models
  - COBOL: 4,232 developers, 14 models
  - Ada: 3,949 developers, 7 models
  - ABAP: 998 developers, 5 models
  - Fortran: 54,374 developers, 7 models (around the fit, not above it)
- COBOL and ABAP are enterprise and mainframe languages with a code-migration market.
- Most other legacy languages have nothing. Visual Basic 6.0, VBA, BASIC, Modula-2/3,
  Eiffel, REXX, RPGLE, ActionScript and CoffeeScript all have 0 models.

## 3. Caveats to state in the post

- **Counts are of language-tagged models.** Big general code models (StarCoder,
  Qwen-Coder, …) are usually tagged just `code`, so they aren't counted for any
  language even when they support it. The analysis measures *language-specific*
  resources, not capability.
- **Some general models tag many languages, and count for each.**
  - 67 models tag more than 3 programming languages.
  - The biggest effect is from Valiant Labs' Esper family, a DevOps assistant tagged
    with `powershell`, `terraform`, `python`, `javascript`, `shell` and more. Without
    such multi-language models, PowerShell falls from 36 models to 9 and HCL from 33
    to 9.
  - The fit without them (`*_dedicated` counts) gives R² 0.37 for models; the headline
    findings don't change.
- **Each model counts once.** 1,927 quantised or converted re-uploads (GGUF, MLX, AWQ,
  …) were removed. Fine-tunes published only in those formats are dropped too.
- **No task tags.** Matching uses language names, aliases and spellings only, so a
  text-to-SQL model tagged `text-to-sql` but not `sql` isn't counted. If anything this
  undercounts the task-driven languages, so their lead is conservative.
- **Tag noise was significant and was cleaned (METHOD.md §3):**
  - `rust` mostly means "has Rust-format weights", not "writes Rust".
  - `swift` is a model family.
  - `ts`, `be` and `hy` are human-language codes on multilingual models.
  - Raw tag matches overstate many languages by 10× or more: Rust 1,190 → 108 models,
    Lua 349 → 9.
- **Languages left out:** a few could not be measured at all, because their names mean
  something else on the Hub (CUDA, Metal, WebAssembly, Apex, …).
- **Developer counts:**
  - They are a lower bound for small languages, since country/language pairs with
    <100 developers are not published. Languages below that everywhere, such as Coq,
    are missing entirely.
  - They rely on GitHub's language detection. Hack was dropped because it is confused
    with PHP. Batchfile's 628k likely reflects incidental `.bat` files in repos rather
    than primary use.
- **SQL** combines several dialects, which slightly overstates its developer count.
