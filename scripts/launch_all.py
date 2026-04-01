import os
import subprocess as sp
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-r", help="Root")
args = parser.parse_args()
rootdir = args.r

if rootdir is None:
    parser.print_help()
    exit(0)

if not os.path.exists(rootdir):
    print(f"folder {rootdir} does not exist ; aborting")
    exit(0)

i = 0
for root, _, files in os.walk(rootdir):
    if "launcher.sh" in files:
        try:
            print(f"launching {root}")
            process = sp.Popen([ 'sbatch', 'launcher.sh' ], cwd=root)
            process.wait()
            i += 1
            print(f"success ({i})")
        except Exception as e:
            print("  error while launching:", e)