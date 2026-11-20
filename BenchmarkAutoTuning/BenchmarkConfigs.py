import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

files = sorted(glob.glob("tuningData_FallingDrop*.csv"))
assert len(files) == 5, f"Found {len(files)} files instead of 5!"

config_cols = [
    "Interaction Type",
    "Container",
    "CellSizeFactor",
    "Traversal",
    "Load Estimator",
    "Data Layout",
    "Newton 3",
    "VectorizationPattern",
]

sample_cols = [
    "rebuildSample 0",
    "rebuildSample 1",
    "rebuildSample 2",
    "traverseInteractionSample 0",
    "traverseInteractionSample 1",
    "traverseInteractionSample 2",
]

file_dfs = []
for f in files:
    df = pd.read_csv(f)
    clean_samples = df[sample_cols].replace(-1, 0)
    df["row_avg_ms"] = (clean_samples.sum(axis=1) / 3.0) / 1e6
    df["tuning_phase"] = (df["Iteration"] // 10000) * 10000
    per_config = df.groupby(config_cols + ["tuning_phase"], as_index=False)["row_avg_ms"].mean()
    file_dfs.append(per_config)

final_df = (
    pd.concat(file_dfs, ignore_index=True)
    .groupby(config_cols + ["tuning_phase"], as_index=False)["row_avg_ms"]
    .mean()
    .rename(columns={"row_avg_ms": "avg_time_ms"})
)

for phase, group in final_df.groupby("tuning_phase"):
    phase_sum_s = group["avg_time_ms"].sum() / 1000.0
    print(f"Tuning Phase {phase}+: Total time across all configurations = {phase_sum_s:.3f} s")

phases = sorted(final_df["tuning_phase"].unique())
bins = np.linspace(0, 45, 46)
x_grid = np.linspace(0, 45, 400)

for phase in phases:
    phase_df = final_df[final_df["tuning_phase"] == phase]
    subset = phase_df[
        (phase_df["avg_time_ms"] >= 0) & (phase_df["avg_time_ms"] < 45)
    ]["avg_time_ms"]

    fig, ax = plt.subplots(figsize=(7.5, 4.5))

    ax.hist(subset, bins=bins, density=True, color="#4C72B0", alpha=0.22, edgecolor="#4C72B0", linewidth=0.6)

    kde = gaussian_kde(subset, bw_method=0.22)
    y_kde = kde(x_grid)
    ax.plot(x_grid, y_kde, color="#2B4C7E", linewidth=2.2, label="Density Curve (KDE)")
    ax.fill_between(x_grid, y_kde, color="#4C72B0", alpha=0.18)

    ax.plot(subset, np.zeros_like(subset) - 0.003, "|", color="#1F365C", alpha=0.55, markersize=8)

    median_val = subset.median()
    ax.axvline(median_val, color="#D95F02", linestyle="--", linewidth=1.6, label=f"Median: {median_val:.2f} ms")

    ax.set_title(
        f"Configuration Runtime Distribution — Tuning Phase {phase}+\n(n = {len(subset)} configurations)",
        fontsize=12,
        fontweight="bold",
        pad=12,
    )
    ax.set_xlabel("Average Time [ms]", fontsize=10.5)
    ax.set_ylabel("Probability Density", fontsize=10.5)
    ax.set_xlim(0, 45)
    ax.set_ylim(bottom=-0.006)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(frameon=True, facecolor="white", framealpha=0.9)

    plt.tight_layout()
    plt.savefig(f"autopas_tuning_phase_FallingDrop_{phase}.png", dpi=300)
    plt.close()