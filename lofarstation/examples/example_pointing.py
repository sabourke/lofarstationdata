#!/usr/bin/env python

from lofarstation.stationdata import ACCData
from casacore.measures import measures

CasA = measures().direction("J2000", "23h23m26s", "+58d48m00s")
CygA = measures().direction("J2000", "19h59m28.3566s", "+40d44m02.096s")

sd = ACCData("20161231_133057_acc_512x192x192.dat",
             station_name="SE607", rcu_mode=3)

# Print time, freq, flux in the direction of CygA
sd.direction = CygA
for i in range(sd.n_time):
    print sd.time[i], sd.frequency[i][0], sd.data[i].mean().real

# Write a MS centred on CasA
sd.direction = CasA
sd.write_ms("CasA.ms")
