import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import matplotlib.pyplot as plt
from numpy.typing import NDArray

# Load the data
df = pd.read_excel("data/sample/DailyProductionReport_17032026.xlsx")

df["Date"] = pd.to_datetime(df["Date"], format="%Y%m%d")
df["Start Time"] = pd.to_datetime(df["Start Time"], format="%d-%m-%Y %H:%M:%S")
df["End Time"] = pd.to_datetime(df["End Time"], format="%d-%m-%Y %H:%M:%S")
df = df.dropna(axis="columns", how="all")

print(df.shape)
print(df.columns.tolist())

df["Duration Min"] = (df["End Time"] - df["Start Time"]).dt.total_seconds() / 60

features = df[["Setting Time Min", "Acp Qty", "Duration Min"]]

print(features.describe())
print(features.isnull().sum())

# Filling the nulls
features = features.fillna(features.median())

print("Nulls after filling:", features.isnull().sum().sum())


# Standardizing
scaler = StandardScaler()
features_scaled: NDArray[np.float64] = scaler.fit_transform(features)

print("Scaled shape:", features_scaled.shape)

# Plotting an elbow plot to find the bets k value for k means
inertia = []
k_values = range(1, 11)

for k in k_values:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(features_scaled)
    inertia.append(km.inertia_)

# Plot it
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

# Apply KMeans with K=3
km = KMeans(n_clusters=3, random_state=42, n_init=10)
df["Cluster"] = km.fit_predict(features_scaled)

print(df["Cluster"].value_counts())

print(df.groupby("Cluster")[["Setting Time Min", "Acp Qty", "Duration Min"]].mean().round(2))

cluster1 = df[df["Cluster"] == 1]

print("Machines with most problem runs:")
print(cluster1["Machine No"].value_counts().head(10))

print("\nOperators with most problem runs:")
print(cluster1["Operator"].value_counts().head(10))

print("\nProblem runs by shift:")
print(cluster1["Shift"].value_counts())

print("\nDown time reasons:")
print(cluster1["Down Time Reason"].value_counts().head(10))

# using PCA
pca = PCA(n_components=2)
# Type hint coords
coords: NDArray[np.float64] = pca.fit_transform(features_scaled)

# KMeans clusters (0=normal, 1=problem, 2=setup heavy)
plt.figure(figsize=(9, 6))
colors = {0: "green", 1: "red", 2: "orange"}
labels = {0: "Normal (Cluster 0)", 1: "Problem runs (Cluster 1)", 2: "Setup heavy (Cluster 2)"}

for cluster_id in [0, 1, 2]:
    mask = df["Cluster"] == cluster_id
    plt.scatter(
        coords[mask, 0],
        coords[mask, 1],
        c=colors[cluster_id],
        label=labels[cluster_id],
        alpha=0.6,
        s=40,
    )

plt.title("KMeans Clusters — Production Runs")
plt.xlabel("PCA Component 1")
plt.ylabel("PCA Component 2")
plt.legend()
plt.tight_layout()
plt.savefig("clusters_plot.png")
print("Cluster plot saved as clusters_plot.png")

# DBSCAN for anomaly detection
dbscan = DBSCAN(eps=0.5, min_samples=5)
df["DBSCAN_Cluster"] = dbscan.fit_predict(features_scaled)

print("DBSCAN cluster counts:")
print(df["DBSCAN_Cluster"].value_counts().sort_index())

anomalies = df[df["DBSCAN_Cluster"] == -1]
print(f"\nAnomalies found: {len(anomalies)} out of {len(df)} runs")
print(f"That's {round(len(anomalies) / len(df) * 100, 1)}% of all runs")

print("\nAnomaly averages:")
print(anomalies[["Setting Time Min", "Acp Qty", "Duration Min"]].mean().round(2))


# Plot DBSCAN results
plt.figure(figsize=(9, 6))

# -1 means DBSCAN labelled it as an ANOMALY (doesn't belong to any cluster)
dbscan_colors = {-1: "red", 0: "green", 1: "orange"}
dbscan_labels = {-1: "Anomaly", 0: "Normal", 1: "Small cluster"}

for cluster_id in [-1, 0, 1]:
    mask = df["DBSCAN_Cluster"] == cluster_id
    plt.scatter(
        coords[mask, 0],
        coords[mask, 1],
        c=dbscan_colors[cluster_id],
        label=dbscan_labels[cluster_id],
        alpha=0.6,
        s=60 if cluster_id == -1 else 40,  # make anomalies bigger
    )

plt.title("DBSCAN — Anomaly Detection on Production Runs")
plt.xlabel("PCA Component 1")
plt.ylabel("PCA Component 2")
plt.legend()
plt.tight_layout()
plt.savefig("dbscan_plot.png")
print("DBSCAN plot saved as dbscan_plot.png")


X = features_scaled
y = df["Cluster"]

# Split into training (80%) and testing (20%)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)
y_pred = rf.predict(X_test)
print(classification_report(y_test, y_pred, target_names=["Normal", "Problem", "Setup heavy"]))
importances = pd.Series(
    rf.feature_importances_, index=["Setting Time Min", "Acp Qty", "Duration Min"]
)
print("\nFeature importances:")
print(importances.sort_values(ascending=False).round(3))
plt.figure(figsize=(7, 4))
importances.sort_values().plot(kind="barh", color=["#4CAF50", "#2196F3", "#FF5722"])
plt.title("Feature Importances — What drives anomaly detection?")
plt.xlabel("Importance score")
plt.tight_layout()
plt.savefig("feature_importance.png")
print("Feature importance plot saved")
