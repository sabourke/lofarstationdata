#!/usr/bin/env python

"""Read Lofar AntennaField conf files.
The "centos7" format files are not supported."""

from __future__ import print_function
import sys
import json
import re

def multi_dim(data, shape, typ=float):
    """Reshape 'data' list into a multi dimensional list with the given shape
    conv is a function that is run on each element. Eg. to convert string to float"""
    ret = []
    if len(shape) == 1:
        # We are on the final axis so read and return the required elements
        for i in range(shape[0]):
            ret.append(typ(data[0]))
            del data[0]
    else:
        for i in range(shape[0]):
            ret.append(multi_dim(data, shape[1:], typ))
    return ret


shape_re = re.compile("\((?P<start>\d+),(?P<end>\d+)\)")
def read_dim(s):
    """Hack to read new blitz format dimensions"""
    match = shape_re.match(s)
    if match:
        return int(match.groupdict()["end"]) - int(match.groupdict()["start"]) + 1
    else:
        raise ValueError("Could not parse {}".format(s))

def read_array(stream):
    str_data = stream.readline().rstrip('\n')
    if str_data == "":
        raise ValueError
    while ']' not in str_data:
        str_data = str_data + ' ' + stream.readline().rstrip('\n')
    shape, str_data = str_data.split('[')
    str_data, empty = str_data.split(']')
    assert empty == ''
    str_data = [x for x in str_data.split(' ') if x != '']
    try:
        shape = [read_dim(s.strip()) for s in shape.split('x')]
    except ValueError:
        shape = [int(s.strip(' ')) for s in shape.split('x')]
    arr = multi_dim(str_data, shape)
    assert len(str_data) == 0
    return arr

def read_positions(stream):
    positions = [read_array(stream)] # reference position
    try:
        # dipole positions, not provided for HBA "ears" in core station
        positions.append(read_array(stream))
    except ValueError:
        pass
    return positions

def from_file(filename):
    stream = open(filename)
    AntennaField = {"NORMAL_VECTOR": {}, "ROTATION_MATRIX": {}}
    line = stream.readline()
    while line != "":
        while line == "\n" or line.startswith('#'):
            line = stream.readline()
        if "NORMAL_VECTOR" in line or "ROTATION_MATRIX" in line:
            arr_name, band = line.split()
            AntennaField[arr_name][band] = read_array(stream)
        else:
            band = line.rstrip('\n')
            AntennaField[band] = read_positions(stream)
        line = stream.readline()
    return AntennaField

if __name__ == "__main__":
    print(json.dumps(from_file(sys.argv[1])))
