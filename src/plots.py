"""Make the blog figures and summary statistics from data/hf_counts.csv.

Figures (written to figures/):
    zipf.png                    rank vs. number of models / datasets, log-log
    developers_vs_models.png    developers vs. models, with an OLS fit
    developers_vs_datasets.png  the same for datasets
    share.png                   share of developers vs. share of models, top languages

Also writes data/stats.json (fit slopes, R², concentration, robustness checks) and
data/residuals_{models,datasets}.csv (how far each language sits above/below the
fit), for quoting in the post.

Usage:
    python src/plots.py
"""

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from adjustText import adjust_text
from matplotlib.axes import Axes
from scipy import stats

from config import DATA, DEDICATED_MAX_LANGUAGES, FIGURES, PERIOD

# colours: one neutral for the bulk, three hues for the highlighted groups
SURFACE = "#f5fafd"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
MID = "#a7a59e"
TOP = "#2a78d6"
UNDER = "#eb6834"
LEGACY = "#0b0b0b"
FIT = "#6250d6"
# datasets bars in the share plot: amber stays distinct from the blue models bars
DATASETS = "#e0a526"

plt.rcParams.update(
    {
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": INK_2,
        "axes.labelcolor": INK,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.color": INK_2,
        "ytick.color": INK_2,
        "font.size": 10.5,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
    },
)

KINDS = ("models", "datasets")

# the keynote these figures credit, each figure says how it relates to it
KEYNOTE = (
    "Anna Korhonen's EMNLP 2026 keynote, "
    "“AI for the Many: Starting from the World, Not the Model”"
)

# the type of scipy's linregress result (scipy doesn't export it publicly)
Fit = stats._stats_py.LinregressResult

# zero counts can't go on a log scale, so where needed they are treated as this
ZERO_AS = 0.5


def gini(
    values: np.ndarray,
) -> float:
    """
    Compute the gini coefficient: 0 is perfectly equal, 1 is everything in one language.

    Returns the coefficient.
    """
    x = np.sort(values.astype(float))
    n = len(x)
    return float((2 * np.arange(1, n + 1) - n - 1) @ x / (n * x.sum()))


def loglog_fit(
    x: pd.Series,
    y: pd.Series,
) -> Fit:
    """
    Fit a straight line to log10(y) against log10(x) by ordinary least squares.

    Returns scipy's fit result (slope, intercept, rvalue, ...).
    """
    return stats.linregress(np.log10(x), np.log10(y))


def by_count(
    df: pd.DataFrame,
    kind: str,
) -> pd.DataFrame:
    """
    Sort languages by count, largest first, breaking ties alphabetically so the order never changes.

    Returns the sorted table.
    """
    return df.sort_values([kind, "language"], ascending=[False, True])


def add_credit(
    fig: plt.Figure,
    lead: str = "Adapted from",
) -> None:
    """Write the keynote credit line along the bottom-right of a figure, starting with lead."""
    fig.text(
        0.995,
        -0.01,
        f"{lead} {KEYNOTE}",
        ha="right",
        va="top",
        fontsize=8.5,
        color=INK_2,
        style="italic",
    )


def loglog_grid(
    ax: Axes,
) -> None:
    """Draw light major and minor grid lines behind a log-log plot."""
    ax.grid(True, which="major", color=GRID, linewidth=0.8)
    ax.grid(True, which="minor", color=GRID, linewidth=0.4, alpha=0.6)
    ax.set_axisbelow(True)


def zipf_panel(
    ax: Axes,
    df: pd.DataFrame,
    kind: str,
) -> dict:
    """
    Draw one rank-vs-count panel, with a power-law fit that leaves out rank 1.

    Returns the fit slope and R², and the ranked table of languages with count ≥ 1.
    """
    d = by_count(df[df[kind] > 0], kind).reset_index(drop=True)
    # "rank" is the position used for plotting and fitting; "joint_rank" gives tied
    # languages the same rank (e.g. every language with 1 model is joint 74th)
    d["rank"] = np.arange(1, len(d) + 1)
    d["joint_rank"] = d[kind].rank(method="min", ascending=False).astype(int)

    # power-law fit, leaving out the rank-1 outlier as the talk does for english
    fit_d = d[d["rank"] > 1]
    fit = loglog_fit(fit_d["rank"], fit_d[kind])
    xs = np.logspace(np.log10(2), np.log10(d["rank"].max()), 50)
    ax.plot(
        xs,
        10 ** (fit.intercept + fit.slope * np.log10(xs)),
        "--",
        color=FIT,
        lw=2,
        label=f"Power-law fit (slope {fit.slope:.2f}, R² {fit.rvalue**2:.2f})",
    )

    ax.scatter(d["rank"][1:], d[kind][1:], s=14, color=INK, zorder=3, linewidths=0)
    ax.scatter(
        d["rank"][:1],
        d[kind][:1],
        s=90,
        color=UNDER,
        zorder=4,
        edgecolor=SURFACE,
        linewidth=1.5,
    )

    # label the top 8 languages
    texts = [
        ax.text(
            r["rank"],
            r[kind],
            r.language,
            fontsize=9.5,
            fontweight="bold",
            color=INK,
        )
        for _, r in d.head(8).iterrows()
    ]
    ax.set_xscale("log")
    ax.set_yscale("log")
    adjust_text(
        texts,
        x=d["rank"].to_numpy(),
        y=d[kind].to_numpy(),
        ax=ax,
        arrowprops=dict(arrowstyle="-", color=INK_2, lw=0.5),
    )
    loglog_grid(ax)
    ax.set_xlabel("Rank (log)")
    ax.set_ylabel(f"Number of {kind} (log)")
    ax.set_title(f"Hugging Face {kind} per programming language")
    ax.legend(loc="lower left", frameon=False, fontsize=9)
    return {"slope": fit.slope, "r2": fit.rvalue**2, "ranked": d}


def zipf_figure(
    df: pd.DataFrame,
    callout: str | None,
) -> dict:
    """
    Draw the two rank-vs-count panels (models, datasets) and point out one language.

    Returns the output of zipf_panel for each kind.
    """
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.6))
    out = {}
    for ax, kind in zip(axes, KINDS):
        out[kind] = zipf_panel(ax, df, kind)
        ranked = out[kind]["ranked"]
        if callout and callout in set(ranked.language):
            r = ranked[ranked.language == callout].iloc[0]
            devs = df.loc[df.language == callout, "developers"].iloc[0]
            noun = kind[:-1] if r[kind] == 1 else kind
            ax.annotate(
                f"Rank {r['joint_rank']}: {callout}\n"
                f"{devs / 1000:,.0f}k developers, {int(r[kind])} {noun}",
                (r["rank"], r[kind]),
                xytext=(0.06, 0.18),
                textcoords="axes fraction",
                fontsize=12,
                fontweight="bold",
                color=UNDER,
                arrowprops=dict(arrowstyle="-|>", color=UNDER, lw=1.8),
            )
    fig.suptitle(
        "Code AI is highly concentrated",
        x=0.01,
        ha="left",
        fontsize=17,
        fontweight="bold",
        color=INK,
    )
    fig.tight_layout()
    add_credit(fig)
    fig.savefig(FIGURES / "zipf.png")
    plt.close(fig)
    return out


def classify(
    df: pd.DataFrame,
    kind: str,
) -> tuple[pd.DataFrame, Fit]:
    """
    Fit log(count) ~ log(developers) over languages with count ≥ 1, and put each language in a group.

    Returns the table with predicted counts, residuals and groups, and the fit.
    """
    d = df.copy()
    pos = d[d[kind] > 0]
    fit = loglog_fit(pos.developers, pos[kind])
    predicted = 10 ** (fit.intercept + fit.slope * np.log10(d.developers))
    d["predicted"] = predicted
    # log10 residual: +1 means 10x more than the fit predicts
    d["residual"] = np.log10(d[kind].clip(lower=ZERO_AS)) - np.log10(predicted)

    # "top": the 5 languages with the most repos in each decade of developers
    d["bin"] = np.floor(np.log10(d.developers)).astype(int)
    top = by_count(d[d[kind] > 0], kind).groupby("bin").head(5).index

    # later assignments win: legacy > under-resourced > top > other
    d["group"] = "mid"
    d.loc[top, "group"] = "top"
    d.loc[(d.developers >= 10_000) & (d.residual <= -1), "group"] = "under"
    d.loc[d.legacy, "group"] = "legacy"
    return d, fit


def scatter_figure(
    df: pd.DataFrame,
    kind: str,
) -> dict:
    """
    Draw developers vs. count with the fit, highlighted groups and a take-aways panel, and save the residuals.

    Returns the fit slope and R², the number of languages with zero count, and the
    under-resourced languages.
    """
    d, fit = classify(df, kind)
    r2 = fit.rvalue**2
    zero_y = 0.55  # where languages with no repos at all are drawn

    fig, (ax, side) = plt.subplots(
        1,
        2,
        figsize=(13.5, 6.4),
        gridspec_kw={"width_ratios": [2.3, 1]},
    )
    style = {
        "mid": dict(color=MID, s=16, label="Other languages"),
        "top": dict(color=TOP, s=46, label="Top 5 per developer bin"),
        "under": dict(color=UNDER, s=46, label="≥10k developers, ≥10× fewer than fit"),
        "legacy": dict(color=LEGACY, s=30, marker="D", label="Legacy languages"),
    }
    for group in ["mid", "top", "under", "legacy"]:
        g = d[d.group == group]
        ax.scatter(
            g.developers,
            g[kind].where(g[kind] > 0, zero_y),
            zorder=3,
            edgecolor=SURFACE,
            linewidth=0.8,
            **style[group],
        )

    xs = np.logspace(np.log10(d.developers.min()), np.log10(d.developers.max()), 50)
    ax.plot(
        xs,
        10 ** (fit.intercept + fit.slope * np.log10(xs)),
        color=FIT,
        lw=2,
        label=f"OLS fit (R² = {r2:.2f})",
        zorder=2,
    )
    # dotted line separating the "0" row from the log-scaled counts
    ax.axhline(0.8, color=INK_2, lw=0.6, ls=":")

    # label the highlighted languages and the biggest few overall, but only the
    # largest few of the many languages sitting on the zero row
    on_zero = d[d[kind] == 0]
    crowded = on_zero.index.difference(on_zero.nlargest(4, "developers").index)
    label = d[
        ((d.group != "mid") | (d.developers >= d.developers.nlargest(6).min()))
        & ~d.index.isin(crowded)
    ]
    texts = [
        ax.text(
            r.developers,
            r[kind] if r[kind] > 0 else zero_y,
            r.language,
            fontsize=8.5,
            color=INK,
        )
        for _, r in label.iterrows()
    ]
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_ylim(bottom=0.4)
    ticks = [t for t in ax.get_yticks() if t >= 1]
    top_y = ax.get_ylim()[1]
    ax.set_yticks([zero_y, *ticks], ["0", *[f"{t:,.0f}" for t in ticks]])
    ax.set_ylim(0.4, top_y)
    adjust_text(
        texts,
        x=d.developers.to_numpy(),
        y=d[kind].where(d[kind] > 0, zero_y).to_numpy(),
        ax=ax,
        arrowprops=dict(arrowstyle="-", color=INK_2, lw=0.4),
    )
    loglog_grid(ax)
    year, quarter = PERIOD
    ax.set_xlabel(f"Active GitHub developers, {year} Q{quarter} (log)")
    ax.set_ylabel(f"Hugging Face {kind} (log)")
    ax.legend(loc="upper left", frameon=False, fontsize=9)

    # right-hand panel: the take-aways, like the talk's slide
    side.axis("off")
    under = d[d.group == "under"].sort_values(
        ["developers", "language"],
        ascending=[False, True],
    )
    top_res = d[d[kind] > 0].nlargest(4, "residual")
    lines = [
        (
            f"Developer count explains only\n~{r2:.0%} of the variation in\n"
            f"{kind} per language*",
            15,
            INK,
            "bold",
        ),
        ("", 6, INK, "normal"),
        ("Most for their size", 11.5, TOP, "bold"),
        (", ".join(top_res.language), 10, INK_2, "normal"),
        ("", 4, INK, "normal"),
        (f"Many developers, few {kind}", 11.5, UNDER, "bold"),
        (", ".join(under.language.head(6)) or "none", 10, INK_2, "normal"),
    ]
    if len(under):
        u = under.iloc[0]
        lines.append(
            (
                f"{u.language}: ~{u.developers / 1000:,.0f}k developers, "
                f"{int(u[kind])} {kind}",
                10,
                INK_2,
                "normal",
            ),
        )
    legacy = by_count(d[d.legacy], kind).head(3)
    lines += [
        ("", 4, INK, "normal"),
        ("Legacy languages", 11.5, LEGACY, "bold"),
        (
            ", ".join(f"{r.language} ({int(r[kind])})" for _, r in legacy.iterrows()),
            10,
            INK_2,
            "normal",
        ),
        ("", 6, INK, "normal"),
        (f"*R² of the fit over languages with ≥1 {kind[:-1]}", 8.5, INK_2, "normal"),
    ]
    # stack the lines from the top, spacing them by font size and line count
    y = 0.95
    for text, size, color, weight in lines:
        side.text(
            0,
            y,
            text,
            fontsize=size,
            color=color,
            fontweight=weight,
            va="top",
            wrap=True,
            transform=side.transAxes,
        )
        y -= 0.025 * size / 10 * (text.count("\n") + 1) + 0.03

    fig.suptitle(
        f"Does developer population explain {kind[:-1]} availability?",
        x=0.01,
        ha="left",
        fontsize=17,
        fontweight="bold",
        color=INK,
    )
    fig.tight_layout()
    add_credit(fig)
    fig.savefig(FIGURES / f"developers_vs_{kind}.png")
    plt.close(fig)

    columns = ["language", "developers", kind, "predicted", "residual", "group"]
    d[columns].sort_values(["residual", "language"]).to_csv(
        DATA / f"residuals_{kind}.csv",
        index=False,
        float_format="%.6g",
    )
    return {
        "slope": fit.slope,
        "r2": r2,
        "zero": int((d[kind] == 0).sum()),
        "under": under.language.tolist(),
    }


def share_figure(
    df: pd.DataFrame,
    n: int = 15,
) -> None:
    """Draw share of developers, models and datasets side by side for the n most-used languages."""
    d = df.sort_values(["developers", "language"], ascending=[False, True]).head(n)

    # each share is out of the total over all 259 languages, not just these n
    bars = [
        ("developers", "Share of developers", MID),
        ("models", "Share of tagged models", TOP),
        ("datasets", "Share of tagged datasets", DATASETS),
    ]
    fig, ax = plt.subplots(figsize=(14, 5.5))
    x = np.arange(len(d))
    width = 0.27
    # one group of three bars per language, centred on its tick
    for i, (column, label, colour) in enumerate(bars):
        ax.bar(
            x + (i - 1) * width,
            d[column] / df[column].sum() * 100,
            width,
            color=colour,
            label=label,
        )
    ax.set_xticks(x, d.language, rotation=35, ha="right")
    ax.set_ylabel("% of total")
    ax.grid(True, axis="y", color=GRID)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", frameon=False)
    ax.set_title(
        f"The {n} most-used languages: developers vs. models and datasets",
        loc="left",
    )
    fig.tight_layout()
    # this plot isn't from the keynote's slides, only the analysis idea is
    add_credit(fig, lead="Analysis inspired by")
    fig.savefig(FIGURES / "share.png")
    plt.close(fig)


def robustness(
    df: pd.DataFrame,
    kind: str,
) -> dict:
    """
    Check how much the developer fit depends on its choices: excluding zero counts, and counting general multi-language models.

    Returns the alternative fits' slopes and R², and the rank correlation over all languages.
    """
    # every language, with zero counts treated as ZERO_AS
    with_zeros = loglog_fit(df.developers, df[kind].clip(lower=ZERO_AS))
    # only repos tagged with few programming languages
    dedicated_col = f"{kind}_dedicated"
    dedicated = df[df[dedicated_col] > 0]
    dedicated_fit = loglog_fit(dedicated.developers, dedicated[dedicated_col])
    return {
        "fit_with_zeros_slope": round(with_zeros.slope, 3),
        "fit_with_zeros_r2": round(with_zeros.rvalue**2, 3),
        "spearman_all_languages": round(
            stats.spearmanr(df.developers, df[kind]).statistic,
            3,
        ),
        "dedicated_max_languages": DEDICATED_MAX_LANGUAGES,
        "dedicated_total": int(df[dedicated_col].sum()),
        "dedicated_fit_slope": round(dedicated_fit.slope, 3),
        "dedicated_fit_r2": round(dedicated_fit.rvalue**2, 3),
    }


def main() -> None:
    """Make every figure and write data/stats.json."""
    FIGURES.mkdir(exist_ok=True)
    df = pd.read_csv(DATA / "hf_counts.csv")
    hf_summary = json.loads((DATA / "hf_summary.json").read_text())

    scatter = {kind: scatter_figure(df, kind) for kind in KINDS}

    # callout: the widely used language (100k+ developers) with the fewest models
    # per developer, like the talk's "Rank 116: Maithili"
    big = df[(df.models > 0) & (df.developers >= 100_000)]
    callout = big.loc[(big.developers / big.models).idxmax(), "language"]
    zipf = zipf_figure(df, callout=callout)
    share_figure(df)

    summary: dict = {"fetched": hf_summary["fetched"], "callout": callout}
    for kind in KINDS:
        ranked = zipf[kind]["ranked"]
        total = ranked[kind].sum()
        summary[kind] = {
            "languages_with_any": int(len(ranked)),
            "languages_with_none": scatter[kind]["zero"],
            "distinct_repos": hf_summary[f"{kind}_with_any_language"],
            "language_repo_pairs": int(total),
            "converted_removed": hf_summary[f"{kind}_converted_removed"],
            "top1": ranked.language.iloc[0],
            "top1_share": round(ranked[kind].iloc[0] / total, 3),
            "top10_share": round(ranked[kind].head(10).sum() / total, 3),
            "gini": round(gini(df[kind].to_numpy()), 3),
            "zipf_slope": round(zipf[kind]["slope"], 3),
            "zipf_r2": round(zipf[kind]["r2"], 3),
            "developers_fit_slope": round(scatter[kind]["slope"], 3),
            "developers_fit_r2": round(scatter[kind]["r2"], 3),
            "robustness": robustness(df, kind),
            "under_resourced": scatter[kind]["under"],
        }

    devs = df.sort_values(["developers", "language"], ascending=[False, True])
    summary["developers"] = {
        "total_pairs": int(devs.developers.sum()),
        "top1": devs.language.iloc[0],
        "top1_share": round(devs.developers.iloc[0] / devs.developers.sum(), 3),
        "top10_share": round(
            devs.developers.head(10).sum() / devs.developers.sum(),
            3,
        ),
        "gini": round(gini(df.developers.to_numpy()), 3),
    }
    (DATA / "stats.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
