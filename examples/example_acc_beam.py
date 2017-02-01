#!/usr/bin/env python

from lofarstation.stationdata import ACCData
from casacore.measures import measures
import glob
import sys
import numpy as np

CasA = measures().direction("J2000", "23h23m26s", "+58d48m00s")
#CygA = measures().direction("J2000", "19h59m28.3566s", "+40d44m02.096s")

def beam_from_acc_dir(accdir, rcu, outnpy):
    dyn_spec = []
    for accfile in sorted(glob.glob("{}/*_acc_*.dat".format(accdir))):
        acc = ACCData(accfile, station_name="SE607", rcu_mode=rcu, direction=CasA)
        dyn_spec.append(acc.data.reshape((acc.data.shape[0],-1)).mean(axis=1).real)
        print(accfile)
    dyn_spec = np.array(dyn_spec)
    np.save(outnpy, dyn_spec)

def main():
    if len(sys.argv) != 4:
        print >> sys.stderr, "Usage: %s <acc_directory> <rcu> <outnpy>" % sys.argv[0]
        sys.exit()
    dirname, rcu, outfile = sys.argv[1:]
    rcu = int(rcu)
    beam_from_acc_dir(dirname, rcu, outfile)

if __name__ == "__main__":
    main()
