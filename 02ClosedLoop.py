import numpy as np
import pandas as pd
import scipy.signal as signal
import matplotlib.pyplot as plt

# ----------------------------------------------------
# 1. Setup & Simulation Parameters
# ----------------------------------------------------
time = np.linspace(0, 30, 600)  # Simulate 30 seconds
tau_base = 2.0                 # Base time constant (seconds)

# Prepare a dictionary to store data for the Excel export
excel_data = {"Time (s)": time}

plt.figure(figsize=(14, 6))

# ----------------------------------------------------
# Part 1: Simulating K from 1 to 10 (Closed Loop)
# ----------------------------------------------------
plt.subplot(1, 2, 1)
for K in range(1, 11):
    # Closed loop transfer function: T(s) = G(s) / (1 + G(s))
    # G(s) = K / (tau*s + 1)
    # T(s) = K / (tau*s + (1 + K))
    num = [K]
    den = [tau_base, 1 + K]
    sys_closed = signal.TransferFunction(num, den)
    
    # Get Step Response (Target temperature change = 1 unit)
    t, y = signal.step(sys_closed, T=time)
    
    # Save to Excel data structure
    excel_data[f"K={K}"] = y
    
    # Plotting
    plt.plot(t, y, label=f"K = {K}")

plt.title("Closed-Loop Step Response: Varying Gain (K)")
plt.xlabel("Time (seconds)")
plt.ylabel("Temperature Change (°C)")
plt.axhline(1.0, color='r', linestyle='--', label='Target (Set Point)')
plt.grid(True)
plt.legend()

# ----------------------------------------------------
# Part 2: Simulating Tau increases (2x and 3x) at K=5
# ----------------------------------------------------
plt.subplot(1, 2, 2)
K_fixed = 5
tau_values = [tau_base, tau_base * 2, tau_base * 3]
labels = ["Base Tau (2s)", "2x Tau (4s)", "3x Tau (6s)"]

for tau, label in zip(tau_values, labels):
    num = [K_fixed]
    den = [tau, 1 + K_fixed]
    sys_closed = signal.TransferFunction(num, den)
    
    t, y = signal.step(sys_closed, T=time)
    plt.plot(t, y, label=label)

plt.title("Closed-Loop Step Response: Varying Time Constant (Tau)")
plt.xlabel("Time (seconds)")
plt.ylabel("Temperature Change (°C)")
plt.axhline(1.0, color='r', linestyle='--', label='Target (Set Point)')
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()

# ----------------------------------------------------
# 3. Exporting Data to Excel
# ----------------------------------------------------
df = pd.DataFrame(excel_data)
df.to_excel("closed_loop_temperature_data.xlsx", index=False)
print("Simulation complete! Data saved to 'closed_loop_temperature_data.xlsx'")