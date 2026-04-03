import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report


df = pd.read_excel("data/sample/DailyProductionReport_17032026.xlsx")

df["Date"] = pd.to_datetime(df["Date"], format="%Y%m%d")
df["Start Time"] = pd.to_datetime(df["Start Time"], format="%d-%m-%Y %H:%M:%S")
df["End Time"]   = pd.to_datetime(df["End Time"],   format="%d-%m-%Y %H:%M:%S")
df = df.dropna(axis="columns", how="all")

print(df.shape)
print(df.columns.tolist())

df["Duration Min"] = (df["End Time"] - df["Start Time"]).dt.total_seconds() / 60

features = df[["Setting Time Min", "Acp Qty", "Duration Min"]]

print(features.describe())

print(features.isnull().sum())

features = features.fillna(features.median())

print("Nulls after filling:", features.isnull().sum().sum())



scaler = StandardScaler()
features_scaled = scaler.fit_transform(features)

print("Scaled shape:", features_scaled.shape)


# Try K values from 1 to 10 and record how "tight" the clusters are
# inertia = sum of distances of each point to its cluster center
# lower inertia = tighter clusters, but more clusters always lowers it
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

# See how many rows landed in each cluster
print(df["Cluster"].value_counts())

# See the average of each feature per cluster
# This tells you WHAT each cluster represents
print(df.groupby("Cluster")[["Setting Time Min", "Acp Qty", "Duration Min"]].mean().round(2))


# Isolate the problem cluster
cluster1 = df[df["Cluster"] == 1]

# Which machines appear most in problem runs?
print("Machines with most problem runs:")
print(cluster1["Machine No"].value_counts().head(10))

# Which operators?
print("\nOperators with most problem runs:")
print(cluster1["Operator"].value_counts().head(10))

# What shift?
print("\nProblem runs by shift:")
print(cluster1["Shift"].value_counts())

# What's the down time reason?
print("\nDown time reasons:")
print(cluster1["Down Time Reason"].value_counts().head(10))



# PCA reduces our 3 features down to 2 dimensions so we can plot them
# Think of it as "squishing" 3D data onto a 2D chart while keeping the shape
pca = PCA(n_components=2)
coords = pca.fit_transform(features_scaled)

# Plot
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
        s=40
    )

plt.title("KMeans Clusters — Production Runs")
plt.xlabel("PCA Component 1")
plt.ylabel("PCA Component 2")
plt.legend()
plt.tight_layout()
plt.savefig("clusters_plot.png")
print("Cluster plot saved as clusters_plot.png")




# eps = how close two points must be to be considered neighbours
# min_samples = minimum points needed to form a cluster
# We start with these values and can tune them
dbscan = DBSCAN(eps=0.5, min_samples=5)
df["DBSCAN_Cluster"] = dbscan.fit_predict(features_scaled)

# -1 means DBSCAN labelled it as an ANOMALY (doesn't belong to any cluster)
print("DBSCAN cluster counts:")
print(df["DBSCAN_Cluster"].value_counts().sort_index())

# How many anomalies did it find?
anomalies = df[df["DBSCAN_Cluster"] == -1]
print(f"\nAnomalies found: {len(anomalies)} out of {len(df)} runs")
print(f"That's {round(len(anomalies)/len(df)*100, 1)}% of all runs")

# What do the anomalies look like?
print("\nAnomaly averages:")
print(anomalies[["Setting Time Min", "Acp Qty", "Duration Min"]].mean().round(2))


# Plot DBSCAN results
plt.figure(figsize=(9, 6))

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
        s=60 if cluster_id == -1 else 40  # make anomalies bigger
    )

plt.title("DBSCAN — Anomaly Detection on Production Runs")
plt.xlabel("PCA Component 1")
plt.ylabel("PCA Component 2")
plt.legend()
plt.tight_layout()
plt.savefig("dbscan_plot.png")
print("DBSCAN plot saved as dbscan_plot.png")



# We use KMeans clusters as our labels (0=normal, 1=problem, 2=setup heavy)
X = features_scaled
y = df["Cluster"]

# Split into training (80%) and testing (20%)
# The model learns on train, we verify it on test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train the classifier
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)

# Test it
y_pred = rf.predict(X_test)
print(classification_report(y_test, y_pred, 
      target_names=["Normal", "Problem", "Setup heavy"]))

# Which features does it rely on most?
importances = pd.Series(rf.feature_importances_, 
                        index=["Setting Time Min", "Acp Qty", "Duration Min"])
print("\nFeature importances:")
print(importances.sort_values(ascending=False).round(3))



plt.figure(figsize=(7, 4))
importances.sort_values().plot(kind="barh", color=["#4CAF50", "#2196F3", "#FF5722"])
plt.title("Feature Importances — What drives anomaly detection?")
plt.xlabel("Importance score")
plt.tight_layout()
plt.savefig("feature_importance.png")
print("Feature importance plot saved")