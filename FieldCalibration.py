import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# HX - Retrieve more data
d_I_hx = np.array([0.2, 0.5, 0.7, 1.0]).reshape(-1, 1) # Input current (desired)
m_I_hx = np.array([0.05, 0.103, 0.148, 0.233]) # Measured current (power supply)
B_hx = np.array([-1.44, -2.175, -2.655, -3.39]) # Measured MF at [0,0]

# HY - Retrieve more data
d_I_hy = np.array([0.2, 0.5, 0.7, 1.0]).reshape(-1, 1)
m_I_hy = np.array([0.015, 0.062, 0.124, 0.251])
B_hy = np.array([-0.009, -0.045, -0.065, -0.107])

# Input vs Measured Current
model_hx = LinearRegression().fit(d_I_hx, m_I_hx)
model_hy = LinearRegression().fit(d_I_hy, m_I_hy)

# Measured Current vs B-field
B_model_hx = LinearRegression().fit(m_I_hx.reshape(-1, 1), B_hx)
B_model_hy = LinearRegression().fit(m_I_hy.reshape(-1, 1), B_hy)

# Predict for smooth lines
x_input = np.linspace(0, 1.1, 100).reshape(-1, 1)
pred_I_hx = model_hx.predict(x_input)
pred_I_hy = model_hy.predict(x_input)

x_current = np.linspace(0, max(m_I_hx.max(), m_I_hy.max())*1.1, 100).reshape(-1, 1)
pred_B_hx = B_model_hx.predict(x_current)
pred_B_hy = B_model_hy.predict(x_current)

# Plot
fig, axs = plt.subplots(1, 2, figsize=(14, 6))

# Input vs Measured Current
axs[0].plot(d_I_hx, m_I_hx, 'ro', label='HX data')
axs[0].plot(x_input, pred_I_hx, 'r--', label=f'HX fit: I = {model_hx.coef_[0]:.3f}·input + {model_hx.intercept_:.3f}')
axs[0].plot(d_I_hy, m_I_hy, 'bo', label='HY data')
axs[0].plot(x_input, pred_I_hy, 'b--', label=f'HY fit: I = {model_hy.coef_[0]:.3f}·input + {model_hy.intercept_:.3f}')
axs[0].set_xlabel("Input Command")
axs[0].set_ylabel("Measured Current (A)")
axs[0].set_title("Input Command vs Measured Current")
axs[0].legend()
axs[0].grid(True)

# Measured Current vs B-field
axs[1].plot(m_I_hx, B_hx, 'ro', label='HX B-field data')
axs[1].plot(x_current, pred_B_hx, 'r--', label=f'HX B = {B_model_hx.coef_[0]:.3f}·I + {B_model_hx.intercept_:.3f}')
axs[1].plot(m_I_hy, B_hy, 'bo', label='HY B-field data')
axs[1].plot(x_current, pred_B_hy, 'b--', label=f'HY B = {B_model_hy.coef_[0]:.3f}·I + {B_model_hy.intercept_:.3f}')
axs[1].set_xlabel("Measured Current (A)")
axs[1].set_ylabel("Measured B-field (mT)")
axs[1].set_title("Measured Current vs B-field")
axs[1].legend()
axs[1].grid(True)

plt.tight_layout()
plt.show()

print("Input to Current Models:")
print(f"HX: Current = {model_hx.coef_[0]:.4f} * Input + {model_hx.intercept_:.4f}")
print(f"HY: Current = {model_hy.coef_[0]:.4f} * Input + {model_hy.intercept_:.4f}")

print("\nCurrent to B-field Models:")
print(f"HX: B = {B_model_hx.coef_[0]:.4f} * Current + {B_model_hx.intercept_:.4f}")
print(f"HY: B = {B_model_hy.coef_[0]:.4f} * Current + {B_model_hy.intercept_:.4f}")