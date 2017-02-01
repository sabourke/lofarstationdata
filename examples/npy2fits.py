#!/usr/bin/env python

from __future__ import print_function
from astropy.io import fits
import numpy as np
import sys

def npy2fits(npyf, fitsf):
    npy = np.load(npyf)
    hdu = fits.PrimaryHDU(npy)
    fits.HDUList([hdu]).writeto(fitsf)

def main():
    if len(sys.argv) != 3:
        print("Usage: {} <in_npy> <out_fits>".format(sys.argv[0]), file=sys.stderr)
        sys.exit()
    npy2fits(sys.argv[1], sys.argv[2])

if __name__ == "__main__":
    main()
