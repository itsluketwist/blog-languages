"""Make the blog figures from data/hf_counts.csv.

Figures (written to figures/):
    zipf.png                    rank vs. number of models / datasets, log-log
    developers_vs_models.png    developers vs. models, with an OLS fit
    developers_vs_datasets.png  the same for datasets
    share.png                   share of developers vs. share of models, top languages

Also writes data/stats.json (fit slopes, R², concentration) and data/residuals.csv
(how far each language sits above/below the fit), for quoting in the post.

Usage:
    python src/plots.py
"""

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from adjustText import adjust_text
from matplotlib.lines import Line2D
from scipy import stats

from config import DATA, FIGURES

# Colours: one neutral for the bulk, three hues for the highlighted groups.
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
MID = "#a7a59e"
TOP = "#2a78d6"
UNDER = "#eb6834"
LEGACY = "#0b0b0b"
FIT = "#6250d6"

plt.rcParams.update({
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
})

LABELS = {"models": "models", "datasets": "datasets"}


def gini(values: np.ndarray) -> float:
    x = np.sort(values.astype(float))
    n = len(x)
    return float((2 * np.arange(1, n + 1) - n - 1) @ x / (n * x.sum()))


def loglog_grid(ax) -> None:
    ax.grid(True, which="major", color=GRID, linewidth=0.8)
    ax.grid(True, which="minor", color=GRID, linewidth=0.4, alpha=0.6)
    ax.set_axisbelow(True)


def zipf_panel(ax, df: pd.DataFrame, kind: str) -> dict:
    d = df[df[kind] > 0].sort_values(kind, ascending=False).reset_index(drop=True)
    d["rank"] = np.arange(1, len(d) + 1)

    # Power-law fit, leaving out the rank-1 outlier as the talk does for English.
    fit_d = d[d["rank"] > 1]
    fit = stats.linregress(np.log10(fit_d["rank"]), np.log10(fit_d[kind]))
    xs = np.logspace(np.log10(2), np.log10(d["rank"].max()), 50)
    ax.plot(xs, 10 ** (fit.intercept + fit.slope * np.log10(xs)), "--", color=FIT,
            lw=2, label=f"Power-law fit (slope {fit.slope:.2f}, R² {fit.rvalue ** 2:.2f})")

    ax.scatter(d["rank"][1:], d[kind][1:], s=14, color=INK, zorder=3, linewidths=0)
    ax.scatter(d["rank"][:1], d[kind][:1], s=90, color=UNDER, zorder=4,
               edgecolor=SURFACE, linewidth=1.5)

    texts = []
    for _, r in d.head(8).iterrows():
        texts.append(ax.text(r["rank"], r[kind], r.language, fontsize=9.5,
                             fontweight="bold", color=INK))
    ax.set_xscale("log")
    ax.set_yscale("log")
    adjust_text(texts, x=d["rank"].to_numpy(), y=d[kind].to_numpy(), ax=ax,
                arrowprops=dict(arrowstyle="-", color=INK_2, lw=0.5))
    loglog_grid(ax)
    ax.set_xlabel("Rank (log)")
    ax.set_ylabel(f"Number of {LABELS[kind]} (log)")
    ax.set_title(f"Hugging Face {LABELS[kind]} per programming language")
    ax.legend(loc="lower left", frameon=False, fontsize=9)
    return {"slope": fit.slope, "r2": fit.rvalue ** 2, "ranked": d}


def zipf_figure(df: pd.DataFrame, callout: str | None) -> dict:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.6))
    out = {}
    for ax, kind in zip(axes, ["models", "datasets"]):
        out[kind] = zipf_panel(ax, df, kind)
        ranked = out[kind]["ranked"]
        if callout and callout in set(ranked.language):
            r = ranked[ranked.language == callout].iloc[0]
            devs = df.loc[df.language == callout, "developers"].iloc[0]
            ax.annotate(f"Rank {int(r['rank'])}: {callout}\n{devs / 1000:,.0f}k developers, "
                        f"{int(r[kind])} {LABELS[kind][:-1] if r[kind] == 1 else LABELS[kind]}",
                        (r["rank"], r[kind]),
                        xytext=(0.06, 0.18), textcoords="axes fraction",
                        fontsize=12, fontweight="bold", color=UNDER,
                        arrowprops=dict(arrowstyle="-|>", color=UNDER, lw=1.8))
    fig.suptitle("Code AI is highly concentrated", x=0.01, ha="left",
                 fontsize=17, fontweight="bold", color=INK)
    fig.tight_layout()
    fig.savefig(FIGURES / "zipf.png")
    plt.close(fig)
    return out


def classify(df: pd.DataFrame, kind: str) -> tuple[pd.DataFrame, object]:
    """Fit log(models) ~ log(developers) and put each language in a group."""
    d = df.copy()
    pos = d[d[kind] > 0]
    fit = stats.linregress(np.log10(pos.developers), np.log10(pos[kind]))
    predicted = 10 ** (fit.intercept + fit.slope * np.log10(d.developers))
    d["predicted"] = predicted
    # log10 residual: +1 means 10x more than the fit predicts; zeros count as 0.5.
    d["residual"] = np.log10(d[kind].clip(lower=0.5)) - np.log10(predicted)

    d["bin"] = np.floor(np.log10(d.developers)).astype(int)
    top = d[d[kind] > 0].sort_values(kind, ascending=False).groupby("bin").head(5).index

    d["group"] = "mid"
    d.loc[top, "group"] = "top"
    d.loc[(d.developers >= 10_000) & (d.residual <= -1), "group"] = "under"
    d.loc[d.legacy, "group"] = "legacy"
    return d, fit


def scatter_figure(df: pd.DataFrame, kind: str) -> dict:
    d, fit = classify(df, kind)
    r2 = fit.rvalue ** 2
    zero_y = 0.55  # where languages with no models at all are drawn

    fig, (ax, side) = plt.subplots(1, 2, figsize=(13.5, 6.4),
                                   gridspec_kw={"width_ratios": [2.3, 1]})
    style = {
        "mid": dict(color=MID, s=16, label="Other languages"),
        "top": dict(color=TOP, s=46, label="Top 5 per developer bin"),
        "under": dict(color=UNDER, s=46, label="≥10k developers, ≥10× fewer than fit"),
        "legacy": dict(color=LEGACY, s=30, marker="D", label="Legacy languages"),
    }
    for group in ["mid", "top", "under", "legacy"]:
        g = d[d.group == group]
        ax.scatter(g.developers, g[kind].where(g[kind] > 0, zero_y), zorder=3,
                   edgecolor=SURFACE, linewidth=0.8, **style[group])

    xs = np.logspace(np.log10(d.developers.min()), np.log10(d.developers.max()), 50)
    ax.plot(xs, 10 ** (fit.intercept + fit.slope * np.log10(xs)), color=FIT, lw=2,
            label=f"OLS fit (R² = {r2:.2f})", zorder=2)
    ax.axhline(0.8, color=INK_2, lw=0.6, ls=":")

    # Label the highlighted languages and the biggest few overall, but only the
    # largest few of the many languages sitting on the zero row.
    on_zero = d[d[kind] == 0]
    crowded = on_zero.index.difference(on_zero.nlargest(4, "developers").index)
    label = d[((d.group != "mid") | (d.developers >= d.developers.nlargest(6).min()))
              & ~d.index.isin(crowded)]
    texts = [ax.text(r.developers, r[kind] if r[kind] > 0 else zero_y, r.language,
                     fontsize=8.5, color=INK) for _, r in label.iterrows()]
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_ylim(bottom=0.4)
    ticks = [t for t in ax.get_yticks() if t >= 1]
    top_y = ax.get_ylim()[1]
    ax.set_yticks([zero_y, *ticks], ["0", *[f"{t:,.0f}" for t in ticks]])
    ax.set_ylim(0.4, top_y)
    adjust_text(texts, x=d.developers.to_numpy(),
                y=d[kind].where(d[kind] > 0, zero_y).to_numpy(), ax=ax,
                arrowprops=dict(arrowstyle="-", color=INK_2, lw=0.4))
    loglog_grid(ax)
    ax.set_xlabel("Active GitHub developers, 2026 Q1 (log)")
    ax.set_ylabel(f"Hugging Face {LABELS[kind]} (log)")
    ax.legend(loc="upper left", frameon=False, fontsize=9)

    # Right-hand panel: the take-aways, like the talk's slide.
    side.axis("off")
    under = d[d.group == "under"].sort_values("developers", ascending=False)
    top_res = d[d[kind] > 0].nlargest(4, "residual")
    lines = [
        (f"Developer count explains only\n~{r2:.0%} of the variation in\n{LABELS[kind]} per language", 15, INK, "bold"),
        ("", 6, INK, "normal"),
        ("Most for their size", 11.5, TOP, "bold"),
        (", ".join(top_res.language), 10, INK_2, "normal"),
        ("", 4, INK, "normal"),
        ("Many developers, few " + LABELS[kind], 11.5, UNDER, "bold"),
        (", ".join(under.language.head(6)) or "none", 10, INK_2, "normal"),
    ]
    if len(under):
        u = under.iloc[0]
        lines.append((f"{u.language}: ~{u.developers / 1000:,.0f}k developers, {int(u[kind])} {LABELS[kind]}",
                      10, INK_2, "normal"))
    legacy = d[d.legacy].nlargest(3, kind)
    lines += [
        ("", 4, INK, "normal"),
        ("Legacy languages", 11.5, LEGACY, "bold"),
        (", ".join(f"{r.language} ({int(r[kind])})" for _, r in legacy.iterrows()), 10, INK_2, "normal"),
    ]
    y = 0.95
    for text, size, color, weight in lines:
        side.text(0, y, text, fontsize=size, color=color, fontweight=weight, va="top",
                  wrap=True, transform=side.transAxes)
        y -= 0.025 * size / 10 * (text.count("\n") + 1) + 0.03

    fig.suptitle(f"Does developer population explain {kind[:-1]} availability?",
                 x=0.01, ha="left", fontsize=17, fontweight="bold", color=INK)
    fig.tight_layout()
    fig.savefig(FIGURES / f"developers_vs_{kind}.png")
    plt.close(fig)

    d[["language", "developers", kind, "predicted", "residual", "group"]].sort_values(
        "residual").to_csv(DATA / f"residuals_{kind}.csv", index=False)
    return {"slope": fit.slope, "r2": r2, "zero": int((d[kind] == 0).sum()),
            "under": under.language.tolist()}


def share_figure(df: pd.DataFrame, n: int = 15) -> None:
    d = df.assign(
        dev_share=df.developers / df.developers.sum(),
        model_share=df.models / df.models.sum(),
    ).nlargest(n, "developers").iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 6.5))
    y = np.arange(len(d))
    h = 0.38
    ax.barh(y + h / 2, d.dev_share * 100, h, color=MID, label="Share of developers")
    ax.barh(y - h / 2, d.model_share * 100, h, color=TOP, label="Share of tagged models")
    ax.set_yticks(y, d.language)
    ax.set_xlabel("% of total")
    ax.grid(True, axis="x", color=GRID)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", frameon=False)
    ax.set_title(f"The {n} most-used languages: developers vs. models", loc="left")
    fig.tight_layout()
    fig.savefig(FIGURES / "share.png")
    plt.close(fig)


def main() -> None:
    FIGURES.mkdir(exist_ok=True)
    df = pd.read_csv(DATA / "hf_counts.csv")

    scatter = {kind: scatter_figure(df, kind) for kind in ["models", "datasets"]}
    under = scatter["models"]["under"]
    # Callout: the widely used language (100k+ developers) with the fewest models
    # per developer, like the talk's "Rank 116: Maithili".
    big = df[(df.models > 0) & (df.developers >= 100_000)]
    callout = big.loc[(big.developers / big.models).idxmax(), "language"]
    zipf = zipf_figure(df, callout=callout)
    share_figure(df)

    summary = {}
    for kind in ["models", "datasets"]:
        ranked = zipf[kind]["ranked"]
        total = ranked[kind].sum()
        summary[kind] = {
            "languages_with_any": int(len(ranked)),
            "languages_with_none": scatter[kind]["zero"],
            "top1": ranked.language.iloc[0],
            "top1_share": round(ranked[kind].iloc[0] / total, 3),
            "top10_share": round(ranked[kind].head(10).sum() / total, 3),
            "gini": round(gini(df[kind].to_numpy()), 3),
            "zipf_slope": round(zipf[kind]["slope"], 3),
            "zipf_r2": round(zipf[kind]["r2"], 3),
            "developers_fit_slope": round(scatter[kind]["slope"], 3),
            "developers_fit_r2": round(scatter[kind]["r2"], 3),
            "under_resourced": under if kind == "models" else scatter[kind]["under"],
        }
    devs = df.sort_values("developers", ascending=False)
    summary["developers"] = {
        "top1": devs.language.iloc[0],
        "top1_share": round(devs.developers.iloc[0] / devs.developers.sum(), 3),
        "top10_share": round(devs.developers.head(10).sum() / devs.developers.sum(), 3),
        "gini": round(gini(df.developers.to_numpy()), 3),
    }
    (DATA / "stats.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
