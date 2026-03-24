import re
import os
import numpy as np 
import matplotlib.pyplot as plt
import argparse

# ----------------- PARSING ARGS -----------------

parser = argparse.ArgumentParser()
parser.add_argument("-r", help="Directory root")
parser.add_argument("-s", help="Varying setting")
args = parser.parse_args()

root = args.r
setting = args.s

if root is None or setting is None:
    parser.print_usage()
    exit(0)

# ----------------- READING DIR -----------------

from utils.simu_results import SimuResults
from utils.prices import prices

simulations = []
for folder in os.listdir(root):
    m = re.findall(f"{setting}_([0-9.]+)", folder)
    if len(m) > 0:
        print(folder)
        simulations.append((float(m[0]), SimuResults(os.path.join(root, folder))))

if len(simulations) == 0:
    print(f"No simulation found for setting {setting} in folder {root} ; aborting")
    exit(0)

simulations.sort(key=lambda s: s[0])

# ----------------- PARSING SIMULATIONS -----------------

r_values = [ 5, 10, 15 ]

setting_values = []
acid_consumed_total_values = []     # tons
U_produced_total_values = []        # tons
npv_values = [ [] for r in r_values ]
for setting_value, sim in simulations:
    setting_values.append(setting_value)
    acid_consumed_total_values.append(sim.acid_consumed_total)
    U_produced_total_values.append(sim.U_produced_total)
    for i, r in enumerate(r_values):
        npv_values[i].append(sim.net_present_value(prices, r/100) / 1e6)

fig, axes = plt.subplots(1, 2, figsize=(12, 6))
axs = axes.flatten()

ax1 = axs[0]
ax2 = ax1.twinx()
ax1.plot(setting_values, U_produced_total_values, label="uranium production", color="green")
ax1.set_ylim(ymin=0)
ax1.set_xlabel(f"{setting}")
ax1.set_ylabel("uranium production ($t$)", color="green")
ax2.plot(setting_values, acid_consumed_total_values, label="acid consumption", color="red")
ax2.set_ylim(ymin=0)
ax2.set_ylabel(f"acid consumption ($t$)", color="red")
ax1.set_title("production and consumption")

for i, r in enumerate(r_values):
    axs[1].plot(setting_values, npv_values[i], label=f"r={r}%")
axs[1].set_xlabel(f"{setting}")
axs[1].set_ylabel("net present value ($)")
axs[1].set_title("NPV for different interest rates")
axs[1].legend()
axs[1].grid()

fig.tight_layout()
fig.savefig(os.path.join(root, f"comparison_{setting}.png"))