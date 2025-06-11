import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# MX
I_mx = np.array([0.015, 0.05, 0.087, 0.17]).reshape(-1, 1)
B_mx = np.array([0.018, 0.025, 0.032, 0.041])

# HX
I_hx = np.array([0.05, 0.103, 0.148, 0.233]).reshape(-1, 1)
B_hx = np.array([-1.44, -2.175, -2.655, -3.39])

# MY
I_my = np.array([0.043, 0.268, 0.515, 1.067]).reshape(-1, 1)
B_my = np.array([-0.003, -0.005, -0.006, -0.018])

# HY
I_hy = np.array([0.015, 0.062, 0.124, 0.251]).reshape(-1, 1)
B_hy = np.array([-0.009, -0.045, -0.065, -0.107])

I_data = [I_mx, I_hx, I_my, I_hy]
B_data = [B_mx, B_hx, B_my, B_hy]
labels = ["MX", "HX", "MY", "HY"]
colors = ['r', 'g', 'b', 'm']

plt.figure(figsize=(10, 8))

for i in range(len(I_data)):
    model = LinearRegression()
    model.fit(I_data[i], B_data[i])

    k = model.coef_[0]
    b = model.intercept_
    print(f"{labels[i]} field model: B = {k:.3f} * I + {b:.3f} mT")

    # Predict for plotting
    I_range = np.linspace(I_data[i].min(), I_data[i].max(), 100).reshape(-1, 1)
    B_pred = model.predict(I_range)

    # Plot
    plt.subplot(2, 2, i + 1)
    plt.scatter(I_data[i], B_data[i], color=colors[i], label='Measured')
    plt.plot(I_range, B_pred, color=colors[i], linestyle='--', label='Linear fit')
    plt.title(f"{labels[i]} Coil")
    plt.xlabel("Current (A)")
    plt.ylabel("B field (mT)")
    plt.legend()
    plt.grid(True)

plt.tight_layout()
plt.show()
