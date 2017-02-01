from lofarstation.stationdata import XSTData
from casacore.measures import measures
import matplotlib.pyplot as plt

sd = XSTData("20151122_125835_xst.dat", station_name="SE607",
             rcu_mode=3, subband=307, integration_time=1.0)

uvw = sd.uvw.reshape((-1,3))
plt.gca().set_aspect('equal', adjustable='box')
plt.plot(uvw[:,0], uvw[:,1], '.')
plt.show()

sd.direction = measures().direction("AZEL", "45deg", "30deg")
uvw = sd.uvw.reshape((-1,3))
plt.plot(uvw[:,0], uvw[:,1], '.')
plt.show()
