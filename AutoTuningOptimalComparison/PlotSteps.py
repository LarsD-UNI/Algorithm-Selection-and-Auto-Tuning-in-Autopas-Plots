import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams.update({
    "font.size": 12,
    "axes.labelsize": 13,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "legend.fontsize": 11,
    "lines.linewidth": 2.0,
})

step_size = 100
max_iteration = 10000

ieee_figsize = (7, 3.8)

dateien = [
    {
        "pfad": "FDLinkedCells.csv",
        "label": "Linked Cells",
        "color": "#1f77b4",  # Blau
    },
    {
        "pfad": "FDVerletClusterList.csv",
        "label": "Verlet Cluster Lists",
        "color": "#ff7f0e",  # Orange
    },
]

ausgabe_vergleich_png = "performance_vergleich.png"
ausgabe_optimal_png = "performance_optimal.png"

grouped_dfs = {}

for daten in dateien:
    df = pd.read_csv(daten["pfad"])

    df = df[df["Iteration"] < max_iteration].copy()

    df["Dauer_ms"] = df["computeInteractionsTotal[ns]"] / 1e6
    df["Block"] = (df["Iteration"] // step_size) * step_size

    grouped = (
        df.groupby("Block")["Dauer_ms"]
        .sum()
        .reset_index()
        .rename(columns={"Dauer_ms": daten["label"]})
    )

    grouped_dfs[daten["label"]] = grouped

label1 = dateien[0]["label"]
label2 = dateien[1]["label"]

df_combined = pd.merge(
    grouped_dfs[label1], grouped_dfs[label2], on="Block", how="inner"
)

df_combined["Optimal"] = df_combined[[label1, label2]].min(axis=1)

marker_size = 3 if step_size <= 100 else 6

gesamtdauer_l1_s = df_combined[label1].sum() / 1000.0
gesamtdauer_l2_s = df_combined[label2].sum() / 1000.0
gesamtdauer_opt_s = df_combined["Optimal"].sum() / 1000.0

y_max = df_combined[[label1, label2]].max().max() * 1.30

plt.figure(figsize=ieee_figsize)

plt.plot(
    df_combined["Block"],
    df_combined[label1],
    marker="o",
    markersize=marker_size,
    linestyle="-",
    linewidth=1.5,
    color=dateien[0]["color"],
    label=f"{label1} (Total: {gesamtdauer_l1_s:.2f} s)",
)
plt.plot(
    df_combined["Block"],
    df_combined[label2],
    marker="o",
    markersize=marker_size,
    linestyle="-",
    linewidth=1.5,
    color=dateien[1]["color"],
    label=f"{label2} (Total: {gesamtdauer_l2_s:.2f} s)",
)

plt.xlabel(f"Start Iteration ({step_size}-Iteration Blocks)", labelpad=6)
plt.ylabel("Execution Time per Block (ms)", labelpad=6)
plt.xlim(0, max_iteration)
plt.ylim(100, y_max+100)
plt.grid(True, linestyle="--", alpha=0.6)
plt.legend(loc="upper left", frameon=True, framealpha=0.9)
plt.tight_layout()
plt.savefig(ausgabe_vergleich_png, dpi=300)
plt.close()

plt.figure(figsize=ieee_figsize)

plt.plot(
    df_combined["Block"],
    df_combined[label1],
    linestyle="--",
    linewidth=1.5,
    color=dateien[0]["color"],
    alpha=0.45,
    label=f"{label1} (Total: {gesamtdauer_l1_s:.2f} s)",
)
plt.plot(
    df_combined["Block"],
    df_combined[label2],
    linestyle="--",
    linewidth=1.5,
    color=dateien[1]["color"],
    alpha=0.45,
    label=f"{label2} (Total: {gesamtdauer_l2_s:.2f} s)",
)

# Optimale Trajektorie hervorgehoben
plt.plot(
    df_combined["Block"],
    df_combined["Optimal"],
    marker="o",
    markersize=marker_size,
    linestyle="-",
    linewidth=1.5,
    color="#2ca02c",  # Grün
    label=f"Dynamic Tuning (Total: {gesamtdauer_opt_s:.2f} s)",
)

plt.xlabel(f"Start Iteration ({step_size}-Iteration Blocks)", labelpad=6)
plt.ylabel("Execution Time per Block (ms)", labelpad=6)
plt.xlim(0, max_iteration)
plt.ylim(100, y_max+100)
plt.grid(True, linestyle="--", alpha=0.6)
plt.legend(loc="upper left", frameon=True, framealpha=0.9)
plt.tight_layout()
plt.savefig(ausgabe_optimal_png, dpi=300)
plt.close()

best_single_s = min(gesamtdauer_l1_s, gesamtdauer_l2_s)
rel_savings = (1 - (gesamtdauer_opt_s / best_single_s)) * 100

print(f"1. Comparison plot saved: '{ausgabe_vergleich_png}'")
print(f"2. Optimal path plot saved: '{ausgabe_optimal_png}'")
print("-" * 55)
print(f"Total time {label1} (0-{max_iteration}): {gesamtdauer_l1_s:.2f} s")
print(f"Total time {label2} (0-{max_iteration}): {gesamtdauer_l2_s:.2f} s")
print(
    f"Optimal total time:       {gesamtdauer_opt_s:.2f} s "
    f"(-{rel_savings:.2f}% vs. best single algorithm)"
)