#!/usr/bin/env python

from __future__ import print_function
from lofarstation.stationdata import XSTData
from casacore.measures import measures

CasA = measures().direction("J2000", "23h23m26s", "+58d48m00s")
CygA = measures().direction("J2000", "19h59m28.3566s", "+40d44m02.096s")
zenith = measures().direction("J2000", "17h50m52.083633s", "+57d13m19.563213s")

sd = XSTData("20151122_125835_xst.dat", subband=307, rcu_mode=3,
             station_name="SE607", integration_time=1.0, direction=zenith)

print(sd.time[0])
print("{} MHz".format(sd.frequency / 1e6))
sd.write_ms("xst1.ms")

sd.set_station_cal("CalTable-SE607-mode3-2015.10.07.dat")
sd.write_ms("xst1-cal.ms")
