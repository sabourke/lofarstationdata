from __future__ import print_function
from lofarstation.uvw import UVW
from lofarstation import antfield
import numpy as np
from datetime import datetime
from casacore.measures import measures
import sys

ants = antfield.from_file("SE607-AntennaField.conf")
ref_pos = np.array(ants["LBA"][0])
ant_pos = np.array(ants["LBA"][1])[:,0,:] + ref_pos

me = measures()
time = me.epoch("UTC", "2017-01-01-12:00:00")

uvw = UVW(ant_pos)
uvw.set_position(ref_pos)
uvw.set_direction(["AZELGEO", "0deg", "90deg"])
uvw.set_time(time)
print(uvw[23,30])

uvw.set_direction(["J2000", "20h00m", "30d23m"])
uvw.set_time(datetime(2017, 1, 1, 12, 30, 0))
print(uvw[23,30])

uvw_arr = uvw()
print(uvw_arr.shape)

baseline_uvw = uvw.packed()
print(baseline_uvw.shape)
