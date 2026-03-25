import numpy as np 
import matplotlib.pyplot as plt
import scipy as sp
import argparse
import os
from utils.distribution import Distribution

def evaluate_gradient(dtb, grad_U, x, y):
    i = int(np.floor(dtb.NX * (x - dtb.x.min()) / (dtb.x.max() - dtb.x.min())))
    j = int(np.floor(dtb.NY * (y - dtb.y.min()) / (dtb.y.max() - dtb.y.min())))
    return grad_U[1][j,i], grad_U[0][j,i]

def function_sum(U, gx, gy, wells, f):
    filter = np.zeros(U.shape)
    for [x, y] in wells:
        filter += f((x - gx) ** 2 + (y - gy) ** 2)
    return filter

def estimated_production_filter(U, gx, gy, injectors, producers, R):
    filter_injectors = function_sum(U, gx, gy, injectors, lambda d: np.exp(-d/(2*R**2)))
    filter_producers = function_sum(U, gx, gy, producers, lambda d: np.exp(-d/(2*R**2)))
    filter_injectors = np.minimum(filter_injectors, 1)
    filter_producers = np.minimum(filter_producers, 1)

    return filter_injectors * filter_producers

    # closeness_injectors = function_sum(U, gx, gy, injectors, lambda d: 1/np.pow(d, 1))
    # closeness_producers = function_sum(U, gx, gy, producers, lambda d: 1/np.pow(d, 1))
    # closeness = closeness_injectors * closeness_producers

    # return np.maximum(0, filter_injectors * filter_producers - closeness * 30)

def estimated_U_production(U, gx, gy, injectors, producers, R):
    filter = estimated_production_filter(U, gx, gy, injectors, producers, R)
    porosity = 0.23
    Vcell = (400/80) * (300/60) * 12            # m3
    Vwater = filter * Vcell * porosity * 1000   # L
    return np.sum(Vwater * U) * 270 / 1e6       # T

def filter_wells(U, gx, gy, wells, R):
    estimated_wells_individual_production = np.array(list(map(lambda pos: (function_sum(U, gx, gy, [pos], lambda d: np.exp(-d/(2*R**2))) * U).sum(), wells)))
    valid_indices = list(filter(lambda i: estimated_wells_individual_production[i] > estimated_wells_individual_production.max() / 4, range(len(wells))))
    return [ wells[i] for i in valid_indices ]

def geometry_htc_string(injectors, producers, R) -> str:
    DX, DY, DZ = 5, 5, 12
    out = ""
    
    all_wells = injectors + producers
    def get_flow_rate(x, y):
        inradius = len(list(filter(lambda w: (w[0]-x)**2 + (w[1]-y)**2 <= R**2*1.1, all_wells))) - 1
        return inradius / 6

    for i, [ x, y ] in enumerate(producers):
        out += f"zone producteur_{i+1} {{\n"
        out += f"  geometry = rectangle {x:.2f}, {y:.2f}, 6 {DX}, {DY}, {DZ} m\n"
        out += f"  global-flux producteur_{i+1} \n"
        out += f"  geochem = aquifer\n"
        out += f"  source = -{get_flow_rate(x,y)} m3/h\n}}\n\n"

    for i, [ x, y ] in enumerate(injectors):
        out += f"zone injecteur_{i+1} {{\n"
        out += f"  geometry = rectangle {x:.2f}, {y:.2f}, 6 {DX}, {DY}, {DZ} m\n"
        out += f"  global-flux injecteur_{i+1} \n"
        out += f"  geochem = aquifer\n"
        out += f"  source = {get_flow_rate(x,y)} m3/h using leaching_solution_20\n"
        out += f"  modify at 30 days, source = {get_flow_rate(x,y)} m3/h using leaching_solution\n}}\n\n"

    return out

def plot_estimated_production(U, dtb, gx, gy, injectors, producers, R, output_path):
    estimated_production = estimated_production_filter(U, gx, gy, injectors, producers, R)
    plt.figure()
    plt.pcolormesh(dtb.x, dtb.y, estimated_production * U)
    for [x, y] in injectors:
        plt.scatter(x, y, marker='x', color='red')
    for [x, y] in producers:
        plt.scatter(x, y, marker='x', color='white')
    plt.suptitle(f"{len(injectors)} injectors, {len(producers)} producers")
    plt.title(f"Estimated production: {estimated_U_production(U, gx, gy, injectors, producers, R):.1f} T")
    plt.savefig(output_path)

def place_hexagons(dtb: Distribution, R: float, output_figure_path: str) -> str:
    # HEXAGONS

    Rs = R * 0.6        # R for sigma

    U = dtb.get_col("Uraninite")
    U_smoothed = dtb.smoothen("Uraninite", "U_smoothed", 8)

    gx, gy = np.meshgrid(dtb.x, dtb.y)
    grad_U = np.gradient(U_smoothed)

    injectors = []
    producers = []

    x, y = dtb.x_min, dtb.y_min
    i, j = 0, 0
    while x < dtb.x_max and y < dtb.y_max:
        if i % 3 == 1:
            producers.append([ x, y ])
        else:
            injectors.append([ x, y ])
        x += R
        i += 1
        if x > dtb.x_max:
            j += 1
            i = (j % 2) * 2
            y += R * np.cos(np.pi / 6)
            x = dtb.x_min + (j % 2) * R / 2

    # injectors = filter_wells(np.array(injectors), R*0.6)
    # producers = filter_wells(np.array(producers), R*0.6)

    def hex_opt_error(opt_X):
        return - estimated_U_production(U, gx, gy, injectors + opt_X, producers + opt_X, Rs)

    res = sp.optimize.minimize(
        hex_opt_error,
        np.array([ 0, 0 ]),
        bounds = [ (-R, R), (-R, R) ],
        # method = "Nelder-Mead"
    )

    print(f"R = {R} m -> optimal delta: {res.x}")
    injectors = filter_wells(U, gx, gy, injectors + res.x, Rs)
    producers = filter_wells(U, gx, gy, producers + res.x, Rs)
    plot_estimated_production(U, dtb, gx, gy, injectors, producers, Rs, output_figure_path)
    return geometry_htc_string(injectors, producers, R)

# dtb = Distribution.load_from_file("../distributions/ellipse/U.dat")
# for R in np.linspace(20, )
# place_hexagons(dtb, 20, "../distributions/ellipse/hex20.geo", "../distributions/ellipse/hex20.png")