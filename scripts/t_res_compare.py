import re
import os
import numpy as np 
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
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
            simulations[R][m] = SimuResults(os.path.join(root, folder, subfolder), R=R*0.6)
        except Exception as e:
            print(f"could not load simulation at {os.path.join(root, folder, subfolder)}")
            print(e)
            continue

# ----------------- PLOTTING RESULTS -----------------

fig, axes = plt.subplots(3, 3, figsize=(12, 12))
axs = axes.flatten()

durations = [ 1, 2, 5 ]    # years

acidonU_max = 0
acid_max = 0
for R, R_sims in simulations.items():
    m_values = list(R_sims.keys())
    m_values.sort()
    RR = int(round(R))

    for i, d in enumerate(durations):
        acid = []
        rratio = []
        acidonU = []
        for m_value in m_values:
            sim = R_sims[m_value]
            rratio.append(sim.get_recuperation_ratio(d))
            acid.append(sim.get_acid_consumption(d)/1e3)
            acidonU.append(sim.get_acid_consumption(d) / sim.get_U_production(d))
        def plot(line, values):
            if RR == 42:    # reference
                axs[3*line+i].plot(m_values, values, label=f"R={RR}m (ref)", color="black", linestyle="dashed")
            else:
                axs[3*line+i].plot(m_values, values, label=f"R={RR}m")
        plot(0, rratio)
        plot(1, acid)
        plot(2, acidonU)
        acid_max = max(acid_max, max(acid))
        acidonU_max = max(acidonU_max, max(acidonU))

for i, d in enumerate(durations):
    years = f"{d} year{'' if d == 1 else 's'}"
    axs[i].set_title(f"Uranium recuperation ratio after {years}")
    axs[3+i].set_title(f"Acid consumption after {years} (kT)")
    axs[6+i].set_title(f"acid / U after {years} (T/T)")
    axs[i].set_ylim((0, 1))
    axs[3+i].set_ylim((0, acid_max*1.1))
    axs[6+i].set_ylim((0, acidonU_max*1.1))

for ax in axs:
    ax.legend()
    ax.grid()
    ax.set_xlabel("$T_\\text{res} / T_\\text{res}^\\text{ref}$")
    ax.set_xscale("log")
    ax.set_xlim((0.2, 5))
    ax.xaxis.set_major_locator(ticker.LogLocator(base=10, subs=[0.2, 0.5, 1.0, 2.0, 5.0]))
    ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.1f}'))

fig.tight_layout()
fig.savefig(os.path.join(root, f"comparison.png"))