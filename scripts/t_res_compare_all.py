import re
import os
import numpy as np 
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import argparse

# ----------------- PARSING ARGS -----------------

parser = argparse.ArgumentParser()
parser.add_argument("-r", help="Directory roots")
parser.add_argument("-n", help="Names")
parser.add_argument("-s", help="Setting")
args = parser.parse_args()

if args.r is None or args.n is None:
    parser.print_usage()
    exit(0)

roots = args.r.split(',')
names = args.n.split(',')
s = args.s or "RC"

if len(roots) != len(names):
    print("the number of roots and names should be the same ; aborting")
    exit(0)

for root in roots:
    if not os.path.exists(root):
        print(f"folder {root} does not exist ; aborting")
        exit(0)

from utils.simu_results import SimuResults
from utils.prices import prices

fig, axes = plt.subplots(3, 3, figsize=(12, 12), dpi=300)
axs = axes.flatten()

durations = [ 1, 2, 5 ]    # years

max_values = {}

for i, root in enumerate(roots):        # hex, sqr, org, etc.
    name = names[i]

    # ----------------- READING DIR -----------------
    simulations = {}                    # m_XXX -> [ value, simulations ]

    for folder in os.listdir(root):     # RC_...

        match = re.findall(f"{s}_([0-9.]+)", folder)
        if len(match) == 0: continue
        s_value = float(match[0])
        RC = s_value if s == 'RC' else 21.8

        for subfolder in os.listdir(os.path.join(root, folder)):        # m_1.00, ...
            match = re.findall(f"m_([0-9.]+)", subfolder)
            if len(match) == 0: continue

            m_value = float(match[0])
            if m_value not in simulations:
                simulations[m_value] = []

            try:
                simulations[m_value].append(SimuResults(os.path.join(root, folder, subfolder), RC))
            except Exception as e:
                print(f"could not load simulation at {os.path.join(root, folder, subfolder)}")
                print(e)
                continue

    def plot_mean(line, value_getter):
        for j, y in enumerate(durations):
            m_values = list(simulations.keys())
            m_values.sort()
            s_values_mean = []
            s_values_std = []
            for m_value in m_values:
                s_values = []
                for sim in simulations[m_value]:
                    value = value_getter(y, sim)
                    s_values.append(value)
                    if line not in max_values: max_values[line] = value
                    else: max_values[line] = max(value, max_values[line])
                s_values = np.array(s_values)
                s_values_mean.append(s_values.mean())
                s_values_std.append(s_values.std())
            s_values_mean = np.array(s_values_mean)
            s_values_std = np.array(s_values_std)
            axs[3*line+j].plot(m_values, s_values_mean)
            axs[3*line+j].fill_between(m_values, s_values_mean - s_values_std, s_values_mean + s_values_std, alpha=0.2, label=name)
    
    plot_mean(0, lambda y, sim: sim.get_recuperation_ratio(y))
    plot_mean(1, lambda y, sim: sim.get_acid_consumption(y)/1e3)
    plot_mean(2, lambda y, sim: sim.get_acid_consumption(y) / sim.get_U_production(y))

max_values[0] = 1/1.1

for j in range(3):
    for i, y in enumerate(durations):
        years = f"{y} year{'' if y == 1 else 's'}"
        title = [
            f"Uranium recuperation ratio after {years}",
            f"Acid consumption after {years} (kT)",
            f"acid / U after {years} (T/T)"
        ] [ j ]
        axs[3*j+i].set_title(title)
        axs[3*j+i].legend()
        if j in max_values:
            axs[3*j+i].set_ylim((0, max_values[j]*1.1))

for ax in axs:
    ax.legend()
    ax.grid()
    ax.set_xlabel("$T_\\text{res} / T_\\text{res}^\\text{ref}$")
    ax.set_xscale("log")
    ax.set_xlim((0.2, 5))
    ax.xaxis.set_major_locator(ticker.LogLocator(base=10, subs=[0.2, 0.5, 1.0, 2.0, 5.0]))
    ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.1f}'))

fig.tight_layout()
fig.savefig(f"compare_all.png")
