import datetime
import casacore.measures

class datetime_casacore(datetime.datetime):
    
    # TODO: add support other time codes than UTC
    measures = casacore.measures.measures()
    
    @classmethod
    def from_datetime(cls, dt):
        """Create from Python datetime object"""
        fmt = "%Y-%m-%d-T%H:%M:%S.%f"
        return cls.strptime(dt.strftime(fmt), fmt)
    
    def mjd_seconds(self):
        """Returns seconds since MJD epoch"""
        q = self.measures.get_value(self.epoch())
        assert len(q) == 1
        return q[0].get_value("s")
    
    def epoch(self):
        """Returns a casacore epoch measures object"""
        return self.measures.epoch("UTC", self.isoformat())
