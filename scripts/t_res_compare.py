import re
import os
import numpy as np 
import matplotlib.pyplot as plt
import argparse

# ----------------- PARSING ARGS -----------------

parser = argparse.ArgumentParser()
parser.add_argument("-r", help="Directory root")
args = parser.parse_args()

root = args.r

if root is None:
    parser.print_usage()
    exit(0)

if not os.path.exists(root):
    print(f"folder {root} does not exist ; aborting")
    exit(0)

# ----------------- READING DIR -----------------

from utils.simu_results import SimuResults
from utils.prices import prices

simulations = {}
for folder in os.listdir(root):
    match = re.findall(f"R_([0-9.]+)", folder)
    if len(match) == 0: continue
    R = float(match[0])
    simulations[R] = {}
    for subfolder in os.listdir(os.path.join(root, folder)):
        match = re.findall(f"m_([0-9.]+)", subfolder)
        if len(match) == 0: continue
        m = float(match[0])
        try:
            simulations[R][m] = SimuResults(os.path.join(root, folder, subfolder))
        except Exception as e:
            print(f"could not load simulation at {os.path.join(root, folder, subfolder)}")
            print(e)
            continue

# ----------------- PLOTTING RESULTS -----------------

fig, axes = plt.subplots(3, 3, figsize=(12, 12))
axs = axes.flatten()

durations = [ 1, 2, 5 ]    # years

for R, R_sims in simulations.items():
    m_values = list(R_sims.keys())
    m_values.sort()

    for i, d in enumerate(durations):
        #Uiy = []
        SO4iy = []
        rratio = []
        Uonacid = []
        for m_value in m_values:
            sim = R_sims[m_value]
            #Uiy.append(sim.get_U_production(d))
            SO4iy.append(sim.get_acid_consumption(d)/1e3)
            rratio.append(sim.get_recuperation_ratio(d, R*0.6))
            Uonacid.append(sim.get_U_production(d) / sim.get_acid_consumption(d))
        axs[i].plot(m_values, rratio, label=f"R={R:.1f}m")
        axs[3+i].plot(m_values, SO4iy, label=f"R={R:.1f}m")
        axs[6+i].plot(m_values, Uonacid, label=f"R={R:.1f}m")
        #axs[6+i].plot(m_values, rratio, label=f"R={R:.1f}m")

for i, d in enumerate(durations):
    axs[i].set_title(f"Uranium recuperation ratio after {d} years")
    axs[i].set_ylim((0, 1))
    axs[3+i].set_title(f"Acid consumption after {d} years (kT)")
    axs[6+i].set_title(f"U / SO4 after {d} years")

for ax in axs:
    ax.legend()
    ax.grid()
    ax.set_xlabel("$T_\\text{res} / T_\\text{res}^\\text{ref}$")
    ax.set_xscale("log")

fig.tight_layout()
fig.savefig(os.path.join(root, f"comparison.png"))