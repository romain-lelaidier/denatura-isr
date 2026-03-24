# generate simulation configurations

import os
import argparse
import shutil
import numpy as np
import subprocess as sp
import re

# input parameters
parser = argparse.ArgumentParser()
parser.add_argument("-r", help="Simulation root")
parser.add_argument("-g", help="Wells geometry file path")
parser.add_argument("-u", help="Uranium distribution file path")
parser.add_argument('-s', help="Varying setting")
parser.add_argument('-f', action="store_true", help="Force overwrite")
parser.add_argument('-l', action="store_true", help="Launch immediately")
args = parser.parse_args()

root = args.r
gpth = args.g
upth = args.u
s = args.s or ""

if root is None or gpth is None or upth is None:
    parser.print_usage()
    exit(0)

# checking files
if not os.path.isdir(root):
    print(f"folder {root} does not exist ; creating it")
    os.mkdir(root)

if not os.path.isfile(gpth):
    print(f"wells geometry file {gpth} does not exist")

if not os.path.isfile(upth):
    print(f"uranium distribution file {upth} does not exist")

LAUNCHER_STR = open("./utils/launcher_str", "r").read()
CONFIG_STR = open("./utils/config_str", "r").read()

shutil.copy(upth, os.path.join(root, "U.dat"))
CONFIG_STR = CONFIG_STR.replace("XXUDATXX", "../U.dat")

geometry = open(gpth, "r").read()
CONFIG_STR = CONFIG_STR.replace("XXGEOXX", geometry)

settings = {
    'MAX_FLOW': 10,     # max injection/production rate (m3/h) on any well
    'GOETHITE': 0.3,    # mmolal
    'FE2': 1,           # g/l
    'FE3': 100          # mg/l      # 50 à KATCO
}
params = s.split(',')

def build_simulation(config_str, name, jobname, settings, launch=False):
    print(f"building simulation {name} with settings {settings}")

    sim_dir = os.path.join(root, name)
    if os.path.isdir(sim_dir):
        if args.f:
            print(f"  /!\\ deleting {sim_dir}")
            shutil.rmtree(sim_dir)
        else:
            print(f"  folder {sim_dir} already exists ; skipping")
            return
    
    os.mkdir(sim_dir)
    config_path = os.path.join(sim_dir, "config.htc")
    launcher_path = os.path.join(sim_dir, "launcher.sh")

    for key, value in settings.items():
        config_str = config_str.replace(f"XX{key}XX", str(value))

    # replacing flows
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
        
    open(config_path, "w").write(config_str_n)
    open(launcher_path, "w").write(LAUNCHER_STR.replace("XXJOBNAMEXX", jobname))

    if launch:
        print("  launching HYTEC node")
        try:
            process = sp.Popen([ 'sbatch', 'launcher.sh' ], cwd=sim_dir)
            process.wait()
        except Exception as e:
            print("  error while launching:", e)

if params[0] == '':
    print("No setting specified: using default values")
    build_simulation(CONFIG_STR, 'default', 'job_def', settings, launch=args.l)

else:
    if params[0] in settings:
        v0 = float(params[1])
        v1 = float(params[2])
        N = int(params[3])
        values = np.logspace(np.log(v0), np.log(v1), N, base=np.e, endpoint=True)
        values = np.round(values * 1000) / 1000
        for i, value in enumerate(values):
            settings[params[0]] = value
            build_simulation(CONFIG_STR, f"{params[0]}_{value}", f"{params[0][0:5]}_{i}", settings, launch=args.l and N <= 10)

    else:
        print(f"setting {params[0]} not recognized ; available are {settings.keys()} ; aborting")
        exit(0)