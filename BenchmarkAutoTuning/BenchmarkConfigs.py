from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

# IEEE-optimierte Schriftgrößen (ca. 15-20 % kleiner für exakte Passung zum Fließtext)
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 10,
    "axes.labelsize": 11,
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "legend.fontsize": 9.5,
})

BASE_DIR = Path(__file__).resolve().parent

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


def analyze_tuning_dataset(
    folder: Path,
    file_pattern: str,
    output_prefix: str,
    label: str,
    expected_files: int = 5,
    cutoff_ms: float = 120.0,
):
    files = sorted(folder.glob(file_pattern))
    assert len(files) == expected_files, (
        f"[{label}] Found {len(files)} files in '{folder}' instead of {expected_files}!"
    )

    print(f"\n{'=' * 80}")
    print(f"Evaluation: {label} | Folder: {folder.name}/ ({len(files)} files)")
    print(f"{'=' * 80}")

    file_dfs = []
    for f in files:
        df = pd.read_csv(f)
        # -1 bedeutet "Sample nicht ausgeführt" -> 0 ns, alle ausgeführten Samples addieren
        clean_samples = df[sample_cols].replace(-1, 0)
        df["row_test_time_ms"] = clean_samples.sum(axis=1) / 1e6
        df["tuning_phase"] = (df["Iteration"] // 10000) * 10000

        per_config = df.groupby(config_cols + ["tuning_phase"], as_index=False)["row_test_time_ms"].sum()
        file_dfs.append(per_config)

    # Über alle Runs (Files) pro Konfiguration und Tuning-Phase mitteln
    final_df = (
        pd.concat(file_dfs, ignore_index=True)
        .groupby(config_cols + ["tuning_phase"], as_index=False)["row_test_time_ms"]
        .mean()
        .rename(columns={"row_test_time_ms": "test_time_ms"})
    )

    for phase, group in final_df.groupby("tuning_phase"):
        filtered = group[(group["test_time_ms"] >= 0) & (group["test_time_ms"] < cutoff_ms)]
        total_sum_s = group["test_time_ms"].sum() / 1000.0
        filtered_sum_s = filtered["test_time_ms"].sum() / 1000.0
        n_total = len(group)
        n_filtered = len(filtered)
        n_outliers = n_total - n_filtered

        print(
            f"Tuning Phase {phase}+: Total tuning time = {total_sum_s:.3f} s (n = {n_total}) | "
            f"Filtered (< {cutoff_ms:.0f} ms) = {filtered_sum_s:.3f} s (n = {n_filtered}, excluded: {n_outliers})"
        )

    phases = sorted(final_df["tuning_phase"].unique())
    bins = np.linspace(0, cutoff_ms, 61)  # 2-ms-Bins bei cutoff_ms = 120.0
    x_grid = np.linspace(0, cutoff_ms, 400)

    for phase in phases:
        phase_df = final_df[final_df["tuning_phase"] == phase]
        subset = phase_df[
            (phase_df["test_time_ms"] >= 0) & (phase_df["test_time_ms"] < cutoff_ms)
        ]["test_time_ms"]

        fig, ax = plt.subplots(figsize=(4.8, 2.8))

        ax.hist(
            subset,
            bins=bins,
            density=True,
            color="#4C72B0",
            alpha=0.22,
            edgecolor="#4C72B0",
            linewidth=0.8,
        )

        if len(subset) > 1 and subset.nunique() > 1:
            kde = gaussian_kde(subset, bw_method=0.22)
            y_kde = kde(x_grid)
            ax.plot(x_grid, y_kde, color="#2B4C7E", linewidth=2.2, label="Density Curve (KDE)")
            ax.fill_between(x_grid, y_kde, color="#4C72B0", alpha=0.18)

        ax.plot(subset, np.zeros_like(subset) - 0.001, "|", color="#1F365C", alpha=0.55, markersize=8)

        median_val = subset.median()
        ax.axvline(
            median_val,
            color="#D95F02",
            linestyle="--",
            linewidth=1.8,
            label=f"Median: {median_val:.2f} ms",
        )

        ax.set_xlabel("Testing Time per Configuration [ms]")
        ax.set_ylabel("Probability Density")
        ax.set_xlim(0, cutoff_ms)
        ax.set_ylim(bottom=-0.002)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.legend(frameon=True, facecolor="white", framealpha=0.9, loc="upper right")

        plt.tight_layout()
        output_path = folder / f"{output_prefix}_{phase}.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight", pad_inches=0.03)
        plt.close()


if __name__ == "__main__":
    datasets = [
        {
            "folder": BASE_DIR / "FullSearch",
            "file_pattern": "*Data*.csv",
            "output_prefix": "autopas_tuning_phase_FallingDrop",
            "label": "FallingDrop (FullSearch)",
        },
        {
            "folder": BASE_DIR / "Reduced",
            "file_pattern": "*Data*.csv",
            "output_prefix": "autopas_tuning_phase_FallingDrop_Reduced",
            "label": "FallingDrop (Reduced)",
        },
    ]

    for ds in datasets:
        analyze_tuning_dataset(
            folder=ds["folder"],
            file_pattern=ds["file_pattern"],
            output_prefix=ds["output_prefix"],
            label=ds["label"],
            expected_files=5,
            cutoff_ms=120.0,
        )