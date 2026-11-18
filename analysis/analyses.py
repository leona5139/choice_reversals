"""Experiment figures and summary tables."""
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from math import isnan, nan

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import FuncFormatter, MultipleLocator, PercentFormatter

from analysis.process_human_benchmark import load_human_players
from analysis.utils import (
    CATEGORIES, MODEL_FIELDS, SETUP_FIELDS, block_tvds, choice_distribution, complete_mean,
    equal_split_summary, group_rows, marginal_distribution, player_key, round_rows, write_csv,
)
from simulation.treatments import tasks_in

FIGURE_DPI = 320
COMPARISON_RED = "#a1421b"
LABELS = ["Over-\ncompensating", "Ex ante\nequalizing", "Mixed\n", "Ex post\nequalizing", "Reinforcing\n"]
CHOICE_FIELDS = ("treatment", "period", "category", "consistency",
                 "count", "percent", "n_players", "n_respondents", "n_choices")
REPORT_NAMES = {
    "anthropic/claude-haiku-5.5": "Haiku 5.5",
    "deepseek/deepseek-v4.1-flash-1017": "DeepSeek V4.1 Flash",
    "google/gemini-3.8-flash": "Gemini 3.8 Flash",
    "google/gemma-4-31b-it": "Gemma 4 31B",
    "openai/gpt-6-luna": "GPT-6 Luna",
    "qwen/qwen3.8-flash": "Qwen 3.8 Flash",
}
EARLIER_GEMMA = ("google/gemma-4-31b-it", 1, "default", "prompt_a", "milestone_2")


def setup_label(setup):
    provider, model, temperature, reasoning, prompt_version = setup
    return f"{provider} / {model} | t={temperature} | r={reasoning} | {prompt_version}"


def model_labels(setups, short=False):
    show_prompt = len({prompt for _, _, _, prompt, _ in setups}) > 1
    labels, settings = [], []
    for model, temp, reasoning, prompt, run in setups:
        label = f"{REPORT_NAMES.get(model, model)} ({reasoning})" if short else f"{model} · {reasoning}"
        if show_prompt:
            label += f" · {prompt or 'unknown prompt'}"
        labels.append(label)
        settings.append(" · ".join(filter(None, (run, f"temperature {temp}"))))
    if len(set(settings)) == 1:
        return labels, settings[0]
    return [f"{label}\n{setting}" for label, setting in zip(labels, settings)], ""


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
        n = len(SETUP_FIELDS)
        print(f"{setup_label(key[:n])} | {key[n]} {key[n + 1]}: "
              f"{len(choices)}/{len(group)} initial choices; "
              f"{record['changed_choices']}/{record['revision_opportunities']} revisions changed")
    return [write_csv(folder / "00_overview.csv", table)]


def draw_panel(ax, records, title, levels=None, frame="A"):
    ax.set_title(title, fontsize=11)
    ax.set_xticks(range(len(LABELS)), LABELS, fontsize=9, va="top")
    ax.set_ylim(0, 100)
    ax.set_ylabel("Choices (%)", fontsize=9)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="0.88", linewidth=0.6)
    ax.set_facecolor("0.94" if frame == "P" else "white")
    if not records or records[0]["n_choices"] == 0:
        ax.set_xlim(-0.6, len(CATEGORIES) - 0.4)
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
MAIN_TREATMENTS = ("2A2P_4AR", "2P2A_4AR", "4A_4AR", "4P_4AR")


def save_paper_figure(png, panels, figsize, top, legend_position):
    levels = sorted({0.25, 0.5, 0.75, 1.0} | {
        r["consistency"] for _, records in panels for r in records if r["consistency"] is not None
    })
    handles = [Patch(color=plt.cm.Greys(0.25 + 0.65 * level), label=f"{level:g}") for level in levels]
    labels = [category.replace("_", " ").title() for category in CATEGORIES]
    font = 12 if len(panels) == 2 else 14
    fig, axes = plt.subplots(1, len(panels), figsize=figsize, sharey=True)
    fig.subplots_adjust(left=0.07 if len(panels) == 2 else 0.06, right=0.992,
                        bottom=0.34, top=0.92, wspace=0.025)
    for ax, (title, records) in zip(axes, panels):
        draw_panel(ax, records, "", levels[::-1])
        ax.grid(False)
        ax.set_ylabel("")
        ax.set_xticks(range(len(labels)), labels, rotation=-90, fontsize=font)
        ax.tick_params(axis="y", labelsize=font)
        ax.add_patch(Rectangle((0, 1), 1, 0.11, transform=ax.transAxes, clip_on=False,
                               facecolor="0.81", edgecolor="black"))
        ax.text(0.5, 1.055, title, ha="center", va="center", transform=ax.transAxes, fontsize=font)
        ax.legend(handles=handles, title="Consistency", loc=legend_position, frameon=False,
                  fontsize=font - 1, title_fontsize=font, labelspacing=0.15, handlelength=1)
    highest_bar = max(ax.dataLim.ymax for ax in axes)
    axes[0].set_ylim(0, max(top, highest_bar * 1.05))
    axes[0].yaxis.set_major_locator(MultipleLocator(20))
    axes[0].yaxis.set_major_formatter(FuncFormatter(lambda percent, _: f"{percent / 100:.1f}"))
    axes[0].set_ylabel("Frequency", fontsize=font)
    fig.supxlabel("Choice category", y=0.015, fontsize=font)
    fig.savefig(png, dpi=FIGURE_DPI)
    plt.close(fig)


def figure_1_choices(rows, by=()):
    selected = [{**r, "period": "1-4"} for r in rows
                if r["treatment"] in FIG1_TREATMENTS and r["round"] <= 4]
    return choice_distribution(selected, with_consistency=True, by=by)


def save_figure_1(table, png, suptitle, by=()):
    if not by:
        panels = [(title, [r for r in table if r["treatment"] == treatment])
                  for title, treatment in zip(("Panel A: Ex Ante Frame", "Panel B: Ex Post Frame"), FIG1_TREATMENTS)]
        save_paper_figure(png, panels, (11, 6.4), 67, "upper right")
        return
    levels = sorted({r["consistency"] for r in table if r["consistency"] is not None})
    groups = group_rows(table, by)
    labels, settings = model_labels(groups)
    fig, axes = plt.subplots(len(groups), 2, figsize=(11, 2.8 * len(groups)), squeeze=False,
                             layout="constrained")
    fig.suptitle(f"{suptitle}\n{settings}".rstrip(), fontsize=14)
    for index, (label, group) in enumerate(zip(labels, groups.values())):
        for col, treatment in enumerate(FIG1_TREATMENTS):
            records = [r for r in group if r["treatment"] == treatment]
            n = records[0]["n_choices"] if records else 0
            title = f"{label}\n{treatment} | {n} choices"
            draw_panel(axes[index, col], records, title, levels, frame="A" if col == 0 else "P")
    handles = [Patch(facecolor=plt.cm.Greys(0.25 + 0.65 * level), label=f"{level:.0%}") for level in levels]
    fig.legend(handles=handles, title="Consistency within rounds 1–4", loc="outside lower center", ncol=4)
    fig.savefig(png, dpi=FIGURE_DPI)
    plt.close(fig)


def figure_1(rows, folder, by_model=False):
    by = MODEL_FIELDS if by_model else ()
    stem = "04_fig1_by_model" if by_model else "01_fig1_choices"
    table = figure_1_choices(rows, by)
    files = [write_csv(folder / f"{stem}.csv", table, (*by, *CHOICE_FIELDS))]
    png = folder / f"{stem}.png"
    if not table:
        png.unlink(missing_ok=True)
        label = "Figure 1 by model" if by_model else "Figure 1"
        print(f"{label}: no data for 4A_4AR or 4P_4AR.")
        return files
    save_figure_1(table, png, "Figure 1. Initial choices by model (rounds 1–4)", by)
    return files + [png]


def figure_1_by_model(rows, folder):
    return figure_1(rows, folder, by_model=True)


FIG3_PANELS = (
    ("initial", "initial_category", "Initial"),
    ("final", "revision_category", "Final"),
    ("changes", "revision_category", "Final (changes only)"),
)
FIG3_FIELDS = ("panel", "category", "consistency", "count", "percent",
               "n_players", "n_respondents", "n_choices")


def figure_3(rows, folder, by_model=False):
    """Pool rounds 5–8 of the four main treatments, as in the authors' plots.R."""
    selected = [r for r in rows if r["treatment"] in MAIN_TREATMENTS and 5 <= r["round"] <= 8]
    by = MODEL_FIELDS if by_model else ()
    groups = group_rows(selected, by) if by else {(): selected}
    table = []
    for setup, group in groups.items():
        offers = [r for r in group if r["revision_offered"]]
        for panel, field, _title in FIG3_PANELS:
            source = group if panel == "initial" else offers
            table.extend({**dict(zip(by, setup)), "panel": panel, **record}
                         for record in marginal_distribution(source, field, changes_only=panel == "changes"))
    stem = "05_fig3_by_model" if by_model else "03_fig3_revisions"
    files = [write_csv(folder / f"{stem}.csv", table, (*by, *FIG3_FIELDS))]
    png = folder / f"{stem}.png"
    if not selected:
        png.unlink(missing_ok=True)
        print("Figure 3: no rounds 5–8 for the four main treatments.")
        return files
    if not by_model:
        panels = [(title, [r for r in table if r["panel"] == panel]) for panel, _, title in FIG3_PANELS]
        save_paper_figure(png, panels, (15, 7.5), 86, "best")
        return files + [png]
    levels = sorted({r["consistency"] for r in table if r["consistency"] is not None})
    panel_groups = group_rows(table, by)
    labels, settings = model_labels(panel_groups)
    fig, axes = plt.subplots(len(panel_groups), 3, figsize=(15, 2.8 * len(panel_groups)), squeeze=False,
                             layout="constrained")
    fig.suptitle(f"Figure 3. Original and final choices by model (all treatments, rounds 5–8)\n{settings}".rstrip(),
                 fontsize=14)
    for row, (label, group) in enumerate(zip(labels, panel_groups.values())):
        for col, (panel, _field, title) in enumerate(FIG3_PANELS):
            records = [r for r in group if r["panel"] == panel]
            title = f"{label}\n{title} | {records[0]['n_choices']} choices"
            draw_panel(axes[row, col], records, title, levels)
    handles = [Patch(facecolor=plt.cm.Greys(0.25 + 0.65 * level), label=f"{level:.0%}") for level in levels]
    fig.legend(handles=handles, title="Consistency", loc="outside lower center", ncol=4)
    fig.savefig(png, dpi=FIGURE_DPI)
    plt.close(fig)
    return files + [png]


def figure_3_by_model(rows, folder):
    return figure_3(rows, folder, by_model=True)


def figure_2(rows, folder):
    periods = ("1-2", "3-4", "5-8")
    selected = [r for r in rows if r["treatment"] in MAIN_TREATMENTS]
    table = choice_distribution(selected)
    files = [write_csv(folder / "02_fig2_choices.csv", table, CHOICE_FIELDS)]
    png = folder / "02_fig2_choices.png"
    if not table:
        png.unlink(missing_ok=True)
        print("Figure 2: no data for the four main treatments.")
        return files
    fig, axes = plt.subplots(4, 3, figsize=(15, 12), squeeze=False)
    fig.suptitle("Figure 2: Initial choices across treatment sequences", fontsize=14)
    for row, treatment in enumerate(MAIN_TREATMENTS):
        for col, period in enumerate(periods):
            records = [r for r in table if r["treatment"] == treatment and r["period"] == period]
            n = records[0]["n_choices"] if records else 0
            frame = "P" if tasks_in(treatment)[int(period[0]) - 1] == "P" else "A"
            title = f"{treatment} | rounds {period} | {frame}\n{n} choices"
            draw_panel(axes[row, col], records, title, frame=frame)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(png, dpi=FIGURE_DPI)
    plt.close(fig)
    return files + [png]


BLOCKS_12 = [(t, p) for t in MAIN_TREATMENTS for p in ("1-2", "3-4", "5-8")]
BLOCKS_6 = [(t, "1-4") for t in FIG1_TREATMENTS] + [(t, "5-8") for t in MAIN_TREATMENTS]


def initial_counts(rows):
    eligible = [r for r in rows if 1 <= r["round"] <= 8
                and (r["task"] != "P" or r["draw_group"] == "participant")]
    counts = defaultdict(Counter)
    for entry in choice_distribution(eligible):
        counts[entry["treatment"], entry["period"]][entry["category"]] = entry["count"]
    for treatment in FIG1_TREATMENTS:
        counts[treatment, "1-4"] = counts[treatment, "1-2"] + counts[treatment, "3-4"]
    return counts


def save_tvd_heatmap(path, setups, blocks, scores):
    fig, ax = plt.subplots(figsize=(4.4 + 0.7 * len(blocks), 2.2 + 0.4 * len(setups)), layout="constrained")
    reds = LinearSegmentedColormap.from_list("comparison_red", ["#fff8f5", COMPARISON_RED])
    image = ax.imshow(scores, aspect="auto", cmap=reds.with_extremes(bad="0.9"),
                      interpolation="nearest", vmin=0, vmax=1)
    fig.suptitle(f"Initial choices vs. humans · {len(blocks)} blocks", fontsize=15)
    labels, settings = model_labels(setups)
    if settings:
        ax.set_title(settings, loc="left", fontsize=10)
    ax.set_yticks(range(len(setups)), labels, fontsize=10)
    ax.set_ylabel("Model setting")
    ax.set_xticks(range(len(blocks)), [f"{t.split('_')[0]}\n{p.replace('-', '–')}" for t, p in blocks], fontsize=10)
    ax.set_xlabel("Treatment and rounds")
    ax.tick_params(length=0, pad=5)
    for i, row in enumerate(scores):
        for j, value in enumerate(row):
            ax.text(j, i, "—" if isnan(value) else f"{value:.2f}", ha="center", va="center",
                    color="white" if value >= 0.84 else "black", fontsize=10)
    fig.colorbar(image, ax=ax, shrink=0.75, label="TVD (lower is closer)")
    fig.supxlabel("Five-category TVD = ½ Σ |model share − human share|  ·  Human data from Andreoni et al. (2020)",
                  fontsize=9)
    fig.savefig(path, dpi=FIGURE_DPI)
    plt.close(fig)


def initial_choice_tvd(rows, folder):
    humans = initial_counts(round_rows(load_human_players()))
    models = {setup: initial_counts(group) for setup, group in group_rows(rows, MODEL_FIELDS).items()}
    files = []
    for blocks in (BLOCKS_12, BLOCKS_6):
        table, scores = [], []
        for setup, counts in models.items():
            row_scores = []
            for (treatment, period), distance in block_tvds(counts, humans, blocks).items():
                model = counts[treatment, period]
                human = humans[treatment, period]
                row_scores.append(nan if distance is None else distance)
                table.append({
                    **dict(zip(MODEL_FIELDS, setup)), "treatment": treatment, "period": period,
                    "model_choices": model.total(), "human_choices": human.total(), "tvd": distance,
                    **{f"model_{c}": model[c] for c in CATEGORIES},
                    **{f"human_{c}": human[c] for c in CATEGORIES},
                })
            scores.append(row_scores)
        stem = f"06_tvd_{len(blocks)}_blocks"
        files.append(write_csv(folder / f"{stem}.csv", table))
        png = folder / f"{stem}.png"
        save_tvd_heatmap(png, models, blocks, scores)
        files.append(png)
    return files


def comparison_groups(rows):
    humans = group_rows(round_rows(load_human_players()), MODEL_FIELDS)
    return humans | group_rows(rows, MODEL_FIELDS)


def framing_row(setup, rows):
    initial = [r for r in rows if 1 <= r["round"] <= 4 and r["initial_a"] is not None]
    a = [r["initial_a"] for r in initial if r["treatment"] == "4A_4AR"]
    p = [r["initial_a"] for r in initial if r["treatment"] == "4P_4AR" and r["draw_group"] == "participant"]
    return equal_split_summary(setup, ("4A · ex ante", a), ("4P · ex post", p))


def revision_rows(setup, rows):
    offers = [r for r in rows if 5 <= r["round"] <= 8 and r["revision_offered"]
              and r["initial_a"] is not None and r["revision_a"] is not None]
    table = []
    for treatment in MAIN_TREATMENTS:
        group = [r for r in offers if r["treatment"] == treatment]
        before = [r["initial_a"] for r in group]
        after = [r["revision_a"] for r in group]
        row = equal_split_summary(setup, ("Before reveal", before), ("After revision offer", after))
        changed = sum(a != b for a, b in zip(before, after))
        to_even = sum(a != 5 and b == 5 for a, b in zip(before, after))
        row.update(treatment=treatment, changed_choices=changed, moved_to_5_5=to_even,
                   moved_from_5_5=sum(a == 5 and b != 5 for a, b in zip(before, after)),
                   changed_percent=100 * changed / len(group) if group else None,
                   percent_of_changes_to_5_5=100 * to_even / changed if changed else None)
        table.append(row)

    summary = {**table[0], "treatment": "equal_treatment_mean"}
    for key in ("first_choices", "second_choices", "first_5_5", "second_5_5",
                "changed_choices", "moved_to_5_5", "moved_from_5_5"):
        summary[key] = sum(row[key] for row in table)
    for key in ("first_percent", "second_percent", "change_pp", "changed_percent", "percent_of_changes_to_5_5"):
        summary[key] = complete_mean(row[key] for row in table)
    return [*table, summary]


def equal_split_frames(rows, folder):
    frames = [framing_row(setup, group) for setup, group in comparison_groups(rows).items()]
    return [write_csv(folder / "07_5_5_frames.csv", frames)]


def equal_split_revisions(rows, folder):
    frames, revisions = [], []
    for setup, group in comparison_groups(rows).items():
        frames.append(framing_row(setup, group))
        revisions.extend(revision_rows(setup, group))
    csv = write_csv(folder / "08_5_5_revisions.csv", revisions)
    means = [r for r in revisions if r["treatment"] == "equal_treatment_mean"]
    labels, settings = model_labels([tuple(r[k] for k in MODEL_FIELDS) for r in frames[1:]], short=True)
    fig, axes = plt.subplots(1, 2, sharey=True, figsize=(11.5, 1.7 + 0.38 * len(frames)), layout="constrained")
    fig.suptitle("Equal (5/5) allocations", fontsize=15)
    y = range(len(frames))
    for ax, table, title in zip(axes, (frames, means), ("Initial choices · rounds 1–4", "Revision offers · rounds 5–8")):
        ax.set_title(title, loc="left", fontsize=12)
        ax.axhspan(-0.45, 0.45, color="#eaf2f5", zorder=0)
        for i, row in enumerate(table):
            ax.plot([row["first_percent"], row["second_percent"]], [i, i], color="0.64", lw=2)
        for stage, marker, size, fill, edge in (("first", "o", 9, "white", "#234f67"),
                                              ("second", "D", 5, COMPARISON_RED, COMPARISON_RED)):
            ax.plot([r[f"{stage}_percent"] for r in table], y, linestyle="none", marker=marker,
                    markersize=size, markerfacecolor=fill, markeredgecolor=edge, markeredgewidth=1.4,
                    label=table[0][f"{stage}_stage"])
        ax.set_xlim(-3, 103)
        ax.set_xticks(range(0, 101, 25))
        ax.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
        ax.grid(axis="x", color="0.9")
        ax.set_axisbelow(True)
        ax.tick_params(axis="y", length=0)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.09), ncols=2, frameon=False)
    axes[0].set_yticks(y, ["Human benchmark", *labels])
    axes[0].get_yticklabels()[0].set_weight("bold")
    axes[0].set_ylim(len(frames) - 0.5, -0.5)
    caption = "Revision rates give each treatment 25% weight"
    fig.supxlabel("  ·  ".join(filter(None, (caption, settings))), fontsize=9)
    png = folder / "08_5_5_framing_and_revisions.png"
    fig.savefig(png, dpi=FIGURE_DPI)
    plt.close(fig)
    return [csv, png]


REPORT_RATES = ("initial_4a_5_5_percent", "initial_4p_5_5_percent", "before_5_5_percent",
                "after_5_5_percent", "changed_percent")


def write_summary_tex(path, rows):
    def number(value, unit):
        if value is None:
            return "---"
        return str(Decimal(str(value)).quantize(Decimal(unit), rounding=ROUND_HALF_UP))

    escapes = str.maketrans({c: "\\" + c for c in "&%$#_{}"} | {
        "\\": r"\textbackslash{}", "^": r"\textasciicircum{}", "~": r"\textasciitilde{}",
    })
    labels, _ = model_labels([tuple(r[k] for k in MODEL_FIELDS) for r in rows[1:]], short=True)
    lines = [r"\begin{tabular}{@{}lrrrrrr@{}}\toprule",
             r" & Mean & \multicolumn{2}{c}{Initial 5/5 (\%)} & \multicolumn{3}{c}{Eligible rounds 5--8 (\%)}\\",
             r"\cmidrule(lr){3-4}\cmidrule(l){5-7}",
             r"Setting & TVD & 4A & 4P & 5/5 before & 5/5 after & Changed\\\midrule"]
    for row, label in zip(rows, ["Human benchmark", *labels]):
        label = label.translate(escapes)
        if "\n" in label:
            label = r"\shortstack[l]{" + label.replace("\n", r"\\") + "}"
        human = row["sample"] == "human"
        tvd = "ref." if human else number(row["mean_tvd"], ".001")
        cells = [label, tvd, *(number(row[key], ".1") for key in REPORT_RATES)]
        line = " & ".join(cells) + r" \\"
        if row["sample"] == "earlier":
            lines.extend([r"\ifdefined\plannedonly\else", r"\midrule", line, r"\fi"])
        else:
            lines.append(line)
        if human:
            lines.append(r"\midrule")
    path.write_text("\n".join([*lines, r"\bottomrule\end{tabular}", ""]), encoding="utf-8")
    return path


def comparison_tables(rows, folder):
    groups = comparison_groups(rows)
    benchmark = next(iter(groups))
    human_counts = initial_counts(groups[benchmark])
    samples = {benchmark: "human", EARLIER_GEMMA: "earlier"}
    tables = {6: [], 12: []}
    for setup, group in groups.items():
        frame = framing_row(setup, group)
        revision = revision_rows(setup, group)[-1]
        counts = human_counts if setup == benchmark else initial_counts(group)
        for blocks in (BLOCKS_6, BLOCKS_12):
            tables[len(blocks)].append({
                **dict(zip(MODEL_FIELDS, setup)), "sample": samples.get(setup, "main"),
                "mean_tvd": complete_mean(block_tvds(counts, human_counts, blocks).values()),
                "initial_4a_5_5_percent": frame["first_percent"], "initial_4p_5_5_percent": frame["second_percent"],
                "before_5_5_percent": revision["first_percent"], "after_5_5_percent": revision["second_percent"],
                "changed_percent": revision["changed_percent"],
            })
    files = []
    for size, table in tables.items():
        table.sort(key=lambda r: (r["sample"] != "human", r["sample"] == "earlier", r["model"], r["reasoning"] != "off"))
        stem = f"09_summary_{size}_blocks"
        files.append(write_csv(folder / f"{stem}.csv", table))
        files.append(write_summary_tex(folder / f"{stem}.tex", table))
    return files
