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

def plot_estimated_production(U, dtb, gx, gy, injectors, producers, R, output_path = None):
    estimated_production = estimated_production_filter(U, gx, gy, injectors, producers, R)
    plt.figure()
    plt.pcolormesh(dtb.x, dtb.y, estimated_production * U)
    for [x, y] in injectors:
        plt.scatter(x, y, marker='x', color='red')
    for [x, y] in producers:
        plt.scatter(x, y, marker='x', color='white')
    plt.suptitle(f"{len(injectors)} injectors, {len(producers)} producers")
    plt.title(f"Estimated production: {estimated_U_production(U, gx, gy, injectors, producers, R):.1f} T")
    if output_path is not None: plt.savefig(output_path)

available_placement_types = [ "HEX", "SQR" ]

def place_wells(placement_type: str, dtb: Distribution, R: float, output_figure_path: str = None) -> str:
    Rs = R * 0.6        # R for sigma

    gx, gy = np.meshgrid(dtb.x, dtb.y)
    cx = (dtb.x_min + dtb.x_max) / 2    # center x
    cy = (dtb.y_min + dtb.y_max) / 2    # center y
    U = dtb.get_col("Uraninite")
    # U_smoothed = dtb.smoothen("Uraninite", "U_smoothed", 8)
    # grad_U = np.gradient(U_smoothed)

    injectors = []
    producers = []

    if placement_type == "HEX":
        surface_per_well = (3*np.sqrt(3)/2) * R**2 / (1+6*1/3)
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

    elif placement_type == "SQR":
        surface_per_well = 2 * R**2 / (1+4*1/4)
        x, y = dtb.x_min, dtb.y_min
        j = 0
        while x < dtb.x_max and y < dtb.y_max:
            if j % 2 == 1:
                producers.append([ x, y ])
            else:
                injectors.append([ x, y ])
            x += np.sqrt(2) * R
            if x > dtb.x_max:
                j += 1
                x = dtb.x_min + (j % 2) * np.sqrt(2) * R / 2
                y += np.sqrt(2) * R / 2

    def transform(well, opt_X):
        x, y = well
        theta, dx, dy = opt_X
        cost, sint = np.cos(theta), np.sin(theta)
        x2, y2 = x + dx - cx, y + dy - cy
        x3, y3 = x2 * cost - y2 * sint, x2 * sint + y2 * cost
        return [ x3 + cx, y3 + cy ]
    
    def transform_wells(wells, opt_X):
        return [ transform(well, opt_X) for well in wells ]

    def opt_error(opt_X):
        ijc = filter_wells(U, gx, gy, transform_wells(injectors, opt_X), Rs)
        pdc = filter_wells(U, gx, gy, transform_wells(producers, opt_X), Rs)
        return - estimated_U_production(U, gx, gy, ijc, pdc, Rs)

    res = sp.optimize.minimize(
        opt_error,
        np.array([ 0, 0, 0 ]),
        bounds = [ (-2*np.pi, 2*np.pi), (-R, R), (-R, R) ],
        method = "Nelder-Mead"
    )

    print(f"[{placement_type}, R={R}m] -> optimal delta: {res.x}")
    injectors = filter_wells(U, gx, gy, transform_wells(injectors, res.x), Rs)
    producers = filter_wells(U, gx, gy, transform_wells(producers, res.x), Rs)

    plot_estimated_production(U, dtb, gx, gy, injectors, producers, Rs, output_figure_path)

    return geometry_htc_string(injectors, producers, R), surface_per_well

# dtb = Distribution.load_from_file("../distributions/ellipse/U.dat")
# for R in np.linspace(20, )
# place_hexagons(dtb, 20, "../distributions/ellipse/hex20.geo", "../distributions/ellipse/hex20.png")