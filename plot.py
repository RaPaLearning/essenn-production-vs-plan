# type: ignore
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from numpy.typing import NDArray
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

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

def run_classification(
    features_scaled: NDArray[np.float64],
    y: pd.Series,
) -> None:
    X_train, X_test, y_train, y_test = train_test_split(
        features_scaled, y, test_size=0.2, random_state=42
    )
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)
    y_pred = rf.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=["Normal", "Problem", "Setup heavy"]))

    importances: pd.Series = pd.Series(
        rf.feature_importances_,
        index=["Setting Time Min", "Acp Qty", "Duration Min"],
    )
    print("\nFeature importances:")
    print(importances.sort_values(ascending=False).round(3))
    plot_feature_importance(importances)