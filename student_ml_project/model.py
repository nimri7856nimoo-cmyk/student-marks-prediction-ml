import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

# Load data
data = pd.read_csv("data.csv")

X = data[['Hours']]
y = data['Marks']

# Train model
model = LinearRegression()
model.fit(X, y)

# Save model
joblib.dump(model, "model.pkl")

print("✅ Model trained and saved!")
import matplotlib.pyplot as plt

plt.scatter(X, y)
plt.plot(X, model.predict(X))
plt.xlabel("Hours")
plt.ylabel("Marks")
plt.title("Study Hours vs Marks")
plt.show()