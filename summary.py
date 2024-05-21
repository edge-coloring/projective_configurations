# %%
import glob
import re
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("logDir")
parser.add_argument("outputPath")
args = parser.parse_args()

#
# Example)
# python3 summary.py reducible/log reducible/summary.csv
# python3 summary.py K1/log K1/summary.csv
# python3 summary.py K2/log K2/summary.csv
# python3 summary.py imply1_star/log imply1_star/summary.csv
# python3 summary.py imply2_star/log imply2_star/summary.csv
# 

xPattern = re.compile(r"critical")
dPattern = re.compile(r"D\-reducible!")
cPattern = re.compile(r"Contracted:([0-9 ,]+)")
nPattern = re.compile(r"not C\-reducible.")
with open(args.outputPath, "w") as sum:
    for path in sorted(glob.glob(os.path.join(args.logDir, "*.log"))):
        name = os.path.splitext(os.path.basename(path))[0]
        with open(path, "r") as f:
            finished = False
            conts = None
            error = False
            for line in f:
                if xPattern.search(line):
                    error = True
                    break
                if dPattern.search(line):
                    conts = []
                    break
                m = cPattern.search(line)
                if m:
                    conts = list(map(lambda s: s.strip(), m.group(1).split(",")))
                    break
                if nPattern.search(line):
                    finished = True
            state = "X" if error else ("N" if finished else "R") if conts == None else "D" if conts == [] else "C"
            size = -1 if conts == None else len(conts)
            vs = "-" if state!="C" else "\"" + "+".join(conts) + "\""
            sum.write(f"{path},{state},{size},{vs}\n")