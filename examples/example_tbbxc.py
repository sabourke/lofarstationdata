#!/usr/bin/env python

from lofarstation.stationdata import TBBXCData
from datetime import datetime
from casacore.measures import measures

zenith_f24 = measures().direction("J2000", "01h01m51s", "+57d07m52s")
t0_f24 = datetime(2017,2,24, 13,56,35, 135000)

sd = TBBXCData("feb24_0.05s_avg.npy",
               station_name="SE607", rcu_mode=3,
               integration_time=0.5, start_time=t0_f24,
               direction=zenith_f24)

sd.write_ms("tbb1.ms")
