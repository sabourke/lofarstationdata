#!/usr/bin/env python

from __future__ import print_function
from lofarstation.stationdata import XSTData

sd = XSTData("20151122_125835_xst.dat", subband=307, rcu_mode=3,
             station_name="SE607", integration_time=1.0)
print(sd.time[0])
print("{} MHz".format(sd.frequency / 1e6))
sd.write_ms("xst1.ms")
