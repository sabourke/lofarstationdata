from casacore.measures import measures
from casacore.quanta import quantity
from .meas_set import MeasurementSet
from . import antfield
import datetime
from datetime import timedelta
from .datetime_casacore import datetime_casacore
from .uvw import UVW
import numpy as np
import logging
import os.path
import re
import vistools.vismanip as vism


C = 299792458.0
DEFAULT_STATION_NAME = "LOFAR_STATION"


def channel_centre_frequencies(band_centre_frequency, n_channel, channel_width):
    """Return an array of frequencies centred on band_centre_frequency and spaced by channel_width"""
    return band_centre_frequency + channel_width * np.arange((1.0-n_channel)/2, (n_channel-1.0)/2+1, 1)


def num_baselines(n_ant, autos=False):
    """Returns the number of baselines for N antennas.
    autos specifies wither auto-correlations are included"""
    if autos:
        return int((n_ant + 1) * n_ant / 2)
    else:
        return int((n_ant - 1) * n_ant / 2)


class RCUMode(object):
    valid_modes = [3,5,6,7]
    n_subband = 512
    def __init__(self, mode):
        assert mode in self.valid_modes
        if mode == 3:
            self.band = "LBA"
            self.clock_frequency = 200e6
            self.freq0 = 0.0
        elif mode == 5:
            self.band = "HBA"
            self.clock_frequency = 200e6
            self.freq0 = 100e6
        elif mode == 6:
            self.band = "HBA"
            self.clock_frequency = 160e6
            self.freq0 = 160e6
        elif mode == 7:
            self.band = "HBA"
            self.clock_frequency = 200e6
            self.freq0 = 200e6
        else:
            raise RuntimeError("Unknown mode {}".format(mode))
        self.nyquist_frequency = self.clock_frequency / 2
        self.subband_width = self.nyquist_frequency / self.n_subband

    def subband_centre_frequency(self, subband):
        # TODO: do aliased subband numbers accend or decend in frequency?
        return self.freq0 + subband * self.subband_width


class XCStationData(object):
    _n_pol = 2 # Polarisations per antenna
    _n_channel = 1 # Frequencies per sub-band

    def __init__(self, datafile, rcu_mode, subband, integration_time, antfile="", start_time=None, direction=None, station_name=""):
        self._datafile = datafile
        self.subband = subband
        self.integration_time = integration_time
        self.rcu_mode = RCUMode(rcu_mode)
        self._set_frequency(subband)
        self.station_name = station_name
        self._set_antenna_field(antfile)
        self._set_raw_data (datafile)
        self._set_time(start_time)
        if direction == None:
            self.direction = measures().direction("AZELGEO", "0deg", "90deg")
        else:
            self.direction = direction

    def _start_time_from_filename(self):
        match = re.match("^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2}).*$", os.path.basename(self._datafile))
        if not match:
            raise ValueError("Start time not provided and could not deduce from file name")
        else:
            return datetime_casacore(*[int(x) for x in match.groups()])

    def _set_time(self, start_time, offset=0):
        if start_time == None:
            start_time = self._start_time_from_filename()
        time = []
        t_delta = timedelta(seconds=self.integration_time)
        t_offset = timedelta(seconds=offset)
        for i in range(self.n_time):
            t = start_time + i * t_delta + t_offset
            time.append(datetime_casacore.from_datetime(t))
        self._time = time

    @property
    def frequency(self):
        return self._frequency

    def _set_frequency(self, subband):
        if subband == -1:
            subband_list = range(RCUMode.n_subband)
        else:
            subband_list = [subband]
        frequency = []
        for sb in subband_list:
            frequency.append(channel_centre_frequencies(self.rcu_mode.subband_centre_frequency(sb),
                                                          self.n_channel,
                                                          self.rcu_mode.subband_width/self.n_channel))
        self._frequency = np.array(frequency)

    @property
    def wavelength(self):
        wl = np.empty_like(self._frequency)
        locs = (self._frequency != 0)
        wl[locs] = C / self._frequency[locs]
        wl[np.invert(locs)] = np.inf
        return wl

    @property
    def antenna_field(self):
        return self._antenna_field

    def _antenna_field_from_station_name(self):
        antfield = os.path.join(os.path.split(__file__)[0], "AntennaFields/{}-AntennaField.conf".format(self.station_name))
        if os.path.exists(antfield):
            return antfield
        else:
            raise ValueError("No AntennaField conf found for station: {}".format(self.station_name))

    def _set_antenna_field(self, antfile=""):
        if antfile == "":
            if self.station_name != "":
                antfile = self._antenna_field_from_station_name()
            else:
                raise ValueError("Cannot set AntennaField, antfile or station name should be set")
        self._antenna_field = antfield.from_file(antfile)
        self._position = np.array(self.antenna_field[self.rcu_mode.band][0])
        antenna_offsets = np.array(self.antenna_field[self.rcu_mode.band][1])[:,0,:]
        self._antenna_positions = antenna_offsets + self.position
        if self.station_name == "":
            station_name_match = re.match("^(?P<name>[A-Z]{2}\d{3})-AntennaField.conf$", os.path.basename(antfile))
            if station_name_match:
                self.station_name = station_name_match.group("name")
            else:
                self.station_name = DEFAULT_STATION_NAME

    @property
    def n_subband(self):
        return self.frequency.shape[0]

    @property
    def n_channel(self):
        return self._n_channel

    @property
    def n_pol(self):
        return self._n_pol

    @property
    def n_pol_out(self):
        return self.n_pol ** 2

    @property
    def n_ant(self):
        return len(self.antenna_field[self.rcu_mode.band][1])

    @property
    def n_baseline(self):
        return num_baselines(self.n_ant, autos=True)

    @property
    def raw_data(self):
        return self._raw_data

    def _set_raw_data(self, datafile):
        _raw_data = np.fromfile(datafile, dtype=np.complex128)
        self._raw_data = _raw_data.reshape((-1, self.n_ant, self.n_pol, self.n_ant, self.n_pol))

    @property
    def n_time(self):
        return self.raw_data.shape[0]

    @property
    def time(self):
        return self._time

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, value):
        self._direction = value
        self._uvw_valid = False
        self._data_valid = False

    @property
    def position(self):
        return self._position

    @property
    def antenna_positions(self):
        return self._antenna_positions

    def _calculate_uvw(self):
        uvw_machine = UVW(self.antenna_positions)
        uvw_machine.set_direction(self.direction)
        position = measures().position("ITRF", *[quantity(x, "m") for x in self.position])
        uvw_machine.set_position(position)
        self._uvw = np.empty(shape=(self.raw_data.shape[0],self.n_ant,self.n_ant,3), dtype=np.float64)
        for i,t in enumerate(self.time):
            uvw_machine.set_time(t.epoch())
            self._uvw[i] = uvw_machine()
        self._uvw_valid = True
        self._data_valid = False

    @property
    def uvw(self):
        if not self._uvw_valid:
            self._calculate_uvw()
        return self._uvw

    def _calculate_data(self):
        """Correct data for the geometric delay (w)"""
        w_shape = list(self.uvw.shape[:-1])
        w_shape.insert(2,1)
        w_shape.insert(4,1)
        w = self.uvw[:,:,:,2].reshape(w_shape)
        phase = np.empty(shape=w.shape, dtype=np.complex128)
        for i, wl in enumerate(np.atleast_1d(self.wavelength.squeeze())):
            phase[i] = np.exp(-2j * np.pi * w[i] / wl)
        self._data = self.raw_data * phase
        self._data_valid = True

    @property
    def data(self):
        if not self._data_valid:
            self._calculate_data()
        return self._data

    def packed_data(self):
        a1, a2 = np.triu_indices(self.n_ant)
        return np.swapaxes(self.data[:,a1,:,a2,:], 0, 1).reshape((-1,self.n_channel,self.n_pol_out))

    def packed_uvw(self):
        a1, a2 = np.triu_indices(self.n_ant)
        return self.uvw[:,a1,a2,:].reshape((-1,3))

    def write_ms(self, ms_name, station_name=""):
        """Write out Measurement Set"""
        logging.info("Creating Measurement Set")
        ms = MeasurementSet(ms_name)

        if station_name == "":
            station_name = self.station_name

        # MAIN table
        logging.info("Populating MAIN Table")
        n_rows = self.n_time * self.n_baseline
        ms.main.addrows(n_rows)
        ant1, ant2 = np.triu_indices(self.n_ant)
        ms.main.putcol("ANTENNA1", np.tile(ant1, self.n_time))
        ms.main.putcol("ANTENNA2", np.tile(ant2, self.n_time))
        ms.main.putcol("WEIGHT", np.ones(shape=(n_rows, self.n_pol_out), dtype=np.float64))
        ms.main.putcol("SIGMA", np.ones(shape=(n_rows, self.n_pol_out), dtype=np.float64))
        ms.main.putcol("INTERVAL", np.full((n_rows,), self.integration_time, dtype=np.float64))
        ms.main.putcol("EXPOSURE", np.full((n_rows,), self.integration_time, dtype=np.float64))
        time_mjd = np.array([t.mjd_seconds() for t in self.time])
        ms.main.putcol("TIME", np.repeat(time_mjd, self.n_baseline))
        ms.main.putcol("TIME_CENTROID", np.repeat(time_mjd, self.n_baseline))
        if self.n_subband > 1:
            ms.main.putcol("DATA_DESC_ID", np.repeat(np.arange(self.n_subband), self.n_baseline))
        else:
            ms.main.putcol("DATA_DESC_ID", np.zeros(shape=(self.n_time * self.n_baseline),dtype=np.int32))
        data = self.packed_data()
        ms.main.putcol("DATA", data)
        ms.main.putcol("FLAG", np.zeros(shape=data.shape, dtype="bool"))
        ms.main.putcol("UVW", self.packed_uvw())
        ms.main.putcolkeyword("UVW", "QuantumUnits", ["m","m","m"])
        ms.main.putcolkeyword("UVW", "MEASINFO", {"Ref": "J2000", "type": "uvw"})


        # ANTENNA table
        logging.info("Populating ANTENNA Table")
        ms.antenna.addrows(self.n_ant)
        ms.antenna[:] = {"TYPE": "GROUND-BASED", "DISH_DIAMETER": 2, "MOUNT": "X-Y", "STATION": station_name}
        ms.antenna.putcol("NAME", ["ANT{:03d}".format(i) for i in range(self.n_ant)])
        ms.antenna.putcol("POSITION", self.antenna_positions)

        # FEED table
        ms.feed.addrows(self.n_ant)
        logging.info("Populating FEED Table")
        ms.feed[:] = {"BEAM_OFFSET": np.zeros(shape=(2,2)), "POLARIZATION_TYPE": np.array(["X","Y"]),
                      "POL_RESPONSE": np.identity(2, dtype="complex64"),
                      "RECEPTOR_ANGLE": np.zeros(shape=(2,)), "BEAM_ID": -1, "FEED_ID": 0,
                      "INTERVAL": 0, "NUM_RECEPTORS": 2, "SPECTRAL_WINDOW_ID": -1, "TIME": time_mjd[0]}
        ms.feed.putcol("ANTENNA_ID", np.arange(self.n_ant))

        # SPECTRAL_WINDOW table
        logging.info("Populating SPECTRAL_WINDOW and DATA_DESCRIPTION Tables")
        ms.spectralWindow.addrows(self.n_subband)
        channel_bandwidth = np.full((self.n_channel,), self.rcu_mode.subband_width / self.n_channel)
        ms.spectralWindow[:] = {"MEAS_FREQ_REF": 1, "CHAN_WIDTH": channel_bandwidth, "EFFECTIVE_BW": channel_bandwidth,
                                "RESOLUTION": channel_bandwidth, "FLAG_ROW": False, "FREQ_GROUP": 0, "FREQ_GROUP_NAME": "Group 1",
                                "IF_CONV_CHAIN": 0, "NET_SIDEBAND": 1, "NUM_CHAN": self.n_channel, "TOTAL_BANDWIDTH": self.rcu_mode.subband_width}
        for i, channel_frequencies in enumerate(self.frequency):
            ms.spectralWindow[i] = {"CHAN_FREQ": channel_frequencies, "REF_FREQUENCY": channel_frequencies[0], "NAME": "SPW{:03d}".format(i)}

        # DATA_DESCRIPTION table
        ms.dataDescription.addrows(self.n_subband)
        ms.dataDescription.putcol("SPECTRAL_WINDOW_ID", np.arange(self.n_subband))

        # OBSERVATION table
        logging.info("Populating OBSERVATION Table")
        ms.observation.addrows(1)
        ms.observation[0] = {"TELESCOPE_NAME": station_name, "OBSERVER": "Default",
                             "RELEASE_DATE": time_mjd[0], "TIME_RANGE": np.array([time_mjd[0], time_mjd[-1]]),
                             "PROJECT": "Default", "SCHEDULE_TYPE": "", "FLAG_ROW": False}

        # POLARIZATION table
        logging.info("Populating POLARIZATION Table")
        ms.polarization.addrows(1)
        ms.polarization[0] = {"CORR_TYPE": np.array([9,10,11,12], dtype=np.int32), "CORR_PRODUCT": np.array([[0,0],[0,1],[1,0],[1,1]], dtype=np.int32), "NUM_CORR": self.n_pol_out}

        # FIELD table
        ms.field.addrows(1)
        logging.info("Populating FIELD Table")
        ms.field[0] = {"DELAY_DIR": np.array([[0.0,np.pi/2]]), "REFERENCE_DIR": np.array([[0.0,np.pi/2]]),
                       "PHASE_DIR": np.array([[self.direction["m0"]["value"], self.direction["m1"]["value"]]]),
                       "NAME": "Field0", "SOURCE_ID": -1, "TIME": time_mjd[0]}
        ms.field.putcolkeyword("PHASE_DIR", "QuantumUnits", [self.direction["m0"]["unit"], self.direction["m1"]["unit"]])
        ms.field.putcolkeyword("PHASE_DIR", "MEASINFO", {"Ref": self.direction["refer"], "type": self.direction["type"]})
        ms.field.putcolkeyword("DELAY_DIR", "QuantumUnits", ["rad", "rad"])
        ms.field.putcolkeyword("DELAY_DIR", "MEASINFO", {"Ref": "AZELGEO", "type": "direction"})
        ms.field.putcolkeyword("REFERENCE_DIR", "QuantumUnits", ["rad", "rad"])
        ms.field.putcolkeyword("REFERENCE_DIR", "MEASINFO", {"Ref": "AZELGEO", "type": "direction"})


class XSTData(XCStationData):
    pass


class ACCData(XCStationData):
    def __init__(self, datafile, rcu_mode, subband=-1, antfile="", start_time=None, direction=None, station_name=""):
        super(ACCData, self).__init__(datafile, rcu_mode, subband, 1.0, antfile, start_time, direction, station_name)

    def _set_raw_data(self, datafile):
        super(ACCData, self)._set_raw_data(datafile)
        if self.subband >= 0:
            # Single subband (integration) selected
            self._raw_data = self._raw_data[np.newaxis,self.subband]

    # TODO: Is the time in the ACC file name start time or end time?
    def _set_time(self, start_time):
        if self.subband >= 0:
            super(ACCData, self)._set_time(start_time, offset=self.subband-512)
        else:
            super(ACCData, self)._set_time(start_time, offset=-512)

class AARTFAACData (XCStationData):
    vis     = None # TransitVis object reference
    trilind = None
    acm     = None # Temporary store of a single ACM.

    def __init__(self, datafile, rcu_mode, subband=-1, antfile="", \
                start_time=None, direction=None, station_name=""):

        self.vis = vism.TransitVis (datafile)

        super(AARTFAACData, self).__init__(self.vis, rcu_mode, subband, \
            self.vis.dt.seconds, antfile, self.vis.tfilestart, direction, station_name)

        if self.trilind is None:
            self.trilind = np.tril_indices (self.n_ant)

        if self.acm is None:
            self.acm = np.zeros ( (self.n_ant, self.n_ant), dtype=np.complex64)


    # NOTE: We misappropriate the datafile parameter to pass the TransitVis
    # object. The superclass constructor assigns the datafile parameter to 
    # the passed TransitVis, so we reassign the data filename here.
    def _set_raw_data (self, datafile):
        ind = 0
        self.datafile = datafile.fname
        self._raw_data = np.zeros ( (1, self.n_ant, self.n_pol, \
                                self.n_ant, self.n_pol), dtype=np.complex64)
        if self.acm is None:
            self.acm = np.zeros ( (self.n_ant, self.n_ant), dtype=np.complex64)
            
        if self.trilind is None:
            self.trilind = np.tril_indices (self.n_ant)

        # while ind < vis.nrec:
        try:
            datafile.read(None)
            self.acm[self.trilind] = np.conjugate (datafile.vis[0])
            self.acm = self.acm.transpose()
            self.acm[self.trilind] = datafile.vis[0]
            self._raw_data [ind, :,0,:,0] = self.acm 
        except:
            print 'Exception in reading from raw visibility file.'
            # break
