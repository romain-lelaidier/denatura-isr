# generate simulation configurations

import os
import argparse
import shutil
import numpy as np
import subprocess as sp
import re
from utils.distribution import Distribution
from utils.placer import DistributionPlacer, build_flow_rates_from_voronoi

# input parameters
parser = argparse.ArgumentParser()
parser.add_argument("-r", help="Simulation root")
parser.add_argument("-g", help="Wells geometry file path")
parser.add_argument("-u", help="Uranium distribution file path")
parser.add_argument('-s', help="Varying setting")
parser.add_argument('-t', help="Varying setting with time dependency")
parser.add_argument('-f', action="store_true", help="Force overwrite")
parser.add_argument('-l', action="store_true", help="Launch immediately")
args = parser.parse_args()

root = args.r
gpth = args.g
upth = args.u
s = args.s or args.t or ""
is_T_res_dependent = args.t is not None
params = s.split(',')

settings = {
    'CHESS': "../../../chess.tdb",
    # 'MAX_FLOW': 10,     # max injection/production rate (m3/h) on any well
    'GOETHITE': 0.3,    # mmolal
    'FE2': 1,           # g/l
    'FE3': 100          # mg/l      # 50 à KATCO
}

if root is None or (gpth is None and params[0] not in DistributionPlacer.available_placement_types) or upth is None:
    parser.print_usage()
    exit(0)

# checking files
if not os.path.isdir(root):
    print(f"folder {root} does not exist ; creating it")
    os.mkdir(root)

if not os.path.isfile(upth):
    print(f"uranium distribution file {upth} does not exist")

LAUNCHER_STR = open("./utils/launcher_str", "r").read()
CONFIG_STR = open("./utils/config_str", "r").read()

def prepare_simulation_folder(name):
    sim_dir = os.path.join(root, name)
    if os.path.isdir(sim_dir):
        if args.f:
            print(f"  /!\\ deleting {sim_dir}")
            shutil.rmtree(sim_dir)
        else:
            print(f"  folder {sim_dir} already exists ; skipping")
            return
    os.mkdir(sim_dir)
    return sim_dir

def build_simulation(name, jobname, settings, launch=False):
    print(f"building simulation {name}")

    sim_dir = prepare_simulation_folder(name)
    config_path = os.path.join(sim_dir, "config.htc")
    launcher_path = os.path.join(sim_dir, "launcher.sh")

    config_str = CONFIG_STR
    for key, value in settings.items():
        config_str = config_str.replace(f"XX{key}XX", str(value))

    # replacing flows
    if "MAX_FLOW" in settings and settings["MAX_FLOW"] is not None:
        flows = re.findall("([0-9.]+) m3/h", config_str)
        flows_values = list(map(float, flows))
        max_flow = max(flows_values)

        config_str_n = ''
        while True:
            match = re.search("([0-9.]+) m3/h", config_str)
            if not match:
                config_str_n += config_str
                break
            
            ib, ie = match.span()
            config_str_n += config_str[0:ib]
            config_str = config_str[ie:]

            flow = float(match.groups()[0])
            config_str_n += f"{flow * settings['MAX_FLOW'] / max_flow} m3/h"

        config_str = config_str_n
        
    open(config_path, "w").write(config_str)
    open(launcher_path, "w").write(LAUNCHER_STR.replace("XXJOBNAMEXX", jobname))

    if launch:
        print("  launching HYTEC node")
        try:
            process = sp.Popen([ 'sbatch', 'launcher.sh' ], cwd=sim_dir)
            process.wait()
        except Exception as e:
            print("  error while launching:", e)

shutil.copy(upth, os.path.join(root, "U.dat"))
settings["UDAT"] = "../U.dat"

if gpth is not None:
    if not os.path.isfile(gpth):
        print(f"wells geometry file {gpth} does not exist")
    settings["GEO"] = open(gpth, "r").read()

if params[0] == '':
    print("No setting specified: using default values")
    build_simulation('default', 'job_def', settings, launch=args.l)
    exit(0)

# generating wanted values for the varying parameter
values = [ float(params[1]) ]
if len(params) == 4:
    v0 = float(params[1])
    v1 = float(params[2])
    N = int(params[3])
    values = np.logspace(np.log(v0), np.log(v1), N, base=np.e, endpoint=True)
    values = np.round(values * 1000) / 1000

if params[0] in DistributionPlacer.available_placement_types:
    dtb = Distribution.load_from_file(upth)
    placer = DistributionPlacer(dtb)

# generating simulations
if is_T_res_dependent:

    settings["CHESS"] = "../" + settings["CHESS"]
    settings["UDAT"] = "../" + settings["UDAT"]
    T_res_m = np.logspace(-0.7, 0.7, 7)
    T_res = T_res_m * DistributionPlacer.T_res_ref  # h

    for value in values:

        name = f"{params[0]}_{value:.3f}"
        sim_dir = prepare_simulation_folder(name)

        if params[0] in DistributionPlacer.available_placement_types:
            placement_settings = {
                "type": params[0],
                "RC": value
            }
            if params[0] == "ORG": 
                placement_settings["IP_ratio"] = 1.5
            wells = placer.place(placement_settings, os.path.join(sim_dir, f"wells.png"))
            RC = value

        else:
            settings[params[0]] = value
            wells = DistributionPlacer.parse_geometry(settings["GEO"])
            RC = 21.8   # à changer pour s'adapter à la géométrie d'entrée

        for jm in range(len(T_res_m)):

            max_flow = build_flow_rates_from_voronoi(wells, RC, T_res[jm], os.path.join(sim_dir, f"flows.png") if jm == 0 else None)  # m3/h
            if max_flow <= 20:  # m3/h
                settings["GEO"] = DistributionPlacer.geometry_htc_string(wells)
                # settings["MAX_FLOW"] = max_flow
                build_simulation(f"{name}/m_{T_res_m[jm]:.2f}", f"{params[0][0:2]}{value:.0f}_{T_res_m[jm]:.2f}", settings, launch=False)

else:
    for i, value in enumerate(values):
        settings[params[0]] = value
        build_simulation(f"{params[0]}_{value}", f"{params[0][0:2]}_{i}", settings, launch=args.l and N <= 10)
