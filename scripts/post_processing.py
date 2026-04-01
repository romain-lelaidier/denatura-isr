import re
import os
import numpy as np 
import matplotlib.pyplot as plt
import argparse

# ----------------- PARSING ARGS -----------------

parser = argparse.ArgumentParser()
parser.add_argument("--root", help="Simulation root")
parser.add_argument("-d", action="store_true", help="Plot distributions")
args = parser.parse_args()

if args.root is None:
    print("No simulation root provided.")
    parser.print_usage()
    exit(0)

root = args.root
print(f"Reading simulation in folder `{root}`.")
if not os.path.isdir(root):
    print("This folder does not exist. Aborting.")
    exit(0)

# ----------------- OPENING FILES -----------------

htcfile = os.path.join(root, "config.htc")
nextLineCoordinates = False
xinj, yinj, xprod, yprod = [], [], [], []
lines = open(htcfile, "r").readlines()

for line in lines:

    if line.startswith("domain"):
        line = line.replace(","," ")
        tks = re.split(r'[ ,]+', line)
        LX, NX, LY, NY, LZ, NZ = float(tks[2]), int(tks[3]), float(tks[4]), int(tks[5]), float(tks[6]), int(tks[7])

    if nextLineCoordinates:
        tokens = re.split(r'[ ,]+', line)
        #print(tokens[2],tokens[3],tokens[4])
        if inj:
            xinj.append(float(tokens[4]))
            yinj.append(float(tokens[5]))
        elif prod:
            xprod.append(float(tokens[4]))
            yprod.append(float(tokens[5]))

    nextLineCoordinates = False
    inj = False
    prod = False

    if line.startswith("zone"):
        if "prod" in line or "inj" in line:
            # we have a prod or inj
            nextLineCoordinates = True
            if "prod" in line:
                prod = True
                inj = False
            else:
                inj = True
                prod = False

DX = LX/NX
DY = LY/NY
DZ = LZ/NZ
print("L", LX,LY,LZ)
print("D", DX,DY,DZ)
xgrid = np.linspace(DX/2,LX-DX/2,NX)
ygrid = np.linspace(DY/2,LY-DY/2,NY)

# ----------------- IMPORTING HYTEC -----------------

print("Preparing Simulation Results object")

from utils.simu_results import SimuResults
from utils.prices import prices

simu = SimuResults(root)
simu.plot_all(prices, title=root, path=os.path.join(root, "result.png"))

# ----------------- PLOTTING DISTRIBUTIONS EVOLUTION -----------------

if args.d:
    print("Plotting uraninite distributions")

    Nfluxsamples = simu.simu.handlers.results.grid_res_data.shape[1]
    timeSim = simu.simu.handlers.results.get_sample_times_from_grid_res()
    pH = simu.simu.handlers.results.extract_field_from_grid_res("pH []", nx=NX, ny = NY, nz=NZ)   
    Sulf = simu.simu.handlers.results.extract_field_from_grid_res('aqueous{SO4[2-]} [mol/kg]', nx=NX, ny = NY, nz=NZ)
    UO2 = simu.simu.handlers.results.extract_field_from_grid_res('Uraninite []', nx=NX, ny = NY, nz=NZ)

    root_figures = os.path.join(root, "2D_figs")
    if not os.path.isdir(root_figures):
        os.mkdir(root_figures)

    def axplot(ax, xgrid, ygrid, var, fancyvar, cmin=0, cmax=None):
        if cmax is None: cmax = np.max(var)
        pcm = ax.pcolormesh(xgrid,ygrid,var.T,vmin=cmin,vmax=cmax)
        ax.set_xlabel('X-axis (m)')
        ax.set_ylabel('Y-axis (m)')
        ax.set_title(fancyvar)
        ax.set_xlim(0,LX)
        ax.set_ylim(0,LY)
        ax.scatter(xinj,yinj,color="red",s=3)
        ax.scatter(xprod,yprod,color="white",s=3)
        plt.colorbar(pcm,ax=ax,label=fancyvar)

    for sam in range(Nfluxsamples):
        print(f" {sam} of {Nfluxsamples}")
        fig, axes = plt.subplots(1, 3, figsize=(18, 5), dpi=300)
        axs = axes.flatten()

        axplot(axs[0], xgrid, ygrid, pH[:,:,0,sam], "pH", cmin=1, cmax=8) # pH
        axplot(axs[1], xgrid, ygrid, Sulf[:,:,0,sam], "Sulfates") # Sulfate
        axplot(axs[2], xgrid, ygrid, 1-UO2[:,:,0,sam]/UO2[:,:,0,0], "Uranium dissolution", cmax=1) 

        fig.suptitle(f"Distributions after {timeSim[sam]:.2f} years")
        fig.tight_layout()
        fig.savefig(os.path.join(root_figures, f"dist_{sam}.png"))