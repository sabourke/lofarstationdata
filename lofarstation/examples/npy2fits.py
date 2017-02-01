#!/usr/bin/env python

from astropy.io import fits
import numpy as np
import sys

npy = np.load(sys.argv[1])
hdu = fits.PrimaryHDU(npy)
fits.HDUList([hdu]).writeto(sys.argv[2])
