"""Compare the saved Milestone 2 runs with the human replication data.

From the repository root, run: python -m analysis.compare_m2
Outputs are descriptive. Rates are fractions in the CSV files. The six initial
choice blocks have equal weight only when their TVDs are averaged. The summary
revision rates average the four condition rates; their count columns sum the
four conditions. A share with a zero denominator is left blank.
"""

from collections import Counter
from pathlib import Path
from statistics import mean

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import PercentFormatter

from analysis.m2_inputs import load_samples
from analysis.utils import CATEGORIES, write_csv

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "analysis" / "m2_comparison"
CONDITIONS = ("4A_4AR", "4P_4AR", "2A2P_4AR", "2P2A_4AR")
BLOCKS = [(condition, 1, 4) for condition in CONDITIONS[:2]] + [
    (condition, 5, 8) for condition in CONDITIONS
]
EXTRA = "google/gemma-4-31b-it [default]"
SUMMARY = "equal_condition_mean"


def share(count, total):
    return count / total if total else None


def initial_analysis(samples):
    """Use every observed initial choice in its block, including all initial AR choices."""
    table = []
    references = {}
    for setting, rows in samples.items():
        for condition, start, end in BLOCKS:
            choices = [
                row["initial_category"] for row in rows
                if row["treatment"] == condition and start <= row["round"] <= end
                and row["initial_a"] is not None
            ]
            counts = Counter(choices)
            if not counts or set(counts).difference(CATEGORIES):
                raise ValueError(f"Empty or unclassified block: {setting}, {condition}, {start}-{end}")
            result = dict(setting=setting, condition=condition, round_start=start, round_end=end,
                          choices=len(choices), tvd_to_human=None)
            for category in CATEGORIES:
                result[f"n_{category}"] = counts[category]
                result[f"share_{category}"] = counts[category] / len(choices)
            if setting == "Human":
                references[condition, start, end] = result
            table.append(result)
    for result in table:
        human = references[result["condition"], result["round_start"], result["round_end"]]
        result["tvd_to_human"] = sum(
            abs(result[f"share_{category}"] - human[f"share_{category}"]) for category in CATEGORIES
        ) / 2
    means = {
        setting: mean(row["tvd_to_human"] for row in table if row["setting"] == setting)
        for setting in samples
    }
    for row in table:
        row["six_block_mean_tvd"] = means[row["setting"]]
    return table


def framing_analysis(initial_table):
    """Connect independent 4A and 4P cohorts; exclude P rounds with no participant decision."""
    table = []
    for setting in dict.fromkeys(row["setting"] for row in initial_table):
        early = {
            row["condition"]: row for row in initial_table
            if row["setting"] == setting and row["round_start"] == 1
        }
        ante, post = (early[condition] for condition in CONDITIONS[:2])
        ante_rate, post_rate = (row["share_ex_post_equalizing"] for row in (ante, post))
        table.append(dict(setting=setting, n_4A=ante["choices"], equal_4A=ante["n_ex_post_equalizing"],
                          share_4A=ante_rate, n_4P=post["choices"],
                          equal_4P=post["n_ex_post_equalizing"], share_4P=post_rate,
                          difference_4P_minus_4A=post_rate - ante_rate))
    return table


def revision_analysis(samples):
    """Pair each initial and final decision on every offered AR revision in rounds 5–8."""
    table = []
    counts = ("eligible", "initial_equal", "final_equal", "changes", "changes_to_equal")
    rates = ("share_initial_equal", "share_final_equal", "difference_final_minus_initial",
             "share_changed", "share_of_changes_to_equal")
    for setting, rows in samples.items():
        per_condition = []
        for condition in CONDITIONS:
            pairs = [
                (row["initial_a"], row["final_a"]) for row in rows
                if row["treatment"] == condition and 5 <= row["round"] <= 8 and row["revision_offered"]
            ]
            if not pairs or any(a is None or b is None for a, b in pairs):
                raise ValueError(f"Missing eligible pair(s) for {setting}, {condition}")
            n = len(pairs)
            initial = sum(a == 5 for a, _ in pairs)
            final = sum(b == 5 for _, b in pairs)
            changes = sum(a != b for a, b in pairs)
            to_equal = sum(a != b and b == 5 for a, b in pairs)
            per_condition.append(dict(setting=setting, condition=condition, eligible=n,
                                      initial_equal=initial, final_equal=final, changes=changes,
                                      changes_to_equal=to_equal, share_initial_equal=initial / n,
                                      share_final_equal=final / n, difference_final_minus_initial=(final - initial) / n,
                                      share_changed=changes / n, share_of_changes_to_equal=share(to_equal, changes)))
        summary = dict(setting=setting, condition=SUMMARY)
        for key in counts:
            summary[key] = sum(row[key] for row in per_condition)
        for key in rates:
            values = [row[key] for row in per_condition]
            summary[key] = mean(values) if all(value is not None for value in values) else None
        table.extend([*per_condition, summary])
    return table


def short_name(setting):
    if setting == "Human":
        return "Humans"
    model, reason = setting.rsplit(" [", 1)
    name = model.rsplit("/", 1)[-1]
    if setting == EXTRA:
        return f"{name} · default*"
    return f"{name} · {reason[:-1]}"


def heatmap(settings, initial, out):
    models = [s for s in settings if s != "Human"]
    distances = {(r["setting"], r["condition"], r["round_start"]): r["tvd_to_human"] for r in initial}
    matrix = [[distances[setting, condition, start] for condition, start, _ in BLOCKS] for setting in models]
    fig, ax = plt.subplots(figsize=(9.2, 6.2))
    fig.subplots_adjust(left=.33, bottom=.18, right=.87, top=.84)
    pic = ax.imshow(matrix, vmin=0, vmax=1, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(BLOCKS)), [
        f"{condition.split('_')[0]}\n{start}–{end}" for condition, start, end in BLOCKS
    ])
    ax.set_xlabel("Condition and rounds")
    ax.set_yticks(range(len(models)), [short_name(s) for s in models])
    for i, line in enumerate(matrix):
        for j, val in enumerate(line):
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=9,
                    color="white" if val >= .56 else "#12283b")
    cax = fig.add_axes([.89, .29, .015, .43])
    fig.colorbar(pic, cax=cax)
    ax.tick_params(length=0)
    fig.text(.04, .95, "How closely did initial allocations match humans?", fontsize=16, weight="bold")
    fig.text(.04, .90, "Total variation distance across five allocation categories. Zero is an exact match.", fontsize=10)
    fig.text(.04, .045, "* Earlier Gemma runs with no explicit reasoning request (10 players per condition). "
             "Other rows have 20 per condition.", fontsize=9)
    fig.savefig(out, dpi=165, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def paired_plot(settings, framing, revisions, out):
    by_setting = {row["setting"]: row for row in framing}
    matched = {row["setting"]: row for row in revisions if row["condition"] == SUMMARY}
    fig, axes = plt.subplots(1, 2, sharey=True, figsize=(11, 7.0))
    fig.subplots_adjust(left=.28, right=.97, top=.76, bottom=.17, wspace=.16)
    for ax, left, right, first_label, second_label, title in (
        (axes[0], [by_setting[s]["share_4A"] for s in settings],
         [by_setting[s]["share_4P"] for s in settings], "4A", "4P", "Initial choices in rounds 1–4"),
        (axes[1], [matched[s]["share_initial_equal"] for s in settings],
         [matched[s]["share_final_equal"] for s in settings], "Before reveal", "After reveal", "Eligible choices in rounds 5–8"),
    ):
        y = list(range(len(settings)))
        for i, (a, b) in enumerate(zip(left, right)):
            ax.plot([a, b], [i, i], color="#7d8790", linewidth=1.5, zorder=2)
        ax.scatter(left, y, s=44, facecolor="white", edgecolor="#176283", linewidth=1.6, zorder=3)
        ax.scatter(right, y, s=21, color="#b84f23", marker="D", zorder=4)
        ax.set_xlim(-.035, 1.035)
        ax.set_xticks([0, .25, .5, .75, 1])
        ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
        ax.grid(axis="x", alpha=.22)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.set_title(title, loc="left", fontsize=11, weight="bold", pad=27)
        ax.legend(handles=[
            Line2D([], [], marker="o", linestyle="none", markerfacecolor="white",
                   markeredgecolor="#176283", label=first_label),
            Line2D([], [], marker="D", linestyle="none", color="#b84f23", markersize=4, label=second_label),
        ], loc="lower left", bbox_to_anchor=(0, 1.0), ncols=2, frameon=False,
                  borderaxespad=0, fontsize=9, handletextpad=.15)
    axes[0].set_yticks(range(len(settings)), [short_name(s) for s in settings])
    axes[0].invert_yaxis()
    fig.text(.04, .95, "How often did participants split the tickets 5/5?", fontsize=16, weight="bold")
    fig.text(.04, .90, "The left panel compares independent groups. The right panel follows the same eligible rounds and weights "
             "the four conditions equally.", fontsize=10)
    fig.text(.04, .055, "* Earlier Gemma runs with no explicit reasoning request. Coincident markers indicate equal rates.", fontsize=9)
    fig.savefig(out, dpi=165, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    samples = load_samples(ROOT)
    settings = ["Human", *sorted(set(samples).difference({"Human", EXTRA}))]
    if EXTRA in samples:
        settings.append(EXTRA)
    samples = {setting: samples[setting] for setting in settings}
    initial = initial_analysis(samples)
    framing = framing_analysis(initial)
    revisions = revision_analysis(samples)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT / "initial_choices.csv", initial)
    write_csv(OUTPUT / "framing.csv", framing)
    write_csv(OUTPUT / "revisions.csv", revisions)
    heatmap(settings, initial, OUTPUT / "tvd.png")
    paired_plot(settings, framing, revisions, OUTPUT / "framing_and_revisions.png")
    print(f"Compared {len(samples)-1} model settings with humans. Results: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
