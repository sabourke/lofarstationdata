from casacore.measures import measures, is_measure
from casacore.quanta import quantity
from .datetime_casacore import datetime_casacore
import numpy as np


class UVW(object):
    _measures = measures()

    """Calculates J2000 baselines UVWs"""
    def __init__(self, antenna_positions):
        self._measures = measures()
        self.antenna_positions = antenna_positions
        self._properties_set = {}
        self._up_to_date = False

    @property
    def antenna_positions(self):
        return self._antenna_positions
    
    @property
    def n_ant(self):
        return len(self.antenna_positions)
    
    @antenna_positions.setter
    def antenna_positions(self, antenna_positions):
        self._antenna_positions = antenna_positions
        x = quantity(self.antenna_positions[:,0], "m")
        y = quantity(self.antenna_positions[:,1], "m")
        z = quantity(self.antenna_positions[:,2], "m")
        self._itrf_baselines = self._measures.baseline('itrf', x, y, z)
        self._up_to_date = False

    def set_time(self, value):
        if is_measure(value):
            self.set_measure(value)
        elif isinstance(value, datetime_casacore):
            self.set_measure(value.epoch())
        elif isinstance(value, datetime):
            self.set_measure(datetime_casacore.from_datetime(value).epoch())
        elif isinstance(value, float):
            self.set_measure(self._measures.epoch("UTC", quantity(value, "s")))
        else:
            raise TypeError("Unsupported type {} in set_time".format(type(value)))

    @classmethod
    def gen_position(cls, value):
        if hasattr(value, "__len__"):
            if len(value) == 3:
                return cls._measures.position("ITRF", *[quantity(x, "m") for x in value])
        raise TypeError("Could not convert {} to position".format(value))
    
    def set_position(self, value):
        if is_measure(value):
            self.set_measure(value)
        else:
            self.set_measure(self.gen_position(value))
    
    @classmethod
    def gen_direction(cls, value):
        if isinstance(value, str) \
                and value in cls._measures.list_codes(cls._measures.direction())["extra"]:
            return cls._measures.direction(value)
        elif hasattr(value, "__len__") \
                and len(value) == 3 \
                and value[0] in cls._measures.list_codes(cls._measures.direction())["normal"]:
            return cls._measures.direction(*value)
        raise TypeError("Could not convert {} to direction".format(value))
    
    def set_direction(self, value):
        if is_measure(value):
            self.set_measure(value)
        else:
            self.set_measure(self.gen_direction(value))
    
    def set_measure(self, value):
        self._properties_set[value["type"]] = value
        self._up_to_date = False
    
    def _update(self):
        """Check that the necessary frame information is set and then calculate J2000 baselines."""
        required_attributes = ["epoch", "direction"]
        for attribute in required_attributes:
            if attribute not in self._properties_set:
                raise ValueError("Attributes: {} must be all set".format(required_attributes))
        if "position" not in self._properties_set:
            antenna_mean = self.antenna_positions.mean(axis=0)
            self.set_measure(self._measures.position("ITRF", *[quantity(x, "m") for x in antenna_mean]))
        self._measures.do_frame(self._properties_set["epoch"])
        self._measures.do_frame(self._properties_set["direction"])
        self._measures.do_frame(self._properties_set["position"])
        self._uvw0 = np.array(self._measures.to_uvw(self._itrf_baselines)["xyz"].get_value("m")).reshape((-1,3)) # to_uvw converts to J2000
        self._up_to_date = True
    
    def __getitem__(self, i2):
        """Returns the J2000 UVW for the two antennas specified"""
        if not self._up_to_date:
            self._update()
        return self._uvw0[i2[0]] - self._uvw0[i2[1]]
    
    def __call__(self):
        """Returns the full matrix of UVWs"""
        if not self._up_to_date:
            self._update()
        return self._uvw0.reshape((-1,1,3)) - self._uvw0.reshape((1,-1,3))
    
    def packed(self):
        """Returns an array of lenght N_baselines of UVWs for the upper triangular correlation matrix"""
        return self()[np.triu_indices(self.n_ant)]
