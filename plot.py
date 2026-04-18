# type: ignore
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from numpy.typing import NDArray


def plot_elbow(k_values: range, inertia: list[float]) -> None:
    plt.figure(figsize=(8, 4))
    plt.plot(k_values, inertia, marker="o")
    plt.xlabel("Number of clusters (K)")
    plt.ylabel("Inertia")
    plt.title("Elbow Method — Finding the right K")
    plt.xticks(k_values)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("elbow_plot.png")
    print("Plot saved as elbow_plot.png")


def plot_clusters(
    coords: NDArray[np.float64],
    cluster_labels: pd.Series,
    cluster_map: dict[int, str],
    color_map: dict[int, str],
    title: str,
    filename: str,
) -> None:
    plt.figure(figsize=(9, 6))
    for cluster_id, label in cluster_map.items():
        mask = cluster_labels == cluster_id
        plt.scatter(
            coords[mask, 0],
            coords[mask, 1],
            c=color_map[cluster_id],
            label=label,
            alpha=0.6,
            s=40,
        )
    plt.title(title)
    plt.xlabel("PCA Component 1")
    plt.ylabel("PCA Component 2")
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename)
    print(f"Plot saved as {filename}")


def plot_feature_importance(importances: pd.Series) -> None:
    plt.figure(figsize=(7, 4))
    importances.sort_values().plot(
        kind="barh", color=["#4CAF50", "#2196F3", "#FF5722"]
    )
    plt.title("Feature Importances — What drives anomaly detection?")
    plt.xlabel("Importance score")
    plt.tight_layout()
    plt.savefig("feature_importance.png")
    print("Feature importance plot saved")