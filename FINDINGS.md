# Findings

Data: GitHub Innovation Graph developer counts for 2026 Q1, and Hugging Face Hub tags
fetched on 2026-10-27. Covers 259 programming languages and 26.1M developer-language
pairs. A developer who writes two languages counts once for each.

## Code AI is highly concentrated (`figures/zipf.png`)

- Only **3,550 models** and **2,033 datasets** on the Hub are tagged with a specific
  programming language. For comparison, 14,805 models and 4,770 datasets carry the
  generic `code` tag.
- **Python** is the "English" of code AI: 22.8% of language-tagged models and 22.5% of
  datasets. The top 10 languages hold 74% of models and datasets.
- Only 100 of 259 languages have any models at all; 159 have none. The ranked counts
  follow a power law closely (slope −2.06 for models, −1.72 for datasets; R² 0.96 and 0.98).
- **Rank 74: Perl.** 138k active developers, 1 model and 2 datasets.

## Does developer population explain availability? (`figures/developers_vs_*.png`)

- Developer count explains only **~46%** of the variation in models per language and
  **~33%** for datasets (OLS on log-log, languages with at least one model or dataset).
- **Most for their size:**
  - **SQL**: 1.4% of developers, 18.4% of models (text-to-SQL).
  - **Lean**: 4.4k developers, 235 models and 211 datasets (AI for formal maths).
  - **Verilog**, **Solidity**, **Cypher** and **Dafny**: hardware, smart contracts,
    graph queries and verification.
- **Many developers, few models:**
  - **JavaScript**: 21.7% of developers but 6.3% of models.
  - **TypeScript**: 10.7% of developers, 3.6% of models.
  - **Kotlin**: 434k developers, 32 models.
  - **Swift**: 378k developers, 37 models.
  - **Dart**: 210k developers, 9 models.
  - **Objective-C**: 276k developers, 0 models.
  - **Perl**: 138k developers, 1 model.
  - **Batchfile**: 628k developers, 0 models.
- **Legacy languages** (the "Latin" of code): **COBOL** (4k developers, 19 models),
  **Smalltalk** (18) and **Fortran** (10) punch above their weight. **Pascal**,
  **Forth** and BASIC-family languages have almost nothing.

## Caveats

- **Tag-based counting** misses models that support a language without tagging it.
  Most big general code models (StarCoder, Qwen-Coder, …) are tagged `code`, not
  per language. These numbers measure *dedicated* language-specific resources.
- **Noisy tags were cleaned up:**
  - Ambiguous tags (`go`, `r`, `rust`, `swift`, `julia`, …) only count next to a
    code tag. On the Hub, `rust` mostly means "has Rust-format weights", and `swift`
    is a model family.
  - Tags that are also human-language codes (`ts`, `lua`, `hy`, …) don't count on
    multilingual models.
  - Languages whose names mostly mean something else on the Hub (CUDA, Metal,
    WebAssembly, Apex, …) are excluded.
- **Developer counts:**
  - Small languages are undercounted, because the Innovation Graph only publishes
    country/language pairs with at least 100 developers.
  - Hack is excluded, because GitHub's language detection confuses it with PHP.
  - SQL dialects are summed into one SQL entry.
