lofarstationdata: Python interface to Lofar single-station and AARTFAAC cross-correlation data
==============================================================================================

This python module provides easy access to Lofar cross correlated station
data (XST & ACC) and AARTFAAC data. UVWs and data corrected for geometric
delay are automatically calculated. It can also write the data out as a
Measurement Set. A command line utility is included for converting to
Measurement Set.

This was written for international stations but might also work for Dutch
HBA stations. It would need modification to work with Dutch LBA -
it doesn't know about the configurations (inner, outer, sparse, etc) for
the Dutch LBA fields.

Antenna positions are obtained from Lofar's AntennaField.conf files
([link](https://svn.astron.nl/LOFAR/trunk/MAC/Deployment/data/StaticMetaData/AntennaFields/)).
A set is included with this package which will be used by default as
long as you specify the station name.

Dependencies
------------

* Python 2.7 or higher
* [python-casacore](https://github.com/casacore/python-casacore) (which in turn depends on casacore)
* casacore-data (see below)
* NumPy

Casacore data:

If you want to maintain your own casacore data directory or use the one
from NRAO's Casa package you can specify its location in ```~/.casarc```
Eg:

    measures.directory: /opt/casa-release-4.7.0-el7/data

Installation
------------

If you're not doing a system wide install the easiest way to install
is with pip:

    pip install --user git+https://github.com/sabourke/lofarstationdata

if you don't have pip:

    wget https://bootstrap.pypa.io/get-pip.py
    python get-pip.py --user

You might need to add ```~/.local/bin``` to your ```PATH``` to use the ```lofar-station-ms```
converter utility.

Alternatively, for a system wide install (requires write access to Python's module directory):

    pip install git+https://github.com/sabourke/lofarstationdata

Usage
-----

The Measurement Set conversion tool is called lofar-station-ms:

    $ lofar-station-ms --help
    usage: lofar-station-ms [-h] [-c ANTFIELD] [-n STATIONNAME] [-t STARTTIME] -r
                            {3,5,6,7} [-s 0..511] [-i INTEGRATION] [-d DIRECTION]
                            [-x | -a | -z] [-q]
                            indata [msname]
    
    positional arguments:
      indata                Input data file name
      msname                Output Measurement Set name
    
    optional arguments:
      -h, --help            show this help message and exit
      -c ANTFIELD, --antfield ANTFIELD
                            Lofar station AntennaField.conf file
      -n STATIONNAME, --stationname STATIONNAME
                            Station name for MS antenna and observation tables
      -t STARTTIME, --starttime STARTTIME
                            Start time (centre point of first integration),
                            YYYYMMDD_HHMMSS
      -s 0..511, --subband 0..511
      -i INTEGRATION, --integration INTEGRATION
      -d DIRECTION, --direction DIRECTION
                            RA,DEC,epoch. The RA/DEC can be specified in a variety
                            of ways acceptable by casacore measures,
                            e.g.,0.23rad,2.1rad,J2000 or 19h23m23s,30d42m32s,J2000
      -x, --xst             File is an XST capture (default, unless filename is
                            standard ACC format)
      -a, --acc             File is an ACC capture
      -z, --aart            File is an AARTFAAC .cal or .vis file. In case of a
                            raw correlator .vis file, please specify the subband
                            number via the -s option. In case of a .cal file, this
                            is extracted from the header. Please also specify the
                            array name via -n [A6,A12]
      -q, --quiet           Only display warnings and errors
    
    required arguments:
      -r {3,5,6,7}, --rcumode {3,5,6,7}

Example:

    lofar-station-ms -r 3 -s 307 -n SE607 20170121_085835_xst.dat test1.ms

Python Examples
---------------

There is a directory example code and a XST sample in the ```examples```
subdirectory (an ACC was not included because of their size). These will
not be installed with ```pip``` so you need to clone the repository to
get them:

    git clone https://github.com/sabourke/lofarstationdata

ACC Example:

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
    print sd.data.shape
    sd.write_ms("CasA.ms")
    
XST Example:

    from lofarstation.stationdata import XSTData
    import matplotlib.pyplot as plt
    
    sd = XSTData("20151122_125835_xst.dat", station_name="SE607",
                 rcu_mode=3, subband=307, integration_time=1.0)
    
    # Plot UV coverage. No direction was specified, default is zenith
    uvw = sd.uvw.reshape((-1,3)) # Standard array shape is N_time * N_ant * N_ant * 3
    plt.gca().set_aspect('equal', adjustable='box')
    plt.plot(uvw[:,0], uvw[:,1], '.')
    plt.show()
    
    # Set direction and plot again
    from casacore.measures import measures
    sd.direction = measures().direction("AZEL", "45deg", "30deg")
    uvw = sd.uvw.reshape((-1,3))
    plt.plot(uvw[:,0], uvw[:,1], '.')
    plt.show()
