#!/usr/bin/env python

from __future__ import division
from __future__ import absolute_import
from casacore.measures import measures
from .stationdata import RCUMode, XSTData, ACCData, AARTFAACData
from datetime import datetime
import sys
import re
import os.path
import logging
import argparse

def create_parser():
    parser = argparse.ArgumentParser()
    required = parser.add_argument_group('required arguments')
    exclusive = parser.add_mutually_exclusive_group()
    parser.add_argument("-c", "--antfield", type=str, help="Lofar station AntennaField.conf file", default="")
    parser.add_argument("-n", "--stationname", type=str, help="Station name for MS antenna and observation tables", default="")
    parser.add_argument("-t", "--starttime", type=str, help="Start time (centre point of first integration), YYYYMMDD_HHMMSS")
    required.add_argument("-r", "--rcumode", type=int, choices=RCUMode.valid_modes, required=True)
    parser.add_argument("-s", "--subband", type=int, choices=list(range(RCUMode.n_subband)), metavar='0..{}'.format(RCUMode.n_subband-1), default=-1)
    parser.add_argument("-i", "--integration", type=float, default=1.0)
    parser.add_argument("-d", "--direction", type=str, default=None, help="RA,DEC,epoch. The RA/DEC can be specified in a variety of ways acceptable by casacore measures, e.g.,0.23rad,2.1rad,J2000 or 19h23m23s,30d42m32s,J2000")
    exclusive.add_argument("-x", "--xst", help="File is an XST capture (default, unless filename is standard ACC format)", action="store_true")
    exclusive.add_argument("-a", "--acc", help="File is an ACC capture", action="store_true")
    exclusive.add_argument("-z", "--cal", help="File is an AARTFAAC .cal file", action="store_true")
    parser.add_argument("-q", "--quiet", help="Only display warnings and errors", action="store_true")
    parser.add_argument("indata", help="Input data file name", type=str)
    parser.add_argument("msname", help="Output Measurement Set name", type=str, nargs="?")
    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()
    if args.quiet:
        logging.basicConfig(format='%(levelname)s: %(message)s')
    else:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    assert os.path.exists(args.indata)

    # MS name
    if args.msname is None:
        if args.indata.endswith(".dat"):
            basename = args.indata[:-len(".dat")]
        else:
            basename = args.indata
        args.msname = basename + ".ms"

    # Direction
    me = measures()
    if args.direction != None:
        m0, m1, refer = args.direction.split(',')
        try:
            args.direction = me.direction(refer, m0, m1)
        except:
            logging.critical("Could not convert string {} to casacore direction".format(args.direction))
            logging.critical("    eg: 0.23rad,2.1rad,J2000 or 19h23m23s,30d42m32s,J2000 ...")
            sys.exit(1)

    # Start time
    if args.starttime != None:
        args.starttime = datetime.strptime(args.starttime, "%Y%m%d_%H%M%S")

    # XST / ACC
    if not args.xst and not args.acc and not args.cal:
        if re.match("^\d{8}_\d{6}_acc_512x192x192.dat$", os.path.basename(args.indata)):
            logging.info("Assuming data is ACC based on filename")
            args.acc = True
        else:
            logging.info("Data type not specified - assuming XST")

    # Convert
    if args.acc:
        station_data = ACCData(args.indata, args.rcumode, args.subband, args.antfield, args.starttime, args.direction, args.stationname)
    elif args.cal:
        station_data = AARTFAACData (args.indata, args.rcumode, args.subband, args.antfield, args.starttime, args.direction, args.stationname)
    else:
        station_data = XSTData(args.indata, args.rcumode, args.subband, args.integration, args.antfield, args.starttime, args.direction, args.stationname)

    station_data.write_ms(args.msname, args.stationname)
