"""Check the hugging face counting rules in fetch_hf.count on small made-up repos."""

import sys
from pathlib import Path

import pandas as pd

# the analysis scripts live in src/ and import each other by plain module name
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fetch_hf import count  # noqa: E402

# a tiny language table in the same format as data/languages.csv
LANGUAGES = pd.DataFrame(
    [
        {"language": "Python", "hf_tags": "py|python", "ambiguous_tags": "py"},
        {"language": "Rust", "hf_tags": "rs|rust", "ambiguous_tags": "rs|rust"},
        {"language": "TypeScript", "hf_tags": "ts|typescript", "ambiguous_tags": "ts"},
        {"language": "Java", "hf_tags": "java", "ambiguous_tags": None},
        {"language": "Go", "hf_tags": "go|golang", "ambiguous_tags": "go"},
    ],
)

# made-up repos: id -> tags
REPOS = {
    "python-only": ["python"],
    "rust-weights": ["rust", "transformers"],  # "rust" meaning rust-format weights
    "rust-coder": ["rust", "code"],
    "rust-and-python": ["rust", "python"],
    "nllb-style": ["ts", "fr", "de", "en"],  # a translation model listing tsonga
    "dataset-multilingual": ["ts", "language:fr", "language:de"],
    "dataset-code": ["ts", "language:code"],
    "python-gguf": ["python", "base_model:quantized:org/python-only"],
    "python-mlx": ["python", "mlx"],  # a converted copy without the hub's marker
    "general-coder": ["python", "java", "typescript", "golang"],
}


def run_count() -> pd.DataFrame:
    """
    Count the made-up repos, listing each one under every tag it carries.

    Returns the per-language table, indexed by language.
    """
    repos = {
        repo_id: {"tags": tags, "downloads": 1, "likes": 0}
        for repo_id, tags in REPOS.items()
    }
    listings: dict[str, list[str]] = {}
    for repo_id, tags in REPOS.items():
        for tag in tags:
            listings.setdefault(tag, []).append(repo_id)
    table, _ = count("models", LANGUAGES, listings, repos)
    return table.set_index("language")


def test_counts_follow_the_rules() -> None:
    """Each rule admits or rejects the repos it is meant to."""
    table = run_count()

    # python: python-only, rust-and-python and general-coder; the gguf and mlx
    # copies are dropped
    assert table.loc["Python", "models"] == 3
    assert table.loc["Python", "models_raw"] == 5

    # rust: needs a code tag or another language's tag, so "rust-weights" is out
    assert table.loc["Rust", "models"] == 2

    # typescript: the multilingual model and dataset are out, the code dataset and
    # the general coder are in
    assert table.loc["TypeScript", "models"] == 2


def test_dedicated_count_drops_general_models() -> None:
    """A repo tagged with more than three programming languages is not 'dedicated'."""
    table = run_count()
    assert table.loc["Java", "models"] == 1
    assert table.loc["Java", "models_dedicated"] == 0
    assert table.loc["Python", "models_dedicated"] == 2
