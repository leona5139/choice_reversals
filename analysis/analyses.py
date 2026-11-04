"""Overview and the initial-choice comparisons in Figures 1 and 2."""
from collections import Counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from analysis.utils import CATEGORIES, SETUP_FIELDS, group_rows, player_key, write_csv
from treatments import tasks_in

# Every label is two lines so a short name stays on the first line, beside its neighbors.
LABELS = ["Over-\ncompensating", "Ex ante\nequalizing", "Mixed\n", "Ex post\nequalizing", "Reinforcing\n"]
CHOICE_FIELDS = ("treatment", "period", "category", "consistency",
                 "count", "percent", "n_players", "n_respondents", "n_choices")


def setup_label(setup):
    provider, model, temperature, prompt_version = setup
    return f"{provider} / {model} | t={temperature} | {prompt_version}"


def overview(rows, folder):
    table = []
    fields = (*SETUP_FIELDS, "treatment", "task")
    for key, group in group_rows(rows, fields).items():
        choices = [r for r in group if r["initial_a"] is not None]
        categories = Counter(r["initial_category"] for r in choices)
        record = dict(zip(fields, key))
        record.update({
            "n_players": len({player_key(r) for r in group}),
            "n_rounds": len(group),
            "initial_choices": len(choices),
            "skipped_initial_choices": len(group) - len(choices),
            "revision_opportunities": sum(r["revision_offered"] for r in group),
            "changed_choices": sum(r["changed"] is True for r in group),
            "changes_to_5_5": sum(r["changed"] is True and r["revision_a"] == 5 for r in group),
        })
        record.update({f"initial_{category}": categories[category] for category in CATEGORIES})
        table.append(record)
        print(f"{setup_label(key[:4])} | {key[4]} {key[5]}: "
              f"{len(choices)}/{len(group)} initial choices; "
              f"{record['changed_choices']}/{record['revision_opportunities']} revisions changed")
    return [write_csv(folder / "00_overview.csv", table)]


def choice_distribution(rows, with_consistency=False, by=()):
    """Groups by treatment and period. Pass by=("model", "temperature") to split further."""
    table = []
    fields = (*by, "treatment", "period")
    for key, group in group_rows(rows, fields).items():
        choices = [r for r in group if r["initial_a"] is not None]
        per_player = {}
        for row in choices:
            per_player.setdefault(player_key(row), Counter())[row["initial_category"]] += 1
        counts = Counter()
        for row in choices:
            category = row["initial_category"]
            own = per_player[player_key(row)]
            consistency = own[category] / own.total() if with_consistency else None
            counts[category, consistency] += 1
        levels = sorted({level for _, level in counts if level is not None}) or [None]
        for category in CATEGORIES:
            for consistency in levels:
                count = counts[category, consistency]
                table.append({
                    **dict(zip(fields, key)),
                    "category": category,
                    "consistency": consistency,
                    "count": count,
                    "percent": 100 * count / len(choices) if choices else None,
                    "n_players": len({player_key(r) for r in group}),
                    "n_respondents": len(per_player),
                    "n_choices": len(choices),
                })
    return table


def draw_panel(ax, records, title, levels=None, frame="A"):
    ax.set_title(title, fontsize=10)
    ax.set_xticks(range(5))
    ax.set_xticklabels(LABELS, fontsize=7.5)
    for label in ax.get_xticklabels():
        label.set_verticalalignment("top")
    ax.set_ylim(0, 100)
    ax.set_ylabel("Choices (%)", fontsize=9)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="0.88", linewidth=0.6)
    ax.set_facecolor("0.94" if frame == "P" else "white")
    if not records or records[0]["n_choices"] == 0:
        ax.text(0.5, 0.5, "No observed choices", ha="center", transform=ax.transAxes)
        return
    bottom = [0.0] * 5
    for level in levels or [None]:
        heights = [sum(r["percent"] for r in records
                       if r["category"] == category and r["consistency"] == level)
                   for category in CATEGORIES]
        color = plt.cm.Greys(0.25 + 0.65 * level) if level is not None else "0.3"
        ax.bar(range(5), heights, bottom=bottom, color=color, edgecolor="white", linewidth=0.4)
        bottom = [a + b for a, b in zip(bottom, heights)]


FIG1_TREATMENTS = ("4A_4AR", "4P_4AR")


def figure_1_choices(rows, by=()):
    selected = [{**r, "period": "1-4"} for r in rows
                if r["treatment"] in FIG1_TREATMENTS and r["round"] <= 4]
    return choice_distribution(selected, with_consistency=True, by=by)


def save_figure_1(table, png, suptitle, by=()):
    """One row per group in `by`. With by empty, a single pooled row."""
    levels = sorted({r["consistency"] for r in table if r["consistency"] is not None})
    groups = group_rows(table, by) if by else {(): table}
    fig, axes = plt.subplots(len(groups), 2, figsize=(11, 4.2 * len(groups)), squeeze=False)
    fig.suptitle(suptitle, fontsize=14)
    for index, (key, group) in enumerate(groups.items()):
        for col, treatment in enumerate(FIG1_TREATMENTS):
            records = [r for r in group if r["treatment"] == treatment]
            n = records[0]["n_choices"] if records else 0
            title = f"{treatment} | {n} choices"
            if by:
                model, temperature = key
                title = f"{model} | t={temperature}\n{title}"
            draw_panel(axes[index, col], records, title, levels, frame="A" if col == 0 else "P")
    handles = [Patch(facecolor=plt.cm.Greys(0.25 + 0.65 * level), label=f"{level:.0%}") for level in levels]
    fig.legend(handles=handles, title="Consistency within rounds 1–4", loc="lower center", ncol=4)
    fig.tight_layout(rect=(0, 0.14 / len(groups), 1, 1 - 0.08 / len(groups)))
    fig.savefig(png, dpi=160)
    plt.close(fig)


def figure_1(rows, folder):
    table = figure_1_choices(rows)
    files = [write_csv(folder / "01_fig1_choices.csv", table, CHOICE_FIELDS)]
    png = folder / "01_fig1_choices.png"
    if not table:
        png.unlink(missing_ok=True)
        print("Figure 1: no data for 4A_4AR or 4P_4AR.")
        return files
    save_figure_1(table, png, "Figure 1: Initial choices in rounds 1–4")
    return files + [png]


def figure_1_by_model(rows, folder):
    by = ("model", "temperature")
    table = figure_1_choices(rows, by)
    files = [write_csv(folder / "04_fig1_by_model.csv", table, (*by, *CHOICE_FIELDS))]
    png = folder / "04_fig1_by_model.png"
    if not table:
        png.unlink(missing_ok=True)
        print("Figure 1 by model: no data for 4A_4AR or 4P_4AR.")
        return files
    save_figure_1(table, png, "Figure 1 by model and temperature: initial choices in rounds 1–4", by)
    return files + [png]


def marginal_distribution(rows, category_field):
    """Same five-category bars as Figure 1, for one already-selected set of rounds."""
    choices = [r for r in rows if r.get(category_field) is not None]
    per_player = {}
    for row in choices:
        per_player.setdefault(player_key(row), Counter())[row[category_field]] += 1
    counts = Counter()
    for row in choices:
        category = row[category_field]
        own = per_player[player_key(row)]
        counts[category, own[category] / own.total()] += 1
    levels = sorted({level for _, level in counts}) or [None]
    table = []
    for category in CATEGORIES:
        for consistency in levels:
            count = counts[category, consistency]
            table.append({
                "category": category,
                "consistency": consistency,
                "count": count,
                "percent": 100 * count / len(choices) if choices else None,
                "n_players": len({player_key(r) for r in rows}),
                "n_respondents": len(per_player),
                "n_choices": len(choices),
            })
    return table


FIG3_PANELS = (
    ("initial", "initial_category", "Initial"),
    ("final", "final_category", "Final"),
    ("changes", "final_category", "Final (changes only)"),
)
FIG3_FIELDS = ("panel", "category", "consistency", "count", "percent",
               "n_players", "n_respondents", "n_choices")


def figure_3(rows, folder):
    """Paper Figure 3: rounds 5–8 of 4A_4AR, original choices, final choices, and revisions only."""
    selected = [r for r in rows if r["treatment"] == "4A_4AR" and r["round"] >= 5]
    table = []
    panels = {}
    for key, field, _title in FIG3_PANELS:
        source = [r for r in selected if r["changed"] is True] if key == "changes" else selected
        panels[key] = marginal_distribution(source, field)
        table.extend({"panel": key, **record} for record in panels[key])
    files = [write_csv(folder / "03_fig3_revisions.csv", table, FIG3_FIELDS)]
    png = folder / "03_fig3_revisions.png"
    if not selected:
        png.unlink(missing_ok=True)
        print("Figure 3: no rounds 5–8 for 4A_4AR.")
        return files
    levels = sorted({r["consistency"] for r in table if r["consistency"] is not None})
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), squeeze=False)
    fig.suptitle("Figure 3: Original and final choices in rounds 5–8 of 4A_4AR", fontsize=14)
    for col, (key, _field, title) in enumerate(FIG3_PANELS):
        records = panels[key]
        n = records[0]["n_choices"] if records else 0
        draw_panel(axes[0, col], records, f"{title}\n{n} choices", levels)
    handles = [Patch(facecolor=plt.cm.Greys(0.25 + 0.65 * level), label=f"{level:.0%}") for level in levels]
    fig.legend(handles=handles, title="Consistency within the panel", loc="lower center", ncol=4)
    fig.tight_layout(rect=(0, 0.14, 1, 0.92))
    fig.savefig(png, dpi=160)
    plt.close(fig)
    return files + [png]


def figure_2(rows, folder):
    treatments = ("2A2P_4AR", "2P2A_4AR", "4A_4AR", "4P_4AR")
    periods = ("1-2", "3-4", "5-8")
    selected = [r for r in rows if r["treatment"] in treatments]
    table = choice_distribution(selected)
    files = [write_csv(folder / "02_fig2_choices.csv", table, CHOICE_FIELDS)]
    png = folder / "02_fig2_choices.png"
    if not table:
        png.unlink(missing_ok=True)
        print("Figure 2: no data for the four main treatments.")
        return files
    fig, axes = plt.subplots(4, 3, figsize=(15, 12), squeeze=False)
    fig.suptitle("Figure 2: Initial choices across treatment sequences", fontsize=14)
    for row, treatment in enumerate(treatments):
        for col, period in enumerate(periods):
            records = [r for r in table if r["treatment"] == treatment and r["period"] == period]
            n = records[0]["n_choices"] if records else 0
            frame = "P" if tasks_in(treatment)[int(period[0]) - 1] == "P" else "A"
            title = f"{treatment} | rounds {period} | {frame}\n{n} choices"
            draw_panel(axes[row, col], records, title, frame=frame)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(png, dpi=160)
    plt.close(fig)
    return files + [png]
