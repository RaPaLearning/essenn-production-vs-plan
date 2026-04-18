import pandas as pd
import numpy as np
from numpy.typing import NDArray
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from data_loader import load_production_report
from plot import plot_elbow, plot_clusters, plot_feature_importance

# Load and prepare
df: pd.DataFrame = load_production_report()

print(df.shape)
print(df.columns.tolist())

# Feature engineering
df["Duration Min"] = (
    df["End Time"] - df["Start Time"]
).dt.total_seconds() / 60

features: pd.DataFrame = df[["Setting Time Min", "Acp Qty", "Duration Min"]]
print(features.describe())
print(features.isnull().sum())

features = features.fillna(features.median())
print("Nulls after filling:", features.isnull().sum().sum())

# Scale
scaler = StandardScaler()
features_scaled: NDArray[np.float64] = scaler.fit_transform(features)
print("Scaled shape:", features_scaled.shape)

# Elbow method
inertia: list[float] = []
k_values = range(1, 11)
for k in k_values:
    km = KMeans(n_clusters=k, random_state=42, n_init="auto")
    km.fit(features_scaled)
    inertia.append(float(km.inertia_))
plot_elbow(k_values, inertia)

# KMeans with K=3
km = KMeans(n_clusters=3, random_state=42, n_init="auto")
df["Cluster"] = km.fit_predict(features_scaled)
print(df["Cluster"].value_counts())
print(
    df.groupby("Cluster")[["Setting Time Min", "Acp Qty", "Duration Min"]]
    .mean()
    .round(2)
)

# Investigate problem cluster
cluster1: pd.DataFrame = df[df["Cluster"] == 1]
print("Machines with most problem runs:")
print(cluster1["Machine No"].value_counts().head(10))
print("\nOperators with most problem runs:")
print(cluster1["Operator"].value_counts().head(10))
print("\nProblem runs by shift:")
print(cluster1["Shift"].value_counts())
print("\nDown time reasons:")
print(cluster1["Down Time Reason"].value_counts().head(10))

# PCA for visualization
pca = PCA(n_components=2)
coords: NDArray[np.float64] = pca.fit_transform(features_scaled)

# Plot KMeans clusters
plot_clusters(
    coords=coords,
    cluster_labels=df["Cluster"],
    cluster_map={0: "Normal (Cluster 0)", 1: "Problem runs (Cluster 1)", 2: "Setup heavy (Cluster 2)"},
    color_map={0: "green", 1: "red", 2: "orange"},
    title="KMeans Clusters — Production Runs",
    filename="clusters_plot.png",
)

# DBSCAN anomaly detection
dbscan = DBSCAN(eps=0.5, min_samples=5)
df["DBSCAN_Cluster"] = dbscan.fit_predict(features_scaled)
print("DBSCAN cluster counts:")
print(df["DBSCAN_Cluster"].value_counts().sort_index())

anomalies: pd.DataFrame = df[df["DBSCAN_Cluster"] == -1]
print(f"\nAnomalies found: {len(anomalies)} out of {len(df)} runs")
print(f"That's {round(len(anomalies) / len(df) * 100, 1)}% of all runs")
print("\nAnomaly averages:")
print(anomalies[["Setting Time Min", "Acp Qty", "Duration Min"]].mean().round(2))

# Plot DBSCAN
plot_clusters(
    coords=coords,
    cluster_labels=df["DBSCAN_Cluster"],
    cluster_map={-1: "Anomaly", 0: "Normal", 1: "Small cluster"},
    color_map={-1: "red", 0: "green", 1: "orange"},
    title="DBSCAN — Anomaly Detection on Production Runs",
    filename="dbscan_plot.png",
)

# Classification
X: NDArray[np.float64] = features_scaled
y: pd.Series = df["Cluster"]
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
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