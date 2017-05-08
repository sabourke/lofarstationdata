#!/usr/bin/env python

import numpy as np

DEFAULT_N_RCU = 192
DEFAULT_N_FREQ = 512

class stationcal(object):
    def __init__(self, filename, n_freq=DEFAULT_N_FREQ, n_rcu=DEFAULT_N_RCU):
	self.n_freq = n_freq
	self.n_rcu = n_rcu
        with open(filename) as self._inf:
            self.header = self._read_header()
            self.cal_data = self._read_cal_data()

    def _read_header(self):
        header = []
        assert self._inf.readline() == "HeaderStart\n"
        line = self._inf.readline()
        while line != "HeaderStop\n":
            header.append(line)
            line = self._inf.readline()
        return header

    def _read_cal_data(self):
        cal_data = np.fromfile(self._inf, dtype=np.complex128, count=(self.n_freq*self.n_rcu))
        return cal_data.reshape((self.n_freq,self.n_rcu))
    
    def header_val(self, key):
        for line in self.header:
            try:
                line_key, line_val = [s.strip() for s in line.split("=")]
            except ValueError:
                continue
            if line_key == key:
                return line_val
        else:
            return ""

def main():
    import matplotlib.pyplot as plt
    import sys

    scal = stationcal(sys.argv[1])
    print "Station:", scal.header_val("CalTableHeader.Observation.Station")
    print "RCU mode:", scal.header_val("CalTableHeader.Observation.Mode")
    print "Obs date:", scal.header_val("CalTableHeader.Observation.Date")

    # Plot phases
    for g in scal.cal_data.T:
        plt.plot(np.arctan2(g.imag, g.real))
    plt.show()
    
    # Plot amplitudes
    for g in scal.cal_data.T:
        plt.plot(abs(g))
    plt.show()

if __name__ == "__main__":
    main()
